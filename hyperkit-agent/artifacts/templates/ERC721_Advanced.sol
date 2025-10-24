// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Burnable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "@openzeppelin/contracts/utils/cryptography/MerkleProof.sol";

/**
 * @title AdvancedERC721
 * @dev Advanced ERC721 NFT contract with multiple features
 * @author HyperKit AI Agent
 */
contract AdvancedERC721 is 
    ERC721, 
    ERC721Enumerable, 
    ERC721URIStorage, 
    ERC721Burnable, 
    AccessControl, 
    Pausable, 
    ReentrancyGuard 
{
    using Counters for Counters.Counter;
    
    Counters.Counter private _tokenIdCounter;
    
    // Roles
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant BURNER_ROLE = keccak256("BURNER_ROLE");
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");
    
    // Contract state
    string private _baseTokenURI;
    uint256 public maxSupply;
    uint256 public mintPrice;
    uint256 public maxMintPerAddress;
    uint256 public maxMintPerTransaction;
    
    // Whitelist and presale
    bytes32 public merkleRoot;
    bool public presaleActive;
    bool public publicSaleActive;
    uint256 public presalePrice;
    
    // Royalties
    address public royaltyRecipient;
    uint256 public royaltyPercentage; // Basis points (100 = 1%)
    
    // Metadata
    mapping(uint256 => string) private _tokenURIs;
    mapping(address => uint256) public mintedByAddress;
    
    // Events
    event TokenMinted(address indexed to, uint256 indexed tokenId, string tokenURI);
    event TokenBurned(uint256 indexed tokenId);
    event BaseURIUpdated(string newBaseURI);
    event MintPriceUpdated(uint256 newPrice);
    event MaxSupplyUpdated(uint256 newMaxSupply);
    event PresaleToggled(bool active);
    event PublicSaleToggled(bool active);
    event MerkleRootUpdated(bytes32 newRoot);
    event RoyaltiesUpdated(address recipient, uint256 percentage);
    
    constructor(
        string memory name,
        string memory symbol,
        string memory baseTokenURI,
        uint256 _maxSupply,
        uint256 _mintPrice,
        uint256 _maxMintPerAddress,
        uint256 _maxMintPerTransaction
    ) ERC721(name, symbol) {
        _baseTokenURI = baseTokenURI;
        maxSupply = _maxSupply;
        mintPrice = _mintPrice;
        maxMintPerAddress = _maxMintPerAddress;
        maxMintPerTransaction = _maxMintPerTransaction;
        
        // Set up roles
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(MINTER_ROLE, msg.sender);
        _grantRole(BURNER_ROLE, msg.sender);
        _grantRole(PAUSER_ROLE, msg.sender);
        
        // Set initial royalty recipient
        royaltyRecipient = msg.sender;
        royaltyPercentage = 250; // 2.5%
    }
    
    /**
     * @dev Mint a new token (public sale)
     * @param to Address to mint the token to
     * @param tokenURI URI for the token metadata
     * @param amount Number of tokens to mint
     */
    function mint(address to, string memory tokenURI, uint256 amount) public payable whenNotPaused nonReentrant {
        require(publicSaleActive, "Public sale not active");
        require(amount > 0 && amount <= maxMintPerTransaction, "Invalid mint amount");
        require(mintedByAddress[to] + amount <= maxMintPerAddress, "Exceeds max mint per address");
        require(maxSupply == 0 || _tokenIdCounter.current() + amount <= maxSupply, "Exceeds max supply");
        require(msg.value >= mintPrice * amount, "Insufficient payment");
        
        for (uint256 i = 0; i < amount; i++) {
            uint256 tokenId = _tokenIdCounter.current();
            _tokenIdCounter.increment();
            
            _safeMint(to, tokenId);
            _setTokenURI(tokenId, tokenURI);
            
            emit TokenMinted(to, tokenId, tokenURI);
        }
        
        mintedByAddress[to] += amount;
    }
    
    /**
     * @dev Mint during presale with merkle proof
     * @param to Address to mint the token to
     * @param tokenURI URI for the token metadata
     * @param amount Number of tokens to mint
     * @param proof Merkle proof for whitelist verification
     */
    function presaleMint(
        address to, 
        string memory tokenURI, 
        uint256 amount, 
        bytes32[] calldata proof
    ) public payable whenNotPaused nonReentrant {
        require(presaleActive, "Presale not active");
        require(amount > 0 && amount <= maxMintPerTransaction, "Invalid mint amount");
        require(mintedByAddress[to] + amount <= maxMintPerAddress, "Exceeds max mint per address");
        require(maxSupply == 0 || _tokenIdCounter.current() + amount <= maxSupply, "Exceeds max supply");
        require(msg.value >= presalePrice * amount, "Insufficient payment");
        require(verifyWhitelist(to, proof), "Not whitelisted");
        
        for (uint256 i = 0; i < amount; i++) {
            uint256 tokenId = _tokenIdCounter.current();
            _tokenIdCounter.increment();
            
            _safeMint(to, tokenId);
            _setTokenURI(tokenId, tokenURI);
            
            emit TokenMinted(to, tokenId, tokenURI);
        }
        
        mintedByAddress[to] += amount;
    }
    
    /**
     * @dev Owner-only minting function
     * @param to Address to mint the token to
     * @param tokenURI URI for the token metadata
     * @param amount Number of tokens to mint
     */
    function ownerMint(address to, string memory tokenURI, uint256 amount) public onlyRole(MINTER_ROLE) {
        require(amount > 0, "Amount must be greater than 0");
        require(maxSupply == 0 || _tokenIdCounter.current() + amount <= maxSupply, "Exceeds max supply");
        
        for (uint256 i = 0; i < amount; i++) {
            uint256 tokenId = _tokenIdCounter.current();
            _tokenIdCounter.increment();
            
            _safeMint(to, tokenId);
            _setTokenURI(tokenId, tokenURI);
            
            emit TokenMinted(to, tokenId, tokenURI);
        }
    }
    
    /**
     * @dev Burn a token
     * @param tokenId Token ID to burn
     */
    function burn(uint256 tokenId) public override onlyRole(BURNER_ROLE) {
        super.burn(tokenId);
        emit TokenBurned(tokenId);
    }
    
    /**
     * @dev Verify whitelist using merkle proof
     * @param account Address to verify
     * @param proof Merkle proof
     * @return True if whitelisted
     */
    function verifyWhitelist(address account, bytes32[] calldata proof) public view returns (bool) {
        bytes32 leaf = keccak256(abi.encodePacked(account));
        return MerkleProof.verify(proof, merkleRoot, leaf);
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
     * @dev Get tokens owned by an address
     * @param owner Address to check
     * @return Array of token IDs
     */
    function tokensOfOwner(address owner) public view returns (uint256[] memory) {
        uint256 tokenCount = balanceOf(owner);
        uint256[] memory tokens = new uint256[](tokenCount);
        
        for (uint256 i = 0; i < tokenCount; i++) {
            tokens[i] = tokenOfOwnerByIndex(owner, i);
        }
        
        return tokens;
    }
    
    /**
     * @dev Set the base URI for all tokens
     * @param baseURI New base URI
     */
    function setBaseURI(string memory baseURI) public onlyRole(DEFAULT_ADMIN_ROLE) {
        _baseTokenURI = baseURI;
        emit BaseURIUpdated(baseURI);
    }
    
    /**
     * @dev Set the minting price
     * @param newPrice New minting price in wei
     */
    function setMintPrice(uint256 newPrice) public onlyRole(DEFAULT_ADMIN_ROLE) {
        mintPrice = newPrice;
        emit MintPriceUpdated(newPrice);
    }
    
    /**
     * @dev Set the presale price
     * @param newPrice New presale price in wei
     */
    function setPresalePrice(uint256 newPrice) public onlyRole(DEFAULT_ADMIN_ROLE) {
        presalePrice = newPrice;
    }
    
    /**
     * @dev Set the maximum supply
     * @param newMaxSupply New maximum supply (0 = unlimited)
     */
    function setMaxSupply(uint256 newMaxSupply) public onlyRole(DEFAULT_ADMIN_ROLE) {
        maxSupply = newMaxSupply;
        emit MaxSupplyUpdated(newMaxSupply);
    }
    
    /**
     * @dev Set the merkle root for whitelist
     * @param root New merkle root
     */
    function setMerkleRoot(bytes32 root) public onlyRole(DEFAULT_ADMIN_ROLE) {
        merkleRoot = root;
        emit MerkleRootUpdated(root);
    }
    
    /**
     * @dev Toggle presale status
     */
    function togglePresale() public onlyRole(DEFAULT_ADMIN_ROLE) {
        presaleActive = !presaleActive;
        emit PresaleToggled(presaleActive);
    }
    
    /**
     * @dev Toggle public sale status
     */
    function togglePublicSale() public onlyRole(DEFAULT_ADMIN_ROLE) {
        publicSaleActive = !publicSaleActive;
        emit PublicSaleToggled(publicSaleActive);
    }
    
    /**
     * @dev Set royalty information
     * @param recipient Address to receive royalties
     * @param percentage Royalty percentage in basis points
     */
    function setRoyalties(address recipient, uint256 percentage) public onlyRole(DEFAULT_ADMIN_ROLE) {
        require(percentage <= 1000, "Royalty percentage too high"); // Max 10%
        royaltyRecipient = recipient;
        royaltyPercentage = percentage;
        emit RoyaltiesUpdated(recipient, percentage);
    }
    
    /**
     * @dev Pause the contract
     */
    function pause() public onlyRole(PAUSER_ROLE) {
        _pause();
    }
    
    /**
     * @dev Unpause the contract
     */
    function unpause() public onlyRole(PAUSER_ROLE) {
        _unpause();
    }
    
    /**
     * @dev Withdraw contract balance
     */
    function withdraw() public onlyRole(DEFAULT_ADMIN_ROLE) {
        uint256 balance = address(this).balance;
        require(balance > 0, "No funds to withdraw");
        
        (bool success, ) = payable(royaltyRecipient).call{value: balance}("");
        require(success, "Withdrawal failed");
    }
    
    /**
     * @dev EIP-2981 royalty info
     * @param tokenId Token ID
     * @param salePrice Sale price
     * @return Receiver and royalty amount
     */
    function royaltyInfo(uint256 tokenId, uint256 salePrice) external view returns (address, uint256) {
        return (royaltyRecipient, (salePrice * royaltyPercentage) / 10000);
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
     * @dev Override _beforeTokenTransfer to add enumerability and pausability
     */
    function _beforeTokenTransfer(
        address from,
        address to,
        uint256 tokenId,
        uint256 batchSize
    ) internal override(ERC721, ERC721Enumerable) whenNotPaused {
        super._beforeTokenTransfer(from, to, tokenId, batchSize);
    }
    
    /**
     * @dev Override supportsInterface to support all interfaces
     * @param interfaceId Interface ID to check
     * @return True if interface is supported
     */
    function supportsInterface(bytes4 interfaceId) public view override(ERC721, ERC721Enumerable, ERC721URIStorage, AccessControl) returns (bool) {
        return super.supportsInterface(interfaceId);
    }
}
