// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";

/**
 * @title YieldFarming
 * @dev Yield farming contract with multiple pools and reward distribution
 * @author HyperKit AI Agent
 */
contract YieldFarming is Ownable, ReentrancyGuard, Pausable {
    using SafeERC20 for IERC20;
    using SafeMath for uint256;
    
    // Pool info
    struct PoolInfo {
        IERC20 lpToken;           // LP token contract
        IERC20 rewardToken;       // Reward token contract
        uint256 allocPoint;       // Allocation points for this pool
        uint256 lastRewardTime;   // Last time reward was calculated
        uint256 accRewardPerShare; // Accumulated reward per share
        uint256 totalStaked;      // Total amount staked in this pool
        uint256 rewardRate;       // Reward rate per second
        uint256 lockTime;         // Lock time in seconds
        bool active;              // Pool active status
    }
    
    // User info
    struct UserInfo {
        uint256 amount;           // Amount staked
        uint256 rewardDebt;       // Reward debt
        uint256 lastStakeTime;    // Last stake time
        uint256 pendingRewards;   // Pending rewards
    }
    
    // Pool array
    PoolInfo[] public poolInfo;
    
    // User info per pool
    mapping(uint256 => mapping(address => UserInfo)) public userInfo;
    
    // Total allocation points
    uint256 public totalAllocPoint = 0;
    
    // Reward per second
    uint256 public rewardPerSecond;
    
    // Start time
    uint256 public startTime;
    
    // End time
    uint256 public endTime;
    
    // Events
    event PoolAdded(uint256 indexed pid, address lpToken, address rewardToken, uint256 allocPoint);
    event PoolUpdated(uint256 indexed pid, uint256 allocPoint);
    event Deposit(address indexed user, uint256 indexed pid, uint256 amount);
    event Withdraw(address indexed user, uint256 indexed pid, uint256 amount);
    event EmergencyWithdraw(address indexed user, uint256 indexed pid, uint256 amount);
    event RewardPaid(address indexed user, uint256 indexed pid, uint256 amount);
    event RewardRateUpdated(uint256 newRate);
    event PoolActivated(uint256 indexed pid, bool active);
    
    constructor(
        uint256 _rewardPerSecond,
        uint256 _startTime,
        uint256 _endTime
    ) {
        rewardPerSecond = _rewardPerSecond;
        startTime = _startTime;
        endTime = _endTime;
    }
    
    /**
     * @dev Add a new pool
     * @param _lpToken LP token contract
     * @param _rewardToken Reward token contract
     * @param _allocPoint Allocation points
     * @param _rewardRate Reward rate per second
     * @param _lockTime Lock time in seconds
     */
    function addPool(
        IERC20 _lpToken,
        IERC20 _rewardToken,
        uint256 _allocPoint,
        uint256 _rewardRate,
        uint256 _lockTime
    ) external onlyOwner {
        require(address(_lpToken) != address(0), "Invalid LP token");
        require(address(_rewardToken) != address(0), "Invalid reward token");
        require(_allocPoint > 0, "Allocation points must be greater than 0");
        
        poolInfo.push(PoolInfo({
            lpToken: _lpToken,
            rewardToken: _rewardToken,
            allocPoint: _allocPoint,
            lastRewardTime: block.timestamp > startTime ? block.timestamp : startTime,
            accRewardPerShare: 0,
            totalStaked: 0,
            rewardRate: _rewardRate,
            lockTime: _lockTime,
            active: true
        }));
        
        totalAllocPoint = totalAllocPoint.add(_allocPoint);
        
        emit PoolAdded(poolInfo.length - 1, address(_lpToken), address(_rewardToken), _allocPoint);
    }
    
    /**
     * @dev Update pool allocation points
     * @param _pid Pool ID
     * @param _allocPoint New allocation points
     */
    function setPoolAllocPoint(uint256 _pid, uint256 _allocPoint) external onlyOwner {
        require(_pid < poolInfo.length, "Invalid pool ID");
        
        totalAllocPoint = totalAllocPoint.sub(poolInfo[_pid].allocPoint).add(_allocPoint);
        poolInfo[_pid].allocPoint = _allocPoint;
        
        emit PoolUpdated(_pid, _allocPoint);
    }
    
    /**
     * @dev Deposit LP tokens to a pool
     * @param _pid Pool ID
     * @param _amount Amount to deposit
     */
    function deposit(uint256 _pid, uint256 _amount) external nonReentrant whenNotPaused {
        require(_pid < poolInfo.length, "Invalid pool ID");
        require(poolInfo[_pid].active, "Pool not active");
        require(_amount > 0, "Amount must be greater than 0");
        
        PoolInfo storage pool = poolInfo[_pid];
        UserInfo storage user = userInfo[_pid][msg.sender];
        
        // Update pool
        updatePool(_pid);
        
        // Pay pending rewards
        if (user.amount > 0) {
            uint256 pending = user.amount.mul(pool.accRewardPerShare).div(1e12).sub(user.rewardDebt);
            if (pending > 0) {
                user.pendingRewards = user.pendingRewards.add(pending);
            }
        }
        
        // Transfer LP tokens from user
        pool.lpToken.safeTransferFrom(msg.sender, address(this), _amount);
        
        // Update user info
        user.amount = user.amount.add(_amount);
        user.rewardDebt = user.amount.mul(pool.accRewardPerShare).div(1e12);
        user.lastStakeTime = block.timestamp;
        
        // Update pool total staked
        pool.totalStaked = pool.totalStaked.add(_amount);
        
        emit Deposit(msg.sender, _pid, _amount);
    }
    
    /**
     * @dev Withdraw LP tokens from a pool
     * @param _pid Pool ID
     * @param _amount Amount to withdraw
     */
    function withdraw(uint256 _pid, uint256 _amount) external nonReentrant {
        require(_pid < poolInfo.length, "Invalid pool ID");
        require(_amount > 0, "Amount must be greater than 0");
        
        PoolInfo storage pool = poolInfo[_pid];
        UserInfo storage user = userInfo[_pid][msg.sender];
        
        require(user.amount >= _amount, "Insufficient staked amount");
        require(block.timestamp >= user.lastStakeTime.add(pool.lockTime), "Tokens still locked");
        
        // Update pool
        updatePool(_pid);
        
        // Pay pending rewards
        uint256 pending = user.amount.mul(pool.accRewardPerShare).div(1e12).sub(user.rewardDebt);
        if (pending > 0) {
            user.pendingRewards = user.pendingRewards.add(pending);
        }
        
        // Update user info
        user.amount = user.amount.sub(_amount);
        user.rewardDebt = user.amount.mul(pool.accRewardPerShare).div(1e12);
        
        // Update pool total staked
        pool.totalStaked = pool.totalStaked.sub(_amount);
        
        // Transfer LP tokens to user
        pool.lpToken.safeTransfer(msg.sender, _amount);
        
        emit Withdraw(msg.sender, _pid, _amount);
    }
    
    /**
     * @dev Claim rewards from a pool
     * @param _pid Pool ID
     */
    function claimRewards(uint256 _pid) external nonReentrant {
        require(_pid < poolInfo.length, "Invalid pool ID");
        
        PoolInfo storage pool = poolInfo[_pid];
        UserInfo storage user = userInfo[_pid][msg.sender];
        
        // Update pool
        updatePool(_pid);
        
        // Calculate pending rewards
        uint256 pending = user.amount.mul(pool.accRewardPerShare).div(1e12).sub(user.rewardDebt);
        if (pending > 0) {
            user.pendingRewards = user.pendingRewards.add(pending);
        }
        
        // Reset reward debt
        user.rewardDebt = user.amount.mul(pool.accRewardPerShare).div(1e12);
        
        // Transfer pending rewards
        if (user.pendingRewards > 0) {
            uint256 rewardAmount = user.pendingRewards;
            user.pendingRewards = 0;
            
            pool.rewardToken.safeTransfer(msg.sender, rewardAmount);
            
            emit RewardPaid(msg.sender, _pid, rewardAmount);
        }
    }
    
    /**
     * @dev Emergency withdraw (forfeit rewards)
     * @param _pid Pool ID
     */
    function emergencyWithdraw(uint256 _pid) external nonReentrant {
        require(_pid < poolInfo.length, "Invalid pool ID");
        
        PoolInfo storage pool = poolInfo[_pid];
        UserInfo storage user = userInfo[_pid][msg.sender];
        
        uint256 amount = user.amount;
        require(amount > 0, "No staked amount");
        
        // Reset user info
        user.amount = 0;
        user.rewardDebt = 0;
        user.pendingRewards = 0;
        
        // Update pool total staked
        pool.totalStaked = pool.totalStaked.sub(amount);
        
        // Transfer LP tokens to user
        pool.lpToken.safeTransfer(msg.sender, amount);
        
        emit EmergencyWithdraw(msg.sender, _pid, amount);
    }
    
    /**
     * @dev Update pool rewards
     * @param _pid Pool ID
     */
    function updatePool(uint256 _pid) public {
        require(_pid < poolInfo.length, "Invalid pool ID");
        
        PoolInfo storage pool = poolInfo[_pid];
        
        if (block.timestamp <= pool.lastRewardTime) {
            return;
        }
        
        if (pool.totalStaked == 0) {
            pool.lastRewardTime = block.timestamp;
            return;
        }
        
        uint256 multiplier = getMultiplier(pool.lastRewardTime, block.timestamp);
        uint256 reward = multiplier.mul(pool.rewardRate).mul(pool.allocPoint).div(totalAllocPoint);
        
        pool.accRewardPerShare = pool.accRewardPerShare.add(reward.mul(1e12).div(pool.totalStaked));
        pool.lastRewardTime = block.timestamp;
    }
    
    /**
     * @dev Get multiplier for time period
     * @param _from Start time
     * @param _to End time
     * @return Multiplier
     */
    function getMultiplier(uint256 _from, uint256 _to) public view returns (uint256) {
        if (_to <= endTime) {
            return _to.sub(_from);
        } else if (_from >= endTime) {
            return 0;
        } else {
            return endTime.sub(_from);
        }
    }
    
    /**
     * @dev Get pending rewards for a user
     * @param _pid Pool ID
     * @param _user User address
     * @return Pending rewards
     */
    function pendingRewards(uint256 _pid, address _user) external view returns (uint256) {
        require(_pid < poolInfo.length, "Invalid pool ID");
        
        PoolInfo storage pool = poolInfo[_pid];
        UserInfo storage user = userInfo[_pid][_user];
        
        uint256 accRewardPerShare = pool.accRewardPerShare;
        uint256 totalStaked = pool.totalStaked;
        
        if (block.timestamp > pool.lastRewardTime && totalStaked != 0) {
            uint256 multiplier = getMultiplier(pool.lastRewardTime, block.timestamp);
            uint256 reward = multiplier.mul(pool.rewardRate).mul(pool.allocPoint).div(totalAllocPoint);
            accRewardPerShare = accRewardPerShare.add(reward.mul(1e12).div(totalStaked));
        }
        
        return user.amount.mul(accRewardPerShare).div(1e12).sub(user.rewardDebt).add(user.pendingRewards);
    }
    
    /**
     * @dev Get pool count
     * @return Pool count
     */
    function poolLength() external view returns (uint256) {
        return poolInfo.length;
    }
    
    /**
     * @dev Set reward rate (only owner)
     * @param _rewardPerSecond New reward rate
     */
    function setRewardRate(uint256 _rewardPerSecond) external onlyOwner {
        rewardPerSecond = _rewardPerSecond;
        emit RewardRateUpdated(_rewardPerSecond);
    }
    
    /**
     * @dev Set pool active status (only owner)
     * @param _pid Pool ID
     * @param _active Active status
     */
    function setPoolActive(uint256 _pid, bool _active) external onlyOwner {
        require(_pid < poolInfo.length, "Invalid pool ID");
        poolInfo[_pid].active = _active;
        emit PoolActivated(_pid, _active);
    }
    
    /**
     * @dev Pause contract (only owner)
     */
    function pause() external onlyOwner {
        _pause();
    }
    
    /**
     * @dev Unpause contract (only owner)
     */
    function unpause() external onlyOwner {
        _unpause();
    }
    
    /**
     * @dev Deposit reward tokens (only owner)
     * @param _pid Pool ID
     * @param _amount Amount to deposit
     */
    function depositRewards(uint256 _pid, uint256 _amount) external onlyOwner {
        require(_pid < poolInfo.length, "Invalid pool ID");
        require(_amount > 0, "Amount must be greater than 0");
        
        PoolInfo storage pool = poolInfo[_pid];
        pool.rewardToken.safeTransferFrom(msg.sender, address(this), _amount);
    }
    
    /**
     * @dev Withdraw reward tokens (only owner)
     * @param _pid Pool ID
     * @param _amount Amount to withdraw
     */
    function withdrawRewards(uint256 _pid, uint256 _amount) external onlyOwner {
        require(_pid < poolInfo.length, "Invalid pool ID");
        require(_amount > 0, "Amount must be greater than 0");
        
        PoolInfo storage pool = poolInfo[_pid];
        pool.rewardToken.safeTransfer(msg.sender, _amount);
    }
}
