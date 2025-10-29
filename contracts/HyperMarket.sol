// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/IERC721.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/utils/introspection/IERC165.sol";

/**
 * @title HyperMarket
 * @author Your Name
 * @notice A feature-rich, secure NFT marketplace for listing, selling, and bidding on ERC721 tokens.
 * Supports ETH and USDC payments, platform fees, and EIP-2981 royalties.
 */
contract HyperMarket is Ownable, ReentrancyGuard, Pausable {

    // EIP-2981 Royalty Standard Interface
    interface IERC2981 is IERC165 {
        function royaltyInfo(uint256 tokenId, uint256 salePrice)
            external
            view
            returns (address receiver, uint256 royaltyAmount);
    }

    // Structs
    struct Listing {
        address seller;
        uint256 price;
        address paymentToken; // address(0) for ETH
        uint256 expiresAt;
    }

    struct Bid {
        address bidder;
        uint256 amount;
    }

    // Constants
    uint16 public constant MAX_FEE_PERCENTAGE = 1000; // 10%
    uint16 private constant BASIS_POINTS = 10000;
    bytes4 private constant _INTERFACE_ID_ERC2981 = 0x2a55205a;
    address private constant ETH_ADDRESS = address(0);

    // State Variables
    uint16 public platformFeeBasisPoints;
    address public immutable usdcTokenAddress;

    // Mappings
    // NFT Contract Address -> Token ID -> Listing
    mapping(address => mapping(uint256 => Listing)) public listings;
    // NFT Contract Address -> Token ID -> Highest Bid
    mapping(address => mapping(uint256 => Bid)) public bids;
    // Token Address -> Amount
    mapping(address => uint256) public platformFeesAccrued;

    // Events
    event NFTListed(
        address indexed seller,
        address indexed nftAddress,
        uint256 indexed tokenId,
        uint256 price,
        address paymentToken,
        uint256 expiresAt
    );
    event NFTUnlisted(
        address indexed seller,
        address indexed nftAddress,
        uint256 indexed tokenId
    );
    event NFTSold(
        address indexed seller,
        address indexed buyer,
        address indexed nftAddress,
        uint256 tokenId,
        uint256 price,
        address paymentToken
    );
    event BidPlaced(
        address indexed bidder,
        address indexed nftAddress,
        uint256 indexed tokenId,
        uint256 amount
    );
    event BidAccepted(
        address indexed seller,
        address indexed bidder,
        address indexed nftAddress,
        uint256 tokenId,
        uint256 amount
    );
    event BidRejected(
        address indexed seller,
        address indexed nftAddress,
        uint256 indexed tokenId,
        address bidder,
        uint256 amount
    );
    event FeesWithdrawn(address indexed token, address indexed recipient, uint256 amount);
    event PlatformFeeUpdated(uint16 newFee);

    // Errors
    error NotNFTOwner();
    error NotApprovedForMarketplace();
    error PriceMustBeAboveZero();
    error DurationMustBeAboveZero();
    error TokenAlreadyListed();
    error TokenNotListed();
    error ListingExpired();
    error NotTheSeller();
    error BuyerCannotBeSeller();
    error InvalidPaymentToken();
    error IncorrectPaymentAmount();
    error NoBid();
    error BidderCannotBeSeller();
    error BidTooLow();
    error TransferFailed();
    error FeeTooHigh();
    error ZeroAddress();


    /**
     * @notice Sets up the marketplace with USDC address and initial platform fee.
     * @param _usdcTokenAddress The address of the USDC contract.
     * @param _initialFeeBasisPoints The initial platform fee in basis points (e.g., 250 for 2.5%).
     */
    constructor(address _usdcTokenAddress, uint16 _initialFeeBasisPoints) Ownable(msg.sender) {
        if (_usdcTokenAddress == address(0)) revert ZeroAddress();
        if (_initialFeeBasisPoints > MAX_FEE_PERCENTAGE) revert FeeTooHigh();
        usdcTokenAddress = _usdcTokenAddress;
        platformFeeBasisPoints = _initialFeeBasisPoints;
    }

    /**
     * @notice Lists an NFT for sale.
     * @dev The contract must be approved to transfer the NFT.
     * @param nftAddress The address of the ERC721 contract.
     * @param tokenId The ID of the token to list.
     * @param price The selling price in the smallest unit of the payment token.
     * @param paymentToken The token for payment (address(0) for ETH, or USDC address).
     * @param duration The duration of the listing in seconds.
     */
    function listNFT(
        address nftAddress,
        uint256 tokenId,
        uint256 price,
        address paymentToken,
        uint256 duration
    ) external whenNotPaused {
        IERC721 nft = IERC721(nftAddress);
        if (nft.ownerOf(tokenId) != msg.sender) revert NotNFTOwner();
        if (!nft.isApprovedForAll(msg.sender, address(this)) && nft.getApproved(tokenId) != address(this)) {
            revert NotApprovedForMarketplace();
        }
        if (price == 0) revert PriceMustBeAboveZero();
        if (duration == 0) revert DurationMustBeAboveZero();
        if (listings[nftAddress][tokenId].seller != address(0)) revert TokenAlreadyListed();
        if (paymentToken != ETH_ADDRESS && paymentToken != usdcTokenAddress) revert InvalidPaymentToken();

        uint256 expiresAt = block.timestamp + duration;
        listings[nftAddress][tokenId] = Listing({
            seller: msg.sender,
            price: price,
            paymentToken: paymentToken,
            expiresAt: expiresAt
        });

        emit NFTListed(msg.sender, nftAddress, tokenId, price, paymentToken, expiresAt);
    }

    /**
     * @notice Removes an NFT from the marketplace.
     * @dev Only the original lister can unlist. If a bid exists, it is refunded.
     * @param nftAddress The address of the ERC721 contract.
     * @param tokenId The ID of the token to unlist.
     */
    function unlistNFT(address nftAddress, uint256 tokenId) external nonReentrant {
        Listing memory listing = listings[nftAddress][tokenId];
        if (listing.seller != msg.sender) revert NotTheSeller();

        _clearListingAndRefundBid(nftAddress, tokenId);
        
        emit NFTUnlisted(msg.sender, nftAddress, tokenId);
    }

    /**
     * @notice Buys a listed NFT.
     * @dev Payment is sent with the transaction (ETH via msg.value, USDC via prior approval).
     * @param nftAddress The address of the ERC721 contract.
     * @param tokenId The ID of the token to buy.
     */
    function buyNFT(address nftAddress, uint256 tokenId) external payable nonReentrant whenNotPaused {
        Listing memory listing = listings[nftAddress][tokenId];

        if (listing.seller == address(0)) revert TokenNotListed();
        if (block.timestamp > listing.expiresAt) revert ListingExpired();
        if (listing.seller == msg.sender) revert BuyerCannotBeSeller();

        if (listing.paymentToken == ETH_ADDRESS) {
            if (msg.value != listing.price) revert IncorrectPaymentAmount();
        } else {
            if (msg.value != 0) revert IncorrectPaymentAmount();
            IERC20(listing.paymentToken).transferFrom(msg.sender, address(this), listing.price);
        }

        _processSale(nftAddress, tokenId, msg.sender);
    }

    /**
     * @notice Places a bid on a listed NFT.
     * @dev A bid must be higher than the current highest bid. The previous bidder is refunded.
     *      Funds for the bid are escrowed.
     * @param nftAddress The address of the ERC721 contract.
     * @param tokenId The ID of the token to bid on.
     * @param bidAmount The amount of the bid in the listing's payment currency.
     */
    function placeBid(address nftAddress, uint256 tokenId, uint256 bidAmount) external payable nonReentrant whenNotPaused {
        Listing memory listing = listings[nftAddress][tokenId];
        if (listing.seller == address(0)) revert TokenNotListed();
        if (block.timestamp > listing.expiresAt) revert ListingExpired();
        if (listing.seller == msg.sender) revert BidderCannotBeSeller();
        if (bidAmount == 0) revert PriceMustBeAboveZero();

        if (listing.paymentToken == ETH_ADDRESS) {
            if (msg.value != bidAmount) revert IncorrectPaymentAmount();
        } else {
            if (msg.value > 0) revert IncorrectPaymentAmount();
            IERC20(listing.paymentToken).transferFrom(msg.sender, address(this), bidAmount);
        }
        
        Bid memory currentBid = bids[nftAddress][tokenId];
        if (bidAmount <= currentBid.amount) revert BidTooLow();

        // Effect: Update the new highest bid first
        bids[nftAddress][tokenId] = Bid({bidder: msg.sender, amount: bidAmount});

        // Interaction: Refund the previous bidder
        if (currentBid.bidder != address(0)) {
            _safeTransfer(listing.paymentToken, currentBid.bidder, currentBid.amount);
        }

        emit BidPlaced(msg.sender, nftAddress, tokenId, bidAmount);
    }

    /**
     * @notice The seller accepts the current highest bid for an NFT.
     * @param nftAddress The address of the ERC721 contract.
     * @param tokenId The ID of the token.
     */
    function acceptBid(address nftAddress, uint256 tokenId) external nonReentrant whenNotPaused {
        Listing memory listing = listings[nftAddress][tokenId];
        if (listing.seller != msg.sender) revert NotTheSeller();
        
        Bid memory highestBid = bids[nftAddress][tokenId];
        if (highestBid.bidder == address(0)) revert NoBid();

        // Override listing price with bid amount for sale processing
        listings[nftAddress][tokenId].price = highestBid.amount;

        _processSale(nftAddress, tokenId, highestBid.bidder);
        
        emit BidAccepted(listing.seller, highestBid.bidder, nftAddress, tokenId, highestBid.amount);
    }

    /**
     * @notice The seller rejects the current highest bid for an NFT.
     * @dev This refunds the bidder and clears the bid, allowing for new bids.
     * @param nftAddress The address of the ERC721 contract.
     * @param tokenId The ID of the token.
     */
    function rejectBid(address nftAddress, uint256 tokenId) external nonReentrant {
        Listing memory listing = listings[nftAddress][tokenId];
        if (listing.seller != msg.sender) revert NotTheSeller();
        
        Bid memory highestBid = bids[nftAddress][tokenId];
        if (highestBid.bidder == address(0)) revert NoBid();

        // Effect
        delete bids[nftAddress][tokenId];
        
        // Interaction
        _safeTransfer(listing.paymentToken, highestBid.bidder, highestBid.amount);
        
        emit BidRejected(listing.seller, nftAddress, tokenId, highestBid.bidder, highestBid.amount);
    }

    // --- Admin Functions ---

    /**
     * @notice Updates the platform fee. Can only be called by the owner.
     * @param _newFeeBasisPoints The new fee in basis points (100 = 1%).
     */
    function setFeePercentage(uint16 _newFeeBasisPoints) external onlyOwner {
        if (_newFeeBasisPoints > MAX_FEE_PERCENTAGE) revert FeeTooHigh();
        platformFeeBasisPoints = _newFeeBasisPoints;
        emit PlatformFeeUpdated(_newFeeBasisPoints);
    }

    /**
     * @notice Withdraws accrued platform fees. Can only be called by the owner.
     * @param tokenAddress The address of the token to withdraw (address(0) for ETH).
     */
    function withdrawFees(address tokenAddress) external onlyOwner nonReentrant {
        uint256 amount = platformFeesAccrued[tokenAddress];
        if (amount == 0) return;
        
        platformFeesAccrued[tokenAddress] = 0;
        _safeTransfer(tokenAddress, owner(), amount);

        emit FeesWithdrawn(tokenAddress, owner(), amount);
    }

    /**
     * @notice Pauses the contract in case of an emergency.
     */
    function pause() external onlyOwner {
        _pause();
    }

    /**
     * @notice Unpauses the contract.
     */
    function unpause() external onlyOwner {
        _unpause();
    }


    // --- Internal & Private Functions ---

    /**
     * @dev Core logic for handling a sale, distributing funds, and transferring the NFT.
     */
    function _processSale(address nftAddress, uint256 tokenId, address buyer) private {
        Listing memory listing = listings[nftAddress][tokenId];

        // 1. Effects (State Changes)
        _clearListingAndBid(nftAddress, tokenId);
        
        // 2. Calculations
        uint256 salePrice = listing.price;
        uint256 fee = (salePrice * platformFeeBasisPoints) / BASIS_POINTS;
        (address royaltyReceiver, uint256 royaltyAmount) = _getRoyaltyInfo(nftAddress, tokenId, salePrice);

        uint256 sellerProceeds = salePrice - fee - royaltyAmount;
        
        platformFeesAccrued[listing.paymentToken] += fee;

        // 3. Interactions (External Calls)
        IERC721(nftAddress).safeTransferFrom(listing.seller, buyer, tokenId);
        
        _safeTransfer(listing.paymentToken, listing.seller, sellerProceeds);
        if (royaltyAmount > 0 && royaltyReceiver != address(0)) {
            _safeTransfer(listing.paymentToken, royaltyReceiver, royaltyAmount);
        }
        // The buyer's payment is already held by the contract from buyNFT/placeBid

        emit NFTSold(listing.seller, buyer, nftAddress, tokenId, salePrice, listing.paymentToken);
    }
    
    /**
     * @dev Clears a listing and its associated bid without refunding. Used during a sale.
     */
    function _clearListingAndBid(address nftAddress, uint256 tokenId) private {
        delete listings[nftAddress][tokenId];
        delete bids[nftAddress][tokenId];
    }

    /**
     * @dev Clears a listing and refunds any existing bid. Used during unlisting.
     */
    function _clearListingAndRefundBid(address nftAddress, uint256 tokenId) private {
        Listing memory listing = listings[nftAddress][tokenId];
        Bid memory currentBid = bids[nftAddress][tokenId];

        delete listings[nftAddress][tokenId];
        delete bids[nftAddress][tokenId];
        
        if (currentBid.bidder != address(0)) {
            _safeTransfer(listing.paymentToken, currentBid.bidder, currentBid.amount);
        }
    }

    /**
     * @dev Retrieves EIP-2981 royalty information if the NFT contract supports it.
     */
    function _getRoyaltyInfo(address nftAddress, uint256 tokenId, uint256 salePrice)
        private
        view
        returns (address receiver, uint256 royaltyAmount)
    {
        try IERC165(nftAddress).supportsInterface(_INTERFACE_ID_ERC2981) returns (bool supports) {
            if (supports) {
                return IERC2981(nftAddress).royaltyInfo(tokenId, salePrice);
            }
        } catch {
            // Contract does not support ERC165 or call reverted. Fallback to no royalties.
        }
        return (address(0), 0);
    }
    
    /**
     * @dev Safely transfers ETH or ERC20 tokens.
     */
    function _safeTransfer(address token, address to, uint256 value) private {
        if (value == 0) return;
        if (token == ETH_ADDRESS) {
            (bool success, ) = to.call{value: value}("");
            if (!success) revert TransferFailed();
        } else {
            IERC20(token).transfer(to, value);
        }
    }

    /**
     * @dev Allow contract to receive ETH.
     */
    receive() external payable {}
}