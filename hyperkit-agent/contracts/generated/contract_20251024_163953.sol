// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// OpenZeppelin Imports
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

/**
 * @title MetisStakingContract
 * @author Expert Solidity Developer
 * @notice A secure, production-ready ERC20 staking contract with a dynamic APY.
 * @dev This contract allows users to stake an ERC20 token to earn rewards based on a configurable
 *      Annual Percentage Yield (APY). It includes features like a lock-in period, early withdrawal
 *      penalties, and anti-whale limits. It is designed with security best practices,
 *      including ReentrancyGuard, Pausable, and the checks-effects-interactions pattern.
 *      This contract is compatible with any EVM chain, including Metis (Chain ID: 1088).
 */
contract MetisStakingContract is Ownable, ReentrancyGuard, Pausable {
    
    // --- State Variables ---

    /// @notice The ERC20 token used for staking and rewards.
    IERC20 public immutable stakingToken;

    // Staking configuration
    uint256 public constant MINIMUM_STAKE = 1000 * 1e18;
    uint256 public constant MAXIMUM_STAKE_PER_USER = 1_000_000 * 1e18;
    uint256 public lockPeriod;
    uint256 public earlyWithdrawalPenaltyBps; // In basis points (1% = 100)
    
    // Reward calculation variables
    uint256 public currentApyBps; // APY in basis points
    uint256 public totalStaked;
    
    /// @dev The rate of rewards distributed per second.
    uint256 public rewardRate;
    
    /// @dev The timestamp of the last time rewards were updated.
    uint256 public lastUpdateTime;
    
    /// @dev The accumulated rewards per token, scaled by 1e18.
    uint256 public rewardPerTokenStored;

    // User-specific data
    struct StakerInfo {
        uint256 amount;
        uint256 stakeTimestamp;
    }
    
    mapping(address => StakerInfo) public stakers;
    mapping(address => uint256) public userRewardPerTokenPaid;
    mapping(address => uint256) public rewards;

    /// @notice Total penalty fees collected from early withdrawals.
    uint256 public collectedPenalties;

    // --- Constants ---

    uint256 private constant BPS_DIVISOR = 10000;
    uint256 private constant SECONDS_IN_YEAR = 365 days;
    uint256 private constant PRECISION = 1e18;

    // --- Events ---

    event Staked(address indexed user, uint256 amount);
    event Unstaked(address indexed user, uint256 amount, uint256 penalty);
    event RewardClaimed(address indexed user, uint256 amount);
    event ApyUpdated(uint256 newApyBps);
    event PenaltiesWithdrawn(address indexed owner, uint256 amount);
    event LockPeriodUpdated(uint256 newLockPeriod);
    event PenaltyRateUpdated(uint256 newPenaltyBps);

    // --- Custom Errors ---

    error ZeroAmount();
    error AmountLessThanMinimum();
    error AmountExceedsMaximum();
    error InsufficientStakedAmount();
    error TransferFailed();
    error InvalidApy();
    error InvalidLockPeriod();
    error InvalidPenaltyRate();
    error ZeroAddress();

    // --- Constructor ---

    /**
     * @notice Initializes the staking contract.
     * @param _stakingToken The address of the ERC20 token to be used for staking.
     */
    constructor(address _stakingToken) Ownable(msg.sender) {
        if (_stakingToken == address(0)) {
            revert ZeroAddress();
        }
        stakingToken = IERC20(_stakingToken);
        
        // Initialize with default values from user request
        currentApyBps = 1200; // 12% APY
        lockPeriod = 7 days;
        earlyWithdrawalPenaltyBps = 1000; // 10% Penalty
        lastUpdateTime = block.timestamp;
    }

    // --- Modifiers ---

    /**
     * @dev Modifier to update reward calculations for a user before a state change.
     *      It ensures that rewards are calculated based on the latest state.
     */
    modifier updateReward(address _account) {
        rewardPerTokenStored = rewardPerToken();
        lastUpdateTime = block.timestamp;
        
        if (_account != address(0)) {
            rewards[_account] = earned(_account);
            userRewardPerTokenPaid[_account] = rewardPerTokenStored;
        }
        _;
    }

    // --- External Functions: Staking and Claiming ---

    /**
     * @notice Stakes a specified amount of tokens.
     * @dev The user must have approved the contract to spend their tokens beforehand.
     *      Rewards are updated before the new stake is added.
     * @param _amount The amount of tokens to stake.
     */
    function stake(uint256 _amount) external nonReentrant whenNotPaused updateReward(msg.sender) {
        if (_amount == 0) revert ZeroAmount();
        
        uint256 currentStake = stakers[msg.sender].amount;
        if (currentStake == 0 && _amount < MINIMUM_STAKE) {
            revert AmountLessThanMinimum();
        }
        if (currentStake + _amount > MAXIMUM_STAKE_PER_USER) {
            revert AmountExceedsMaximum();
        }

        // --- Effects ---
        totalStaked += _amount;
        stakers[msg.sender].amount += _amount;
        // Set stake timestamp only on the first stake to enforce the lock period
        if (currentStake == 0) {
            stakers[msg.sender].stakeTimestamp = block.timestamp;
        }
        
        _updateRewardRate();
        
        // --- Interaction ---
        if (!stakingToken.transferFrom(msg.sender, address(this), _amount)) {
            revert TransferFailed();
        }

        emit Staked(msg.sender, _amount);
    }
    
    /**
     * @notice Unstakes a specified amount of tokens.
     * @dev An early withdrawal penalty may be applied if unstaked before the lock period ends.
     *      Rewards are updated before the stake is removed.
     * @param _amount The amount of tokens to unstake.
     */
    function unstake(uint256 _amount) external nonReentrant whenNotPaused updateReward(msg.sender) {
        if (_amount == 0) revert ZeroAmount();
        if (stakers[msg.sender].amount < _amount) revert InsufficientStakedAmount();

        // --- Effects ---
        totalStaked -= _amount;
        stakers[msg.sender].amount -= _amount;
        
        _updateRewardRate();
        
        uint256 amountToReturn = _amount;
        uint256 penalty = 0;

        // Apply penalty if withdrawing early
        if (block.timestamp < stakers[msg.sender].stakeTimestamp + lockPeriod) {
            penalty = (_amount * earlyWithdrawalPenaltyBps) / BPS_DIVISOR;
            amountToReturn -= penalty;
            collectedPenalties += penalty;
        }
        
        // Reset stake timestamp if user unstakes their full balance
        if (stakers[msg.sender].amount == 0) {
            stakers[msg.sender].stakeTimestamp = 0;
        }

        // --- Interaction ---
        if (amountToReturn > 0) {
            if (!stakingToken.transfer(msg.sender, amountToReturn)) {
                revert TransferFailed();
            }
        }

        emit Unstaked(msg.sender, _amount, penalty);
    }

    /**
     * @notice Claims all available rewards for the caller.
     * @dev Rewards are transferred to the user's wallet.
     */
    function claimRewards() external nonReentrant updateReward(msg.sender) {
        uint256 rewardAmount = rewards[msg.sender];
        if (rewardAmount == 0) revert ZeroAmount();

        // --- Effects ---
        rewards[msg.sender] = 0;

        // --- Interaction ---
        if (!stakingToken.transfer(msg.sender, rewardAmount)) {
            revert TransferFailed();
        }
        
        emit RewardClaimed(msg.sender, rewardAmount);
    }

    /**
     * @notice Unstakes all tokens and claims all available rewards in a single transaction.
     */
    function exit() external {
        // `unstake` and `claimRewards` already handle `nonReentrant` and `updateReward`
        uint256 stakedAmount = stakers[msg.sender].amount;
        if (stakedAmount > 0) {
            unstake(stakedAmount);
        }
        // It's possible for a user to have rewards without any stake (e.g., they unstaked without claiming)
        if (rewards[msg.sender] > 0) {
            claimRewards();
        }
    }

    // --- Owner Functions ---

    /**
     * @notice Pauses staking and unstaking functionality. Can only be called by the owner.
     * @dev Claiming rewards and exiting is not affected.
     */
    function pause() external onlyOwner {
        _pause();
    }

    /**
     * @notice Unpauses staking and unstaking functionality. Can only be called by the owner.
     */
    function unpause() external onlyOwner {
        _unpause();
    }
    
    /**
     * @notice Updates the staking APY.
     * @dev This will affect the reward rate for all subsequent calculations.
     * @param _newApyBps The new APY in basis points (e.g., 15% is 1500).
     */
    function setApy(uint256 _newApyBps) external onlyOwner updateReward(address(0)) {
        if (_newApyBps == 0 || _newApyBps > BPS_DIVISOR) { // Max 100% APY
            revert InvalidApy();
        }
        currentApyBps = _newApyBps;
        _updateRewardRate();
        emit ApyUpdated(_newApyBps);
    }

    /**
     * @notice Updates the lock-in period for new stakes.
     * @param _newLockPeriod The new lock period in seconds.
     */
    function setLockPeriod(uint256 _newLockPeriod) external onlyOwner {
        if (_newLockPeriod == 0) revert InvalidLockPeriod();
        lockPeriod = _newLockPeriod;
        emit LockPeriodUpdated(_newLockPeriod);
    }

    /**
     * @notice Updates the early withdrawal penalty rate.
     * @param _newPenaltyBps The new penalty in basis points.
     */
    function setEarlyWithdrawalPenalty(uint256 _newPenaltyBps) external onlyOwner {
        if (_newPenaltyBps > BPS_DIVISOR) revert InvalidPenaltyRate(); // Cannot be more than 100%
        earlyWithdrawalPenaltyBps = _newPenaltyBps;
        emit PenaltyRateUpdated(_newPenaltyBps);
    }

    /**
     * @notice Withdraws collected penalty fees to the owner's address.
     */
    function withdrawPenalties() external onlyOwner nonReentrant {
        uint256 penaltyAmount = collectedPenalties;
        if (penaltyAmount == 0) revert ZeroAmount();
        
        collectedPenalties = 0;

        if (!stakingToken.transfer(owner(), penaltyAmount)) {
            revert TransferFailed();
        }
        emit PenaltiesWithdrawn(owner(), penaltyAmount);
    }

    /**
     * @notice Withdraws a specified amount of unallocated reward tokens from the contract.
     * @dev This is intended for recovering excess tokens sent to the contract that are not
     *      part of the total staked amount. Can only be called by the owner.
     * @param _amount The amount of tokens to withdraw.
     */
    function withdrawRewardTokens(uint256 _amount) external onlyOwner nonReentrant {
        if (_amount == 0) revert ZeroAmount();
        uint256 availableToWithdraw = stakingToken.balanceOf(address(this)) - totalStaked;
        if (_amount > availableToWithdraw) {
            revert InsufficientStakedAmount(); // Reusing error for insufficient contract balance
        }

        if (!stakingToken.transfer(owner(), _amount)) {
            revert TransferFailed();
        }
    }


    // --- View and Pure Functions ---

    /**
     * @notice Calculates the reward per token accumulated so far.
     * @return The reward per token, scaled by 1e18.
     */
    function rewardPerToken() public view returns (uint256) {
        if (totalStaked == 0) {
            return rewardPerTokenStored;
        }
        uint256 timePassed = block.timestamp - lastUpdateTime;
        return rewardPerTokenStored + (timePassed * rewardRate * PRECISION) / totalStaked;
    }

    /**
     * @notice Calculates the total rewards earned by a specific account but not yet claimed.
     * @param _account The address of the user.
     * @return The total rewards earned.
     */
    function earned(address _account) public view returns (uint256) {
        uint256 stakerAmount = stakers[_account].amount;
        return (stakerAmount * (rewardPerToken() - userRewardPerTokenPaid[_account])) / PRECISION + rewards[_account];
    }

    /**
     * @notice Checks if a user is currently within their lock period.
     * @param _account The address of the user.
     * @return True if the user is locked, false otherwise.
     */
    function isLocked(address _account) public view returns (bool) {
        StakerInfo storage staker = stakers[_account];
        if (staker.amount == 0) {
            return false;
        }
        return block.timestamp < staker.stakeTimestamp + lockPeriod;
    }

    // --- Internal Functions ---

    /**
     * @dev Recalculates the rewardRate based on the current total staked amount and APY.
     */
    function _updateRewardRate() internal {
        // Reward rate is the total rewards to be distributed per second.
        // Formula: (totalStaked * APY_in_BPS / 10000) / seconds_in_year
        rewardRate = (totalStaked * currentApyBps) / BPS_DIVISOR / SECONDS_IN_YEAR;
    }
}