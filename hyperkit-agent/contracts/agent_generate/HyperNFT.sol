// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Burnable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title HyperNFT
 * @author Your Name
 * @notice A simple, secure, and production-ready ERC721 NFT contract.
 * @dev This contract implements a basic NFT with minting, burning, and metadata functionalities.
 * It uses OpenZeppelin contracts for standard implementations and security.
 * Access control is managed by Ownable, allowing only the owner to mint tokens and manage settings.
 */
contract HyperNFT is ERC721, ERC721Burnable, Ownable, ReentrancyGuard {
    using Counters for Counters.Counter;

    // A counter to keep track of the next token ID to be minted.
    Counters.Counter private _tokenIdCounter;

    // The base URI for the token metadata.
    string private _baseURIextended;

    /**
     * @dev Emitted when the base URI is updated.
     * @param newBaseURI The new base URI string.
     */
    event BaseURIUpdated(string newBaseURI);

    /**
     * @notice Thrown when an operation is attempted on a non-existent token.
     * @param tokenId The ID of the token that does not exist.
     */
    error HyperNFT__TokenDoesNotExist(uint256 tokenId);

    /**
     * @notice Thrown when attempting to mint to the zero address.
     */
    error HyperNFT__MintToZeroAddress();

    /**
     * @notice Initializes the contract, setting the name, symbol, and owner.
     * @param initialOwner The address that will be the initial owner of the contract.
     */
    constructor(address initialOwner) ERC721("HyperNFT", "HNFT") Ownable(initialOwner) {}

    /**
     * @notice Returns the base URI for the token metadata.
     * @dev This is an internal function that overrides the one in ERC721.
     * @return The base URI string.
     */
    function _baseURI() internal view override returns (string memory) {
        return _baseURIextended;
    }

    /**
     * @notice Sets the base URI for all token IDs.
     * @dev The URI is used to construct the metadata URL for each token.
     * The final URL will be `baseURI` + `tokenId`.
     * This function can only be called by the contract owner.
     * @param baseURI_ The new base URI string.
     */
    function setBaseURI(string calldata baseURI_) public onlyOwner {
        _baseURIextended = baseURI_;
        emit BaseURIUpdated(baseURI_);
    }

    /**
     * @notice Mints a new NFT and assigns it to a specified address.
     * @dev This function can only be called by the contract owner.
     * It increments the token ID counter and uses `_safeMint` to ensure
     * the recipient can receive ERC721 tokens.
     * Reentrancy guard is used as a security best practice.
     * @param to The address to mint the new NFT to.
     * @return The ID of the newly minted token.
     */
    function safeMint(address to) public onlyOwner nonReentrant returns (uint256) {
        if (to == address(0)) {
            revert HyperNFT__MintToZeroAddress();
        }
        uint256 tokenId = _tokenIdCounter.current();
        _tokenIdCounter.increment();
        _safeMint(to, tokenId);
        return tokenId;
    }

    /**
     * @notice Overrides the `burn` function to include a check for token existence.
     * @dev Although ERC721Burnable handles most checks, this provides a more specific error.
     * @param tokenId The ID of the token to burn.
     */
    function burn(uint256 tokenId) public override(ERC721Burnable) {
        if (!_exists(tokenId)) {
            revert HyperNFT__TokenDoesNotExist(tokenId);
        }
        super.burn(tokenId);
    }
    
    /**
     * @notice Returns the URI for a given token ID.
     * @dev Throws if the token ID does not exist.
     * Constructs the URI by concatenating the base URI and the token ID.
     * @param tokenId The ID of the token.
     * @return The token URI string.
     */
    function tokenURI(uint256 tokenId) public view override(ERC721) returns (string memory) {
        if (!_exists(tokenId)) {
            revert HyperNFT__TokenDoesNotExist(tokenId);
        }
        return super.tokenURI(tokenId);
    }

    /**
     * @notice Allows the owner to withdraw any Ether sent to this contract.
     * @dev This is a protective measure against accidentally sending funds to the contract.
     * Reentrancy guard is used to prevent reentrancy attacks during the transfer.
     */
    function withdraw() public onlyOwner nonReentrant {
        uint256 balance = address(this).balance;
        require(balance > 0, "No Ether to withdraw");
        (bool success, ) = owner().call{value: balance}("");
        require(success, "Failed to send Ether");
    }
}