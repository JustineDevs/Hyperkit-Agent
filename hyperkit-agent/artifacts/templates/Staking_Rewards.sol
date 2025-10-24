// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";

/**
 * @title StakingRewards
 * @dev Staking contract with reward distribution
 * @author HyperKit AI Agent
 */
contract StakingRewards is Ownable, ReentrancyGuard, Pausable {
    using SafeERC20 for IERC20;
    using SafeMath for uint256;
    
    // Staking token
    IERC20 public stakingToken;
    
    // Reward token
    IERC20 public rewardToken;
    
    // Staking period
    uint256 public stakingPeriod;
    
    // Reward rate (tokens per second)
    uint256 public rewardRate;
    
    // Last update time
    uint256 public lastUpdateTime;
    
    // Reward per token stored
    uint256 public rewardPerTokenStored;
    
    // User staking info
    struct UserStake {
        uint256 amount;
        uint256 rewardPerTokenPaid;
        uint256 rewards;
        uint256 stakeTime;
        uint256 lockTime;
    }
    
    // User stakes
    mapping(address => UserStake) public userStakes;
    
    // Total staked amount
    uint256 public totalStaked;
    
    // Total rewards distributed
    uint256 public totalRewardsDistributed;
    
    // Events
    event Staked(address indexed user, uint256 amount, uint256 lockTime);
    event Withdrawn(address indexed user, uint256 amount);
    event RewardPaid(address indexed user, uint256 reward);
    event RewardRateUpdated(uint256 newRate);
    event StakingPeriodUpdated(uint256 newPeriod);
    event EmergencyWithdraw(address indexed user, uint256 amount);
    
    constructor(
        address _stakingToken,
        address _rewardToken,
        uint256 _rewardRate,
        uint256 _stakingPeriod
    ) {
        stakingToken = IERC20(_stakingToken);
        rewardToken = IERC20(_rewardToken);
        rewardRate = _rewardRate;
        stakingPeriod = _stakingPeriod;
        lastUpdateTime = block.timestamp;
    }
    
    /**
     * @dev Stake tokens
     * @param amount Amount to stake
     */
    function stake(uint256 amount) external nonReentrant whenNotPaused {
        require(amount > 0, "Amount must be greater than 0");
        require(stakingToken.balanceOf(msg.sender) >= amount, "Insufficient balance");
        
        // Update rewards for user
        _updateReward(msg.sender);
        
        // Transfer staking tokens from user
        stakingToken.safeTransferFrom(msg.sender, address(this), amount);
        
        // Update user stake
        UserStake storage userStake = userStakes[msg.sender];
        userStake.amount = userStake.amount.add(amount);
        userStake.stakeTime = block.timestamp;
        userStake.lockTime = block.timestamp.add(stakingPeriod);
        
        // Update total staked
        totalStaked = totalStaked.add(amount);
        
        emit Staked(msg.sender, amount, userStake.lockTime);
    }
    
    /**
     * @dev Withdraw staked tokens
     * @param amount Amount to withdraw
     */
    function withdraw(uint256 amount) external nonReentrant {
        require(amount > 0, "Amount must be greater than 0");
        require(userStakes[msg.sender].amount >= amount, "Insufficient staked amount");
        require(block.timestamp >= userStakes[msg.sender].lockTime, "Tokens still locked");
        
        // Update rewards for user
        _updateReward(msg.sender);
        
        // Update user stake
        UserStake storage userStake = userStakes[msg.sender];
        userStake.amount = userStake.amount.sub(amount);
        
        // Update total staked
        totalStaked = totalStaked.sub(amount);
        
        // Transfer staking tokens to user
        stakingToken.safeTransfer(msg.sender, amount);
        
        emit Withdrawn(msg.sender, amount);
    }
    
    /**
     * @dev Claim rewards
     */
    function claimRewards() external nonReentrant {
        _updateReward(msg.sender);
        
        uint256 reward = userStakes[msg.sender].rewards;
        if (reward > 0) {
            userStakes[msg.sender].rewards = 0;
            totalRewardsDistributed = totalRewardsDistributed.add(reward);
            
            rewardToken.safeTransfer(msg.sender, reward);
            
            emit RewardPaid(msg.sender, reward);
        }
    }
    
    /**
     * @dev Emergency withdraw (forfeit rewards)
     */
    function emergencyWithdraw() external nonReentrant {
        UserStake storage userStake = userStakes[msg.sender];
        uint256 amount = userStake.amount;
        
        require(amount > 0, "No staked amount");
        
        // Reset user stake
        userStake.amount = 0;
        userStake.rewards = 0;
        userStake.rewardPerTokenPaid = 0;
        
        // Update total staked
        totalStaked = totalStaked.sub(amount);
        
        // Transfer staking tokens to user
        stakingToken.safeTransfer(msg.sender, amount);
        
        emit EmergencyWithdraw(msg.sender, amount);
    }
    
    /**
     * @dev Update reward for a user
     * @param user User address
     */
    function _updateReward(address user) internal {
        rewardPerTokenStored = rewardPerToken();
        lastUpdateTime = lastTimeRewardApplicable();
        
        if (user != address(0)) {
            UserStake storage userStake = userStakes[user];
            userStake.rewards = earned(user);
            userStake.rewardPerTokenPaid = rewardPerTokenStored;
        }
    }
    
    /**
     * @dev Calculate reward per token
     * @return Reward per token
     */
    function rewardPerToken() public view returns (uint256) {
        if (totalStaked == 0) {
            return rewardPerTokenStored;
        }
        
        return rewardPerTokenStored.add(
            lastTimeRewardApplicable()
                .sub(lastUpdateTime)
                .mul(rewardRate)
                .mul(1e18)
                .div(totalStaked)
        );
    }
    
    /**
     * @dev Get last time reward was applicable
     * @return Last time reward was applicable
     */
    function lastTimeRewardApplicable() public view returns (uint256) {
        return block.timestamp;
    }
    
    /**
     * @dev Calculate earned rewards for a user
     * @param user User address
     * @return Earned rewards
     */
    function earned(address user) public view returns (uint256) {
        UserStake memory userStake = userStakes[user];
        
        return userStake.amount
            .mul(rewardPerToken().sub(userStake.rewardPerTokenPaid))
            .div(1e18)
            .add(userStake.rewards);
    }
    
    /**
     * @dev Get user staking info
     * @param user User address
     * @return User stake info
     */
    function getUserStake(address user) external view returns (UserStake memory) {
        return userStakes[user];
    }
    
    /**
     * @dev Check if user can withdraw
     * @param user User address
     * @return True if can withdraw
     */
    function canWithdraw(address user) external view returns (bool) {
        return block.timestamp >= userStakes[user].lockTime;
    }
    
    /**
     * @dev Get remaining lock time for user
     * @param user User address
     * @return Remaining lock time in seconds
     */
    function getRemainingLockTime(address user) external view returns (uint256) {
        if (block.timestamp >= userStakes[user].lockTime) {
            return 0;
        }
        return userStakes[user].lockTime.sub(block.timestamp);
    }
    
    /**
     * @dev Set reward rate (only owner)
     * @param newRate New reward rate
     */
    function setRewardRate(uint256 newRate) external onlyOwner {
        _updateReward(address(0)); // Update global state
        rewardRate = newRate;
        emit RewardRateUpdated(newRate);
    }
    
    /**
     * @dev Set staking period (only owner)
     * @param newPeriod New staking period in seconds
     */
    function setStakingPeriod(uint256 newPeriod) external onlyOwner {
        stakingPeriod = newPeriod;
        emit StakingPeriodUpdated(newPeriod);
    }
    
    /**
     * @dev Pause staking (only owner)
     */
    function pause() external onlyOwner {
        _pause();
    }
    
    /**
     * @dev Unpause staking (only owner)
     */
    function unpause() external onlyOwner {
        _unpause();
    }
    
    /**
     * @dev Deposit reward tokens (only owner)
     * @param amount Amount of reward tokens to deposit
     */
    function depositRewards(uint256 amount) external onlyOwner {
        require(amount > 0, "Amount must be greater than 0");
        rewardToken.safeTransferFrom(msg.sender, address(this), amount);
    }
    
    /**
     * @dev Withdraw reward tokens (only owner)
     * @param amount Amount of reward tokens to withdraw
     */
    function withdrawRewards(uint256 amount) external onlyOwner {
        require(amount > 0, "Amount must be greater than 0");
        rewardToken.safeTransfer(msg.sender, amount);
    }
    
    /**
     * @dev Get contract balance of staking token
     * @return Balance
     */
    function getStakingTokenBalance() external view returns (uint256) {
        return stakingToken.balanceOf(address(this));
    }
    
    /**
     * @dev Get contract balance of reward token
     * @return Balance
     */
    function getRewardTokenBalance() external view returns (uint256) {
        return rewardToken.balanceOf(address(this));
    }
}
