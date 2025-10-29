// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/interfaces/IERC2981.sol";
import "@openzeppelin/contracts/utils/Context.sol";

/**
 * @title HyperMarket
 * @author Your Name
 * @notice A secure and feature-rich NFT marketplace.
 * It combines ERC721 NFT functionality with a marketplace for listing, selling, and bidding.
 * Supports sales in native ETH and USDC, with built-in platform fees and creator royalties (EIP-2981).
 * This contract is designed for Metis (1088) and Hyperion (133717) chains.
 */
contract HyperMarket is ERC721, ERC721Enumerable, ERC721URIStorage, IERC2981, Ownable, Pausable, ReentrancyGuard {

    //----------- STRUCTS -----------//

    struct Listing {
        address seller;
        uint256 price;
        address paymentToken; // address(0) for ETH
        uint256 expiresAt;
    }

    struct Bid {
        address bidder;
        uint256 amount;
        address paymentToken; // Matches the listing's payment token
    }

    //----------- STATE VARIABLES -----------//

    uint256 private _nextTokenId;

    address public usdcTokenAddress;
    address payable public feeRecipient;

    uint256 public platformFeePercentage; // In basis points, e.g., 250 for 2.5%
    uint256 public constant ROYALTY_PERCENTAGE = 500; // 5% creator royalty
    uint256 public constant BASIS_POINTS = 10000;

    mapping(uint256 => Listing) public listings;
    mapping(uint256 => Bid) public highestBid;
    mapping(uint256 => address) private _tokenCreators;
    mapping(address => uint256) public accumulatedFees;

    //----------- EVENTS -----------//

    event Listed(uint256 indexed tokenId, address indexed seller, uint256 price, address indexed paymentToken, uint256 expiresAt);
    event Unlisted(uint256 indexed tokenId);
    event Sold(uint256 indexed tokenId, address seller, address indexed buyer, uint256 price, address indexed paymentToken);
    event BidPlaced(uint256 indexed tokenId, address indexed bidder, uint256 amount, address indexed paymentToken);
    event BidAccepted(uint256 indexed tokenId, address seller, address indexed bidder, uint256 amount, address indexed paymentToken);
    event FeePercentageChanged(uint256 newFeePercentage);
    event FeesWithdrawn(address indexed recipient, address indexed token, uint256 amount);

    //----------- ERRORS -----------//

    error NotNFTOwner();
    error TokenNotListed();
    error TokenAlreadyListed();
    error ListingExpired();
    error ListingNotExpired();
    error PriceMustBeGreaterThanZero();
    error DurationMustBePositive();
    error InvalidPaymentToken();
    error IncorrectPaymentAmount();
    error NoBidExists();
    error BidTooLow();
    error NotHighestBidder();
    error CallerNotSeller();
    error Paused();
    error InvalidFeePercentage();
    error TransferFailed();
    error NotTheCreator();

    //----------- CONSTRUCTOR -----------//

    /**
     * @param _usdcTokenAddress The address of the USDC stablecoin contract.
     * @param _feeRecipient The address where platform fees will be sent.
     */
    constructor(address _usdcTokenAddress, address payable _feeRecipient) ERC721("HyperMarket NFT", "HNFT") {
        if (_usdcTokenAddress == address(0) || _feeRecipient == address(0)) {
            revert("Zero address not allowed");
        }
        usdcTokenAddress = _usdcTokenAddress;
        feeRecipient = _feeRecipient;
        platformFeePercentage = 250; // Default 2.5%
    }

    //----------- MARKETPLACE - LISTING FUNCTIONS -----------//

    /**
     * @notice Lists an NFT for sale.
     * @dev The NFT is transferred to the contract for escrow.
     * @param tokenId The ID of the token to list.
     * @param price The selling price in wei (for ETH) or atomic units (for USDC).
     * @param duration The duration in seconds for which the listing will be active.
     */
    function listNFT(uint256 tokenId, uint256 price, uint256 duration) external whenNotPaused {
        if (ownerOf(tokenId) != _msgSender()) revert NotNFTOwner();
        if (_isListed(tokenId)) revert TokenAlreadyListed();
        if (price == 0) revert PriceMustBeGreaterThanZero();
        if (duration == 0) revert DurationMustBePositive();
        
        address paymentToken = usdcTokenAddress; // Default to USDC, can be extended for more tokens

        uint256 expiresAt = block.timestamp + duration;
        listings[tokenId] = Listing(_msgSender(), price, paymentToken, expiresAt);

        _safeTransfer(msg.sender, address(this), tokenId, "");
        
        emit Listed(tokenId, _msgSender(), price, paymentToken, expiresAt);
    }
    
    /**
     * @notice Unlists an NFT from the marketplace.
     * @dev Refunds any existing highest bid and returns the NFT to the seller.
     * @param tokenId The ID of the token to unlist.
     */
    function unlistNFT(uint256 tokenId) external nonReentrant {
        Listing memory listing = listings[tokenId];
        if (listing.seller != _msgSender()) revert CallerNotSeller();

        _clearListingAndRefundBid(tokenId);

        _safeTransfer(address(this), listing.seller, tokenId, "");

        emit Unlisted(tokenId);
    }

    //----------- MARKETPLACE - BUYING FUNCTIONS -----------//

    /**
     * @notice Buys a listed NFT using ETH.
     * @dev The function is payable and expects msg.value to be the price.
     * @param tokenId The ID of the token to buy.
     */
    function buyNFTWithETH(uint256 tokenId) external payable whenNotPaused nonReentrant {
        Listing memory listing = listings[tokenId];
        if (listing.price == 0) revert TokenNotListed();
        if (block.timestamp > listing.expiresAt) revert ListingExpired();
        if (msg.value != listing.price) revert IncorrectPaymentAmount();

        _handleSale(tokenId, _msgSender());
    }

    /**
     * @notice Buys a listed NFT using USDC.
     * @dev Caller must have approved the contract to spend USDC on their behalf.
     * @param tokenId The ID of the token to buy.
     */
    function buyNFTWithUSDC(uint256 tokenId) external whenNotPaused nonReentrant {
        Listing memory listing = listings[tokenId];
        if (listing.price == 0) revert TokenNotListed();
        if (block.timestamp > listing.expiresAt) revert ListingExpired();
        if (listing.paymentToken != usdcTokenAddress) revert InvalidPaymentToken();
        
        IERC20(usdcTokenAddress).transferFrom(_msgSender(), address(this), listing.price);

        _handleSale(tokenId, _msgSender());
    }

    //----------- MARKETPLACE - BIDDING FUNCTIONS -----------//

    /**
     * @notice Places a bid on a listed NFT.
     * @dev Holds the bid amount in escrow. Refunds the previous highest bidder.
     * @param tokenId The ID of the token to bid on.
     * @param bidAmount The amount of the bid.
     */
    function placeBid(uint256 tokenId, uint256 bidAmount) external payable whenNotPaused nonReentrant {
        Listing memory listing = listings[tokenId];
        if (listing.price == 0) revert TokenNotListed();
        if (block.timestamp > listing.expiresAt) revert ListingExpired();

        Bid memory currentHighestBid = highestBid[tokenId];
        if (bidAmount <= currentHighestBid.amount) revert BidTooLow();

        _refundBid(tokenId); // Refund previous bidder if one exists

        // Escrow the new bid
        if (listing.paymentToken == usdcTokenAddress) {
            IERC20(usdcTokenAddress).transferFrom(_msgSender(), address(this), bidAmount);
        } else { // Handle native ETH
             if(msg.value != bidAmount) revert IncorrectPaymentAmount();
        }

        highestBid[tokenId] = Bid(_msgSender(), bidAmount, listing.paymentToken);
        emit BidPlaced(tokenId, _msgSender(), bidAmount, listing.paymentToken);
    }
    
    /**
     * @notice Accepts the highest bid for a listed NFT.
     * @dev Can only be called by the NFT seller.
     * @param tokenId The ID of the token.
     */
    function acceptBid(uint256 tokenId) external whenNotPaused nonReentrant {
        Listing memory listing = listings[tokenId];
        if (listing.seller != _msgSender()) revert CallerNotSeller();
        if (block.timestamp > listing.expiresAt) revert ListingExpired();

        Bid memory bidToAccept = highestBid[tokenId];
        if (bidToAccept.bidder == address(0)) revert NoBidExists();

        // The bid amount is already held in escrow by the contract
        _handleSale(tokenId, bidToAccept.bidder);
    }

    //----------- ADMIN FUNCTIONS -----------//

    /**
     * @notice Sets the platform fee percentage.
     * @param _newFeePercentage The new fee in basis points (e.g., 300 for 3.0%).
     */
    function setFeePercentage(uint256 _newFeePercentage) external onlyOwner {
        if (_newFeePercentage > 1000) revert InvalidFeePercentage(); // Max 10% fee
        platformFeePercentage = _newFeePercentage;
        emit FeePercentageChanged(_newFeePercentage);
    }

    /**
     * @notice Withdraws accumulated fees to the fee recipient.
     */
    function withdrawFees() external onlyOwner nonReentrant {
        uint256 ethBalance = accumulatedFees[address(0)];
        if (ethBalance > 0) {
            accumulatedFees[address(0)] = 0;
            (bool success, ) = feeRecipient.call{value: ethBalance}("");
            if (!success) revert TransferFailed();
            emit FeesWithdrawn(feeRecipient, address(0), ethBalance);
        }

        uint256 usdcBalance = accumulatedFees[usdcTokenAddress];
        if (usdcBalance > 0) {
            accumulatedFees[usdcTokenAddress] = 0;
            IERC20(usdcTokenAddress).transfer(feeRecipient, usdcBalance);
            emit FeesWithdrawn(feeRecipient, usdcTokenAddress, usdcBalance);
        }
    }
    
    /**
     * @notice Pauses key marketplace functions in an emergency.
     */
    function emergencyPause() external onlyOwner {
        _pause();
    }

    /**
     * @notice Resumes the marketplace after a pause.
     */
    function unpause() external onlyOwner {
        _unpause();
    }

    //----------- NFT MINTING & ROYALTY FUNCTIONS -----------//

    /**
     * @notice Mints a new NFT and assigns its creator for royalty purposes.
     * @param to The address to mint the NFT to.
     * @param tokenURI_ The URI for the token's metadata.
     * @return The ID of the newly minted token.
     */
    function safeMint(address to, string memory tokenURI_) external onlyOwner returns (uint256) {
        uint256 tokenId = _nextTokenId++;
        _safeMint(to, tokenId);
        _setTokenURI(tokenId, tokenURI_);
        _tokenCreators[tokenId] = to; // Set the initial minter as the creator
        return tokenId;
    }
    
    /**
     * @notice EIP-2981 royalty information.
     * @param tokenId The ID of the token.
     * @param salePrice The price the token was sold for.
     * @return The royalty recipient and the royalty amount.
     */
    function royaltyInfo(uint256 tokenId, uint256 salePrice) external view override returns (address receiver, uint256 royaltyAmount) {
        address creator = _tokenCreators[tokenId];
        if (creator == address(0)) {
            return (address(0), 0);
        }
        return (creator, (salePrice * ROYALTY_PERCENTAGE) / BASIS_POINTS);
    }
    
    //----------- INTERNAL & HELPER FUNCTIONS -----------//
    
    /**
     * @dev Internal function to handle the logic of a sale.
     * Calculates and distributes funds for fees, royalties, and to the seller.
     * Transfers the NFT to the buyer and cleans up state.
     */
    function _handleSale(uint256 tokenId, address buyer) internal {
        Listing memory listing = listings[tokenId];
        uint256 price = highestBid[tokenId].amount > 0 ? highestBid[tokenId].amount : listing.price;
        
        // 1. Calculate and distribute funds
        uint256 platformFee = (price * platformFeePercentage) / BASIS_POINTS;
        uint256 creatorRoyalty = (price * ROYALTY_PERCENTAGE) / BASIS_POINTS;
        uint256 sellerProceeds = price - platformFee - creatorRoyalty;
        
        address creator = _tokenCreators[tokenId];

        accumulatedFees[listing.paymentToken] += platformFee;

        // 2. Transfer funds
        if (listing.paymentToken == usdcTokenAddress) {
            IERC20(usdcTokenAddress).transfer(creator, creatorRoyalty);
            IERC20(usdcTokenAddress).transfer(listing.seller, sellerProceeds);
        } else {
            _sendValue(payable(creator), creatorRoyalty);
            _sendValue(payable(listing.seller), sellerProceeds);
        }
        
        // 3. Clean up state and transfer NFT
        _clearListingAndRefundBid(tokenId);
        _safeTransfer(address(this), buyer, tokenId, "");
        
        emit Sold(tokenId, listing.seller, buyer, price, listing.paymentToken);
    }

    /**
     * @dev Clears a listing and refunds any existing highest bid.
     */
    function _clearListingAndRefundBid(uint256 tokenId) internal {
        _refundBid(tokenId);
        delete listings[tokenId];
    }
    
    /**
     * @dev Refunds the current highest bid for a token, if one exists.
     */
    function _refundBid(uint256 tokenId) internal {
        Bid memory currentHighestBid = highestBid[tokenId];
        if (currentHighestBid.bidder != address(0)) {
            delete highestBid[tokenId];
            if (currentHighestBid.paymentToken == usdcTokenAddress) {
                IERC20(usdcTokenAddress).transfer(currentHighestBid.bidder, currentHighestBid.amount);
            } else {
                _sendValue(payable(currentHighestBid.bidder), currentHighestBid.amount);
            }
        }
    }

    /**
     * @dev Helper to check if a token is currently listed.
     */
    function _isListed(uint256 tokenId) internal view returns (bool) {
        return listings[tokenId].seller != address(0);
    }

    /**
     * @dev Safe ETH transfer helper.
     */
    function _sendValue(address payable recipient, uint256 amount) internal {
        if (amount == 0) return;
        (bool success, ) = recipient.call{value: amount}("");
        if (!success) revert TransferFailed();
    }

    //----------- OVERRIDES -----------//

    function _beforeTokenTransfer(address from, address to, uint256 tokenId, uint256 batchSize) internal override(ERC721, ERC721Enumerable) {
        super._beforeTokenTransfer(from, to, tokenId, batchSize);
        // Prevent transfer of a listed token unless it's the marketplace contract moving it
        if (from != address(this) && to != address(this) && _isListed(tokenId)) {
            revert("Token is locked in the marketplace.");
        }
    }

    function _burn(uint256 tokenId) internal override(ERC721, ERC721URIStorage) {
        if(_isListed(tokenId)) revert TokenAlreadyListed();
        super._burn(tokenId);
    }

    function tokenURI(uint256 tokenId) public view override(ERC721, ERC721URIStorage) returns (string memory) {
        return super.tokenURI(tokenId);
    }

    function supportsInterface(bytes4 interfaceId) public view override(ERC721, ERC721Enumerable, ERC721URIStorage, IERC165) returns (bool) {
        return interfaceId == type(IERC2981).interfaceId || super.supportsInterface(interfaceId);
    }
}