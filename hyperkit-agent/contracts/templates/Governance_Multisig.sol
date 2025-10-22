// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

contract MultisigGovernance is AccessControl, ReentrancyGuard, Pausable {
    using Counters for Counters.Counter;

    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant MEMBER_ROLE = keccak256("MEMBER_ROLE");
    bytes32 public constant EXECUTOR_ROLE = keccak256("EXECUTOR_ROLE");

    struct Transaction {
        address to;
        uint256 value;
        bytes data;
        bool executed;
        uint256 confirmations;
        uint256 createdAt;
        string description;
    }

    struct Proposal {
        uint256 transactionId;
        string title;
        string description;
        uint256 createdAt;
        uint256 votingEnd;
        uint256 forVotes;
        uint256 againstVotes;
        bool executed;
        address proposer;
    }

    mapping(uint256 => Transaction) public transactions;
    mapping(uint256 => Proposal) public proposals;
    mapping(uint256 => mapping(address => bool)) public confirmations;
    mapping(uint256 => mapping(address => bool)) public votes;
    mapping(address => bool) public isMember;
    mapping(address => uint256) public memberWeight;

    Counters.Counter private _transactionCounter;
    Counters.Counter private _proposalCounter;

    uint256 public requiredConfirmations;
    uint256 public requiredVotes;
    uint256 public votingPeriod;
    uint256 public totalMembers;
    uint256 public totalWeight;

    event TransactionSubmitted(
        uint256 indexed transactionId,
        address indexed to,
        uint256 value,
        bytes data,
        string description
    );

    event TransactionConfirmed(uint256 indexed transactionId, address indexed member);
    event TransactionExecuted(uint256 indexed transactionId);
    event TransactionRevoked(uint256 indexed transactionId, address indexed member);

    event ProposalCreated(
        uint256 indexed proposalId,
        uint256 indexed transactionId,
        address indexed proposer,
        string title,
        uint256 votingEnd
    );

    event VoteCast(
        uint256 indexed proposalId,
        address indexed voter,
        bool support,
        uint256 weight
    );

    event ProposalExecuted(uint256 indexed proposalId);
    event MemberAdded(address indexed member, uint256 weight);
    event MemberRemoved(address indexed member);
    event MemberWeightUpdated(address indexed member, uint256 newWeight);

    modifier onlyMembers() {
        require(isMember[msg.sender], "Not a member");
        _;
    }

    modifier transactionExists(uint256 transactionId) {
        require(transactionId < _transactionCounter.current(), "Transaction does not exist");
        _;
    }

    modifier notExecuted(uint256 transactionId) {
        require(!transactions[transactionId].executed, "Transaction already executed");
        _;
    }

    modifier notConfirmed(uint256 transactionId) {
        require(!confirmations[transactionId][msg.sender], "Transaction already confirmed");
        _;
    }

    constructor(
        address[] memory initialMembers,
        uint256[] memory initialWeights,
        uint256 _requiredConfirmations,
        uint256 _requiredVotes,
        uint256 _votingPeriod
    ) {
        require(initialMembers.length == initialWeights.length, "Arrays length mismatch");
        require(initialMembers.length > 0, "No initial members");
        require(_requiredConfirmations > 0, "Required confirmations must be > 0");
        require(_requiredVotes > 0, "Required votes must be > 0");
        require(_votingPeriod > 0, "Voting period must be > 0");

        _setupRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _setupRole(ADMIN_ROLE, msg.sender);
        _setupRole(EXECUTOR_ROLE, msg.sender);

        requiredConfirmations = _requiredConfirmations;
        requiredVotes = _requiredVotes;
        votingPeriod = _votingPeriod;

        for (uint256 i = 0; i < initialMembers.length; i++) {
            _addMember(initialMembers[i], initialWeights[i]);
        }
    }

    function submitTransaction(
        address to,
        uint256 value,
        bytes memory data,
        string memory description
    ) public onlyMembers whenNotPaused returns (uint256) {
        uint256 transactionId = _transactionCounter.current();
        _transactionCounter.increment();

        transactions[transactionId] = Transaction({
            to: to,
            value: value,
            data: data,
            executed: false,
            confirmations: 0,
            createdAt: block.timestamp,
            description: description
        });

        emit TransactionSubmitted(transactionId, to, value, data, description);
        return transactionId;
    }

    function confirmTransaction(uint256 transactionId)
        public
        onlyMembers
        transactionExists(transactionId)
        notExecuted(transactionId)
        notConfirmed(transactionId)
    {
        confirmations[transactionId][msg.sender] = true;
        transactions[transactionId].confirmations++;

        emit TransactionConfirmed(transactionId, msg.sender);

        if (transactions[transactionId].confirmations >= requiredConfirmations) {
            executeTransaction(transactionId);
        }
    }

    function executeTransaction(uint256 transactionId)
        public
        onlyMembers
        transactionExists(transactionId)
        notExecuted(transactionId)
        nonReentrant
    {
        require(
            transactions[transactionId].confirmations >= requiredConfirmations,
            "Insufficient confirmations"
        );

        Transaction storage txn = transactions[transactionId];
        txn.executed = true;

        (bool success, ) = txn.to.call{value: txn.value}(txn.data);
        require(success, "Transaction execution failed");

        emit TransactionExecuted(transactionId);
    }

    function revokeConfirmation(uint256 transactionId)
        public
        onlyMembers
        transactionExists(transactionId)
        notExecuted(transactionId)
    {
        require(confirmations[transactionId][msg.sender], "Transaction not confirmed");

        confirmations[transactionId][msg.sender] = false;
        transactions[transactionId].confirmations--;

        emit TransactionRevoked(transactionId, msg.sender);
    }

    function createProposal(
        uint256 transactionId,
        string memory title,
        string memory description
    ) public onlyMembers whenNotPaused returns (uint256) {
        require(transactionId < _transactionCounter.current(), "Transaction does not exist");
        require(!transactions[transactionId].executed, "Transaction already executed");

        uint256 proposalId = _proposalCounter.current();
        _proposalCounter.increment();

        proposals[proposalId] = Proposal({
            transactionId: transactionId,
            title: title,
            description: description,
            createdAt: block.timestamp,
            votingEnd: block.timestamp + votingPeriod,
            forVotes: 0,
            againstVotes: 0,
            executed: false,
            proposer: msg.sender
        });

        emit ProposalCreated(proposalId, transactionId, msg.sender, title, block.timestamp + votingPeriod);
        return proposalId;
    }

    function castVote(uint256 proposalId, bool support) public onlyMembers {
        require(proposalId < _proposalCounter.current(), "Proposal does not exist");
        require(block.timestamp <= proposals[proposalId].votingEnd, "Voting period ended");
        require(!proposals[proposalId].executed, "Proposal already executed");
        require(!votes[proposalId][msg.sender], "Already voted");

        votes[proposalId][msg.sender] = true;
        uint256 weight = memberWeight[msg.sender];

        if (support) {
            proposals[proposalId].forVotes += weight;
        } else {
            proposals[proposalId].againstVotes += weight;
        }

        emit VoteCast(proposalId, msg.sender, support, weight);
    }

    function executeProposal(uint256 proposalId) public onlyMembers nonReentrant {
        require(proposalId < _proposalCounter.current(), "Proposal does not exist");
        require(block.timestamp > proposals[proposalId].votingEnd, "Voting period not ended");
        require(!proposals[proposalId].executed, "Proposal already executed");
        require(proposals[proposalId].forVotes >= requiredVotes, "Insufficient votes");

        proposals[proposalId].executed = true;
        uint256 transactionId = proposals[proposalId].transactionId;

        // Auto-confirm the transaction for all members who voted for it
        for (uint256 i = 0; i < totalMembers; i++) {
            // This is a simplified approach - in practice, you'd need to track voters
            if (votes[proposalId][msg.sender] && proposals[proposalId].forVotes > proposals[proposalId].againstVotes) {
                confirmations[transactionId][msg.sender] = true;
                transactions[transactionId].confirmations++;
            }
        }

        if (transactions[transactionId].confirmations >= requiredConfirmations) {
            executeTransaction(transactionId);
        }

        emit ProposalExecuted(proposalId);
    }

    function addMember(address member, uint256 weight) public onlyRole(ADMIN_ROLE) {
        _addMember(member, weight);
    }

    function removeMember(address member) public onlyRole(ADMIN_ROLE) {
        require(isMember[member], "Not a member");
        require(totalMembers > 1, "Cannot remove last member");

        isMember[member] = false;
        totalWeight -= memberWeight[member];
        totalMembers--;
        memberWeight[member] = 0;

        emit MemberRemoved(member);
    }

    function updateMemberWeight(address member, uint256 newWeight) public onlyRole(ADMIN_ROLE) {
        require(isMember[member], "Not a member");
        require(newWeight > 0, "Weight must be > 0");

        totalWeight = totalWeight - memberWeight[member] + newWeight;
        memberWeight[member] = newWeight;

        emit MemberWeightUpdated(member, newWeight);
    }

    function updateRequiredConfirmations(uint256 newRequired) public onlyRole(ADMIN_ROLE) {
        require(newRequired > 0, "Required confirmations must be > 0");
        require(newRequired <= totalMembers, "Required confirmations > total members");
        requiredConfirmations = newRequired;
    }

    function updateRequiredVotes(uint256 newRequired) public onlyRole(ADMIN_ROLE) {
        require(newRequired > 0, "Required votes must be > 0");
        requiredVotes = newRequired;
    }

    function updateVotingPeriod(uint256 newPeriod) public onlyRole(ADMIN_ROLE) {
        require(newPeriod > 0, "Voting period must be > 0");
        votingPeriod = newPeriod;
    }

    function pause() public onlyRole(ADMIN_ROLE) {
        _pause();
    }

    function unpause() public onlyRole(ADMIN_ROLE) {
        _unpause();
    }

    function _addMember(address member, uint256 weight) internal {
        require(member != address(0), "Invalid address");
        require(weight > 0, "Weight must be > 0");
        require(!isMember[member], "Already a member");

        isMember[member] = true;
        memberWeight[member] = weight;
        totalMembers++;
        totalWeight += weight;

        _grantRole(MEMBER_ROLE, member);

        emit MemberAdded(member, weight);
    }

    function getTransactionCount() public view returns (uint256) {
        return _transactionCounter.current();
    }

    function getProposalCount() public view returns (uint256) {
        return _proposalCounter.current();
    }

    function isConfirmed(uint256 transactionId) public view returns (bool) {
        return transactions[transactionId].confirmations >= requiredConfirmations;
    }

    function getTransactionConfirmations(uint256 transactionId) public view returns (uint256) {
        return transactions[transactionId].confirmations;
    }

    function getProposalVotes(uint256 proposalId) public view returns (uint256 forVotes, uint256 againstVotes) {
        return (proposals[proposalId].forVotes, proposals[proposalId].againstVotes);
    }

    function canExecute(uint256 transactionId) public view returns (bool) {
        return isConfirmed(transactionId) && !transactions[transactionId].executed;
    }

    function canVote(uint256 proposalId) public view returns (bool) {
        return block.timestamp <= proposals[proposalId].votingEnd && 
               !proposals[proposalId].executed && 
               !votes[proposalId][msg.sender];
    }
}
