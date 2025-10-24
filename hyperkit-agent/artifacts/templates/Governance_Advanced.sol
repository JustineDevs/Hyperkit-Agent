// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/governance/Governor.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorSettings.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorCountingSimple.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorVotes.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorVotesQuorumFraction.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorTimelockControl.sol";
import "@openzeppelin/contracts/governance/TimelockController.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Votes.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

contract AdvancedGovernance is 
    Governor,
    GovernorSettings,
    GovernorCountingSimple,
    GovernorVotes,
    GovernorVotesQuorumFraction,
    GovernorTimelockControl,
    Ownable,
    Pausable
{
    struct ProposalMetadata {
        string title;
        string description;
        string category;
        uint256 createdAt;
        address proposer;
        bool executed;
    }

    mapping(uint256 => ProposalMetadata) public proposalMetadata;
    mapping(string => bool) public categories;
    mapping(address => bool) public whitelistedProposers;
    mapping(address => uint256) public proposerVotingPower;

    uint256 public constant MIN_PROPOSAL_THRESHOLD = 1000 * 10**18; // 1000 tokens
    uint256 public constant MAX_PROPOSAL_THRESHOLD = 100000 * 10**18; // 100000 tokens
    uint256 public constant MIN_VOTING_PERIOD = 1 days;
    uint256 public constant MAX_VOTING_PERIOD = 30 days;
    uint256 public constant MIN_VOTING_DELAY = 1 hours;
    uint256 public constant MAX_VOTING_DELAY = 7 days;

    event ProposalCreatedWithMetadata(
        uint256 indexed proposalId,
        address indexed proposer,
        string title,
        string category,
        uint256 votingStart,
        uint256 votingEnd
    );

    event CategoryAdded(string category);
    event CategoryRemoved(string category);
    event ProposerWhitelisted(address indexed proposer);
    event ProposerRemoved(address indexed proposer);

    constructor(
        ERC20Votes _token,
        TimelockController _timelock,
        uint256 _votingDelay,
        uint256 _votingPeriod,
        uint256 _proposalThreshold,
        uint256 _quorumPercentage
    )
        Governor("AdvancedGovernance")
        GovernorSettings(_votingDelay, _votingPeriod, _proposalThreshold)
        GovernorVotes(_token)
        GovernorVotesQuorumFraction(_quorumPercentage)
        GovernorTimelockControl(_timelock)
    {
        // Initialize default categories
        categories["Treasury"] = true;
        categories["Protocol"] = true;
        categories["Governance"] = true;
        categories["Technical"] = true;
    }

    modifier onlyWhitelistedProposer() {
        require(whitelistedProposers[msg.sender], "Proposer not whitelisted");
        _;
    }

    modifier validProposalThreshold(uint256 threshold) {
        require(threshold >= MIN_PROPOSAL_THRESHOLD, "Threshold too low");
        require(threshold <= MAX_PROPOSAL_THRESHOLD, "Threshold too high");
        _;
    }

    function proposeWithMetadata(
        address[] memory targets,
        uint256[] memory values,
        bytes[] memory calldatas,
        string memory description,
        string memory title,
        string memory category
    ) public onlyWhitelistedProposer whenNotPaused returns (uint256) {
        require(categories[category], "Invalid category");
        
        uint256 proposalId = propose(targets, values, calldatas, description);
        
        proposalMetadata[proposalId] = ProposalMetadata({
            title: title,
            description: description,
            category: category,
            createdAt: block.timestamp,
            proposer: msg.sender,
            executed: false
        });

        emit ProposalCreatedWithMetadata(
            proposalId,
            msg.sender,
            title,
            category,
            proposalSnapshot(proposalId),
            proposalDeadline(proposalId)
        );

        return proposalId;
    }

    function executeWithMetadata(uint256 proposalId) public {
        execute(targets(proposalId), values(proposalId), calldatas(proposalId), descriptionHash(proposalId));
        proposalMetadata[proposalId].executed = true;
    }

    function addCategory(string memory category) public onlyOwner {
        categories[category] = true;
        emit CategoryAdded(category);
    }

    function removeCategory(string memory category) public onlyOwner {
        categories[category] = false;
        emit CategoryRemoved(category);
    }

    function whitelistProposer(address proposer) public onlyOwner {
        whitelistedProposers[proposer] = true;
        emit ProposerWhitelisted(proposer);
    }

    function removeProposer(address proposer) public onlyOwner {
        whitelistedProposers[proposer] = false;
        emit ProposerRemoved(proposer);
    }

    function setProposalThreshold(uint256 newProposalThreshold) 
        public 
        override 
        onlyOwner 
        validProposalThreshold(newProposalThreshold) 
    {
        _setProposalThreshold(newProposalThreshold);
    }

    function setVotingDelay(uint256 newVotingDelay) public override onlyOwner {
        require(newVotingDelay >= MIN_VOTING_DELAY, "Voting delay too short");
        require(newVotingDelay <= MAX_VOTING_DELAY, "Voting delay too long");
        _setVotingDelay(newVotingDelay);
    }

    function setVotingPeriod(uint256 newVotingPeriod) public override onlyOwner {
        require(newVotingPeriod >= MIN_VOTING_PERIOD, "Voting period too short");
        require(newVotingPeriod <= MAX_VOTING_PERIOD, "Voting period too long");
        _setVotingPeriod(newVotingPeriod);
    }

    function pause() public onlyOwner {
        _pause();
    }

    function unpause() public onlyOwner {
        _unpause();
    }

    function getProposalMetadata(uint256 proposalId) public view returns (ProposalMetadata memory) {
        return proposalMetadata[proposalId];
    }

    function getProposalsByCategory(string memory category) public view returns (uint256[] memory) {
        uint256 totalProposals = proposalCount();
        uint256[] memory categoryProposals = new uint256[](totalProposals);
        uint256 count = 0;

        for (uint256 i = 0; i < totalProposals; i++) {
            if (keccak256(bytes(proposalMetadata[i].category)) == keccak256(bytes(category))) {
                categoryProposals[count] = i;
                count++;
            }
        }

        // Resize array to actual count
        uint256[] memory result = new uint256[](count);
        for (uint256 i = 0; i < count; i++) {
            result[i] = categoryProposals[i];
        }

        return result;
    }

    function getProposerStats(address proposer) public view returns (
        uint256 totalProposals,
        uint256 executedProposals,
        uint256 activeProposals
    ) {
        uint256 total = proposalCount();
        
        for (uint256 i = 0; i < total; i++) {
            if (proposalMetadata[i].proposer == proposer) {
                totalProposals++;
                if (proposalMetadata[i].executed) {
                    executedProposals++;
                }
                if (state(i) == ProposalState.Active) {
                    activeProposals++;
                }
            }
        }
    }

    // Override required functions
    function votingDelay()
        public
        pure
        override(IGovernor, GovernorSettings)
        returns (uint256)
    {
        return super.votingDelay();
    }

    function votingPeriod()
        public
        pure
        override(IGovernor, GovernorSettings)
        returns (uint256)
    {
        return super.votingPeriod();
    }

    function proposalThreshold()
        public
        pure
        override(Governor, GovernorSettings)
        returns (uint256)
    {
        return super.proposalThreshold();
    }

    function quorum(uint256 blockNumber)
        public
        view
        override(IGovernor, GovernorVotesQuorumFraction)
        returns (uint256)
    {
        return super.quorum(blockNumber);
    }

    function state(uint256 proposalId)
        public
        view
        override(Governor, GovernorTimelockControl)
        returns (ProposalState)
    {
        return super.state(proposalId);
    }

    function propose(
        address[] memory targets,
        uint256[] memory values,
        bytes[] memory calldatas,
        string memory description
    ) public override(Governor, IGovernor) returns (uint256) {
        return super.propose(targets, values, calldatas, description);
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

    function _executor() internal view override(Governor, GovernorTimelockControl) returns (address) {
        return super._executor();
    }

    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(Governor, GovernorTimelockControl)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
}
