// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

/**
 * @title GameERC721
 * @dev ERC721 NFT contract with gaming features like levels, stats, and upgrades
 * @author HyperKit AI Agent
 */
contract GameERC721 is ERC721, ERC721Enumerable, ERC721URIStorage, Ownable, ReentrancyGuard {
    using Counters for Counters.Counter;
    
    Counters.Counter private _tokenIdCounter;
    
    // Game stats structure
    struct GameStats {
        uint256 level;
        uint256 experience;
        uint256 strength;
        uint256 agility;
        uint256 intelligence;
        uint256 vitality;
        uint256 lastUpgrade;
    }
    
    // Token metadata
    struct TokenMetadata {
        string name;
        string description;
        string image;
        string[] attributes;
        GameStats stats;
    }
    
    // Contract state
    string private _baseTokenURI;
    uint256 public maxSupply;
    uint256 public mintPrice;
    uint256 public upgradeCost;
    
    // Game mechanics
    mapping(uint256 => GameStats) public tokenStats;
    mapping(uint256 => TokenMetadata) public tokenMetadata;
    mapping(address => uint256) public playerLevel;
    
    // Events
    event TokenMinted(address indexed to, uint256 indexed tokenId, string name);
    event TokenUpgraded(uint256 indexed tokenId, uint256 newLevel, uint256 newExp);
    event StatsUpdated(uint256 indexed tokenId, GameStats stats);
    event PlayerLevelUp(address indexed player, uint256 newLevel);
    event UpgradeCostUpdated(uint256 newCost);
    
    constructor(
        string memory name,
        string memory symbol,
        string memory baseTokenURI,
        uint256 _maxSupply,
        uint256 _mintPrice,
        uint256 _upgradeCost
    ) ERC721(name, symbol) {
        _baseTokenURI = baseTokenURI;
        maxSupply = _maxSupply;
        mintPrice = _mintPrice;
        upgradeCost = _upgradeCost;
    }
    
    /**
     * @dev Mint a new game NFT
     * @param to Address to mint the token to
     * @param name Token name
     * @param description Token description
     * @param image Token image URI
     * @param attributes Array of attributes
     * @param initialStats Initial game stats
     */
    function mintGameToken(
        address to,
        string memory name,
        string memory description,
        string memory image,
        string[] memory attributes,
        GameStats memory initialStats
    ) public payable nonReentrant {
        require(maxSupply == 0 || _tokenIdCounter.current() < maxSupply, "Max supply reached");
        require(msg.value >= mintPrice, "Insufficient payment");
        require(initialStats.level > 0, "Level must be greater than 0");
        
        uint256 tokenId = _tokenIdCounter.current();
        _tokenIdCounter.increment();
        
        _safeMint(to, tokenId);
        
        // Set token metadata
        tokenMetadata[tokenId] = TokenMetadata({
            name: name,
            description: description,
            image: image,
            attributes: attributes,
            stats: initialStats
        });
        
        // Set initial stats
        tokenStats[tokenId] = initialStats;
        
        // Update player level
        _updatePlayerLevel(to);
        
        emit TokenMinted(to, tokenId, name);
        emit StatsUpdated(tokenId, initialStats);
    }
    
    /**
     * @dev Upgrade a token's stats
     * @param tokenId Token ID to upgrade
     * @param statType Stat type to upgrade (1=strength, 2=agility, 3=intelligence, 4=vitality)
     * @param amount Amount to increase the stat by
     */
    function upgradeToken(
        uint256 tokenId,
        uint256 statType,
        uint256 amount
    ) public payable nonReentrant {
        require(_exists(tokenId), "Token does not exist");
        require(ownerOf(tokenId) == msg.sender, "Not token owner");
        require(msg.value >= upgradeCost * amount, "Insufficient payment");
        require(statType >= 1 && statType <= 4, "Invalid stat type");
        require(amount > 0, "Amount must be greater than 0");
        
        GameStats storage stats = tokenStats[tokenId];
        
        // Update the specified stat
        if (statType == 1) {
            stats.strength += amount;
        } else if (statType == 2) {
            stats.agility += amount;
        } else if (statType == 3) {
            stats.intelligence += amount;
        } else if (statType == 4) {
            stats.vitality += amount;
        }
        
        // Add experience
        stats.experience += amount * 10;
        stats.lastUpgrade = block.timestamp;
        
        // Check for level up
        uint256 newLevel = _calculateLevel(stats.experience);
        if (newLevel > stats.level) {
            stats.level = newLevel;
            emit TokenUpgraded(tokenId, newLevel, stats.experience);
        }
        
        emit StatsUpdated(tokenId, stats);
    }
    
    /**
     * @dev Add experience to a token
     * @param tokenId Token ID
     * @param expAmount Experience amount to add
     */
    function addExperience(uint256 tokenId, uint256 expAmount) public {
        require(_exists(tokenId), "Token does not exist");
        require(ownerOf(tokenId) == msg.sender, "Not token owner");
        require(expAmount > 0, "Experience amount must be greater than 0");
        
        GameStats storage stats = tokenStats[tokenId];
        stats.experience += expAmount;
        
        // Check for level up
        uint256 newLevel = _calculateLevel(stats.experience);
        if (newLevel > stats.level) {
            stats.level = newLevel;
            emit TokenUpgraded(tokenId, newLevel, stats.experience);
        }
        
        emit StatsUpdated(tokenId, stats);
    }
    
    /**
     * @dev Get token stats
     * @param tokenId Token ID
     * @return Game stats
     */
    function getTokenStats(uint256 tokenId) public view returns (GameStats memory) {
        require(_exists(tokenId), "Token does not exist");
        return tokenStats[tokenId];
    }
    
    /**
     * @dev Get token metadata
     * @param tokenId Token ID
     * @return Token metadata
     */
    function getTokenMetadata(uint256 tokenId) public view returns (TokenMetadata memory) {
        require(_exists(tokenId), "Token does not exist");
        return tokenMetadata[tokenId];
    }
    
    /**
     * @dev Get player's total level across all tokens
     * @param player Player address
     * @return Total level
     */
    function getPlayerTotalLevel(address player) public view returns (uint256) {
        uint256 totalLevel = 0;
        uint256 balance = balanceOf(player);
        
        for (uint256 i = 0; i < balance; i++) {
            uint256 tokenId = tokenOfOwnerByIndex(player, i);
            totalLevel += tokenStats[tokenId].level;
        }
        
        return totalLevel;
    }
    
    /**
     * @dev Get tokens owned by a player with their stats
     * @param player Player address
     * @return Array of token IDs and their stats
     */
    function getPlayerTokens(address player) public view returns (uint256[] memory, GameStats[] memory) {
        uint256 balance = balanceOf(player);
        uint256[] memory tokenIds = new uint256[](balance);
        GameStats[] memory stats = new GameStats[](balance);
        
        for (uint256 i = 0; i < balance; i++) {
            uint256 tokenId = tokenOfOwnerByIndex(player, i);
            tokenIds[i] = tokenId;
            stats[i] = tokenStats[tokenId];
        }
        
        return (tokenIds, stats);
    }
    
    /**
     * @dev Calculate level based on experience
     * @param experience Experience points
     * @return Level
     */
    function _calculateLevel(uint256 experience) internal pure returns (uint256) {
        if (experience < 100) return 1;
        if (experience < 300) return 2;
        if (experience < 600) return 3;
        if (experience < 1000) return 4;
        if (experience < 1500) return 5;
        if (experience < 2100) return 6;
        if (experience < 2800) return 7;
        if (experience < 3600) return 8;
        if (experience < 4500) return 9;
        if (experience < 5500) return 10;
        
        // For levels above 10, use a more complex formula
        return 10 + ((experience - 5500) / 1000);
    }
    
    /**
     * @dev Update player level
     * @param player Player address
     */
    function _updatePlayerLevel(address player) internal {
        uint256 newLevel = getPlayerTotalLevel(player);
        if (newLevel > playerLevel[player]) {
            playerLevel[player] = newLevel;
            emit PlayerLevelUp(player, newLevel);
        }
    }
    
    /**
     * @dev Set the upgrade cost
     * @param newCost New upgrade cost in wei
     */
    function setUpgradeCost(uint256 newCost) public onlyOwner {
        upgradeCost = newCost;
        emit UpgradeCostUpdated(newCost);
    }
    
    /**
     * @dev Set the minting price
     * @param newPrice New minting price in wei
     */
    function setMintPrice(uint256 newPrice) public onlyOwner {
        mintPrice = newPrice;
    }
    
    /**
     * @dev Set the maximum supply
     * @param newMaxSupply New maximum supply (0 = unlimited)
     */
    function setMaxSupply(uint256 newMaxSupply) public onlyOwner {
        maxSupply = newMaxSupply;
    }
    
    /**
     * @dev Set the base URI for all tokens
     * @param baseURI New base URI
     */
    function setBaseURI(string memory baseURI) public onlyOwner {
        _baseTokenURI = baseURI;
    }
    
    /**
     * @dev Withdraw contract balance
     */
    function withdraw() public onlyOwner {
        uint256 balance = address(this).balance;
        require(balance > 0, "No funds to withdraw");
        
        (bool success, ) = payable(owner()).call{value: balance}("");
        require(success, "Withdrawal failed");
    }
    
    /**
     * @dev Get the current token ID counter
     * @return Current token ID
     */
    function getCurrentTokenId() public view returns (uint256) {
        return _tokenIdCounter.current();
    }
    
    /**
     * @dev Get the total supply
     * @return Total number of tokens minted
     */
    function totalSupply() public view returns (uint256) {
        return _tokenIdCounter.current();
    }
    
    /**
     * @dev Override _baseURI to return the base token URI
     * @return Base token URI
     */
    function _baseURI() internal view override returns (string memory) {
        return _baseTokenURI;
    }
    
    /**
     * @dev Override tokenURI to return the full URI
     * @param tokenId Token ID
     * @return Full token URI
     */
    function tokenURI(uint256 tokenId) public view override(ERC721, ERC721URIStorage) returns (string memory) {
        return super.tokenURI(tokenId);
    }
    
    /**
     * @dev Override _beforeTokenTransfer to add enumerability
     */
    function _beforeTokenTransfer(
        address from,
        address to,
        uint256 tokenId,
        uint256 batchSize
    ) internal override(ERC721, ERC721Enumerable) {
        super._beforeTokenTransfer(from, to, tokenId, batchSize);
        
        // Update player levels when tokens are transferred
        if (from != address(0)) {
            _updatePlayerLevel(from);
        }
        if (to != address(0)) {
            _updatePlayerLevel(to);
        }
    }
    
    /**
     * @dev Override supportsInterface to support all interfaces
     * @param interfaceId Interface ID to check
     * @return True if interface is supported
     */
    function supportsInterface(bytes4 interfaceId) public view override(ERC721, ERC721Enumerable, ERC721URIStorage) returns (bool) {
        return super.supportsInterface(interfaceId);
    }
}
