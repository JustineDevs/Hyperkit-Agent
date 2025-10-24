// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Votes.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";

/**
 * @title IGameRewards
 * @dev Interface for game-related reward mechanics.
 */
interface IGameRewards {
    /**
     * @dev Rewards a player for completing a quest.
     * Must be called by a trusted game server or game master.
     * @param player The address of the player to reward.
     * @param baseAmount The base reward amount for the quest.
     */
    function rewardQuestCompletion(address player, uint256 baseAmount) external;
}

/**
 * @title ITreasuryManagement
 * @dev Interface for managing the contract's treasury.
 */
interface ITreasuryManagement {
    /**
     * @dev Sets the address of the treasury wallet.
     * @param _treasuryAddress The new treasury address.
     */
    function setTreasuryAddress(address _treasuryAddress) external;

    /**
     * @dev Returns the current treasury address.
     */
    function getTreasuryAddress() external view returns (address);
}

/**
 * @title GAMEX Token
 * @author Your Name
 * @notice A secure, production-ready play-to-earn ERC20 token for the GAMEX ecosystem.
 * @dev This contract implements ERC20, staking, vesting, anti-whale measures, and governance capabilities.
 * It is intended for deployment on EVM-compatible chains like Hyperion testnet (Chain ID: 133717).
 */
contract GAMEX is
    ERC20,
    ERC20Burnable,
    Pausable,
    AccessControl,
    EIP712,
    ERC20Votes,
    ReentrancyGuard,
    IGameRewards,
    ITreasuryManagement
{
    using SafeMath for uint256;

    // --- Roles ---
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");
    bytes32 public constant GAME_MASTER_ROLE = keccak256("GAME_MASTER_ROLE");
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");

    // --- Events ---
    event TokensStaked(address indexed user, uint256 amount);
    event TokensUnstaked(address indexed user, uint256 amount);
    event QuestRewardPaid(address indexed player, uint256 netAmount, uint256 burnedAmount);
    event VestedTokensReleased(address indexed recipient, uint256 amount);
    event TreasuryAddressUpdated(address indexed newTreasury);
    event AntiWhaleExemptionSet(address indexed account, bool isExempt);
    event MaxTotalSupplyUpdated(uint256 newMaxSupply);

    // --- Tokenomics Constants ---
    uint256 public immutable INITIAL_DISTRIBUTABLE_SUPPLY = 500_000_000 * 10**18;
    uint256 public maxTotalSupply;

    // --- Vesting ---
    uint256 public immutable VESTING_START_TIME;
    uint256 public constant VESTING_DURATION = 3 years;
    uint256 public constant TGE_PERCENTAGE = 10;
    uint256 public constant TREASURY_PERCENTAGE = 20;
    uint256 public totalVestedAndReleased;
    address public treasuryAddress;

    // --- Staking ---
    mapping(address => uint256) private _stakedBalances;
    uint256 private _totalStaked;

    // --- Anti-Whale ---
    uint256 public immutable MAX_TX_AMOUNT = (INITIAL_DISTRIBUTABLE_SUPPLY * 2) / 100;
    uint256 public immutable HOLDER_CAP = 10_000_000 * 10**18;
    uint256 public constant LARGE_TX_THRESHOLD = INITIAL_DISTRIBUTABLE_SUPPLY / 100; // 1% of supply
    uint256 public constant TRANSFER_COOLDOWN = 5 minutes;
    mapping(address => uint256) private _lastLargeTxTimestamp;
    mapping(address => bool) public isExemptFromAntiWhale;

    /**
     * @dev Sets up the token, roles, initial supply, and vesting schedule.
     * @param _initialAdmin The address to be granted initial admin, pauser, and game master roles.
     * @param _treasuryAddress The address for the project's treasury.
     */
    constructor(address _initialAdmin, address _treasuryAddress)
        ERC20("GAMEX Token", "GAMEX")
        EIP712("GAMEX Token", "1")
    {
        require(_initialAdmin != address(0), "GAMEX: Admin cannot be zero address");
        require(_treasuryAddress != address(0), "GAMEX: Treasury cannot be zero address");

        // --- Role Setup ---
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(ADMIN_ROLE, _initialAdmin);
        _grantRole(PAUSER_ROLE, _initialAdmin);
        _grantRole(GAME_MASTER_ROLE, _initialAdmin);
        _setRoleAdmin(ADMIN_ROLE, ADMIN_ROLE);
        _setRoleAdmin(PAUSER_ROLE, ADMIN_ROLE);
        _setRoleAdmin(GAME_MASTER_ROLE, ADMIN_ROLE);

        // --- Vesting & Supply Setup ---
        VESTING_START_TIME = block.timestamp;
        maxTotalSupply = 1_000_000_000 * 10**18; // 1B token cap including P2E inflation
        treasuryAddress = _treasuryAddress;

        // --- Initial Mint (TGE) ---
        uint256 tgeAmount = INITIAL_DISTRIBUTABLE_SUPPLY.mul(TGE_PERCENTAGE).div(100);
        totalVestedAndReleased = tgeAmount;
        _mint(_initialAdmin, tgeAmount);

        // --- Anti-Whale Exemptions ---
        isExemptFromAntiWhale[address(this)] = true;
        isExemptFromAntiWhale[_initialAdmin] = true;
        isExemptFromAntiWhale[_treasuryAddress] = true;
    }

    // --- External Functions: Staking ---

    /**
     * @notice Stakes GAMEX tokens to earn double quest rewards.
     * @dev Transfers tokens from the user to this contract.
     * @param amount The amount of tokens to stake.
     */
    function stake(uint256 amount) external nonReentrant whenNotPaused {
        require(amount > 0, "GAMEX: Cannot stake zero tokens");
        _stakedBalances[msg.sender] = _stakedBalances[msg.sender].add(amount);
        _totalStaked = _totalStaked.add(amount);
        emit TokensStaked(msg.sender, amount);
        transfer(address(this), amount);
    }

    /**
     * @notice Unstakes GAMEX tokens.
     * @dev Transfers tokens from this contract back to the user.
     * @param amount The amount of tokens to unstake.
     */
    function unstake(uint256 amount) external nonReentrant whenNotPaused {
        require(amount > 0, "GAMEX: Cannot unstake zero tokens");
        uint256 userStakedBalance = _stakedBalances[msg.sender];
        require(userStakedBalance >= amount, "GAMEX: Unstake amount exceeds staked balance");

        _stakedBalances[msg.sender] = userStakedBalance.sub(amount);
        _totalStaked = _totalStaked.sub(amount);
        emit TokensUnstaked(msg.sender, amount);
        _transfer(address(this), msg.sender, amount);
    }

    /**
     * @notice View the staked balance of an account.
     * @param account The address to query.
     * @return The amount of tokens staked by the account.
     */
    function stakedBalanceOf(address account) external view returns (uint256) {
        return _stakedBalances[account];
    }

    /**
     * @notice Check if an account is currently staking any tokens.
     * @param account The address to query.
     * @return True if the account has a staked balance > 0, false otherwise.
     */
    function isStaking(address account) public view returns (bool) {
        return _stakedBalances[account] > 0;
    }

    // --- External Functions: Vesting & Treasury ---

    /**
     * @notice Releases vested tokens according to the 3-year linear schedule.
     * @dev Can be called by anyone. Mints and distributes new tokens to the admin and treasury wallets.
     */
    function releaseVestedTokens() external whenNotPaused {
        uint256 claimable = getClaimableVestedTokens();
        require(claimable > 0, "GAMEX: No tokens available to release");

        totalVestedAndReleased = totalVestedAndReleased.add(claimable);

        uint256 treasuryAmount = claimable.mul(TREASURY_PERCENTAGE).div(100);
        uint256 teamAmount = claimable.sub(treasuryAmount);
        
        address admin = getRoleMember(ADMIN_ROLE, 0);

        if (treasuryAmount > 0) {
            _mint(treasuryAddress, treasuryAmount);
            emit VestedTokensReleased(treasuryAddress, treasuryAmount);
        }
        if (teamAmount > 0) {
            _mint(admin, teamAmount);
            emit VestedTokensReleased(admin, teamAmount);
        }
    }

    /**
     * @notice Calculates the amount of tokens that can be released from the vesting schedule.
     * @return The amount of claimable vested tokens.
     */
    function getClaimableVestedTokens() public view returns (uint256) {
        if (block.timestamp < VESTING_START_TIME) {
            return 0;
        }

        uint256 elapsedTime = block.timestamp.sub(VESTING_START_TIME);
        if (elapsedTime >= VESTING_DURATION) {
             uint256 totalVestable = INITIAL_DISTRIBUTABLE_SUPPLY;
             if (totalVestedAndReleased >= totalVestable) return 0;
             return totalVestable.sub(totalVestedAndReleased);
        }

        uint256 totalVestable = INITIAL_DISTRIBUTABLE_SUPPLY;
        uint256 vestedSoFar = totalVestable.mul(elapsedTime).div(VESTING_DURATION);

        if (vestedSoFar <= totalVestedAndReleased) {
            return 0;
        }

        return vestedSoFar.sub(totalVestedAndReleased);
    }

    /**
     * @notice Returns the current treasury address.
     * @return The address of the treasury.
     */
    function getTreasuryAddress() external view override returns (address) {
        return treasuryAddress;
    }

    // --- External Functions: In-Game Mechanics ---

    /**
     * @notice Mints tokens to a player for quest completion.
     * @dev Can only be called by a Game Master.
     * Staking doubles the reward. 5% of the gross reward is burned (by not minting it).
     * @param player The address of the player to reward.
     * @param baseAmount The base reward, must be between 10 and 100 tokens.
     */
    function rewardQuestCompletion(address player, uint256 baseAmount) external override nonReentrant whenNotPaused {
        require(hasRole(GAME_MASTER_ROLE, msg.sender), "GAMEX: Caller is not a Game Master");
        require(player != address(0), "GAMEX: Cannot reward the zero address");
        uint256 baseAmountWithDecimals = baseAmount.mul(10**18);
        require(baseAmountWithDecimals >= 10 * 10**18 && baseAmountWithDecimals <= 100 * 10**18, "GAMEX: Base amount out of range (10-100)");

        uint256 grossReward = isStaking(player) ? baseAmountWithDecimals.mul(2) : baseAmountWithDecimals;
        uint256 burnAmount = grossReward.mul(5).div(100);
        uint256 netReward = grossReward.sub(burnAmount);

        require(totalSupply().add(netReward) <= maxTotalSupply, "GAMEX: Minting would exceed max total supply");

        _mint(player, netReward);
        emit QuestRewardPaid(player, netReward, burnAmount);
    }

    // --- External Functions: Admin ---

    /**
     * @notice Pauses all token transfers, staking, and unstaking.
     * @dev Can only be called by an address with the PAUSER_ROLE.
     */
    function pause() external {
        require(hasRole(PAUSER_ROLE, msg.sender), "GAMEX: Caller is not a pauser");
        _pause();
    }

    /**
     * @notice Unpauses the contract, resuming all functions.
     * @dev Can only be called by an address with the PAUSER_ROLE.
     */
    function unpause() external {
        require(hasRole(PAUSER_ROLE, msg.sender), "GAMEX: Caller is not a pauser");
        _unpause();
    }

    /**
     * @notice Sets or removes an address from the anti-whale exemption list.
     * @dev Can only be called by an address with the ADMIN_ROLE.
     * @param account The address to modify.
     * @param isExempt True to exempt, false to remove exemption.
     */
    function setExemptFromAntiWhale(address account, bool isExempt) external {
        require(hasRole(ADMIN_ROLE, msg.sender), "GAMEX: Caller is not an admin");
        isExemptFromAntiWhale[account] = isExempt;
        emit AntiWhaleExemptionSet(account, isExempt);
    }

    /**
     * @notice Updates the treasury address.
     * @dev Can only be called by an address with the ADMIN_ROLE.
     * @param _treasuryAddress The new address for the treasury.
     */
    function setTreasuryAddress(address _treasuryAddress) external override {
        require(hasRole(ADMIN_ROLE, msg.sender), "GAMEX: Caller is not an admin");
        require(_treasuryAddress != address(0), "GAMEX: Treasury cannot be zero address");
        treasuryAddress = _treasuryAddress;
        setExemptFromAntiWhale(_treasuryAddress, true); // Automatically exempt new treasury
        emit TreasuryAddressUpdated(_treasuryAddress);
    }

    /**
     * @notice Updates the maximum total supply of the token.
     * @dev Can only be called by an address with the ADMIN_ROLE.
     * @param _newMaxSupply The new maximum total supply.
     */
    function setMaxTotalSupply(uint256 _newMaxSupply) external {
        require(hasRole(ADMIN_ROLE, msg.sender), "GAMEX: Caller is not an admin");
        require(_newMaxSupply >= totalSupply(), "GAMEX: New max supply cannot be less than current total supply");
        maxTotalSupply = _newMaxSupply;
        emit MaxTotalSupplyUpdated(_newMaxSupply);
    }

    // --- Internal & Overridden Functions ---

    /**
     * @dev Hook that is called before any token transfer, including minting and burning.
     * Enforces anti-whale measures.
     */
    function _beforeTokenTransfer(address from, address to, uint256 amount) internal virtual override whenNotPaused {
        super._beforeTokenTransfer(from, to, amount);

        if (isExemptFromAntiWhale[from] || isExemptFromAntiWhale[to]) {
            return;
        }

        // Max Transaction Amount Check
        require(amount <= MAX_TX_AMOUNT, "AntiWhale: Transaction amount exceeds limit");

        // Holder Cap Check
        if (to != address(0)) { // Exclude burns
            require(balanceOf(to).add(amount) <= HOLDER_CAP, "AntiWhale: Receiver balance would exceed holder cap");
        }

        // Transfer Cooldown Check for large transactions
        if (amount >= LARGE_TX_THRESHOLD) {
            require(
                block.timestamp >= _lastLargeTxTimestamp[from].add(TRANSFER_COOLDOWN),
                "AntiWhale: Cooldown active for large transactions"
            );
            _lastLargeTxTimestamp[from] = block.timestamp;
        }
    }

    /**
     * @dev Overrides for ERC20Votes compatibility.
     */
    function _afterTokenTransfer(address from, address to, uint256 amount) internal virtual override(ERC20, ERC20Votes) {
        super._afterTokenTransfer(from, to, amount);
    }

    function _mint(address to, uint256 amount) internal virtual override(ERC20, ERC20Votes) {
        super._mint(to, amount);
    }

    function _burn(address account, uint256 amount) internal virtual override(ERC20, ERC20Votes) {
        super._burn(account, amount);
    }
}