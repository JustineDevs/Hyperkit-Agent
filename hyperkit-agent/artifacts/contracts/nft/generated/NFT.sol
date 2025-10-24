// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/**
 * @title MyNFT
 * @author Your Name
 * @notice A simple, secure, and production-ready ERC721 NFT contract.
 * @dev This contract uses OpenZeppelin's ERC721, Ownable, Counters, and ReentrancyGuard
 * for a robust implementation. Minting is restricted to the owner.
 */
contract MyNFT is ERC721, Ownable, ReentrancyGuard {
    using Counters for Counters.Counter;

    // Counter to keep track of the next token ID to be minted.
    Counters.Counter private _tokenIdCounter;

    /**
     * @notice Initializes the contract, setting the name, symbol, and initial owner.
     * @dev The deployer of the contract will be set as the initial owner.
     * @param initialOwner The address to be set as the initial owner of the contract.
     */
    constructor(address initialOwner)
        ERC721("MyNFT", "MNFT")
        Ownable(initialOwner)
    {
        // The counter starts at 1, so the first minted token ID will be 1.
        _tokenIdCounter.increment();
    }

    /**
     * @notice Mints a new NFT and assigns it to the specified address.
     * @dev This function can only be called by the contract owner. It is protected
     * against reentrancy attacks. The token ID is auto-incremented.
     * A {Transfer} event is emitted upon successful minting.
     * @param to The address that will receive the minted NFT.
     * @return The ID of the newly minted token.
     */
    function safeMint(address to) public onlyOwner nonReentrant returns (uint256) {
        require(to != address(0), "MyNFT: Cannot mint to the zero address");

        uint256 tokenId = _tokenIdCounter.current();
        _tokenIdCounter.increment();
        _safeMint(to, tokenId);

        return tokenId;
    }

    /**
     * @dev See {IERC721Metadata-tokenURI}.
     * This implementation is a placeholder and should be overridden to return
     * the actual metadata URI for a given token ID.
     * @param tokenId The ID of the token to query the URI for.
     * @return A string containing the URI for the token's metadata.
     */
    function tokenURI(uint256 tokenId)
        public
        view
        override(ERC721)
        returns (string memory)
    {
        require(_exists(tokenId), "MyNFT: URI query for nonexistent token");

        // The baseURI function should be implemented to return the base path for your metadata files.
        // For example:
        // string memory baseURI = "https://api.mynft.com/metadata/";
        // return string(abi.encodePacked(baseURI, Strings.toString(tokenId)));
        return "";
    }
}