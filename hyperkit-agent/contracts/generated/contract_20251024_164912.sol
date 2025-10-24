// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Votes.sol";
import "@openzeppelin/contracts/governance/Governor.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorSettings.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorVotes.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorVotesQuorumFraction.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorTimelockControl.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

/**
 * @title GDAO
 * @author HyperDAO
 * @notice The governance token for HyperDAO.
 * @dev This is an ERC20 token with snapshot and delegation capabilities for voting,
 * based on OpenZeppelin's ERC20Votes.
 */
contract GDAO is ERC20Votes {
    /**
     * @notice Mints the initial supply of GDAO tokens to the contract deployer.
     * @param initialSupply The total amount of tokens to mint initially.
     */
    constructor(uint256 initialSupply) ERC20("GDAO", "GDAO") ERC20Permit("GDAO") {
        _mint(msg.sender, initialSupply);
    }

    /**
     * @dev See {ERC20Votes-_update}.
     */
    function _update(address from, address to, uint256 value) internal override(ERC20, ERC20Votes) {
        super._update(from, to, value);
    }

    /**
     * @dev See {ERC20Votes-_mint}.
     */
    function _mint(address to, uint256 amount) internal override(ERC20, ERC20Votes) {
        super._mint(to, amount);
    }

    /**
     * @dev See {ERC20Votes-_burn}.
     */
    function _burn(address account, uint256 amount) internal override(ERC20, ERC20Votes) {
        super._burn(account, amount);
    }
}

/**
 * @title HyperDAO
 * @author HyperDAO
 * @notice A comprehensive DAO governance contract with token-based voting, a timelock, and robust proposal lifecycle.
 * @dev This contract orchestrates the entire governance process. Proposals are created, voted on,
 * and, if successful, queued in a Timelock contract for delayed execution. It uses GDAO as the
 * governance token. This contract is intended to be the primary proposer for a TimelockController,
 * which in turn would be the owner/admin of other protocol contracts (e.g., treasury, proxies).
 */
contract HyperDAO is Governor, GovernorSettings, GovernorVotes, GovernorVotesQuorumFraction, GovernorTimelockControl, AccessControl {

    // --- Roles ---

    /**
     * @dev Role that grants permission to cancel proposals, in addition to the proposer.
     */
    bytes32 public constant CANCELLER_ROLE = keccak256("CANCELLER_ROLE");

    // --- Constants ---

    /// @notice The number of blocks for the voting period (approx. 7 days).
    uint256 private constant VOTING_PERIOD_BLOCKS = 50400; // 7 days, assuming 12-second block time

    /// @notice The delay before a vote begins after a proposal is created (1 block).
    uint256 private constant VOTING_DELAY_BLOCKS = 1;

    /// @notice The minimum number of GDAO tokens required to create a proposal (100,000 GDAO).
    uint256 private constant PROPOSAL_THRESHOLD_AMOUNT = 100_000 * 1e18;

    /// @notice The quorum percentage required for a vote to be valid (30%).
    uint256 private constant QUORUM_PERCENTAGE = 30;

    /// @notice The approval threshold numerator for 'yes' votes (60%).
    uint256 private constant APPROVAL_THRESHOLD_NUMERATOR = 60;

    /// @notice The approval threshold denominator (100 for percentage).
    uint256 private constant APPROVAL_THRESHOLD_DENOMINATOR = 100;

    /**
     * @notice Sets up the governance contract with all necessary parameters.
     * @param _token The GDAO governance token contract address.
     * @param _timelock The TimelockController contract address for execution delay.
     * @param _admin The address to be granted admin and canceller roles.
     */
    constructor(IVotes _token, TimelockController _timelock, address _admin)
        Governor("HyperDAO")
        GovernorSettings(VOTING_DELAY_BLOCKS, VOTING_PERIOD_BLOCKS, PROPOSAL_THRESHOLD_AMOUNT)
        GovernorVotes(_token)
        GovernorVotesQuorumFraction(QUORUM_PERCENTAGE)
        GovernorTimelockControl(_timelock)
    {
        _grantRole(DEFAULT_ADMIN_ROLE, _admin);
        _grantRole(CANCELLER_ROLE, _admin);
    }

    // --- Overridden Functions ---

    /**
     * @notice Determines if a vote has passed based on the 60% approval threshold.
     * @dev Overrides the default simple majority check. A proposal succeeds if the number of 'For'
     * votes is at least 60% of the total 'For' and 'Against' votes. Abstain votes are not included.
     * @param proposalId The ID of the proposal to check.
     * @return A boolean indicating if the vote succeeded.
     */
    function _voteSucceeded(uint256 proposalId) internal view override returns (bool) {
        ProposalCore storage proposal = _proposals[proposalId];
        uint256 totalVotes = proposal.forVotes + proposal.againstVotes;

        // A proposal with no 'for' or 'against' votes cannot succeed.
        if (totalVotes == 0) {
            return false;
        }

        // Check if For votes meet the 60% threshold.
        // The calculation `forVotes * 100 >= totalVotes * 60` avoids division and floating-point math.
        return proposal.forVotes * APPROVAL_THRESHOLD_DENOMINATOR >= totalVotes * APPROVAL_THRESHOLD_NUMERATOR;
    }

    /**
     * @notice Cancels a proposal.
     * @dev Can only be called by the original proposer or an account with the CANCELLER_ROLE.
     * This overrides the default behavior which also allows cancellation if the proposer's voting
     * power drops below the proposal threshold.
     * @param targets The array of target addresses for the proposal's actions.
     * @param values The array of ETH values to be sent with the actions.
     * @param calldatas The array of calldata for the actions.
     * @param descriptionHash The keccak256 hash of the proposal's description.
     * @return The proposal ID.
     */
    function cancel(
        address[] memory targets,
        uint256[] memory values,
        bytes[] memory calldatas,
        bytes32 descriptionHash
    ) public override(Governor, IGovernor) returns (uint256) {
        uint256 proposalId = hashProposal(targets, values, calldatas, descriptionHash);
        address proposer = proposer(proposalId);

        // Require sender to be the proposer or have the CANCELLER_ROLE.
        if (_msgSender() != proposer) {
            _checkRole(CANCELLER_ROLE);
        }

        return _cancel(targets, values, calldatas, descriptionHash);
    }

    /**
     * @notice Returns the voting delay in blocks.
     */
    function votingDelay() public view override(IGovernor, GovernorSettings) returns (uint256) {
        return super.votingDelay();
    }

    /**
     * @notice Returns the voting period in blocks.
     */
    function votingPeriod() public view override(IGovernor, GovernorSettings) returns (uint256) {
        return super.votingPeriod();
    }

    /**
     * @notice Returns the proposal threshold.
     */
    function proposalThreshold() public view override(Governor, GovernorSettings) returns (uint256) {
        return super.proposalThreshold();
    }

    /**
     * @notice Returns the quorum required for a vote to be valid.
     * @dev Uses the snapshot of the token's total supply at the time the proposal was created.
     * @param blockNumber The block number at which to check the quorum.
     * @return The number of votes required for quorum.
     */
    function quorum(uint256 blockNumber) public view override(IGovernor, GovernorVotesQuorumFraction) returns (uint256) {
        return super.quorum(blockNumber);
    }

    /**
     * @notice Returns the state of a proposal.
     */
    function state(uint256 proposalId) public view override(Governor, GovernorTimelockControl) returns (ProposalState) {
        return super.state(proposalId);
    }

    /**
     * @notice Creates a new proposal.
     * @param targets The array of target addresses for the proposal's actions.
     * @param values The array of ETH values to be sent with the actions.
     * @param calldatas The array of calldata for the actions.
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
     * @notice Queues a successful proposal for execution in the Timelock.
     * @param targets The array of target addresses for the proposal's actions.
     * @param values The array of ETH values to be sent with the actions.
     * @param calldatas The array of calldata for the actions.
     * @param descriptionHash The keccak256 hash of the proposal's description.
     * @return The proposal ID.
     */
    function queue(
        address[] memory targets,
        uint256[] memory values,
        bytes[] memory calldatas,
        bytes32 descriptionHash
    ) public override(Governor, GovernorTimelockControl) returns (uint256) {
        return super.queue(targets, values, calldatas, descriptionHash);
    }

    /**
     * @notice Executes a queued proposal.
     * @param targets The array of target addresses for the proposal's actions.
     * @param values The array of ETH values to be sent with the actions.
     * @param calldatas The array of calldata for the actions.
     * @param descriptionHash The keccak256 hash of the proposal's description.
     * @return The proposal ID.
     */
    function execute(
        address[] memory targets,
        uint256[] memory values,
        bytes[] memory calldatas,
        bytes32 descriptionHash
    ) public payable override(Governor, GovernorTimelockControl) returns (uint256) {
        return super.execute(targets, values, calldatas, descriptionHash);
    }

    /**
     * @dev See {IGovernor-getVotes}.
     */
    function getVotes(address account, uint256 blockNumber) public view override(IGovernor, GovernorVotes) returns (uint256) {
        return super.getVotes(account, blockNumber);
    }

    /**
     * @dev See {IERC165-supportsInterface}.
     */
    function supportsInterface(bytes4 interfaceId) public view override(Governor, GovernorTimelockControl, AccessControl) returns (bool) {
        return super.supportsInterface(interfaceId);
    }

    /**
     * @dev Internal execution logic, calling the Timelock.
     */
    function _execute(
        uint256, /* proposalId */
        address[] memory targets,
        uint256[] memory values,
        bytes[] memory calldatas,
        bytes32 descriptionHash
    ) internal override(Governor, GovernorTimelockControl) {
        super._execute(0, targets, values, calldatas, descriptionHash);
    }

    /**
     * @dev Internal cancellation logic.
     */
    function _cancel(
        address[] memory targets,
        uint256[] memory values,
        bytes[] memory calldatas,
        bytes32 descriptionHash
    ) internal override(Governor, GovernorTimelockControl) returns (uint256) {
        return super._cancel(targets, values, calldatas, descriptionHash);
    }
}