pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

// Interfaces
interface IGameRewards {
    function questComplete(address player, uint256 questID) external returns (uint256);
}

interface ITreasuryManagement {
    function deposit(uint256 amount) external;
    function withdraw(uint256 amount) external;
}


contract GAMEX is ERC20, ERC20Burnable, Ownable, ReentrancyGuard, IGameRewards, ITreasuryManagement {

    // Constants
    uint256 public constant TOTAL_SUPPLY = 500_000_000 * 10**18; // 500M tokens with 18 decimals
    uint256 public constant INITIAL_RELEASE_PERCENTAGE = 10; // 10%
    uint256 public constant BURN_PERCENTAGE = 5; // 5%
    uint256 public constant TREASURY_PERCENTAGE = 20; // 20%
    uint256 public constant MAX_TRANSACTION_PERCENTAGE = 2; // 2%
    uint256 public constant HOLDER_CAP = 10_000_000 * 10**18; // 10M tokens cap
    uint256 public constant COOLDOWN_PERIOD = 5 minutes; // 5 minute cooldown
    uint256 public constant MIN_REWARD = 10 * 10**18; // Minimum quest reward
    uint256 public constant MAX_REWARD = 100 * 10**18; // Maximum quest reward


    // State variables
    uint256 public releasedSupply;
    uint256 public vestingStartTime;
    uint256 public vestingDuration; // In seconds
    mapping(address => uint256) public lastTransferTime;
    address public treasury;

    // Events
    event TokensVested(address indexed recipient, uint256 amount);
    event TokensBurned(address indexed burner, uint256 amount);


    // Constructor
    constructor(address _treasury) ERC20("GAMEX", "GAMEX") Ownable(msg.sender) {
        treasury = _treasury;

        // Calculate initial release
        uint256 initialRelease = (TOTAL_SUPPLY * INITIAL_RELEASE_PERCENTAGE) / 100;
        _mint(owner(), initialRelease);
        releasedSupply = initialRelease;

        // Initialize vesting schedule (assuming 3 years)
        vestingStartTime = block.timestamp;
        vestingDuration = 3 years;

        // Transfer 20% to treasury
        uint256 treasuryAllocation = (TOTAL_SUPPLY * TREASURY_PERCENTAGE) / 100;
        _transfer(owner(), treasury, treasuryAllocation);

    }

    // --- Core Functions ---

    // Override _beforeTokenTransfer to implement anti-whale measures and holder cap
    


        // Anti-whale measures
        if (from != address(0) && to != address(0)) { // Exclude minting and burning
           // Max Transaction Size
            uint256 maxTransaction = (totalSupply() * MAX_TRANSACTION_PERCENTAGE) / 100;
            require(amount <= maxTransaction, "GAMEX: Transaction amount exceeds maximum allowed.");

            // Cooldown for large transactions (excluding treasury)
            if (amount > maxTransaction / 10 && from != treasury && to != treasury) { // Trigger cooldown for >10% of max tx size
                require(block.timestamp >= lastTransferTime[from] + COOLDOWN_PERIOD, "GAMEX: Transfer cooldown active.");
                lastTransferTime[from] = block.timestamp;
            }
        }
    }


    // Release tokens over time
    function releaseTokens() public onlyOwner {
      uint256 tokensToRelease = calculateTokensToRelease();
      if (tokensToRelease > 0) {
        _mint(owner(), tokensToRelease);
        releasedSupply += tokensToRelease;
        emit TokensVested(owner(), tokensToRelease);
      }
    }

    function calculateTokensToRelease() public view returns (uint256) {
        uint256 elapsedTime = block.timestamp - vestingStartTime;
        uint256 maxRelease = TOTAL_SUPPLY - releasedSupply; //Remaining tokens to release
        if (elapsedTime >= vestingDuration) {
           return maxRelease;
        }

        uint256 releasedAmount = (maxRelease * elapsedTime) / vestingDuration;
        return releasedAmount;
    }


    // --- Game Mechanics ---

    // Quest Completion
    function questComplete(address player, uint256 questID) external override returns (uint256) {
        require(questID > 0, "GAMEX: Invalid quest ID");

        // Reward amount
        uint256 rewardAmount = (uint256(keccak256(abi.encodePacked(block.timestamp, player, questID))) % (MAX_REWARD - MIN_REWARD + 1)) + MIN_REWARD;
        // Apply staking bonus if applicable (dummy implementation)
        // In a real implementation, this would involve checking stake status.
        if (isStaked(player)) {
            rewardAmount = rewardAmount * 2;
        }

        // Mint and burn tokens
        _mint(player, rewardAmount);

        //Burn 5%
        uint256 burnAmount = (rewardAmount * BURN_PERCENTAGE) / 100;
        _burn(player, burnAmount);
        emit TokensBurned(player, burnAmount);
        return rewardAmount;
    }

    // Staking Check (Dummy Implementation - Replace with your staking contract integration)
    function isStaked(address _player) public pure returns (bool) {
        // Replace with your actual staking contract logic
        // For this example, let's assume no one is staked
        return false;
    }


    // --- Treasury Management ---
    function deposit(uint256 amount) external override onlyTreasury {
        _transfer(msg.sender, treasury, amount);
    }

    function withdraw(uint256 amount) external override onlyTreasury {
        _transfer(treasury, msg.sender, amount);
    }


    // --- Owner-Only Functions ---
    function setTreasury(address _newTreasury) external onlyOwner {
        treasury = _newTreasury;
    }

    // --- Helper functions---
     function transferOwnership(address newOwner) public override onlyOwner {
        releaseTokens();
        super.transferOwnership(newOwner);
    }



    // --- Modifiers ---
    modifier onlyTreasury() {
        require(msg.sender == treasury, "GAMEX: Only treasury can call this function");
        _;
    }

    // --- ERC20 Compliance---
    function supportsInterface(bytes4 interfaceId) public view virtual override(ERC20) returns (bool) {
        return interfaceId == type(IGameRewards).interfaceId || interfaceId == type(ITreasuryManagement).interfaceId || super.supportsInterface(interfaceId);
    }
}