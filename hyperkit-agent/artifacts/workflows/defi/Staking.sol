// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/**
 * @title Metis ERC20 Staking Contract
 * @author Expert Solidity Developer
 * @notice A secure, production-ready ERC20 staking contract designed for the Metis mainnet.
 * @dev This contract allows users to stake an ERC20 token to earn rewards over time.
 * It includes features like a lock-in period with an early withdrawal penalty,
 * anti-whale limits, and administrative controls for pausing and managing rewards.
 * Rewards are calculated based on a per-second rate derived from the total rewards
 * funded for a specific period, providing a dynamic APY. This implementation is based on
 * battle-tested reward distribution patterns to ensure fairness and security.
 *
 * Security measures include OpenZeppelin's Ownable, Pausable, and ReentrancyGuard,
 * adherence to the checks-effects-interactions pattern, and built-in overflow
 * protection from Solidity ^0.8.0.
 * Compatible with Metis Mainnet (Chain ID: 1088).
 */
contract MetisStaking is Ownable, Pausable, ReentrancyGuard {
    // --- State Variables ---

    /**
     * @notice The ERC20 token used for both staking and rewards.
     */
    IERC20 public immutable stakingToken;

    /**
     * @notice The address where early withdrawal penalties are sent.
     */
    address public penaltyWallet;

    // --- Staking Configuration ---

    /**
     * @notice The minimum amount of tokens a user must stake in a single transaction.
     */
    uint256 public constant MINIMUM_STAKE = 1_000 * 10**18;

    /**
     * @notice The maximum total amount of tokens a single user can have staked.
     */
    uint256 public constant MAXIMUM_STAKE_PER_USER = 1_000_000 * 10**18;

    /**
     * @notice The duration for which staked tokens are locked before penalty-free withdrawal.
     */
    uint256 public constant LOCKIN_PERIOD = 7 days;

    /**
     * @notice The penalty fee for withdrawing before the lock-in period ends, in basis points (1000 = 10%).
     */
    uint256 public earlyWithdrawalPenaltyBps = 1000;

    /**
     * @notice The divisor for basis points calculations.
     */
    uint256 public constant BPS_DIVISOR = 10000;

    // --- Staking Data ---

    /**
     * @dev A struct to hold staking information for each user.
     * @param amount The total amount of tokens staked by the user.
     * @param stakeTimestamp The timestamp of the user's first stake, which starts the lock-in period.
     */
    struct Staker {
        uint256 amount;
        uint256 stakeTimestamp;
    }

    /**
     * @notice Mapping from a user's address to their staking information.
     */
    mapping(address => Staker) public stakers;

    /**
     * @notice The total amount of tokens currently staked in the contract.
     */
    uint256 public totalStaked;

    // --- Reward Data ---

    /**
     * @notice The duration over which rewards are distributed. Default is 365 days.
     */
    uint256 public rewardsDuration = 365 days;

    /**
     * @notice The timestamp when the current reward period ends.
     */
    uint256 public finishAt;

    /**
     * @notice The timestamp when rewards were last updated.
     */
    uint256 public updatedAt;

    /**
     * @notice The rate of reward distribution per second.
     */
    uint256 public rewardRate;

    /**
     * @notice The cumulative reward per token, scaled by 1e18.
     */
    uint256 public rewardPerTokenStored;

    /**
     * @notice Mapping to track the reward per token paid to each user.
     */
    mapping(address => uint256) public userRewardPerTokenPaid;

    /**
     * @notice Mapping to store the accrued, unclaimed rewards for each user.
     */
    mapping(address => uint256) public rewards;

    // --- Events ---

    event Staked(address indexed user, uint256 amount);
    event Unstaked(address indexed user, uint256 amount, uint256 penalty);
    event RewardClaimed(address indexed user, uint256 amount);
    event RewardNotified(uint256 rewardAmount);
    event PenaltyWalletUpdated(address indexed newWallet);
    event EarlyWithdrawalPenaltyBpsUpdated(uint256 newBps);
    event RewardsDurationUpdated(uint256 newDuration);
    event Recovered(address indexed token, uint256 amount);

    // --- Modifiers ---

    /**
     * @dev Modifier to update rewards for a user before a state-changing action.
     * @param _account The address of the user.
     */
    modifier updateReward(address _account) {
        rewardPerTokenStored = rewardPerToken();
        updatedAt = lastTimeRewardApplicable();
        if (_account != address(0)) {
            rewards[_account] = earned(_account);
            userRewardPerTokenPaid[_account] = rewardPerTokenStored;
        }
        _;
    }

    // --- Constructor ---

    /**
     * @notice Initializes the staking contract.
     * @param _stakingTokenAddress The address of the ERC20 token to be staked.
     * @param _penaltyWalletAddress The address to receive early withdrawal penalties.
     */
    constructor(address _stakingTokenAddress, address _penaltyWalletAddress) Ownable(msg.sender) {
        require(_stakingTokenAddress != address(0), "Staking token cannot be zero address");
        require(_penaltyWalletAddress != address(0), "Penalty wallet cannot be zero address");
        stakingToken = IERC20(_stakingTokenAddress);
        penaltyWallet = _penaltyWalletAddress;
    }

    // --- View Functions ---

    /**
     * @notice Returns the timestamp when the current reward period ends or the current time if the period is ongoing.
     * @return The Unix timestamp.
     */
    function lastTimeRewardApplicable() public view returns (uint256) {
        return block.timestamp < finishAt ? block.timestamp : finishAt;
    }

    /**
     * @notice Calculates the reward per token accumulated since the last update.
     * @return The cumulative reward per token, scaled by 1e18.
     */
    function rewardPerToken() public view returns (uint256) {
        if (totalStaked == 0) {
            return rewardPerTokenStored;
        }
        return
            rewardPerTokenStored +
            (((lastTimeRewardApplicable() - updatedAt) * rewardRate * 1e18) / totalStaked);
    }

    /**
     * @notice Calculates the amount of rewards a user has earned but not yet claimed.
     * @param _account The address of the user.
     * @return The total unclaimed rewards for the user.
     */
    function earned(address _account) public view returns (uint256) {
        return
            ((stakers[_account].amount * (rewardPerToken() - userRewardPerTokenPaid[_account])) / 1e18) +
            rewards[_account];
    }

    /**
     * @notice Calculates the current estimated Annual Percentage Yield (APY).
     * @dev The APY is dynamic and changes based on the total amount staked and the reward rate.
     * @return The APY in basis points (e.g., 1200 for 12.00%).
     */
    function getApy() public view returns (uint256) {
        if (totalStaked == 0 || rewardRate == 0) {
            return 0;
        }
        return (rewardRate * 365 days * BPS_DIVISOR) / totalStaked;
    }

    // --- User Functions ---

    /**
     * @notice Stakes a specified amount of tokens.
     * @dev The user must first approve the contract to spend their tokens.
     * The stake amount must meet the minimum and not exceed the per-user maximum.
     * @param _amount The amount of tokens to stake.
     */
    function stake(uint256 _amount)
        external
        whenNotPaused
        nonReentrant
        updateReward(msg.sender)
    {
        require(_amount >= MINIMUM_STAKE, "Amount is below minimum stake");
        uint256 currentStake = stakers[msg.sender].amount;
        require(currentStake + _amount <= MAXIMUM_STAKE_PER_USER, "Stake exceeds per-user maximum");

        // Effects
        if (currentStake == 0) {
            stakers[msg.sender].stakeTimestamp = block.timestamp;
        }
        totalStaked += _amount;
        stakers[msg.sender].amount += _amount;

        // Interaction
        require(stakingToken.transferFrom(msg.sender, address(this), _amount), "Token transfer failed");

        emit Staked(msg.sender, _amount);
    }

    /**
     * @notice Unstakes a specified amount of tokens.
     * @dev If unstaking occurs before the lock-in period ends, a penalty is applied.
     * Any earned rewards are claimed automatically before unstaking.
     * @param _amount The amount of tokens to unstake.
     */
    function unstake(uint256 _amount)
        external
        nonReentrant
        updateReward(msg.sender)
    {
        uint256 currentStake = stakers[msg.sender].amount;
        require(_amount > 0, "Amount must be greater than zero");
        require(currentStake >= _amount, "Insufficient staked amount");

        // Claim rewards first
        _claimReward(msg.sender);

        // Effects
        totalStaked -= _amount;
        stakers[msg.sender].amount -= _amount;

        uint256 amountToTransfer = _amount;
        uint256 penalty = 0;

        // Check for early withdrawal penalty
        if (block.timestamp < stakers[msg.sender].stakeTimestamp + LOCKIN_PERIOD) {
            penalty = (_amount * earlyWithdrawalPenaltyBps) / BPS_DIVISOR;
            amountToTransfer -= penalty;
            
            // Interaction for penalty
            if (penalty > 0) {
                 require(stakingToken.transfer(penaltyWallet, penalty), "Penalty transfer failed");
            }
        }
        
        // Interaction for unstake
        if(amountToTransfer > 0) {
            require(stakingToken.transfer(msg.sender, amountToTransfer), "Unstake transfer failed");
        }

        emit Unstaked(msg.sender, _amount, penalty);
    }
    
    /**
     * @notice Claims all earned rewards for the message sender.
     */
    function claimReward() external nonReentrant updateReward(msg.sender) {
        _claimReward(msg.sender);
    }
    
    /**
     * @dev Internal function to handle the reward claiming logic.
     * @param _account The address of the user claiming rewards.
     */
    function _claimReward(address _account) private {
        uint256 reward = rewards[_account];
        if (reward > 0) {
            rewards[_account] = 0;
            require(stakingToken.transfer(_account, reward), "Reward transfer failed");
            emit RewardClaimed(_account, reward);
        }
    }


    // --- Owner Functions ---

    /**
     * @notice Pauses the staking functionality. Unstaking remains active.
     * @dev Can only be called by the contract owner.
     */
    function pause() external onlyOwner {
        _pause();
    }

    /**
     * @notice Unpauses the staking functionality.
     * @dev Can only be called by the contract owner.
     */
    function unpause() external onlyOwner {
        _unpause();
    }

    /**
     * @notice Funds the contract with reward tokens for a new reward period.
     * @dev This will start a new reward distribution period, overriding the previous one.
     * The owner must approve the contract to spend the reward tokens beforehand.
     * This function effectively adjusts the APY by changing the reward rate.
     * @param _rewardAmount The total amount of reward tokens to distribute for the new period.
     */
    function notifyRewardAmount(uint256 _rewardAmount)
        external
        onlyOwner
        updateReward(address(0))
    {
        require(rewardsDuration > 0, "Rewards duration must be set");

        if (block.timestamp >= finishAt) {
            rewardRate = _rewardAmount / rewardsDuration;
        } else {
            uint256 remaining = finishAt - block.timestamp;
            uint256 leftover = remaining * rewardRate;
            rewardRate = (_rewardAmount + leftover) / rewardsDuration;
        }
        
        require(rewardRate > 0, "Reward rate cannot be zero");

        require(stakingToken.transferFrom(msg.sender, address(this), _rewardAmount), "Reward token transfer failed");

        finishAt = block.timestamp + rewardsDuration;
        updatedAt = block.timestamp;

        emit RewardNotified(_rewardAmount);
    }

    /**
     * @notice Updates the rewards duration.
     * @dev Can only be called by the owner, and only when a reward period is not active.
     * @param _newDuration The new duration in seconds (e.g., 365 days).
     */
    function setRewardsDuration(uint256 _newDuration) external onlyOwner {
        require(block.timestamp > finishAt, "Cannot change duration during a reward period");
        require(_newDuration > 0, "Duration must be greater than zero");
        rewardsDuration = _newDuration;
        emit RewardsDurationUpdated(_newDuration);
    }

    /**
     * @notice Updates the early withdrawal penalty percentage.
     * @param _newBps The new penalty in basis points (e.g., 1000 for 10%).
     */
    function setEarlyWithdrawalPenaltyBps(uint256 _newBps) external onlyOwner {
        require(_newBps <= BPS_DIVISOR, "Penalty cannot exceed 100%");
        earlyWithdrawalPenaltyBps = _newBps;
        emit EarlyWithdrawalPenaltyBpsUpdated(_newBps);
    }

    /**
     * @notice Updates the wallet address that receives penalties.
     * @param _newWallet The new address for the penalty wallet.
     */
    function setPenaltyWallet(address _newWallet) external onlyOwner {
        require(_newWallet != address(0), "Penalty wallet cannot be zero address");
        penaltyWallet = _newWallet;
        emit PenaltyWalletUpdated(_newWallet);
    }

    /**
     * @notice Allows the owner to recover accidentally sent ERC20 tokens or leftover reward tokens.
     * @dev Leftover reward tokens can only be withdrawn after the reward period has finished.
     * This prevents the owner from draining funds meant for rewards during an active period.
     * @param _tokenAddress The address of the ERC20 token to recover.
     * @param _amount The amount of tokens to recover.
     */
    function recoverERC20(address _tokenAddress, uint256 _amount) external onlyOwner {
        if (_tokenAddress == address(stakingToken)) {
            // Can only recover surplus rewards after the reward period has ended.
            require(block.timestamp > finishAt, "Cannot withdraw rewards before period ends");
            uint256 surplus = stakingToken.balanceOf(address(this)) - totalStaked;
            require(_amount <= surplus, "Cannot withdraw more than surplus");
            require(IERC20(_tokenAddress).transfer(owner(), _amount), "Staking token recovery failed");
        } else {
            // Can recover any other accidentally sent ERC20 token at any time.
            require(IERC20(_tokenAddress).transfer(owner(), _amount), "Token recovery failed");
        }
        emit Recovered(_tokenAddress, _amount);
    }
}