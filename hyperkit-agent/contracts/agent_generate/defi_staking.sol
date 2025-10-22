// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/**
 * @title StakingRewards
 * @author Your Name Here
 * @notice A DeFi staking contract where users can stake an ERC20 token to earn rewards in another ERC20 token.
 * @dev This contract is based on the Synthetix StakingRewards model. It calculates rewards per second for each user
 * based on their share of the total staked amount.
 * The owner is responsible for setting the reward rate and ensuring the contract is funded with enough reward tokens.
 */
contract StakingRewards is Ownable, ReentrancyGuard {
    using SafeERC20 for IERC20;

    /* ========== STATE VARIABLES ========== */

    /// @notice The token that users stake.
    IERC20 public immutable stakingToken;
    /// @notice The token that is distributed as rewards.
    IERC20 public immutable rewardsToken;

    /// @notice The rate at which rewards are distributed per second (in the smallest unit of the rewardsToken).
    uint256 public rewardRate;
    /// @notice The total amount of staking tokens currently staked in the contract.
    uint256 public totalSupply;
    /// @notice The timestamp of the last time the reward variables were updated.
    uint256 public lastUpdateTime;
    /// @notice The accumulated rewards per staked token, scaled by 1e18 for precision.
    uint256 public rewardPerTokenStored;

    /// @notice Tracks the amount of rewards earned by each user that have not yet been claimed.
    mapping(address => uint256) public rewards;
    /// @notice Tracks the amount staked by each user.
    mapping(address => uint256) public balances;
    /// @notice Tracks the rewardPerTokenStored value for each user the last time their rewards were updated.
    mapping(address => uint256) private userRewardPerTokenPaid;


    /* ========== EVENTS ========== */

    /// @notice Emitted when a new reward rate is set.
    /// @param newRate The new rewards per second rate.
    event RewardRateSet(uint256 newRate);

    /// @notice Emitted when the contract is funded with more reward tokens.
    /// @param amount The amount of reward tokens added.
    event RewardsFunded(uint256 amount);

    /// @notice Emitted when a user stakes tokens.
    /// @param user The address of the staker.
    /// @param amount The amount of tokens staked.
    event Staked(address indexed user, uint256 amount);

    /// @notice Emitted when a user withdraws staked tokens.
    /// @param user The address of the user withdrawing.
    /// @param amount The amount of tokens withdrawn.
    event Withdrawn(address indexed user, uint256 amount);

    /// @notice Emitted when a user claims their earned rewards.
    /// @param user The address of the user claiming rewards.
    /// @param reward The amount of reward tokens claimed.
    event RewardPaid(address indexed user, uint256 reward);


    /* ========== ERRORS ========== */

    /// @notice Error for operations with a zero amount.
    error ZeroAmount();
    /// @notice Error for attempting to withdraw more than the staked balance.
    error InsufficientStakedAmount();

    /* ========== CONSTRUCTOR ========== */

    /**
     * @notice Sets the staking and reward tokens.
     * @param _stakingToken The address of the token to be staked.
     * @param _rewardsToken The address of the token to be given as a reward.
     */
    constructor(address _stakingToken, address _rewardsToken) Ownable(msg.sender) {
        if (_stakingToken == address(0) || _rewardsToken == address(0)) {
            revert ZeroAddress();
        }
        stakingToken = IERC20(_stakingToken);
        rewardsToken = IERC20(_rewardsToken);
    }

    /* ========== VIEWS ========== */

    /**
     * @notice Calculates the amount of rewards earned by a specific account.
     * @param _account The address of the account to check.
     * @return The amount of unclaimed rewards.
     */
    function earned(address _account) public view returns (uint256) {
        uint256 currentRewardPerToken = rewardPerToken();
        return (balances[_account] * (currentRewardPerToken - userRewardPerTokenPaid[_account])) / 1e18
               + rewards[_account];
    }

    /**
     * @notice Calculates the current reward-per-token rate.
     * @dev This calculation is based on the time elapsed since the last update.
     * @return The reward per token, scaled by 1e18.
     */
    function rewardPerToken() public view returns (uint256) {
        if (totalSupply == 0) {
            return rewardPerTokenStored;
        }
        uint256 timeSinceLastUpdate = block.timestamp - lastUpdateTime;
        return rewardPerTokenStored + (timeSinceLastUpdate * rewardRate * 1e18) / totalSupply;
    }

    /* ========== MUTATIVE FUNCTIONS ========== */

    /**
     * @notice Stakes a specified amount of staking tokens.
     * @dev The user must first approve the contract to spend their tokens.
     * @param _amount The amount of staking tokens to stake.
     */
    function stake(uint256 _amount) external nonReentrant {
        if (_amount == 0) revert ZeroAmount();

        _updateReward(msg.sender);

        totalSupply += _amount;
        balances[msg.sender] += _amount;
        
        stakingToken.safeTransferFrom(msg.sender, address(this), _amount);

        emit Staked(msg.sender, _amount);
    }

    /**
     * @notice Withdraws a specified amount of staked tokens.
     * @param _amount The amount of staking tokens to withdraw.
     */
    function withdraw(uint256 _amount) external nonReentrant {
        if (_amount == 0) revert ZeroAmount();
        if (balances[msg.sender] < _amount) revert InsufficientStakedAmount();
        
        _updateReward(msg.sender);

        totalSupply -= _amount;
        balances[msg.sender] -= _amount;

        stakingToken.safeTransfer(msg.sender, _amount);

        emit Withdrawn(msg.sender, _amount);
    }

    /**
     * @notice Claims all available rewards for the message sender.
     */
    function claimRewards() external nonReentrant {
        _updateReward(msg.sender);
        
        uint256 reward = rewards[msg.sender];
        if (reward > 0) {
            rewards[msg.sender] = 0;
            rewardsToken.safeTransfer(msg.sender, reward);
            emit RewardPaid(msg.sender, reward);
        }
    }

    /* ========== OWNER FUNCTIONS ========== */

    /**
     * @notice Sets the reward rate.
     * @dev Can only be called by the owner. It first updates the reward state
     * for all participants before changing the rate.
     * @param _newRate The new reward rate per second.
     */
    function setRewardRate(uint256 _newRate) external onlyOwner {
        _updateReward(address(0)); // Update global state
        rewardRate = _newRate;
        emit RewardRateSet(_newRate);
    }

    /**
     * @notice Funds the contract with reward tokens.
     * @dev Can only be called by the owner. The owner must first approve the contract
     * to spend the reward tokens. It is the owner's responsibility to ensure the
     * contract has enough balance to pay out rewards.
     * @param _amount The amount of reward tokens to add.
     */
    function addRewards(uint256 _amount) external onlyOwner {
        if (_amount == 0) revert ZeroAmount();
        rewardsToken.safeTransferFrom(msg.sender, address(this), _amount);
        emit RewardsFunded(_amount);
    }

    /* ========== INTERNAL FUNCTIONS ========== */

    /**
     * @dev Updates reward-related state variables. If an account is provided,
     * it also calculates and stores the pending rewards for that specific account.
     * @param _account The account to update rewards for. Pass address(0) to only update global state.
     */
    function _updateReward(address _account) internal {
        uint256 currentRewardPerToken = rewardPerToken();
        uint256 currentTimestamp = block.timestamp;
        
        // Ensure lastUpdateTime is not in the future
        if (currentTimestamp > lastUpdateTime) {
            rewardPerTokenStored = currentRewardPerToken;
            lastUpdateTime = currentTimestamp;
        }

        if (_account != address(0)) {
            rewards[_account] = earned(_account);
            userRewardPerTokenPaid[_account] = currentRewardPerToken;
        }
    }
}