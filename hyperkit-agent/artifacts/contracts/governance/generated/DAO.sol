// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Votes.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/governance/Governor.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorSettings.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorTimelockControl.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorVotes.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorVotesQuorumFraction.sol";
import "@openzeppelin/contracts/governance/TimelockController.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

/**
 * @title GDAOToken
 * @author HyperDAO Team
 * @notice The governance token for HyperDAO, granting voting rights to holders.
 * @dev This is an ERC20 token with snapshot and delegation capabilities provided by ERC20Votes.
 * The contract owner can mint new tokens. Ownership should be transferred to the DAO (via Timelock) after setup.
 */
contract GDAOToken is ERC20, ERC20Burnable, ERC20Votes, Ownable {
    /**
     * @notice Constructs the GDAO token contract.
     * @param initialOwner The address that will receive the initial supply and contract ownership.
     */
    constructor(address initialOwner)
        ERC20("HyperDAO Governance Token", "GDAO")
        Ownable(initialOwner)
    {
        // Mint an initial supply of 1,000,000 GDAO to the deployer.
        _mint(initialOwner, 1_000_000 * 10**decimals());
    }

    /**
     * @notice Mints new tokens.
     * @dev Can only be called by the current owner. It is recommended to transfer ownership
     * to the DAO's Timelock contract to allow governance to control token supply.
     * @param to The address to mint tokens to.
     * @param amount The amount of tokens to mint.
     */
    function mint(address to, uint256 amount) public virtual onlyOwner {
        _mint(to, amount);
    }

    // The following functions are overrides required by Solidity.

    /**
     * @dev Hook that is called before any token transfer. This is used by ERC20Votes to
     * create snapshots of balances for voting.
     */
    function _update(address from, address to, uint256 value)
        internal
        override(ERC20, ERC20Votes)
    {
        super._update(from, to, value);
    }

    function nonces(address owner)
        public
        view
        override(ERC20Permit, Nonces)
        returns (uint256)
    {
        return super.nonces(owner);
    }
}

/**
 * @title HyperDAO
 * @author HyperDAO Team
 * @notice The main governance contract for the HyperDAO ecosystem.
 * @dev This contract manages the full proposal lifecycle: creation, voting, queuing, and execution.
 * It uses a GDAOToken (ERC20Votes) for voting power, a TimelockController for delayed execution,
 * and features a 30% quorum and a 60% approval threshold.
 *
 * --- DEPLOYMENT AND SETUP ---
 * 1. Deploy GDAOToken, transferring initial supply to the DAO founders/community.
 * 2. Deploy TimelockController with:
 *    - minDelay: 172800 (48 hours).
 *    - proposers: [address(0)] (initially, will be updated).
 *    - executors: [address(0)] (allows anyone to execute a passed proposal).
 *    - admin: deployer's address.
 * 3. Deploy this HyperDAO contract, providing the addresses of the GDAOToken and TimelockController.
 * 4. Configure roles in TimelockController:
 *    - Grant PROPOSER_ROLE to this HyperDAO contract address.
 *    - Grant CANCELLER_ROLE to this HyperDAO contract address.
 *    - Revoke the deployer's admin access by calling `renounceRole` for the TIMELOCK_ADMIN_ROLE.
 * 5. Transfer ownership of any controlled contracts (e.g., Treasury, GDAOToken) to the TimelockController address.
 */
contract HyperDAO is
    Governor,
    GovernorSettings,
    GovernorTimelockControl,
    GovernorVotes,
    GovernorVotesQuorumFraction,
    AccessControl
{
    /// @dev Role for addresses that can cancel proposals, in addition to the proposer.
    bytes32 public constant CANCELLER_ROLE = keccak256("CANCELLER_ROLE");

    // --- Governance Parameters ---
    // Note: Block times can vary. This assumes a 12-second block time.
    // 1 block voting delay.
    uint256 private constant VOTING_DELAY_BLOCKS = 1;
    // 7 day voting period. (7 * 24 * 60 * 60) / 12 = 50400 blocks.
    uint256 private constant VOTING_PERIOD_BLOCKS = 50400;
    // Proposal threshold: 100,000 GDAO.
    uint256 private constant PROPOSAL_THRESHOLD_GDAO = 100_000 * 1e18;
    // Quorum: 30% of total GDAO supply.
    uint256 private constant QUORUM_PERCENTAGE = 30;

    /**
     * @notice Constructs the HyperDAO governance contract.
     * @param _token The address of the GDAO governance token (must implement IVotes).
     * @param _timelock The address of the TimelockController contract.
     * @param _admin The address to be granted initial admin and canceller roles.
     */
    constructor(
        IVotes _token,
        TimelockController _timelock,
        address _admin
    )
        Governor("HyperDAO")
        GovernorSettings(
            VOTING_DELAY_BLOCKS,
            VOTING_PERIOD_BLOCKS,
            PROPOSAL_THRESHOLD_GDAO
        )
        GovernorTimelockControl(_timelock)
        GovernorVotes(_token)
        GovernorVotesQuorumFraction(QUORUM_PERCENTAGE)
    {
        _setupRole(DEFAULT_ADMIN_ROLE, _admin);
        _setupRole(CANCELLER_ROLE, _admin);
    }

    /**
     * @notice Returns the current state of a proposal, with a custom 60% approval threshold.
     * @dev Overrides the default `state` function to add a check:
     * `forVotes / (forVotes + againstVotes) >= 60%`.
     * The proposal is only `Succeeded` if it meets quorum, simple majority, and this 60% threshold.
     * @param proposalId The ID of the proposal to check.
     * @return The proposal's current state.
     */
    function state(uint256 proposalId)
        public
        view
        override(Governor, IGovernor)
        returns (ProposalState)
    {
        ProposalState status = super.state(proposalId);

        // If the proposal has not yet reached the 'Succeeded' state by default checks,
        // (e.g., still active, defeated by 'no' votes, canceled), return the status as is.
        if (status != ProposalState.Succeeded) {
            return status;
        }

        // Default 'Succeeded' state means: voting is over, quorum is met, and forVotes > againstVotes.
        // Now, we apply our custom 60% approval threshold.
        (
            uint256 againstVotes,
            uint256 forVotes,
            /* uint256 abstainVotes */
        ) = proposalVotes(proposalId);

        // To avoid floating-point math, we check if `forVotes * 100 >= (forVotes + againstVotes) * 60`.
        // This simplifies to: `forVotes * 5 >= (forVotes + againstVotes) * 3`.
        if (forVotes * 5 < (forVotes + againstVotes) * 3) {
            // If the threshold is not met, the proposal is considered defeated.
            return ProposalState.Defeated;
        }

        // If the threshold is met, the proposal remains 'Succeeded'.
        return ProposalState.Succeeded;
    }

    /**
     * @notice Cancels a proposal.
     * @dev Overrides the default `cancel` function to restrict cancellation to the original
     * proposer or an address with the CANCELLER_ROLE.
     * @param targets The array of target addresses for the proposal's actions.
     * @param values The array of ETH values to be sent with the actions.
     * @param calldatas The array of calldata for the actions.
     * @param descriptionHash The keccak256 hash of the proposal's description.
     * @return The ID of the cancelled proposal.
     */
    function cancel(
        address[] memory targets,
        uint256[] memory values,
        bytes[] memory calldatas,
        bytes32 descriptionHash
    ) public override(Governor, IGovernor) returns (uint256) {
        uint256 proposalId = hashProposal(
            targets,
            values,
            calldatas,
            descriptionHash
        );
        address proposer = proposalProposer(proposalId);

        // A proposal can only be cancelled by its proposer or a designated canceller.
        require(
            msg.sender == proposer || hasRole(CANCELLER_ROLE, msg.sender),
            "HyperDAO: sender is not proposer or canceller"
        );

        return super.cancel(targets, values, calldatas, descriptionHash);
    }

    /**
     * @notice Creates a new proposal.
     * @dev The `propose` function is inherited from the OpenZeppelin Governor contract.
     * Voters can then vote on the proposal.
     * @param targets The array of target addresses for the proposal's actions.
     * @param values The array of ETH values to be sent with the actions.
     * @param calldatas The array of calldata for the actions (function signatures and arguments).
     * @param description A human-readable description of the proposal.
     * @return The ID of the newly created proposal.
     */
    function propose(
        address[] memory targets,
        uint256[] memory values,
        bytes[] memory calldatas,
        string memory description
    ) public override(Governor, IGovernor) returns (uint256) {
        return super.propose(targets, values, calldatas, description);
    }

    /**
     * @notice Cast a vote on a proposal.
     * @dev The `vote` function is inherited from the OpenZeppelin Governor contract.
     * Emits a {VoteCast} event.
     * @param proposalId The ID of the proposal to vote on.
     * @param support The type of vote to cast. Standard values are:
     * - 0 for Against
     * - 1 for For
     * - 2 for Abstain
     */
    function castVote(uint256 proposalId, uint8 support)
        public
        override(IGovernor)
        returns (uint256)
    {
        return super.castVote(proposalId, support);
    }

    // The following functions are overrides required by Solidity for inheritance.

    function votingDelay()
        public
        view
        override(Governor, GovernorSettings, IGovernor)
        returns (uint256)
    {
        return super.votingDelay();
    }

    function votingPeriod()
        public
        view
        override(Governor, GovernorSettings, IGovernor)
        returns (uint256)
    {
        return super.votingPeriod();
    }

    function proposalThreshold()
        public
        view
        override(Governor, GovernorSettings)
        returns (uint256)
    {
        return super.proposalThreshold();
    }

    function quorum(uint256 blockNumber)
        public
        view
        override(Governor, GovernorVotesQuorumFraction, IGovernor)
        returns (uint256)
    {
        return super.quorum(blockNumber);
    }

    function getVotes(address account, uint256 blockNumber)
        public
        view
        override(Governor, IGovernor)
        returns (uint256)
    {
        return super.getVotes(account, blockNumber);
    }

    function _queue(
        address[] memory targets,
        uint256[] memory values,
        bytes[] memory calldatas,
        bytes32 descriptionHash
    ) internal override(Governor, GovernorTimelockControl) returns (uint256) {
        return super._queue(targets, values, calldatas, descriptionHash);
    }

    function _execute(
        uint256 proposalId,
        address[] memory targets,
        uint256[] memory values,
        bytes[] memory calldatas,
        bytes32 descriptionHash
    ) internal override(Governor, GovernorTimelockControl) {
        super._execute(proposalId, targets, values, calldatas, descriptionHash);
    }

    function _cancel(
        address[] memory targets,
        uint256[] memory values,
        bytes[] memory calldatas,
        bytes32 descriptionHash
    ) internal override(Governor, GovernorTimelockControl) returns (uint256) {
        return super._cancel(targets, values, calldatas, descriptionHash);
    }

    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(Governor, AccessControl, IGovernor)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
}