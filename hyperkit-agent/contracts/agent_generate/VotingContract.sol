// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/**
 * @title SimpleDAO
 * @author Your Name
 * @notice A simple governance contract for a Decentralized Autonomous Organization (DAO).
 * @dev This contract allows members to create and vote on proposals.
 *      Membership is managed by the contract owner. It uses OpenZeppelin's
 *      Ownable for access control and ReentrancyGuard for security.
 */
contract SimpleDAO is Ownable, ReentrancyGuard {
    //==============================================================
    // State Variables
    //==============================================================

    /**
     * @dev The duration for which voting on a proposal is open.
     */
    uint256 public constant VOTING_PERIOD = 7 days;

    /**
     * @dev A counter for the total number of proposals created. Serves as proposal ID.
     */
    uint256 public proposalCount;

    /**
     * @dev A mapping from an address to a boolean indicating membership.
     */
    mapping(address => bool) public members;

    /**
     * @dev A counter for the total number of members.
     */
    uint256 public memberCount;

    /**
     * @dev A struct to represent a governance proposal.
     */
    struct Proposal {
        uint256 id;
        address proposer;
        string description;
        uint256 forVotes;
        uint256 againstVotes;
        uint256 startTime;
        uint256 endTime;
        bool executed;
    }

    /**
     * @dev A mapping from a proposal ID to the Proposal struct.
     */
    mapping(uint256 => Proposal) public proposals;

    /**
     * @dev A nested mapping to track if a member has voted on a specific proposal.
     *      mapping(proposalId => mapping(voterAddress => hasVoted))
     */
    mapping(uint256 => mapping(address => bool)) public hasVoted;

    //==============================================================
    // Events
    //==============================================================

    event MemberAdded(address indexed member);
    event MemberRemoved(address indexed member);
    event ProposalCreated(uint256 indexed proposalId, address indexed proposer, string description);
    event Voted(uint256 indexed proposalId, address indexed voter, bool inFavor);
    event ProposalExecuted(uint256 indexed proposalId);

    //==============================================================
    // Custom Errors
    //==============================================================

    error NotMember();
    error AlreadyMember();
    error ZeroAddress();
    error CannotRemoveLastMember();
    error ProposalNotFound();
    error VotingIsClosed();
    error AlreadyVoted();
    error VotingInProgress();
    error ProposalNotPassed();
    error ProposalAlreadyExecuted();
    error EmptyDescription();

    //==============================================================
    // Modifiers
    //==============================================================

    /**
     * @dev Throws an error if called by any account that is not a member.
     */
    modifier onlyMember() {
        if (!members[msg.sender]) revert NotMember();
        _;
    }

    //==============================================================
    // Constructor
    //==============================================================

    /**
     * @notice Initializes the contract, setting the deployer as the first owner and member.
     * @param initialOwner The address that will be the initial owner of the contract.
     */
    constructor(address initialOwner) Ownable(initialOwner) {
        if (initialOwner == address(0)) revert ZeroAddress();
        members[initialOwner] = true;
        memberCount = 1;
        emit MemberAdded(initialOwner);
    }

    //==============================================================
    // Member Management Functions (Owner-only)
    //==============================================================

    /**
     * @notice Adds a new member to the DAO.
     * @dev Can only be called by the contract owner.
     * @param _member The address of the new member.
     */
    function addMember(address _member) external onlyOwner {
        if (_member == address(0)) revert ZeroAddress();
        if (members[_member]) revert AlreadyMember();

        members[_member] = true;
        memberCount++;
        emit MemberAdded(_member);
    }

    /**
     * @notice Removes a member from the DAO.
     * @dev Can only be called by the contract owner.
     * @param _member The address of the member to remove.
     */
    function removeMember(address _member) external onlyOwner {
        if (!members[_member]) revert NotMember();
        if (memberCount <= 1) revert CannotRemoveLastMember();

        members[_member] = false;
        memberCount--;
        emit MemberRemoved(_member);
    }

    //==============================================================
    // Proposal and Voting Functions (Member-only)
    //==============================================================

    /**
     * @notice Creates a new proposal for members to vote on.
     * @dev Can only be called by a member. The voting period starts immediately.
     * @param _description A description of the proposal.
     * @return The ID of the newly created proposal.
     */
    function createProposal(string calldata _description)
        external
        onlyMember
        nonReentrant
        returns (uint256)
    {
        if (bytes(_description).length == 0) revert EmptyDescription();

        proposalCount++;
        uint256 newProposalId = proposalCount;

        proposals[newProposalId] = Proposal({
            id: newProposalId,
            proposer: msg.sender,
            description: _description,
            forVotes: 0,
            againstVotes: 0,
            startTime: block.timestamp,
            endTime: block.timestamp + VOTING_PERIOD,
            executed: false
        });

        emit ProposalCreated(newProposalId, msg.sender, _description);
        return newProposalId;
    }

    /**
     * @notice Casts a vote on an active proposal.
     * @dev Can only be called by a member. A member can only vote once per proposal.
     * @param _proposalId The ID of the proposal to vote on.
     * @param _inFavor A boolean representing the vote (true for 'For', false for 'Against').
     */
    function vote(uint256 _proposalId, bool _inFavor) external onlyMember nonReentrant {
        Proposal storage p = proposals[_proposalId];

        if (p.id == 0) revert ProposalNotFound();
        if (block.timestamp > p.endTime) revert VotingIsClosed();
        if (hasVoted[_proposalId][msg.sender]) revert AlreadyVoted();

        hasVoted[_proposalId][msg.sender] = true;

        if (_inFavor) {
            p.forVotes++;
        } else {
            p.againstVotes++;
        }

        emit Voted(_proposalId, msg.sender, _inFavor);
    }

    /**
     * @notice Executes a proposal that has passed.
     * @dev A proposal is considered passed if it has more 'For' votes than 'Against' votes
     *      after the voting period has ended. Can be called by any member.
     *      In a real-world scenario, this function would trigger an on-chain action.
     * @param _proposalId The ID of the proposal to execute.
     */
    function executeProposal(uint256 _proposalId) external onlyMember nonReentrant {
        Proposal storage p = proposals[_proposalId];

        if (p.id == 0) revert ProposalNotFound();
        if (block.timestamp <= p.endTime) revert VotingInProgress();
        if (p.executed) revert ProposalAlreadyExecuted();
        if (p.forVotes <= p.againstVotes) revert ProposalNotPassed();

        p.executed = true;
        // In a real DAO, this is where you would add the logic to be executed,
        // for example, calling another contract:
        // (bool success, ) = targetContract.call{value: ethAmount}(calldata);
        // require(success, "Execution failed");

        emit ProposalExecuted(_proposalId);
    }

    //==============================================================
    // View Functions
    //==============================================================

    /**
     * @notice Retrieves the details of a specific proposal.
     * @param _proposalId The ID of the proposal.
     * @return The full Proposal struct containing all its data.
     */
    function getProposal(uint256 _proposalId)
        public
        view
        returns (Proposal memory)
    {
        if (proposals[_proposalId].id == 0) revert ProposalNotFound();
        return proposals[_proposalId];
    }
}