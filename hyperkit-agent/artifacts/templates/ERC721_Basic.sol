// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

/**
 * @title BasicERC721
 * @dev Basic ERC721 NFT contract with URI storage and ownership
 * @author HyperKit AI Agent
 */
contract BasicERC721 is ERC721, ERC721URIStorage, Ownable {
    using Counters for Counters.Counter;
    
    Counters.Counter private _tokenIdCounter;
    
    // Base URI for metadata
    string private _baseTokenURI;
    
    // Maximum supply (0 = unlimited)
    uint256 public maxSupply;
    
    // Minting price
    uint256 public mintPrice;
    
    // Events
    event TokenMinted(address indexed to, uint256 indexed tokenId, string tokenURI);
    event BaseURIUpdated(string newBaseURI);
    event MintPriceUpdated(uint256 newPrice);
    event MaxSupplyUpdated(uint256 newMaxSupply);
    
    constructor(
        string memory name,
        string memory symbol,
        string memory baseTokenURI,
        uint256 _maxSupply,
        uint256 _mintPrice
    ) ERC721(name, symbol) {
        _baseTokenURI = baseTokenURI;
        maxSupply = _maxSupply;
        mintPrice = _mintPrice;
    }
    
    /**
     * @dev Mint a new token to the specified address
     * @param to Address to mint the token to
     * @param tokenURI URI for the token metadata
     */
    function mint(address to, string memory tokenURI) public payable {
        require(maxSupply == 0 || _tokenIdCounter.current() < maxSupply, "Max supply reached");
        require(msg.value >= mintPrice, "Insufficient payment");
        
        uint256 tokenId = _tokenIdCounter.current();
        _tokenIdCounter.increment();
        
        _safeMint(to, tokenId);
        _setTokenURI(tokenId, tokenURI);
        
        emit TokenMinted(to, tokenId, tokenURI);
    }
    
    /**
     * @dev Mint multiple tokens in a batch
     * @param to Address to mint the tokens to
     * @param tokenURIs Array of URIs for the token metadata
     */
    function batchMint(address to, string[] memory tokenURIs) public payable {
        require(maxSupply == 0 || _tokenIdCounter.current() + tokenURIs.length <= maxSupply, "Exceeds max supply");
        require(msg.value >= mintPrice * tokenURIs.length, "Insufficient payment");
        
        for (uint256 i = 0; i < tokenURIs.length; i++) {
            uint256 tokenId = _tokenIdCounter.current();
            _tokenIdCounter.increment();
            
            _safeMint(to, tokenId);
            _setTokenURI(tokenId, tokenURIs[i]);
            
            emit TokenMinted(to, tokenId, tokenURIs[i]);
        }
    }
    
    /**
     * @dev Owner-only minting function
     * @param to Address to mint the token to
     * @param tokenURI URI for the token metadata
     */
    function ownerMint(address to, string memory tokenURI) public onlyOwner {
        require(maxSupply == 0 || _tokenIdCounter.current() < maxSupply, "Max supply reached");
        
        uint256 tokenId = _tokenIdCounter.current();
        _tokenIdCounter.increment();
        
        _safeMint(to, tokenId);
        _setTokenURI(tokenId, tokenURI);
        
        emit TokenMinted(to, tokenId, tokenURI);
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
     * @dev Set the base URI for all tokens
     * @param baseURI New base URI
     */
    function setBaseURI(string memory baseURI) public onlyOwner {
        _baseTokenURI = baseURI;
        emit BaseURIUpdated(baseURI);
    }
    
    /**
     * @dev Set the minting price
     * @param newPrice New minting price in wei
     */
    function setMintPrice(uint256 newPrice) public onlyOwner {
        mintPrice = newPrice;
        emit MintPriceUpdated(newPrice);
    }
    
    /**
     * @dev Set the maximum supply
     * @param newMaxSupply New maximum supply (0 = unlimited)
     */
    function setMaxSupply(uint256 newMaxSupply) public onlyOwner {
        maxSupply = newMaxSupply;
        emit MaxSupplyUpdated(newMaxSupply);
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
     * @dev Override supportsInterface to support both ERC721 and ERC721URIStorage
     * @param interfaceId Interface ID to check
     * @return True if interface is supported
     */
    function supportsInterface(bytes4 interfaceId) public view override(ERC721, ERC721URIStorage) returns (bool) {
        return super.supportsInterface(interfaceId);
    }
}
