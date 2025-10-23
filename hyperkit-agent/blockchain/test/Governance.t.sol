// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "forge-std/console.sol";
import "../contracts/agent_generate/VotingContract.sol";

contract GovernanceTest is Test {
    VotingContract public governance;
    MockERC20 public token;
    
    address public owner = address(0x1);
    address public voter1 = address(0x2);
    address public voter2 = address(0x3);
    address public voter3 = address(0x4);
    
    uint256 public constant INITIAL_SUPPLY = 1000000 * 10**18;
    uint256 public constant VOTING_POWER = 1000 * 10**18;
    
    event ProposalCreated(uint256 indexed proposalId, address indexed proposer, string description);
    event VoteCast(uint256 indexed proposalId, address indexed voter, bool support, uint256 votes);
    event ProposalExecuted(uint256 indexed proposalId);
    
    function setUp() public {
        // Deploy mock ERC20 token
        token = new MockERC20("Governance Token", "GOV", INITIAL_SUPPLY);
        
        // Deploy governance contract
        governance = new VotingContract(address(token));
        
        // Transfer tokens to voters
        token.transfer(voter1, VOTING_POWER);
        token.transfer(voter2, VOTING_POWER);
        token.transfer(voter3, VOTING_POWER);
        
        // Approve governance contract to spend tokens
        vm.prank(voter1);
        token.approve(address(governance), type(uint256).max);
        
        vm.prank(voter2);
        token.approve(address(governance), type(uint256).max);
        
        vm.prank(voter3);
        token.approve(address(governance), type(uint256).max);
    }
    
    function testInitialState() public {
        assertEq(governance.owner(), owner);
        assertEq(address(governance.votingToken()), address(token));
        assertEq(governance.proposalCount(), 0);
    }
    
    function testCreateProposal() public {
        string memory description = "Test proposal";
        uint256 votingPeriod = 7 days;
        
        vm.prank(voter1);
        uint256 proposalId = governance.createProposal(description, votingPeriod);
        
        assertEq(proposalId, 1);
        assertEq(governance.proposalCount(), 1);
        
        (address proposer, string memory desc, uint256 startTime, uint256 endTime, bool executed, uint256 forVotes, uint256 againstVotes) = governance.proposals(proposalId);
        
        assertEq(proposer, voter1);
        assertEq(desc, description);
        assertEq(executed, false);
        assertEq(forVotes, 0);
        assertEq(againstVotes, 0);
    }
    
    function testCreateProposalInsufficientBalance() public {
        address poorVoter = address(0x5);
        
        vm.prank(poorVoter);
        vm.expectRevert("Insufficient token balance to create proposal");
        governance.createProposal("Test proposal", 7 days);
    }
    
    function testVote() public {
        vm.prank(voter1);
        uint256 proposalId = governance.createProposal("Test proposal", 7 days);
        
        vm.prank(voter1);
        governance.vote(proposalId, true);
        
        (,,,,, uint256 forVotes, uint256 againstVotes) = governance.proposals(proposalId);
        assertEq(forVotes, VOTING_POWER);
        assertEq(againstVotes, 0);
    }
    
    function testVoteAgainst() public {
        vm.prank(voter1);
        uint256 proposalId = governance.createProposal("Test proposal", 7 days);
        
        vm.prank(voter1);
        governance.vote(proposalId, false);
        
        (,,,,, uint256 forVotes, uint256 againstVotes) = governance.proposals(proposalId);
        assertEq(forVotes, 0);
        assertEq(againstVotes, VOTING_POWER);
    }
    
    function testVoteInsufficientBalance() public {
        address poorVoter = address(0x5);
        
        vm.prank(voter1);
        uint256 proposalId = governance.createProposal("Test proposal", 7 days);
        
        vm.prank(poorVoter);
        vm.expectRevert("Insufficient token balance to vote");
        governance.vote(proposalId, true);
    }
    
    function testVoteOnNonExistentProposal() public {
        vm.prank(voter1);
        vm.expectRevert("Proposal does not exist");
        governance.vote(999, true);
    }
    
    function testVoteAfterDeadline() public {
        vm.prank(voter1);
        uint256 proposalId = governance.createProposal("Test proposal", 1 seconds);
        
        vm.warp(block.timestamp + 2 seconds);
        
        vm.prank(voter1);
        vm.expectRevert("Voting period has ended");
        governance.vote(proposalId, true);
    }
    
    function testExecuteProposal() public {
        vm.prank(voter1);
        uint256 proposalId = governance.createProposal("Test proposal", 7 days);
        
        // Vote for the proposal
        vm.prank(voter1);
        governance.vote(proposalId, true);
        
        vm.prank(voter2);
        governance.vote(proposalId, true);
        
        // Fast forward past voting period
        vm.warp(block.timestamp + 8 days);
        
        vm.prank(owner);
        governance.executeProposal(proposalId);
        
        (,,,, bool executed,,) = governance.proposals(proposalId);
        assertTrue(executed);
    }
    
    function testExecuteProposalBeforeDeadline() public {
        vm.prank(voter1);
        uint256 proposalId = governance.createProposal("Test proposal", 7 days);
        
        vm.prank(voter1);
        governance.vote(proposalId, true);
        
        vm.prank(owner);
        vm.expectRevert("Voting period has not ended");
        governance.executeProposal(proposalId);
    }
    
    function testExecuteProposalAlreadyExecuted() public {
        vm.prank(voter1);
        uint256 proposalId = governance.createProposal("Test proposal", 7 days);
        
        vm.prank(voter1);
        governance.vote(proposalId, true);
        
        vm.warp(block.timestamp + 8 days);
        
        vm.prank(owner);
        governance.executeProposal(proposalId);
        
        vm.prank(owner);
        vm.expectRevert("Proposal already executed");
        governance.executeProposal(proposalId);
    }
    
    function testExecuteProposalOnlyOwner() public {
        vm.prank(voter1);
        uint256 proposalId = governance.createProposal("Test proposal", 7 days);
        
        vm.prank(voter1);
        governance.vote(proposalId, true);
        
        vm.warp(block.timestamp + 8 days);
        
        vm.prank(voter1);
        vm.expectRevert("Ownable: caller is not the owner");
        governance.executeProposal(proposalId);
    }
    
    function testFuzzCreateProposal(string memory description, uint256 votingPeriod) public {
        vm.assume(bytes(description).length > 0 && bytes(description).length <= 1000);
        vm.assume(votingPeriod >= 1 days && votingPeriod <= 30 days);
        
        vm.prank(voter1);
        uint256 proposalId = governance.createProposal(description, votingPeriod);
        
        assertEq(proposalId, 1);
        assertEq(governance.proposalCount(), 1);
    }
    
    function testFuzzVote(uint256 proposalId, bool support) public {
        vm.assume(proposalId > 0 && proposalId <= 1000);
        
        vm.prank(voter1);
        governance.createProposal("Test proposal", 7 days);
        
        if (proposalId == 1) {
            vm.prank(voter1);
            governance.vote(proposalId, support);
            
            (,,,,, uint256 forVotes, uint256 againstVotes) = governance.proposals(proposalId);
            
            if (support) {
                assertEq(forVotes, VOTING_POWER);
                assertEq(againstVotes, 0);
            } else {
                assertEq(forVotes, 0);
                assertEq(againstVotes, VOTING_POWER);
            }
        } else {
            vm.prank(voter1);
            vm.expectRevert("Proposal does not exist");
            governance.vote(proposalId, support);
        }
    }
    
    function testMultipleVoters() public {
        vm.prank(voter1);
        uint256 proposalId = governance.createProposal("Test proposal", 7 days);
        
        vm.prank(voter1);
        governance.vote(proposalId, true);
        
        vm.prank(voter2);
        governance.vote(proposalId, true);
        
        vm.prank(voter3);
        governance.vote(proposalId, false);
        
        (,,,,, uint256 forVotes, uint256 againstVotes) = governance.proposals(proposalId);
        assertEq(forVotes, VOTING_POWER * 2);
        assertEq(againstVotes, VOTING_POWER);
    }
    
    function testGasOptimization() public {
        uint256 gasStart = gasleft();
        
        vm.prank(voter1);
        governance.createProposal("Test proposal", 7 days);
        
        uint256 gasUsed = gasStart - gasleft();
        console.log("Gas used for createProposal:", gasUsed);
        
        // Should be reasonable (adjust threshold as needed)
        assertLt(gasUsed, 300000);
    }
    
    function testProposalState() public {
        vm.prank(voter1);
        uint256 proposalId = governance.createProposal("Test proposal", 7 days);
        
        // Check initial state
        (,,,, bool executed,,) = governance.proposals(proposalId);
        assertFalse(executed);
        
        // Vote and execute
        vm.prank(voter1);
        governance.vote(proposalId, true);
        
        vm.warp(block.timestamp + 8 days);
        
        vm.prank(owner);
        governance.executeProposal(proposalId);
        
        // Check final state
        (,,,, executed,,) = governance.proposals(proposalId);
        assertTrue(executed);
    }
}

// Mock ERC20 token for testing
contract MockERC20 {
    string public name;
    string public symbol;
    uint8 public decimals = 18;
    uint256 public totalSupply;
    
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    
    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
    
    constructor(string memory _name, string memory _symbol, uint256 _totalSupply) {
        name = _name;
        symbol = _symbol;
        totalSupply = _totalSupply;
        balanceOf[msg.sender] = _totalSupply;
        emit Transfer(address(0), msg.sender, _totalSupply);
    }
    
    function transfer(address to, uint256 amount) public returns (bool) {
        require(balanceOf[msg.sender] >= amount, "Insufficient balance");
        balanceOf[msg.sender] -= amount;
        balanceOf[to] += amount;
        emit Transfer(msg.sender, to, amount);
        return true;
    }
    
    function approve(address spender, uint256 amount) public returns (bool) {
        allowance[msg.sender][spender] = amount;
        emit Approval(msg.sender, spender, amount);
        return true;
    }
    
    function transferFrom(address from, address to, uint256 amount) public returns (bool) {
        require(balanceOf[from] >= amount, "Insufficient balance");
        require(allowance[from][msg.sender] >= amount, "Insufficient allowance");
        
        balanceOf[from] -= amount;
        balanceOf[to] += amount;
        allowance[from][msg.sender] -= amount;
        
        emit Transfer(from, to, amount);
        return true;
    }
}
