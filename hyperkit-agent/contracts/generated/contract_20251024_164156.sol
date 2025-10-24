// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Permit.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Votes.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/math/Math.sol";

/**
 * @title IGameRewards Interface
 * @dev Interface for the game mechanics that grant rewards.
 */
interface IGameRewards {
    /**
     * @dev Grants a quest reward to a player. The final amount is determined
     * by in-contract logic (e.g., staking bonuses).
     * @param player The address of the player receiving the reward.
     * @param baseRewardAmount The base reward amount for the quest, before any multipliers.
     */
    function grantQuestReward(address player, uint256 baseRewardAmount) external;
}

/**
 * @title ITreasuryManagement Interface
 * @dev Interface for managing the release of vested treasury funds.
 */
interface ITreasuryManagement {
    /**
     * @dev Releases vested tokens to the treasury.
     * The amount released is calculated based on a linear vesting schedule.
     */
    function releaseVestedTreasuryTokens() external;
}

/**
 * @title GAMEX Token Contract
 * @author Expert Solidity Developer
 * @notice This is a secure, production-ready play-to-earn gaming token.
 * It includes features like a fixed supply, vesting schedule, in-game reward mechanics,
 * staking bonuses, anti-whale measures, and on-chain governance capabilities.
 * @dev Inherits from OpenZeppelin's ERC20, ERC20Burnable, ERC20Votes, AccessControl, and ReentrancyGuard.
 * The contract manages its own supply as a vault for rewards and vesting.
 * Chain ID for Hyperion testnet is 133717.
 */
contract GAMEX is ERC20, ERC20Burnable, ERC20Permit, ERC20Votes, AccessControl, ReentrancyGuard, IGameRewards, ITreasuryManagement {

    // --- Roles ---
    bytes32 public constant GAME_ROLE = keccak256("GAME_ROLE");
    bytes32 public constant TREASURY_ROLE = keccak256("TREASURY_ROLE");

    // --- Tokenomics Constants ---
    uint256 public constant TOTAL_SUPPLY = 500_000_000 * 10**18;
    uint256 public constant TGE_AMOUNT = TOTAL_SUPPLY * 10 / 100; // 10% for launch
    uint256 public constant TREASURY_VESTING_POOL = TOTAL_SUPPLY * 20 / 100; // 20% for treasury
    uint256 public constant VESTING_DURATION = 3 years;

    // --- In-Game Mechanics Constants ---
    uint256 public constant MIN_QUEST_REWARD = 10 * 10**18;
    uint256 public constant MAX_QUEST_REWARD = 100 * 10**18;
    uint256 public constant REWARD_BURN_PERCENT = 5; // 5%

    // --- Anti-Whale Constants ---
    uint256 public constant MAX_TX_AMOUNT = TOTAL_SUPPLY * 2 / 100; // Max 2% of total supply per transaction
    uint256 public constant HOLDER_CAP = 10_000_000 * 10**18; // Max 10M tokens per wallet
    uint256 public constant LARGE_TX_THRESHOLD = TOTAL_SUPPLY / 100; // 1% of total supply
    uint256 public constant TX_COOLDOWN = 5 minutes;

    // --- State Variables ---
    uint256 public immutable vestingStartTime;
    uint256 public p2eRewardPool;
    uint256 public totalTreasuryReleased;

    mapping(address => uint256) public stakedBalances;
    uint256 public totalStaked;

    mapping(address => uint256) private _lastLargeTxTimestamp;
    mapping(address => bool) public isExemptFromAntiWhale;

    // --- Custom Errors ---
    error InvalidRewardAmount(uint256 amount);
    error P2ERewardPoolExhausted();
    error NoTokensToRelease();
    error ZeroAmount();
    error InsufficientStakedBalance();
    error ExceedsMaxTransactionAmount(uint256 amount);
    error ExceedsHolderCap(address recipient, uint256 balance, uint256 amount);
    error TransferCooldownActive(address account, uint256 nextAvailableTimpstamp);

    // --- Events ---
    event QuestRewardGranted(address indexed player, uint256 rewardAmount, uint256 burnAmount);
    event TokensStaked(address indexed user, uint256 amount);
    event TokensUnstaked(address indexed user, uint256 amount);
    event TreasuryTokensReleased(address indexed treasury, uint256 amount);
    event AntiWhaleExemptionSet(address indexed account, bool isExempt);


    /**
     * @dev Sets up the contract, roles, initial token distribution, and vesting schedule.
     * @param initialAdmin The address that will receive the DEFAULT_ADMIN_ROLE.
     * @param gameContract The address of the game contract, granted GAME_ROLE.
     * @param treasuryAddress The address of the treasury, granted TREASURY_ROLE and receiving TGE/vested tokens.
     */
    constructor(
        address initialAdmin,
        address gameContract,
        address treasuryAddress
    ) ERC20("GAMEX", "GMX") ERC20Permit("GAMEX") {
        if (initialAdmin == address(0) || gameContract == address(0) || treasuryAddress == address(0)) {
            revert("Zero address provided");
        }

        // Setup roles
        _grantRole(DEFAULT_ADMIN_ROLE, initialAdmin);
        _grantRole(GAME_ROLE, gameContract);
        _grantRole(TREASURY_ROLE, treasuryAddress);

        // Mint the entire supply to this contract to act as a vault
        _mint(address(this), TOTAL_SUPPLY);

        // Set P2E reward pool size (total supply - TGE - treasury vesting)
        p2eRewardPool = TOTAL_SUPPLY - TGE_AMOUNT - TREASURY_VESTING_POOL;

        // Set vesting start time
        vestingStartTime = block.timestamp;

        // Set anti-whale exemptions for critical addresses
        isExemptFromAntiWhale[address(this)] = true;
        isExemptFromAntiWhale[treasuryAddress] = true;

        // Transfer 10% TGE amount to the treasury
        _transfer(address(this), treasuryAddress, TGE_AMOUNT);
        emit TreasuryTokensReleased(treasuryAddress, TGE_AMOUNT);
    }

    // --- In-Game Mechanics ---

    /**
     * @notice Grants quest rewards to a player, applying staking bonuses and burning a portion.
     * @dev Can only be called by an address with GAME_ROLE.
     * The total reward (reward + burn) is deducted from the P2E reward pool.
     * @param player The address of the player to reward.
     * @param baseRewardAmount The base reward, must be between 10 and 100 tokens.
     */
    function grantQuestReward(address player, uint256 baseRewardAmount) external override onlyRole(GAME_ROLE) {
        if (baseRewardAmount < MIN_QUEST_REWARD || baseRewardAmount > MAX_QUEST_REWARD) {
            revert InvalidRewardAmount(baseRewardAmount);
        }

        uint256 totalReward = baseRewardAmount;
        // Apply 2x staking bonus
        if (stakedBalances[player] > 0) {
            totalReward *= 2;
        }

        uint256 burnAmount = (totalReward * REWARD_BURN_PERCENT) / 100;
        uint256 playerAmount = totalReward - burnAmount;

        if (totalReward > p2eRewardPool) {
            revert P2ERewardPoolExhausted();
        }

        p2eRewardPool -= totalReward;

        // Transfer player's reward from the contract's vault
        _transfer(address(this), player, playerAmount);
        
        // Burn 5% of the earned reward from the contract's vault
        _burn(address(this), burnAmount);

        emit QuestRewardGranted(player, playerAmount, burnAmount);
    }

    // --- Staking ---

    /**
     * @notice Stakes GAMEX tokens to become eligible for 2x quest rewards.
     * @dev Tokens are transferred from the user to this contract.
     * @param amount The amount of tokens to stake.
     */
    function stake(uint256 amount) external nonReentrant {
        if (amount == 0) revert ZeroAmount();
        _transfer(msg.sender, address(this), amount);
        stakedBalances[msg.sender] += amount;
        totalStaked += amount;
        emit TokensStaked(msg.sender, amount);
    }

    /**
     * @notice Unstakes GAMEX tokens.
     * @dev Tokens are transferred from this contract back to the user.
     * @param amount The amount of tokens to unstake.
     */
    function unstake(uint256 amount) external nonReentrant {
        if (amount == 0) revert ZeroAmount();
        if (stakedBalances[msg.sender] < amount) {
            revert InsufficientStakedBalance();
        }
        stakedBalances[msg.sender] -= amount;
        totalStaked -= amount;
        _transfer(address(this), msg.sender, amount);
        emit TokensUnstaked(msg.sender, amount);
    }

    /**
     * @notice Gets the staked balance of a user.
     * @param user The address of the user.
     * @return The amount of tokens staked by the user.
     */
    function getStakedBalance(address user) external view returns (uint256) {
        return stakedBalances[user];
    }

    // --- Treasury & Vesting ---

    /**
     * @notice Calculates the total amount of treasury tokens that have vested over time.
     * @return The amount of vested tokens.
     */
    function getVestedTreasuryAmount() public view returns (uint256) {
        if (block.timestamp < vestingStartTime) {
            return 0;
        }
        uint256 timeElapsed = block.timestamp - vestingStartTime;
        if (timeElapsed >= VESTING_DURATION) {
            return TREASURY_VESTING_POOL;
        }
        return (TREASURY_VESTING_POOL * timeElapsed) / VESTING_DURATION;
    }

    /**
     * @notice Releases vested treasury tokens to the treasury address.
     * @dev Can only be called by an address with TREASURY_ROLE.
     * The amount is based on a linear vesting schedule over 3 years.
     */
    function releaseVestedTreasuryTokens() external override onlyRole(TREASURY_ROLE) {
        uint256 vestedAmount = getVestedTreasuryAmount();
        uint256 releasableAmount = vestedAmount - totalTreasuryReleased;

        if (releasableAmount == 0) {
            revert NoTokensToRelease();
        }

        totalTreasuryReleased += releasableAmount;
        address treasuryAddress = _getRoleMember(TREASURY_ROLE, 0);
        _transfer(address(this), treasuryAddress, releasableAmount);

        emit TreasuryTokensReleased(treasuryAddress, releasableAmount);
    }

    // --- Anti-Whale Measures ---

    /**
     * @dev Internal hook from OpenZeppelin ERC20 that is called before any token transfer.
     * Implements anti-whale measures: max transaction amount, holder cap, and transfer cooldown.
     */
    function _beforeTokenTransfer(
        address from,
        address to,
        uint256 amount
    ) internal virtual override(ERC20, ERC20Votes) {
        super._beforeTokenTransfer(from, to, amount);

        // No restrictions on minting, burning, or transfers involving exempt addresses
        if (from == address(0) || to == address(0) || isExemptFromAntiWhale[from] || isExemptFromAntiWhale[to]) {
            return;
        }

        // 1. Max transaction amount check (2% of total supply)
        if (amount > MAX_TX_AMOUNT) {
            revert ExceedsMaxTransactionAmount(amount);
        }

        // 2. Holder cap check (max 10M tokens)
        if (balanceOf(to) + amount > HOLDER_CAP) {
            revert ExceedsHolderCap(to, balanceOf(to), amount);
        }

        // 3. Transfer cooldown check for large transactions (5 minutes)
        if (amount >= LARGE_TX_THRESHOLD) {
            uint256 nextAvailable = _lastLargeTxTimestamp[from] + TX_COOLDOWN;
            if (block.timestamp < nextAvailable) {
                revert TransferCooldownActive(from, nextAvailable);
            }
            _lastLargeTxTimestamp[from] = block.timestamp;
        }
    }

    // --- Admin Functions ---

    /**
     * @notice Sets an address as exempt from anti-whale measures.
     * @dev Useful for exchange wallets, bridges, or other core protocol contracts.
     * Can only be called by the DEFAULT_ADMIN_ROLE.
     * @param account The address to set exemption for.
     * @param isExempt The exemption status.
     */
    function setAntiWhaleExemption(address account, bool isExempt) external onlyRole(DEFAULT_ADMIN_ROLE) {
        isExemptFromAntiWhale[account] = isExempt;
        emit AntiWhaleExemptionSet(account, isExempt);
    }

    // --- Governance Hooks (from ERC20Votes) ---
    // The following functions are overrides required by Solidity to handle diamond inheritance.
    // They ensure that both the core ERC20 functionality and the ERC20Votes snapshotting
    // functionality are executed correctly during transfers, mints, and burns.

    function _afterTokenTransfer(address from, address to, uint256 amount) internal virtual override(ERC20, ERC20Votes) {
        super._afterTokenTransfer(from, to, amount);
    }

    function _mint(address to, uint256 amount) internal virtual override(ERC20, ERC20Votes) {
        super._mint(to, amount);
    }

    function _burn(address account, uint256 amount) internal virtual override(ERC20, ERC20Burnable, ERC20Votes) {
        super._burn(account, amount);
    }
}