// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

/**
 * @title LinearVesting
 * @dev Linear token vesting contract
 * @notice This contract handles token vesting with linear distribution
 * @author HyperKit Agent
 */
contract LinearVesting is Ownable, ReentrancyGuard, Pausable {
    IERC20 public immutable token;
    
    struct VestingSchedule {
        uint256 totalAmount;
        uint256 startTime;
        uint256 duration;
        uint256 cliff;
        uint256 released;
        bool revocable;
        bool revoked;
    }
    
    mapping(address => VestingSchedule) public vestingSchedules;
    mapping(address => bool) public hasVestingSchedule;
    
    uint256 public totalVested;
    uint256 public totalReleased;
    
    event VestingScheduleCreated(address indexed beneficiary, uint256 totalAmount, uint256 startTime, uint256 duration);
    event TokensReleased(address indexed beneficiary, uint256 amount);
    event VestingRevoked(address indexed beneficiary);
    
    constructor(address _token) {
        require(_token != address(0), "Invalid token address");
        token = IERC20(_token);
    }
    
    function createVestingSchedule(
        address beneficiary,
        uint256 totalAmount,
        uint256 startTime,
        uint256 duration,
        uint256 cliff,
        bool revocable
    ) external onlyOwner {
        require(beneficiary != address(0), "Invalid beneficiary");
        require(totalAmount > 0, "Invalid amount");
        require(!hasVestingSchedule[beneficiary], "Vesting already exists");
        require(startTime >= block.timestamp, "Invalid start time");
        require(duration > 0, "Invalid duration");
        require(cliff <= duration, "Cliff exceeds duration");
        
        vestingSchedules[beneficiary] = VestingSchedule(
            totalAmount,
            startTime,
            duration,
            cliff,
            0,
            revocable,
            false
        );
        
        hasVestingSchedule[beneficiary] = true;
        totalVested += totalAmount;
        
        emit VestingScheduleCreated(beneficiary, totalAmount, startTime, duration);
    }
    
    function release() external nonReentrant whenNotPaused {
        require(hasVestingSchedule[msg.sender], "No vesting schedule");
        require(!vestingSchedules[msg.sender].revoked, "Vesting revoked");
        
        uint256 releasableAmount = getReleasableAmount(msg.sender);
        require(releasableAmount > 0, "No tokens to release");
        
        vestingSchedules[msg.sender].released += releasableAmount;
        totalReleased += releasableAmount;
        
        require(token.transfer(msg.sender, releasableAmount), "Transfer failed");
        
        emit TokensReleased(msg.sender, releasableAmount);
    }
    
    function getReleasableAmount(address beneficiary) public view returns (uint256) {
        if (!hasVestingSchedule[beneficiary] || vestingSchedules[beneficiary].revoked) {
            return 0;
        }
        
        VestingSchedule memory schedule = vestingSchedules[beneficiary];
        uint256 currentTime = block.timestamp;
        
        if (currentTime < schedule.startTime + schedule.cliff) {
            return 0;
        }
        
        uint256 vestedAmount = getVestedAmount(beneficiary);
        return vestedAmount - schedule.released;
    }
    
    function getVestedAmount(address beneficiary) public view returns (uint256) {
        if (!hasVestingSchedule[beneficiary] || vestingSchedules[beneficiary].revoked) {
            return 0;
        }
        
        VestingSchedule memory schedule = vestingSchedules[beneficiary];
        uint256 currentTime = block.timestamp;
        
        if (currentTime < schedule.startTime) {
            return 0;
        }
        
        if (currentTime >= schedule.startTime + schedule.duration) {
            return schedule.totalAmount;
        }
        
        return (schedule.totalAmount * (currentTime - schedule.startTime)) / schedule.duration;
    }
    
    function revokeVesting(address beneficiary) external onlyOwner {
        require(hasVestingSchedule[beneficiary], "No vesting schedule");
        require(vestingSchedules[beneficiary].revocable, "Not revocable");
        require(!vestingSchedules[beneficiary].revoked, "Already revoked");
        
        vestingSchedules[beneficiary].revoked = true;
        
        emit VestingRevoked(beneficiary);
    }
    
    function emergencyWithdraw() external onlyOwner {
        uint256 balance = token.balanceOf(address(this));
        require(balance > 0, "No tokens to withdraw");
        require(token.transfer(owner(), balance), "Transfer failed");
    }
}