// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "forge-std/console.sol";
import "../contracts/agent_generate/defi_staking.sol";

contract VaultTest is Test {
    Vault public vault;
    MockERC20 public token;
    
    address public owner = address(0x1);
    address public user1 = address(0x2);
    address public user2 = address(0x3);
    
    uint256 public constant INITIAL_SUPPLY = 1000000 * 10**18;
    uint256 public constant STAKE_AMOUNT = 1000 * 10**18;
    
    event Staked(address indexed user, uint256 amount, uint256 timestamp);
    event Unstaked(address indexed user, uint256 amount, uint256 timestamp);
    event RewardsClaimed(address indexed user, uint256 amount, uint256 timestamp);
    
    function setUp() public {
        // Deploy mock ERC20 token
        token = new MockERC20("Test Token", "TEST", INITIAL_SUPPLY);
        
        // Deploy vault
        vault = new Vault(address(token));
        
        // Transfer tokens to users
        token.transfer(user1, STAKE_AMOUNT * 2);
        token.transfer(user2, STAKE_AMOUNT * 2);
        
        // Approve vault to spend tokens
        vm.prank(user1);
        token.approve(address(vault), type(uint256).max);
        
        vm.prank(user2);
        token.approve(address(vault), type(uint256).max);
    }
    
    function testInitialState() public {
        assertEq(vault.owner(), owner);
        assertEq(address(vault.stakingToken()), address(token));
        assertEq(vault.totalStaked(), 0);
        assertEq(vault.rewardRate(), 0);
    }
    
    function testStake() public {
        vm.prank(user1);
        vault.stake(STAKE_AMOUNT);
        
        assertEq(vault.balanceOf(user1), STAKE_AMOUNT);
        assertEq(vault.totalStaked(), STAKE_AMOUNT);
        assertEq(token.balanceOf(address(vault)), STAKE_AMOUNT);
    }
    
    function testStakeZeroAmount() public {
        vm.prank(user1);
        vm.expectRevert("Amount must be greater than 0");
        vault.stake(0);
    }
    
    function testStakeInsufficientBalance() public {
        vm.prank(user1);
        vm.expectRevert("Insufficient token balance");
        vault.stake(STAKE_AMOUNT * 10);
    }
    
    function testUnstake() public {
        // First stake
        vm.prank(user1);
        vault.stake(STAKE_AMOUNT);
        
        // Then unstake
        vm.prank(user1);
        vault.unstake(STAKE_AMOUNT);
        
        assertEq(vault.balanceOf(user1), 0);
        assertEq(vault.totalStaked(), 0);
        assertEq(token.balanceOf(user1), STAKE_AMOUNT * 2);
    }
    
    function testUnstakeZeroAmount() public {
        vm.prank(user1);
        vault.stake(STAKE_AMOUNT);
        
        vm.prank(user1);
        vm.expectRevert("Amount must be greater than 0");
        vault.unstake(0);
    }
    
    function testUnstakeInsufficientStake() public {
        vm.prank(user1);
        vault.stake(STAKE_AMOUNT);
        
        vm.prank(user1);
        vm.expectRevert("Insufficient staked amount");
        vault.unstake(STAKE_AMOUNT + 1);
    }
    
    function testFuzzStake(uint256 amount) public {
        vm.assume(amount > 0 && amount <= STAKE_AMOUNT);
        
        vm.prank(user1);
        vault.stake(amount);
        
        assertEq(vault.balanceOf(user1), amount);
        assertEq(vault.totalStaked(), amount);
    }
    
    function testFuzzUnstake(uint256 stakeAmount, uint256 unstakeAmount) public {
        vm.assume(stakeAmount > 0 && stakeAmount <= STAKE_AMOUNT);
        vm.assume(unstakeAmount > 0 && unstakeAmount <= stakeAmount);
        
        vm.prank(user1);
        vault.stake(stakeAmount);
        
        vm.prank(user1);
        vault.unstake(unstakeAmount);
        
        assertEq(vault.balanceOf(user1), stakeAmount - unstakeAmount);
        assertEq(vault.totalStaked(), stakeAmount - unstakeAmount);
    }
    
    function testMultipleUsersStake() public {
        vm.prank(user1);
        vault.stake(STAKE_AMOUNT);
        
        vm.prank(user2);
        vault.stake(STAKE_AMOUNT);
        
        assertEq(vault.balanceOf(user1), STAKE_AMOUNT);
        assertEq(vault.balanceOf(user2), STAKE_AMOUNT);
        assertEq(vault.totalStaked(), STAKE_AMOUNT * 2);
    }
    
    function testSetRewardRate() public {
        uint256 newRate = 100;
        
        vm.prank(owner);
        vault.setRewardRate(newRate);
        
        assertEq(vault.rewardRate(), newRate);
    }
    
    function testSetRewardRateOnlyOwner() public {
        vm.prank(user1);
        vm.expectRevert("Ownable: caller is not the owner");
        vault.setRewardRate(100);
    }
    
    function testEmergencyWithdraw() public {
        vm.prank(user1);
        vault.stake(STAKE_AMOUNT);
        
        vm.prank(owner);
        vault.emergencyWithdraw();
        
        assertEq(vault.totalStaked(), 0);
        assertEq(token.balanceOf(address(vault)), 0);
    }
    
    function testEmergencyWithdrawOnlyOwner() public {
        vm.prank(user1);
        vault.stake(STAKE_AMOUNT);
        
        vm.prank(user1);
        vm.expectRevert("Ownable: caller is not the owner");
        vault.emergencyWithdraw();
    }
    
    function testGasOptimization() public {
        // Test gas usage for common operations
        uint256 gasStart = gasleft();
        
        vm.prank(user1);
        vault.stake(STAKE_AMOUNT);
        
        uint256 gasUsed = gasStart - gasleft();
        console.log("Gas used for stake:", gasUsed);
        
        // Should be reasonable (adjust threshold as needed)
        assertLt(gasUsed, 200000);
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
