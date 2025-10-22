// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC721/IERC721.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

/**
 * @title EnglishAuction
 * @dev English auction contract
 * @notice This contract handles english auction functionality
 * @author HyperKit Agent
 */
contract EnglishAuction is Ownable, ReentrancyGuard, Pausable {
    IERC721 public immutable nft;
    IERC20 public immutable paymentToken;
    
    struct Auction {
        uint256 tokenId;
        address seller;
        uint256 startingPrice;
        uint256 currentPrice;
        uint256 endTime;
        address highestBidder;
        bool ended;
        bool cancelled;
    }
    
    mapping(uint256 => Auction) public auctions;
    mapping(uint256 => mapping(address => uint256)) public bids;
    
    uint256 public auctionCount;
    uint256 public platformFee;
    address public feeRecipient;
    
    event AuctionCreated(uint256 indexed auctionId, uint256 indexed tokenId, address indexed seller, uint256 startingPrice, uint256 endTime);
    event BidPlaced(uint256 indexed auctionId, address indexed bidder, uint256 amount);
    event AuctionEnded(uint256 indexed auctionId, address indexed winner, uint256 finalPrice);
    event AuctionCancelled(uint256 indexed auctionId);
    
    constructor(address _nft, address _paymentToken, address _feeRecipient) {
        require(_nft != address(0), "Invalid NFT address");
        require(_paymentToken != address(0), "Invalid payment token address");
        require(_feeRecipient != address(0), "Invalid fee recipient");
        
        nft = IERC721(_nft);
        paymentToken = IERC20(_paymentToken);
        feeRecipient = _feeRecipient;
        platformFee = 250; // 2.5%
    }
    
    function createAuction(
        uint256 tokenId,
        uint256 startingPrice,
        uint256 duration
    ) external whenNotPaused {
        require(nft.ownerOf(tokenId) == msg.sender, "Not token owner");
        require(startingPrice > 0, "Invalid starting price");
        require(duration > 0, "Invalid duration");
        
        nft.transferFrom(msg.sender, address(this), tokenId);
        
        uint256 auctionId = auctionCount++;
        auctions[auctionId] = Auction(
            tokenId,
            msg.sender,
            startingPrice,
            startingPrice,
            block.timestamp + duration,
            address(0),
            false,
            false
        );
        
        emit AuctionCreated(auctionId, tokenId, msg.sender, startingPrice, block.timestamp + duration);
    }
    
    function placeBid(uint256 auctionId, uint256 amount) external nonReentrant whenNotPaused {
        Auction storage auction = auctions[auctionId];
        require(!auction.ended, "Auction ended");
        require(!auction.cancelled, "Auction cancelled");
        require(block.timestamp < auction.endTime, "Auction expired");
        require(amount > auction.currentPrice, "Bid too low");
        
        // Refund previous highest bidder
        if (auction.highestBidder != address(0)) {
            require(paymentToken.transfer(auction.highestBidder, bids[auctionId][auction.highestBidder]), "Refund failed");
        }
        
        // Transfer new bid
        require(paymentToken.transferFrom(msg.sender, address(this), amount), "Transfer failed");
        
        auction.currentPrice = amount;
        auction.highestBidder = msg.sender;
        bids[auctionId][msg.sender] = amount;
        
        emit BidPlaced(auctionId, msg.sender, amount);
    }
    
    function endAuction(uint256 auctionId) external nonReentrant {
        Auction storage auction = auctions[auctionId];
        require(!auction.ended, "Auction already ended");
        require(auction.seller == msg.sender || block.timestamp >= auction.endTime, "Not authorized");
        
        auction.ended = true;
        
        if (auction.highestBidder != address(0)) {
            // Transfer NFT to winner
            nft.transferFrom(address(this), auction.highestBidder, auction.tokenId);
            
            // Calculate fees
            uint256 fee = (auction.currentPrice * platformFee) / 10000;
            uint256 sellerAmount = auction.currentPrice - fee;
            
            // Transfer payment to seller
            require(paymentToken.transfer(auction.seller, sellerAmount), "Transfer to seller failed");
            
            // Transfer fee to platform
            require(paymentToken.transfer(feeRecipient, fee), "Transfer fee failed");
            
            emit AuctionEnded(auctionId, auction.highestBidder, auction.currentPrice);
        } else {
            // No bids, return NFT to seller
            nft.transferFrom(address(this), auction.seller, auction.tokenId);
            emit AuctionEnded(auctionId, address(0), 0);
        }
    }
    
    function cancelAuction(uint256 auctionId) external {
        Auction storage auction = auctions[auctionId];
        require(auction.seller == msg.sender, "Not seller");
        require(!auction.ended, "Auction ended");
        require(!auction.cancelled, "Already cancelled");
        
        auction.cancelled = true;
        
        // Refund highest bidder if any
        if (auction.highestBidder != address(0)) {
            require(paymentToken.transfer(auction.highestBidder, bids[auctionId][auction.highestBidder]), "Refund failed");
        }
        
        // Return NFT to seller
        nft.transferFrom(address(this), auction.seller, auction.tokenId);
        
        emit AuctionCancelled(auctionId);
    }
    
    function setPlatformFee(uint256 _fee) external onlyOwner {
        require(_fee <= 1000, "Fee too high"); // Max 10%
        platformFee = _fee;
    }
    
    function setFeeRecipient(address _feeRecipient) external onlyOwner {
        require(_feeRecipient != address(0), "Invalid address");
        feeRecipient = _feeRecipient;
    }
}