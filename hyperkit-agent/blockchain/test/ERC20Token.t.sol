// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "forge-std/console.sol";
import "../contracts/agent_generate/HyperToken.sol";

contract ERC20TokenTest is Test {
    HyperToken public token;
    
    address public owner = address(0x1);
    address public user1 = address(0x2);
    address public user2 = address(0x3);
    address public spender = address(0x4);
    
    uint256 public constant INITIAL_SUPPLY = 1000000 * 10**18;
    uint256 public constant TRANSFER_AMOUNT = 1000 * 10**18;
    
    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
    event Mint(address indexed to, uint256 amount);
    event Burn(address indexed from, uint256 amount);
    
    function setUp() public {
        vm.prank(owner);
        token = new HyperToken("HyperToken", "HYP", INITIAL_SUPPLY);
    }
    
    function testInitialState() public {
        assertEq(token.name(), "HyperToken");
        assertEq(token.symbol(), "HYP");
        assertEq(token.decimals(), 18);
        assertEq(token.totalSupply(), INITIAL_SUPPLY);
        assertEq(token.balanceOf(owner), INITIAL_SUPPLY);
    }
    
    function testTransfer() public {
        vm.prank(owner);
        bool success = token.transfer(user1, TRANSFER_AMOUNT);
        
        assertTrue(success);
        assertEq(token.balanceOf(owner), INITIAL_SUPPLY - TRANSFER_AMOUNT);
        assertEq(token.balanceOf(user1), TRANSFER_AMOUNT);
    }
    
    function testTransferInsufficientBalance() public {
        vm.prank(user1);
        vm.expectRevert("ERC20: transfer amount exceeds balance");
        token.transfer(user2, TRANSFER_AMOUNT);
    }
    
    function testTransferZeroAmount() public {
        vm.prank(owner);
        bool success = token.transfer(user1, 0);
        
        assertTrue(success);
        assertEq(token.balanceOf(owner), INITIAL_SUPPLY);
        assertEq(token.balanceOf(user1), 0);
    }
    
    function testTransferToZeroAddress() public {
        vm.prank(owner);
        vm.expectRevert("ERC20: transfer to the zero address");
        token.transfer(address(0), TRANSFER_AMOUNT);
    }
    
    function testApprove() public {
        vm.prank(owner);
        bool success = token.approve(spender, TRANSFER_AMOUNT);
        
        assertTrue(success);
        assertEq(token.allowance(owner, spender), TRANSFER_AMOUNT);
    }
    
    function testTransferFrom() public {
        vm.prank(owner);
        token.approve(spender, TRANSFER_AMOUNT);
        
        vm.prank(spender);
        bool success = token.transferFrom(owner, user1, TRANSFER_AMOUNT);
        
        assertTrue(success);
        assertEq(token.balanceOf(owner), INITIAL_SUPPLY - TRANSFER_AMOUNT);
        assertEq(token.balanceOf(user1), TRANSFER_AMOUNT);
        assertEq(token.allowance(owner, spender), 0);
    }
    
    function testTransferFromInsufficientAllowance() public {
        vm.prank(owner);
        token.approve(spender, TRANSFER_AMOUNT - 1);
        
        vm.prank(spender);
        vm.expectRevert("ERC20: insufficient allowance");
        token.transferFrom(owner, user1, TRANSFER_AMOUNT);
    }
    
    function testTransferFromInsufficientBalance() public {
        vm.prank(user1);
        token.approve(spender, TRANSFER_AMOUNT);
        
        vm.prank(spender);
        vm.expectRevert("ERC20: transfer amount exceeds balance");
        token.transferFrom(user1, user2, TRANSFER_AMOUNT);
    }
    
    function testMint() public {
        uint256 mintAmount = 1000 * 10**18;
        
        vm.prank(owner);
        token.mint(user1, mintAmount);
        
        assertEq(token.balanceOf(user1), mintAmount);
        assertEq(token.totalSupply(), INITIAL_SUPPLY + mintAmount);
    }
    
    function testMintOnlyOwner() public {
        vm.prank(user1);
        vm.expectRevert("Ownable: caller is not the owner");
        token.mint(user1, 1000 * 10**18);
    }
    
    function testMintZeroAmount() public {
        vm.prank(owner);
        vm.expectRevert("Amount must be greater than 0");
        token.mint(user1, 0);
    }
    
    function testBurn() public {
        uint256 burnAmount = 1000 * 10**18;
        
        vm.prank(owner);
        token.burn(burnAmount);
        
        assertEq(token.balanceOf(owner), INITIAL_SUPPLY - burnAmount);
        assertEq(token.totalSupply(), INITIAL_SUPPLY - burnAmount);
    }
    
    function testBurnInsufficientBalance() public {
        vm.prank(user1);
        vm.expectRevert("ERC20: burn amount exceeds balance");
        token.burn(1000 * 10**18);
    }
    
    function testBurnZeroAmount() public {
        vm.prank(owner);
        vm.expectRevert("Amount must be greater than 0");
        token.burn(0);
    }
    
    function testFuzzTransfer(uint256 amount) public {
        vm.assume(amount <= INITIAL_SUPPLY);
        
        vm.prank(owner);
        bool success = token.transfer(user1, amount);
        
        assertTrue(success);
        assertEq(token.balanceOf(owner), INITIAL_SUPPLY - amount);
        assertEq(token.balanceOf(user1), amount);
    }
    
    function testFuzzApprove(uint256 amount) public {
        vm.prank(owner);
        bool success = token.approve(spender, amount);
        
        assertTrue(success);
        assertEq(token.allowance(owner, spender), amount);
    }
    
    function testFuzzMint(uint256 amount) public {
        vm.assume(amount > 0 && amount <= 1000000 * 10**18);
        
        vm.prank(owner);
        token.mint(user1, amount);
        
        assertEq(token.balanceOf(user1), amount);
        assertEq(token.totalSupply(), INITIAL_SUPPLY + amount);
    }
    
    function testFuzzBurn(uint256 amount) public {
        vm.assume(amount > 0 && amount <= INITIAL_SUPPLY);
        
        vm.prank(owner);
        token.burn(amount);
        
        assertEq(token.balanceOf(owner), INITIAL_SUPPLY - amount);
        assertEq(token.totalSupply(), INITIAL_SUPPLY - amount);
    }
    
    function testGasOptimization() public {
        // Test gas usage for common operations
        uint256 gasStart = gasleft();
        
        vm.prank(owner);
        token.transfer(user1, TRANSFER_AMOUNT);
        
        uint256 gasUsed = gasStart - gasleft();
        console.log("Gas used for transfer:", gasUsed);
        
        // Should be reasonable (adjust threshold as needed)
        assertLt(gasUsed, 100000);
    }
    
    function testMultipleTransfers() public {
        vm.startPrank(owner);
        
        token.transfer(user1, TRANSFER_AMOUNT);
        token.transfer(user2, TRANSFER_AMOUNT);
        
        vm.stopPrank();
        
        assertEq(token.balanceOf(user1), TRANSFER_AMOUNT);
        assertEq(token.balanceOf(user2), TRANSFER_AMOUNT);
        assertEq(token.balanceOf(owner), INITIAL_SUPPLY - (TRANSFER_AMOUNT * 2));
    }
    
    function testAllowanceDecrease() public {
        vm.prank(owner);
        token.approve(spender, TRANSFER_AMOUNT * 2);
        
        vm.prank(spender);
        token.transferFrom(owner, user1, TRANSFER_AMOUNT);
        
        assertEq(token.allowance(owner, spender), TRANSFER_AMOUNT);
    }
    
    function testAllowanceIncrease() public {
        vm.prank(owner);
        token.approve(spender, TRANSFER_AMOUNT);
        
        vm.prank(owner);
        token.approve(spender, TRANSFER_AMOUNT * 2);
        
        assertEq(token.allowance(owner, spender), TRANSFER_AMOUNT * 2);
    }
}
