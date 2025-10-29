// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Royalty.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

/**
 * @title HyperMarket
 * @author Your Name
 * @notice A secure and feature-rich NFT marketplace that also serves as the ERC721 contract.
 * It includes listing, buying (ETH/ERC20), bidding, platform fees, and creator royalties.
 * This contract is designed for production use on EVM-compatible chains like Metis and Hyperion.
 */
contract HyperMarket is ERC721, ERC721URIStorage, ERC721Royalty, Ownable, Pausable, ReentrancyGuard {
    // =============================================================
    //                           STRUCTS
    // =============================================================

    struct Listing {
        address seller;
        uint256 price;
        uint256 expiresAt;
        address paymentToken; // address(0) for ETH, otherwise ERC20 address
    }

    struct Bid {
        address bidder;
        uint256 amount; // Bids are always in ETH
    }

    // =============================================================
    //                           STATE
    // =============================================================

    uint256 private _platformFeePercentage; // In basis points (e.g., 250 = 2.5%)
    uint256 private _royaltyPercentage;     // In basis points (e.g., 500 = 5.0%)

    mapping(uint256 => Listing) private _listings;
    mapping(uint256 => Bid) private _bids;
    mapping(uint256 => address) private _creators;
    mapping(address => uint256) public accruedFees; // paymentToken => amount

    // =============================================================
    //                           EVENTS
    // =============================================================

    event Listed(uint256 indexed tokenId, address indexed seller, uint256 price, address indexed paymentToken, uint256 expiresAt);
    event Unlisted(uint256 indexed tokenId);
    event Sold(uint256 indexed tokenId, address indexed seller, address indexed buyer, uint256 price, address paymentToken);
    event BidPlaced(uint256 indexed tokenId, address indexed bidder, uint256 amount);
    event BidAccepted(uint256 indexed tokenId, address indexed seller, address indexed bidder, uint256 amount);
    event BidRejected(uint256 indexed tokenId, address indexed bidder, uint256 amount);
    event FeePercentageChanged(uint256 newPercentage);
    event FeesWithdrawn(address indexed paymentToken, uint256 amount);

    // =============================================================
    //                           ERRORS
    // =============================================================

    error NotOwner();
    error AlreadyListed();
    error PriceMustBePositive();
    error DurationMustBePositive();
    error NotSeller();
    error NotListed();
    error ListingExpired();
    error IncorrectPaymentToken();
    error IncorrectEthAmount();
    error SellerCannotBeBuyer();
    error BidTooLow();
    error NoActiveBid();
    error FeeTooHigh();
    error RoyaltyTooHigh();
    error TransferFailed();
    error NoFeesToWithdraw();
    error TokenIsListed();

    // =============================================================
    //                         CONSTRUCTOR
    // =============================================================

    /**
     * @notice Sets up the contract, naming the NFT collection and setting initial fees.
     */
    constructor() ERC721("HyperMarket NFT", "HNFT") Ownable(msg.sender) {
        _platformFeePercentage = 250; // 2.5%
        _royaltyPercentage = 500;     // 5.0%
    }

    // =============================================================
    //                      LISTING FUNCTIONS
    // =============================================================

    /**
     * @notice Lists an NFT for sale on the marketplace.
     * @dev The NFT is transferred to the contract for escrow.
     * @param tokenId The ID of the token to list.
     * @param price The selling price.
     * @param duration The duration in seconds the listing will be active.
     * @param paymentToken The ERC20 token address for payment, or address(0) for ETH.
     */
    function listNFT(uint256 tokenId, uint256 price, uint256 duration, address paymentToken)
        external
        whenNotPaused
        nonReentrant
    {
        if (ownerOf(tokenId) != msg.sender) revert NotOwner();
        if (_listings[tokenId].price > 0) revert AlreadyListed();
        if (price == 0) revert PriceMustBePositive();
        if (duration == 0) revert DurationMustBePositive();

        uint256 expiresAt = block.timestamp + duration;
        _listings[tokenId] = Listing(msg.sender, price, expiresAt, paymentToken);

        _transfer(msg.sender, address(this), tokenId);
        emit Listed(tokenId, msg.sender, price, paymentToken, expiresAt);
    }

    /**
     * @notice Cancels an active listing.
     * @dev The NFT is returned to the seller. Any active bids are refunded.
     * @param tokenId The ID of the token to unlist.
     */
    function unlistNFT(uint256 tokenId) external whenNotPaused nonReentrant {
        Listing memory listing = _listings[tokenId];
        if (listing.seller != msg.sender) revert NotSeller();

        delete _listings[tokenId];
        _refundHighestBid(tokenId);

        _transfer(address(this), msg.sender, tokenId);
        emit Unlisted(tokenId);
    }

    // =============================================================
    //                       BUYING FUNCTIONS
    // =============================================================

    /**
     * @notice Buys a listed NFT using ETH.
     * @param tokenId The ID of the token to purchase.
     */
    function buyNFTWithEth(uint256 tokenId) external payable whenNotPaused nonReentrant {
        Listing memory listing = _listings[tokenId];
        if (listing.price == 0) revert NotListed();
        if (block.timestamp >= listing.expiresAt) revert ListingExpired();
        if (listing.paymentToken != address(0)) revert IncorrectPaymentToken();
        if (msg.value != listing.price) revert IncorrectEthAmount();
        if (listing.seller == msg.sender) revert SellerCannotBeBuyer();

        address seller = listing.seller;
        delete _listings[tokenId];
        _refundHighestBid(tokenId);

        _handlePayment(tokenId, listing.price, seller, msg.sender, address(0));
        _transfer(address(this), msg.sender, tokenId);

        emit Sold(tokenId, seller, msg.sender, listing.price, address(0));
    }

    /**
     * @notice Buys a listed NFT using a specified ERC20 token (e.g., USDC).
     * @dev Caller must have approved the marketplace to spend the required amount of the ERC20 token.
     * @param tokenId The ID of the token to purchase.
     */
    function buyNFTWithUsdc(uint256 tokenId) external whenNotPaused nonReentrant {
        Listing memory listing = _listings[tokenId];
        if (listing.price == 0) revert NotListed();
        if (block.timestamp >= listing.expiresAt) revert ListingExpired();
        if (listing.paymentToken == address(0)) revert IncorrectPaymentToken();
        if (listing.seller == msg.sender) revert SellerCannotBeBuyer();

        address seller = listing.seller;
        address paymentToken = listing.paymentToken;
        delete _listings[tokenId];
        _refundHighestBid(tokenId);

        IERC20(paymentToken).transferFrom(msg.sender, address(this), listing.price);

        _handlePayment(tokenId, listing.price, seller, msg.sender, paymentToken);
        _transfer(address(this), msg.sender, tokenId);

        emit Sold(tokenId, seller, msg.sender, listing.price, paymentToken);
    }

    // =============================================================
    //                       BIDDING FUNCTIONS
    // =============================================================

    /**
     * @notice Places a bid in ETH on a listed NFT.
     * @dev The bid amount is sent with the transaction and held in escrow.
     * Reverts if the bid is not higher than the current highest bid.
     * @param tokenId The ID of the token to bid on.
     */
    function placeBid(uint256 tokenId) external payable whenNotPaused nonReentrant {
        Listing memory listing = _listings[tokenId];
        if (listing.price == 0) revert NotListed();
        if (block.timestamp >= listing.expiresAt) revert ListingExpired();
        if (listing.seller == msg.sender) revert SellerCannotBeBuyer();

        Bid memory currentBid = _bids[tokenId];
        if (msg.value <= currentBid.amount) revert BidTooLow();

        if (currentBid.amount > 0) {
            (bool success, ) = currentBid.bidder.call{value: currentBid.amount}("");
            if (!success) revert TransferFailed();
        }

        _bids[tokenId] = Bid(msg.sender, msg.value);
        emit BidPlaced(tokenId, msg.sender, msg.value);
    }

    /**
     * @notice The seller accepts the current highest bid.
     * @dev Transfers the NFT to the bidder and distributes funds.
     * @param tokenId The ID of the token.
     */
    function acceptBid(uint256 tokenId) external whenNotPaused nonReentrant {
        Listing memory listing = _listings[tokenId];
        Bid memory bid = _bids[tokenId];
        if (listing.seller != msg.sender) revert NotSeller();
        if (bid.amount == 0) revert NoActiveBid();

        address seller = listing.seller;
        address bidder = bid.bidder;
        uint256 bidAmount = bid.amount;

        delete _listings[tokenId];
        delete _bids[tokenId];

        _handlePayment(tokenId, bidAmount, seller, bidder, address(0)); // Bids are in ETH
        _transfer(address(this), bidder, tokenId);

        emit BidAccepted(tokenId, seller, bidder, bidAmount);
        emit Sold(tokenId, seller, bidder, bidAmount, address(0));
    }

    /**
     * @notice The seller rejects the current highest bid.
     * @dev Refunds the bidder and allows for new, potentially higher bids.
     * @param tokenId The ID of the token.
     */
    function rejectBid(uint256 tokenId) external whenNotPaused nonReentrant {
        Listing memory listing = _listings[tokenId];
        Bid memory bid = _bids[tokenId];
        if (listing.seller != msg.sender) revert NotSeller();
        if (bid.amount == 0) revert NoActiveBid();

        address bidder = bid.bidder;
        uint256 amount = bid.amount;
        delete _bids[tokenId];

        (bool success, ) = bidder.call{value: amount}("");
        if (!success) revert TransferFailed();
        emit BidRejected(tokenId, bidder, amount);
    }

    // =============================================================
    //                       ADMIN FUNCTIONS
    // =============================================================

    /**
     * @notice Mints a new NFT and assigns it to an owner.
     * @dev Sets the creator for royalty purposes. Only callable by the contract owner.
     * @param to The address to receive the new NFT.
     * @param tokenId The ID of the new token.
     * @param uri The metadata URI for the new token.
     */
    function safeMint(address to, uint256 tokenId, string memory uri) external onlyOwner {
        _safeMint(to, tokenId);
        _setTokenURI(tokenId, uri);
        _creators[tokenId] = to;
    }

    /**
     * @notice Pauses critical marketplace functions in an emergency.
     * @dev Only callable by the contract owner.
     */
    function emergencyPause() external onlyOwner {
        _pause();
    }

    /**
     * @notice Resumes marketplace functions after a pause.
     * @dev Only callable by the contract owner.
     */
    function unpause() external onlyOwner {
        _unpause();
    }

    /**
     * @notice Updates the platform fee percentage.
     * @param newFeePercentage The new fee in basis points (e.g., 300 for 3.0%). Max 10%.
     */
    function setFeePercentage(uint256 newFeePercentage) external onlyOwner {
        if (newFeePercentage > 1000) revert FeeTooHigh(); // Max 10%
        _platformFeePercentage = newFeePercentage;
        emit FeePercentageChanged(newFeePercentage);
    }

    /**
     * @notice Withdraws accumulated platform fees for a specific token.
     * @param paymentToken The address of the token to withdraw, or address(0) for ETH.
     */
    function withdrawFees(address paymentToken) external onlyOwner {
        uint256 amount = accruedFees[paymentToken];
        if (amount == 0) revert NoFeesToWithdraw();

        accruedFees[paymentToken] = 0;

        if (paymentToken == address(0)) {
            (bool success, ) = owner().call{value: amount}("");
            if (!success) revert TransferFailed();
        } else {
            IERC20(paymentToken).transfer(owner(), amount);
        }
        emit FeesWithdrawn(paymentToken, amount);
    }

    // =============================================================
    //                      INTERNAL & HELPERS
    // =============================================================

    /**
     * @notice Internal function to calculate and distribute funds from a sale.
     */
    function _handlePayment(uint256 tokenId, uint256 price, address seller, address buyer, address paymentToken)
        internal
    {
        (address royaltyRecipient, uint256 royaltyAmount) = royaltyInfo(tokenId, price);
        uint256 platformFee = (price * _platformFeePercentage) / 10000;
        uint256 sellerProceeds = price - platformFee - royaltyAmount;

        accruedFees[paymentToken] += platformFee;

        if (paymentToken == address(0)) { // ETH payment
            (bool s1, ) = seller.call{value: sellerProceeds}("");
            if (!s1) revert TransferFailed();
            if (royaltyAmount > 0) {
                (bool s2, ) = royaltyRecipient.call{value: royaltyAmount}("");
                if (!s2) revert TransferFailed();
            }
        } else { // ERC20 payment
            IERC20 token = IERC20(paymentToken);
            token.transfer(seller, sellerProceeds);
            if (royaltyAmount > 0) {
                token.transfer(royaltyRecipient, royaltyAmount);
            }
        }
    }

    /**
     * @notice Internal function to refund the highest bid for a token, if one exists.
     */
    function _refundHighestBid(uint256 tokenId) internal {
        Bid memory bid = _bids[tokenId];
        if (bid.amount > 0) {
            delete _bids[tokenId];
            (bool success, ) = bid.bidder.call{value: bid.amount}("");
            if (!success) revert TransferFailed();
            emit BidRejected(tokenId, bid.bidder, bid.amount);
        }
    }

    // =============================================================
    //                       VIEW & OVERRIDES
    // =============================================================

    /**
     * @notice Hook to prevent direct transfers of listed NFTs.
     */
    function _beforeTokenTransfer(address from, address to, uint256 tokenId, uint256 batchSize)
        internal
        override(ERC721)
    {
        super._beforeTokenTransfer(from, to, tokenId, batchSize);
        if (from != address(this) && to != address(this) && from != address(0)) {
            if (_listings[tokenId].price > 0) revert TokenIsListed();
        }
    }

    /**
     * @notice Returns royalty information for a given token sale, compliant with EIP-2981.
     */
    function royaltyInfo(uint256 tokenId, uint256 salePrice)
        public
        view
        override
        returns (address receiver, uint256 royaltyAmount)
    {
        address creator = _creators[tokenId];
        if (creator == address(0)) {
            return (address(0), 0);
        }
        return (creator, (salePrice * _royaltyPercentage) / 10000);
    }

    function _burn(uint256 tokenId) internal override(ERC721, ERC721URIStorage, ERC721Royalty) {
        super._burn(tokenId);
    }

    function tokenURI(uint256 tokenId)
        public
        view
        override(ERC721, ERC721URIStorage)
        returns (string memory)
    {
        return super.tokenURI(tokenId);
    }

    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC721, ERC721URIStorage, ERC721Royalty)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }

    /**
     * @notice Returns the active listing details for a token.
     */
    function getListing(uint256 tokenId) external view returns (Listing memory) {
        return _listings[tokenId];
    }

    /**
     * @notice Returns the current highest bid for a token.
     */
    function getHighestBid(uint256 tokenId) external view returns (Bid memory) {
        return _bids[tokenId];
    }

    /**
     * @notice Returns the current platform fee percentage in basis points.
     */
    function getPlatformFeePercentage() external view returns (uint256) {
        return _platformFeePercentage;
    }
}