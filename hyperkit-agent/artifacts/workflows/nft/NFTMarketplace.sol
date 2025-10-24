// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/IERC721.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";

/**
 * @title NftAuctionMarketplace
 * @author Your Name Here
 * @notice A secure and feature-rich marketplace for auctioning gaming NFTs.
 * @dev This contract allows users to create auctions for their ERC721 tokens,
 * place bids, and finalize sales. It includes a platform fee, access control,
 * and security measures like reentrancy guards and a pausable mechanism.
 */
contract NftAuctionMarketplace is Ownable, Pausable, ReentrancyGuard {
    // =============================================================
    //                           STRUCTS
    // =============================================================

    struct Auction {
        address seller;
        IERC721 nftContract;
        uint256 tokenId;
        uint256 startingBid;
        uint256 endAt;
        address highestBidder;
        uint256 highestBid;
        bool started;
        bool ended;
    }

    // =============================================================
    //                        STATE VARIABLES
    // =============================================================

    uint256 private _auctionIdCounter;
    mapping(uint256 => Auction) public auctions;

    /// @notice The platform's fee percentage (e.g., 250 for 2.50%).
    uint256 public platformFeePercent; // Basis points (10000 = 100%)

    /// @notice The amount of fees accumulated and available for withdrawal by the owner.
    uint256 public accumulatedFees;

    // =============================================================
    //                           EVENTS
    // =============================================================

    /**
     * @notice Emitted when a new auction is created.
     * @param auctionId The unique identifier for the auction.
     * @param seller The address of the NFT owner starting the auction.
     * @param nftContract The address of the ERC721 contract.
     * @param tokenId The ID of the token being auctioned.
     * @param startingBid The minimum initial price for the NFT.
     * @param endAt The timestamp when the auction will end.
     */
    event AuctionCreated(
        uint256 indexed auctionId,
        address indexed seller,
        address indexed nftContract,
        uint256 tokenId,
        uint256 startingBid,
        uint256 endAt
    );

    /**
     * @notice Emitted when a bid is successfully placed on an auction.
     * @param auctionId The ID of the auction being bid on.
     * @param bidder The address of the user placing the bid.
     * @param amount The value of the bid in wei.
     */
    event BidPlaced(
        uint256 indexed auctionId,
        address indexed bidder,
        uint256 amount
    );

    /**
     * @notice Emitted when an auction successfully ends and the NFT is transferred.
     * @param auctionId The ID of the auction that ended.
     * @param winner The address of the highest bidder who won the auction.
     * @param finalPrice The final price the NFT was sold for.
     */
    event AuctionEnded(
        uint256 indexed auctionId,
        address winner,
        uint256 finalPrice
    );

    /**
     * @notice Emitted when an auction is cancelled by the seller.
     * @param auctionId The ID of the auction that was cancelled.
     * @param seller The address of the seller who cancelled the auction.
     */
    event AuctionCancelled(uint256 indexed auctionId, address indexed seller);

    /**
     * @notice Emitted when the platform fee is updated by the owner.
     * @param newFeePercent The new fee in basis points.
     */
    event PlatformFeeUpdated(uint256 newFeePercent);

    /**
     * @notice Emitted when platform fees are withdrawn by the owner.
     * @param amount The amount of fees withdrawn in wei.
     */
    event FeesWithdrawn(uint256 amount);


    // =============================================================
    //                           ERRORS
    // =============================================================

    error ZeroAddress();
    error InvalidDuration();
    error NotNftOwner();
    error NftNotApprovedForMarketplace();
    error AuctionDoesNotExist();
    error AuctionAlreadyEnded();
    error AuctionIsStillActive();
    error AuctionHasNotStarted();
    error BidTooLow();
    error OnlySellerCanCancel();
    error CannotCancelWithBids();
    error NoBidsPlaced();
    error InvalidFeePercent();
    error ZeroAmount();

    // =============================================================
    //                         CONSTRUCTOR
    // =============================================================

    /**
     * @notice Sets up the contract, initializes the owner, and sets the initial platform fee.
     * @param _initialFeePercent The initial platform fee in basis points (e.g., 250 for 2.50%).
     */
    constructor(uint256 _initialFeePercent) Ownable(msg.sender) {
        if (_initialFeePercent > 10000) revert InvalidFeePercent();
        platformFeePercent = _initialFeePercent;
        emit PlatformFeeUpdated(_initialFeePercent);
    }

    // =============================================================
    //                      AUCTION FUNCTIONS
    // =============================================================

    /**
     * @notice Creates a new auction for an ERC721 token.
     * @dev The caller must be the owner of the NFT and must have approved this contract
     * to transfer the token on their behalf via `approve()` or `setApprovalForAll()`.
     * @param _nftContract The address of the ERC721 token contract.
     * @param _tokenId The ID of the token to be auctioned.
     * @param _startingBid The minimum bid amount in wei.
     * @param _duration The duration of the auction in seconds.
     * @return auctionId The ID of the newly created auction.
     */
    function createAuction(
        address _nftContract,
        uint256 _tokenId,
        uint256 _startingBid,
        uint256 _duration
    ) external whenNotPaused returns (uint256) {
        if (_nftContract == address(0)) revert ZeroAddress();
        if (_duration == 0) revert InvalidDuration();

        IERC721 nft = IERC721(_nftContract);
        if (nft.ownerOf(_tokenId) != msg.sender) revert NotNftOwner();
        if (nft.getApproved(_tokenId) != address(this) && !nft.isApprovedForAll(msg.sender, address(this))) {
            revert NftNotApprovedForMarketplace();
        }

        uint256 auctionId = ++_auctionIdCounter;
        uint256 endTime = block.timestamp + _duration;

        auctions[auctionId] = Auction({
            seller: msg.sender,
            nftContract: nft,
            tokenId: _tokenId,
            startingBid: _startingBid,
            endAt: endTime,
            highestBidder: address(0),
            highestBid: 0,
            started: true,
            ended: false
        });

        emit AuctionCreated(
            auctionId,
            msg.sender,
            _nftContract,
            _tokenId,
            _startingBid,
            endTime
        );

        return auctionId;
    }

    /**
     * @notice Places a bid on an active auction.
     * @dev The sent `msg.value` must be greater than the current highest bid
     * (or the starting bid if it's the first bid). The previous highest bidder
     * will be refunded their bid amount.
     * @param _auctionId The ID of the auction to bid on.
     */
    function placeBid(uint256 _auctionId) external payable nonReentrant whenNotPaused {
        Auction storage currentAuction = auctions[_auctionId];

        if (!currentAuction.started) revert AuctionDoesNotExist();
        if (currentAuction.ended) revert AuctionAlreadyEnded();
        if (block.timestamp >= currentAuction.endAt) revert AuctionAlreadyEnded();

        uint256 currentHighestBid = currentAuction.highestBid == 0 ? currentAuction.startingBid : currentAuction.highestBid;
        if (msg.value <= currentHighestBid) revert BidTooLow();

        address previousHighestBidder = currentAuction.highestBidder;
        uint256 previousHighestBid = currentAuction.highestBid;

        currentAuction.highestBidder = msg.sender;
        currentAuction.highestBid = msg.value;

        // Refund the previous highest bidder if they exist
        if (previousHighestBidder != address(0)) {
            (bool success, ) = previousHighestBidder.call{value: previousHighestBid}("");
            // If the refund fails, the transaction is reverted.
            // This is generally safe but relies on the recipient being able to accept Ether.
            // A pull pattern could be used for more robustness against misbehaving contracts.
            require(success, "Failed to refund previous bidder");
        }

        emit BidPlaced(_auctionId, msg.sender, msg.value);
    }

    /**
     * @notice Ends an auction, transferring the NFT to the winner and funds to the seller.
     * @dev Can be called by anyone after the auction's end time has passed.
     * The platform fee is calculated and stored for the owner to withdraw.
     * @param _auctionId The ID of the auction to end.
     */
    function endAuction(uint256 _auctionId) external nonReentrant whenNotPaused {
        Auction storage currentAuction = auctions[_auctionId];

        if (!currentAuction.started) revert AuctionDoesNotExist();
        if (currentAuction.ended) revert AuctionAlreadyEnded();
        if (block.timestamp < currentAuction.endAt) revert AuctionIsStillActive();
        
        currentAuction.ended = true; // State change before external calls

        address winner = currentAuction.highestBidder;

        if (winner == address(0)) {
            // No bids were placed, so just end the auction.
            emit AuctionEnded(_auctionId, address(0), 0);
            return;
        }

        uint256 finalPrice = currentAuction.highestBid;
        address seller = currentAuction.seller;
        IERC721 nftContract = currentAuction.nftContract;
        uint256 tokenId = currentAuction.tokenId;

        // Calculate and collect platform fee
        uint256 fee = (finalPrice * platformFeePercent) / 10000;
        accumulatedFees += fee;
        uint256 sellerProceeds = finalPrice - fee;

        // Transfer NFT to winner
        // This requires prior approval from the seller
        nftContract.safeTransferFrom(seller, winner, tokenId);

        // Transfer funds to seller
        (bool success, ) = seller.call{value: sellerProceeds}("");
        require(success, "Failed to send funds to seller");

        emit AuctionEnded(_auctionId, winner, finalPrice);
    }

    /**
     * @notice Allows the seller to cancel an auction before any bids have been placed.
     * @param _auctionId The ID of the auction to cancel.
     */
    function cancelAuction(uint256 _auctionId) external whenNotPaused {
        Auction storage currentAuction = auctions[_auctionId];

        if (!currentAuction.started) revert AuctionDoesNotExist();
        if (currentAuction.ended) revert AuctionAlreadyEnded();
        if (msg.sender != currentAuction.seller) revert OnlySellerCanCancel();
        if (currentAuction.highestBidder != address(0)) revert CannotCancelWithBids();

        currentAuction.ended = true;

        emit AuctionCancelled(_auctionId, msg.sender);
    }

    // =============================================================
    //                       ADMIN FUNCTIONS
    // =============================================================

    /**
     * @notice Pauses all major marketplace functions.
     * @dev Only the contract owner can call this. Useful for emergencies.
     */
    function pause() external onlyOwner {
        _pause();
    }

    /**
     * @notice Unpauses the marketplace, resuming normal operations.
     * @dev Only the contract owner can call this.
     */
    function unpause() external onlyOwner {
        _unpause();
    }

    /**
     * @notice Updates the platform fee percentage.
     * @dev The fee is represented in basis points (1/100 of a percent). Max fee is 100% (10000).
     * @param _newFeePercent The new fee in basis points (e.g., 500 for 5.00%).
     */
    function setPlatformFee(uint256 _newFeePercent) external onlyOwner {
        if (_newFeePercent > 10000) revert InvalidFeePercent(); // Max 100% fee
        platformFeePercent = _newFeePercent;
        emit PlatformFeeUpdated(_newFeePercent);
    }

    /**
     * @notice Allows the contract owner to withdraw accumulated platform fees.
     */
    function withdrawFees() external onlyOwner nonReentrant {
        uint256 amount = accumulatedFees;
        if (amount == 0) revert ZeroAmount();

        accumulatedFees = 0; // State change before external call
        
        (bool success, ) = owner().call{value: amount}("");
        require(success, "Fee withdrawal failed");

        emit FeesWithdrawn(amount);
    }

    // =============================================================
    //                        VIEW FUNCTIONS
    // =============================================================

    /**
     * @notice Returns the details of a specific auction.
     * @param _auctionId The ID of the auction.
     * @return A tuple containing all auction details.
     */
    function getAuction(uint256 _auctionId) external view returns (Auction memory) {
        return auctions[_auctionId];
    }
}