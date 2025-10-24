// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

/**
 * @title StakingToken
 * @dev This is a sample ERC20 token for the StakingRewards contract.
 * In a production environment, you would use an existing, deployed ERC20 token.
 * This contract mints an initial supply of 1 billion tokens to the deployer.
 */
contract StakingToken is ERC20, Ownable {
    /**
     * @dev Mints 1,000,000,000 tokens to the contract deployer.
     */
    constructor() ERC20("Staking Token", "STK") Ownable(msg.sender) {
        _mint(msg.sender, 1_000_000_000 * (10 ** decimals()));
    }
}

/**
 * @title StakingRewards
 * @author Expert Solidity Developer
 * @notice This contract allows users to stake an ERC20 token to earn rewards.
 * It is based on the Synthetix StakingRewards model, which provides a fair,
 * continuous reward distribution mechanism. This is more secure and less gameable
 * than a snapshot-based system.
 *
 * Features:
 * - Time-based rewards: Rewards accrue per second.
 * - Lock-in period: A configurable period during which unstaking incurs a penalty.
 * - Staking limits: Minimum and maximum stake amounts per user.
 * - Owner controls: The owner can fund rewards, pause the contract, and adjust parameters.
 * - Security: Implements ReentrancyGuard, Pausable, and follows the checks-effects-interactions pattern.
 */
contract StakingRewards is Ownable, ReentrancyGuard, Pausable {
    
    // ==================================================================
    // State Variables
    // ==================================================================

    /// @notice The ERC20 token used for staking and rewards.
    IERC20 public immutable stakingToken;

    /// @notice The address where early withdrawal penalties are sent.
    address public penaltyTreasury;

    // --- Staking Configuration ---
    uint256 public constant MINIMUM_STAKE = 1000 * 1e18;
    uint256 public constant MAX_STAKE_PER_USER = 1_000_000 * 1e18;
    uint256 public constant LOCKIN_PERIOD = 7 days;
    uint256 public constant EARLY_WITHDRAWAL_PENALTY_BPS = 1000; // 10.00%
    uint256 private constant BPS_DIVISOR = 10000;
    uint256 private constant SECONDS_IN_YEAR = 365 days;

    // --- Reward Variables ---
    /// @notice The timestamp when the current reward period ends.
    uint256 public periodFinish;
    /// @notice The rate at which rewards are distributed per second.
    uint256 public rewardRate;
    /// @notice The timestamp of the last reward distribution update.
    uint256 public lastUpdateTime;
    /// @notice The accumulated rewards per staked token.
    uint256 public rewardPerTokenStored;

    /// @notice Mapping from user address to their paid-out rewards per token.
    mapping(address => uint256) public userRewardPerTokenPaid;
    /// @notice Mapping from user address to their earned but unclaimed rewards.
    mapping(address => uint256) public rewards;

    // --- Staking Balances ---
    /// @notice Total amount of tokens staked in the contract.
    uint256 private _totalStaked;
    /// @notice Mapping from user address to their staked balance.
    mapping(address => uint256) private _stakedAmount;
    /// @notice Mapping from user address to the timestamp of their last stake action.
    mapping(address => uint256) public stakeTimestamp;

    // ==================================================================
    // Events
    // ==================================================================

    event Staked(address indexed user, uint256 amount);
    event Unstaked(address indexed user, uint256 amount, uint256 penalty);
    event RewardClaimed(address indexed user, uint256 reward);
    event RewardPeriodUpdated(uint256 newRewardRate, uint256 periodFinish);
    event PenaltyTreasuryUpdated(address indexed newTreasury);
    event EmergencyRecovery(address indexed token, address indexed to, uint256 amount);

    // ==================================================================
    // Modifiers
    // ==================================================================

    /**
     * @dev Modifier to update reward states for a given account before an action.
     * @param account The address of the user whose rewards need updating.
     */
    modifier updateReward(address account) {
        rewardPerTokenStored = rewardPerToken();
        lastUpdateTime = lastTimeRewardApplicable();
        if (account != address(0)) {
            rewards[account] = earned(account);
            userRewardPerTokenPaid[account] = rewardPerTokenStored;
        }
        _;
    }

    // ==================================================================
    // Constructor
    // ==================================================================
    
    /**
     * @param _stakingToken The address of the ERC20 token to be staked.
     * @param _penaltyTreasury The address to receive early withdrawal penalties.
     */
    constructor(address _stakingToken, address _penaltyTreasury) Ownable(msg.sender) {
        require(_stakingToken != address(0), "StakingRewards: Staking token cannot be zero address");
        require(_penaltyTreasury != address(0), "StakingRewards: Penalty treasury cannot be zero address");
        stakingToken = IERC20(_stakingToken);
        penaltyTreasury = _penaltyTreasury;
    }

    // ==================================================================
    // View Functions
    // ==================================================================

    /**
     * @notice Returns the total amount of tokens staked in the contract.
     */
    function totalStaked() external view returns (uint256) {
        return _totalStaked;
    }

    /**
     * @notice Returns the staked balance of a specific user.
     * @param account The address of the user.
     */
    function stakedBalanceOf(address account) external view returns (uint256) {
        return _stakedAmount[account];
    }

    /**
     * @notice The last timestamp that rewards are applicable for.
     * @return The minimum of the current block timestamp and the reward period finish time.
     */
    function lastTimeRewardApplicable() public view returns (uint256) {
        return block.timestamp < periodFinish ? block.timestamp : periodFinish;
    }

    /**
     * @notice Calculates the reward per token accumulated since the last update.
     * @return The total reward per token.
     */
    function rewardPerToken() public view returns (uint256) {
        if (_totalStaked == 0) {
            return rewardPerTokenStored;
        }
        return
            rewardPerTokenStored +
            (((lastTimeRewardApplicable() - lastUpdateTime) * rewardRate * 1e18) / _totalStaked);
    }

    /**
     * @notice Calculates the amount of rewards earned by a user.
     * @param account The address of the user.
     * @return The total rewards earned by the user.
     */
    function earned(address account) public view returns (uint256) {
        return
            ((_stakedAmount[account] * (rewardPerToken() - userRewardPerTokenPaid[account])) / 1e18) +
            rewards[account];
    }
    
    /**
     * @notice Calculates the current annual percentage yield (APY) in basis points (BPS).
     * 100 BPS = 1%.
     * @return The current APY in BPS. Returns 0 if no tokens are staked.
     */
    function getApyBps() public view returns (uint256) {
        if (_totalStaked == 0 || rewardRate == 0) {
            return 0;
        }
        return (rewardRate * SECONDS_IN_YEAR * BPS_DIVISOR) / _totalStaked;
    }

    /**
     * @notice Returns the remaining lock time for a user in seconds.
     * @param account The address of the user.
     * @return The remaining seconds until the user's stake is unlocked.
     */
    function getRemainingLockTime(address account) public view returns (uint256) {
        if (_stakedAmount[account] == 0) {
            return 0;
        }
        uint256 unlockTime = stakeTimestamp[account] + LOCKIN_PERIOD;
        return block.timestamp >= unlockTime ? 0 : unlockTime - block.timestamp;
    }

    // ==================================================================
    // User Functions
    // ==================================================================

    /**
     * @notice Stakes a specified amount of tokens.
     * @dev The user must have approved the contract to spend their tokens.
     * @param amount The amount of tokens to stake.
     */
    function stake(uint256 amount)
        external
        whenNotPaused
        nonReentrant
        updateReward(msg.sender)
    {
        require(amount >= MINIMUM_STAKE, "StakingRewards: Amount is below minimum stake");
        uint256 newTotal = _stakedAmount[msg.sender] + amount;
        require(newTotal <= MAX_STAKE_PER_USER, "StakingRewards: Stake exceeds maximum per user");

        _totalStaked += amount;
        _stakedAmount[msg.sender] = newTotal;
        stakeTimestamp[msg.sender] = block.timestamp;

        stakingToken.transferFrom(msg.sender, address(this), amount);
        emit Staked(msg.sender, amount);
    }

    /**
     * @notice Unstakes a specified amount of tokens.
     * @dev A 10% penalty is applied if unstaking occurs within the 7-day lock-in period.
     * @param amount The amount of tokens to unstake.
     */
    function unstake(uint256 amount)
        external
        whenNotPaused
        nonReentrant
        updateReward(msg.sender)
    {
        require(amount > 0, "StakingRewards: Amount must be greater than zero");
        require(_stakedAmount[msg.sender] >= amount, "StakingRewards: Insufficient staked balance");

        _totalStaked -= amount;
        _stakedAmount[msg.sender] -= amount;

        uint256 penalty = 0;
        if (getRemainingLockTime(msg.sender) > 0) {
            penalty = (amount * EARLY_WITHDRAWAL_PENALTY_BPS) / BPS_DIVISOR;
            if (penalty > 0) {
                stakingToken.transfer(penaltyTreasury, penalty);
            }
        }
        
        uint256 amountToReturn = amount - penalty;
        stakingToken.transfer(msg.sender, amountToReturn);
        
        emit Unstaked(msg.sender, amountToReturn, penalty);
    }

    /**
     * @notice Claims all earned rewards for the message sender.
     */
    function claimRewards() external nonReentrant updateReward(msg.sender) {
        uint256 reward = rewards[msg.sender];
        if (reward > 0) {
            rewards[msg.sender] = 0;
            stakingToken.transfer(msg.sender, reward);
            emit RewardClaimed(msg.sender, reward);
        }
    }

    /**
     * @notice Unstakes all tokens and claims all rewards in a single transaction.
     */
    function exit() external {
        // Unstake first to ensure correct reward calculation on the final balance.
        unstake(_stakedAmount[msg.sender]);
        claimRewards();
    }

    // ==================================================================
    // Owner Functions
    // ==================================================================

    /**
     * @notice Starts a new reward distribution period.
     * @dev This function funds the contract with rewards and sets the rate over a duration.
     * It can be called to start a new period or to top up an existing one.
     * Any previous reward period is overridden.
     * This is the primary method for the owner to manage the APY.
     * @param reward The total amount of rewards to distribute.
     * @param duration The duration in seconds over which the rewards will be distributed.
     */
    function notifyRewardAmount(uint256 reward, uint256 duration)
        external
        onlyOwner
        updateReward(address(0))
    {
        require(duration > 0, "StakingRewards: Duration must be greater than zero");
        require(reward > 0, "StakingRewards: Reward must be greater than zero");

        if (block.timestamp >= periodFinish) {
            rewardRate = reward / duration;
        } else {
            uint256 remaining = periodFinish - block.timestamp;
            uint256 leftover = remaining * rewardRate;
            rewardRate = (reward + leftover) / duration;
        }
        
        uint256 requiredBalance = rewardRate * duration;
        require(stakingToken.balanceOf(address(this)) >= requiredBalance + _totalStaked, "StakingRewards: Insufficient reward token balance");

        lastUpdateTime = block.timestamp;
        periodFinish = block.timestamp + duration;
        emit RewardPeriodUpdated(rewardRate, periodFinish);
    }
    
    /**
     * @notice Pauses staking and unstaking functionality. Claiming rewards is not affected.
     */
    function pause() external onlyOwner {
        _pause();
    }

    /**
     * @notice Unpauses the contract, resuming normal operations.
     */
    function unpause() external onlyOwner {
        _unpause();
    }

    /**
     * @notice Updates the address where early withdrawal penalties are sent.
     * @param _newTreasury The new treasury address.
     */
    function setPenaltyTreasury(address _newTreasury) external onlyOwner {
        require(_newTreasury != address(0), "StakingRewards: New treasury cannot be zero address");
        penaltyTreasury = _newTreasury;
        emit PenaltyTreasuryUpdated(_newTreasury);
    }

    /**
     * @notice Recovers ERC20 tokens that are not part of the staking or reward pools.
     * @dev This can only be called after the reward period has finished to prevent rug-pulling rewards.
     * It can be used to recover staking tokens sent to the contract by mistake or other ERC20 tokens.
     * @param tokenAddress The address of the ERC20 token to recover.
     * @param amount The amount to recover.
     */
    function recoverERC20(address tokenAddress, uint256 amount) external onlyOwner {
        require(block.timestamp > periodFinish, "StakingRewards: Cannot recover tokens during reward period");
        require(tokenAddress != address(stakingToken), "StakingRewards: Cannot recover active staking token, use recoverUnallocatedStakingTokens");
        IERC20(tokenAddress).transfer(owner(), amount);
        emit EmergencyRecovery(tokenAddress, owner(), amount);
    }

    /**
     * @notice Recovers unallocated staking tokens after the reward period ends.
     * @dev Unallocated tokens are those in excess of the total staked amount.
     */
    function recoverUnallocatedStakingTokens() external onlyOwner {
        require(block.timestamp > periodFinish, "StakingRewards: Cannot recover tokens during reward period");
        uint256 unallocated = stakingToken.balanceOf(address(this)) - _totalStaked;
        if (unallocated > 0) {
            stakingToken.transfer(owner(), unallocated);
            emit EmergencyRecovery(address(stakingToken), owner(), unallocated);
        }
    }
}