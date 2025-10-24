// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

/**
 * @title HyperMarket
 * @author Your Name
 * @notice An integrated NFT (ERC721) and marketplace contract.
 * @dev This contract provides functionalities for minting, listing, buying, and bidding on NFTs.
 * It includes features like platform fees, creator royalties, and a pull-based withdrawal system for security.
 * It is designed to be secure, with reentrancy guards, pausable functionality, and access control.
 */
contract HyperMarket is ERC721, ERC721Enumerable, Ownable, Pausable, ReentrancyGuard {
    using Counters for Counters.Counter;
    Counters.Counter private _tokenIdCounter;

    uint256 public platformFeePercentage; // In basis points, e.g., 250 for 2.5%
    uint256 public creatorRoyaltyPercentage; // In basis points, e.g., 500 for 5%
    address public feeRecipient;

    struct Listing {
        address seller;
        uint256 price;
        address paymentToken; // address(0) for ETH
        uint256 expiresAt;
    }

    struct Bid {
        address bidder;
        uint256 amount;
        address paymentToken; // address(0) for ETH
    }

    // Mapping from token ID to its listing details
    mapping(uint256 => Listing) public listings;
    // Mapping from token ID to its creator for royalty distribution
    mapping(uint256 => address) public tokenCreators;
    // Mapping from token ID -> bidder address -> Bid
    mapping(uint256 => mapping(address => Bid)) public bids;
    // Mapping from user address -> token address -> balance to be withdrawn
    mapping(address => mapping(address => uint256)) public pendingWithdrawals;

    event Listed(
        uint256 indexed tokenId,
        address indexed seller,
        uint256 price,
        address indexed paymentToken,
        uint256 expiresAt
    );
    event Unlisted(uint256 indexed tokenId);
    event Sold(
        uint256 indexed tokenId,
        address seller,
        address indexed buyer,
        uint256 price,
        address indexed paymentToken
    );
    event BidPlaced(
        uint256 indexed tokenId,
        address indexed bidder,
        uint256 amount,
        address indexed paymentToken
    );
    event BidCancelled(uint256 indexed tokenId, address indexed bidder);
    event BidAccepted(
        uint256 indexed tokenId,
        address seller,
        address indexed bidder,
        uint256 amount,
        address indexed paymentToken
    );
    event FeesWithdrawn(address indexed recipient, address indexed token, uint256 amount);
    event PlatformFeeChanged(uint256 newPercentage);
    event CreatorRoyaltyChanged(uint256 newPercentage);

    /**
     * @notice Contract constructor.
     * @param _initialOwner The address that will have administrative control.
     * @param _feeRecipient The address that will receive platform fees.
     */
    constructor(address _initialOwner, address _feeRecipient) ERC721("HyperMarket NFT", "HNFT") Ownable(_initialOwner) {
        feeRecipient = _feeRecipient;
        platformFeePercentage = 250; // 2.5%
        creatorRoyaltyPercentage = 500; // 5.0%
    }

    /**
     * @notice Mints a new NFT and assigns its creator for royalty purposes.
     * @dev Only the contract owner can mint new NFTs.
     * @param to The address to mint the NFT to.
     * @param tokenURI The URI for the NFT's metadata.
     * @return The ID of the newly minted token.
     */
    function mintNFT(address to, string memory tokenURI) public onlyOwner returns (uint256) {
        _tokenIdCounter.increment();
        uint256 tokenId = _tokenIdCounter.current();
        _safeMint(to, tokenId);
        _setTokenURI(tokenId, tokenURI);
        tokenCreators[tokenId] = to; // Initial minter is the creator
        return tokenId;
    }

    /**
     * @notice Lists an NFT for sale on the marketplace.
     * @dev The caller must be the owner of the NFT. The contract must be approved to transfer the NFT.
     * @param tokenId The ID of the token to list.
     * @param price The selling price.
     * @param paymentToken The token for payment (address(0) for ETH).
     * @param duration The duration in seconds for which the listing will be active.
     */
    function listNFT(uint256 tokenId, uint256 price, address paymentToken, uint256 duration) public whenNotPaused nonReentrant {
        require(_isApprovedOrOwner(msg.sender, tokenId), "HyperMarket: Caller is not owner or approved");
        require(listings[tokenId].price == 0, "HyperMarket: Token already listed");
        require(price > 0, "HyperMarket: Price must be greater than zero");
        require(duration > 0, "HyperMarket: Duration must be positive");

        // Escrow the NFT by transferring it to the contract
        _transfer(msg.sender, address(this), tokenId);

        listings[tokenId] = Listing({
            seller: msg.sender,
            price: price,
            paymentToken: paymentToken,
            expiresAt: block.timestamp + duration
        });

        emit Listed(tokenId, msg.sender, price, paymentToken, block.timestamp + duration);
    }

    /**
     * @notice Removes an NFT listing from the marketplace.
     * @dev Only the original seller can unlist the NFT.
     * @param tokenId The ID of the token to unlist.
     */
    function unlistNFT(uint256 tokenId) public whenNotPaused nonReentrant {
        Listing storage listing = listings[tokenId];
        require(listing.seller == msg.sender, "HyperMarket: Not the seller");
        require(listing.price > 0, "HyperMarket: Token not listed");

        delete listings[tokenId];
        // Return the NFT from escrow to the seller
        _transfer(address(this), msg.sender, tokenId);

        emit Unlisted(tokenId);
    }

    /**
     * @notice Buys a listed NFT using ETH.
     * @dev The sent ETH value must match the listing price.
     * @param tokenId The ID of the token to buy.
     */
    function buyNFT(uint256 tokenId) public payable whenNotPaused nonReentrant {
        Listing memory listing = listings[tokenId];
        require(listing.price > 0, "HyperMarket: Token not listed");
        require(block.timestamp <= listing.expiresAt, "HyperMarket: Listing expired");
        require(listing.paymentToken == address(0), "HyperMarket: Listing is not for ETH");
        require(msg.value == listing.price, "HyperMarket: Incorrect ETH amount");
        require(listing.seller != msg.sender, "HyperMarket: Buyer cannot be seller");

        address seller = listing.seller;
        delete listings[tokenId];

        _handleSale(tokenId, msg.sender, seller, msg.value, address(0));
    }

    /**
     * @notice Buys a listed NFT using an ERC20 token.
     * @dev The buyer must have approved the marketplace contract to spend the required amount of ERC20 tokens.
     * @param tokenId The ID of the token to buy.
     * @param paymentToken The address of the ERC20 token to use for payment.
     */
    function buyNFTWithERC20(uint256 tokenId, address paymentToken) public whenNotPaused nonReentrant {
        Listing memory listing = listings[tokenId];
        require(listing.price > 0, "HyperMarket: Token not listed");
        require(block.timestamp <= listing.expiresAt, "HyperMarket: Listing expired");
        require(listing.paymentToken == paymentToken, "HyperMarket: Incorrect payment token");
        require(listing.seller != msg.sender, "HyperMarket: Buyer cannot be seller");
        
        address seller = listing.seller;
        uint256 price = listing.price;
        delete listings[tokenId];
        
        // Pull funds from buyer
        IERC20(paymentToken).transferFrom(msg.sender, address(this), price);

        _handleSale(tokenId, msg.sender, seller, price, paymentToken);
    }

    /**
     * @notice Places a bid on a listed NFT.
     * @dev The bidder must approve the contract to spend the bid amount if using an ERC20 token.
     *      ETH bids are not supported in this offer-style system to avoid complex fund management.
     * @param tokenId The ID of the token to bid on.
     * @param amount The bid amount in the specified ERC20 token.
     * @param paymentToken The address of the ERC20 token for the bid.
     */
    function placeBid(uint256 tokenId, uint256 amount, address paymentToken) public whenNotPaused {
        Listing memory listing = listings[tokenId];
        require(listing.price > 0, "HyperMarket: Token not listed");
        require(block.timestamp <= listing.expiresAt, "HyperMarket: Listing expired");
        require(listing.seller != msg.sender, "HyperMarket: Seller cannot bid");
        require(amount > 0, "HyperMarket: Bid amount must be positive");
        require(paymentToken != address(0), "HyperMarket: Only ERC20 bids are supported");
        
        // Check if bidder has sufficient allowance
        uint256 allowance = IERC20(paymentToken).allowance(msg.sender, address(this));
        require(allowance >= amount, "HyperMarket: Insufficient token allowance");

        bids[tokenId][msg.sender] = Bid({
            bidder: msg.sender,
            amount: amount,
            paymentToken: paymentToken
        });

        emit BidPlaced(tokenId, msg.sender, amount, paymentToken);
    }

    /**
     * @notice Cancels a previously placed bid.
     * @dev Only the original bidder can cancel their bid.
     * @param tokenId The ID of the token on which the bid was placed.
     */
    function cancelBid(uint256 tokenId) public whenNotPaused {
        Bid memory bid = bids[tokenId][msg.sender];
        require(bid.bidder == msg.sender, "HyperMarket: No bid from this address");

        delete bids[tokenId][msg.sender];

        emit BidCancelled(tokenId, msg.sender);
    }

    /**
     * @notice Accepts a bid for an NFT.
     * @dev Only the seller of the NFT can accept a bid. This completes the sale.
     * @param tokenId The ID of the token.
     * @param bidder The address of the bidder whose offer is being accepted.
     */
    function acceptBid(uint256 tokenId, address bidder) public whenNotPaused nonReentrant {
        Listing memory listing = listings[tokenId];
        require(listing.seller == msg.sender, "HyperMarket: Not the seller");
        
        Bid memory bid = bids[tokenId][bidder];
        require(bid.bidder == bidder, "HyperMarket: No bid from this address");

        address seller = listing.seller;
        uint256 price = bid.amount;
        address paymentToken = bid.paymentToken;

        delete listings[tokenId];
        // A simple way to clear all bids for this token is to let them expire with the listing.
        // A more robust implementation might iterate and delete them, but that risks high gas costs.

        // Pull funds from bidder
        IERC20(paymentToken).transferFrom(bidder, address(this), price);
        
        _handleSale(tokenId, bidder, seller, price, paymentToken);

        emit BidAccepted(tokenId, seller, bidder, price, paymentToken);
    }

    /**
     * @notice Withdraws accumulated funds (from sales, royalties, or fees) for a specific token.
     * @dev This is a pull-based mechanism for secure fund transfers.
     * @param tokenAddress The address of the token to withdraw (address(0) for ETH).
     */
    function withdrawFunds(address tokenAddress) public nonReentrant {
        uint256 amount = pendingWithdrawals[msg.sender][tokenAddress];
        require(amount > 0, "HyperMarket: No funds to withdraw");
        
        // Checks-Effects-Interactions
        pendingWithdrawals[msg.sender][tokenAddress] = 0;

        if (tokenAddress == address(0)) {
            (bool success, ) = msg.sender.call{value: amount}("");
            require(success, "HyperMarket: ETH transfer failed");
        } else {
            IERC20(tokenAddress).transfer(msg.sender, amount);
        }

        emit FeesWithdrawn(msg.sender, tokenAddress, amount);
    }

    /**
     * @notice [ADMIN] Pauses all marketplace activities.
     */
    function pause() public onlyOwner {
        _pause();
    }

    /**
     * @notice [ADMIN] Resumes all marketplace activities.
     */
    function unpause() public onlyOwner {
        _unpause();
    }

    /**
     * @notice [ADMIN] Sets the platform fee percentage.
     * @param _newFeePercentage The new fee in basis points (e.g., 300 for 3.0%).
     */
    function setFeePercentage(uint256 _newFeePercentage) public onlyOwner {
        require(_newFeePercentage <= 1000, "HyperMarket: Fee cannot exceed 10%"); // Sanity check
        platformFeePercentage = _newFeePercentage;
        emit PlatformFeeChanged(_newFeePercentage);
    }

    /**
     * @notice [ADMIN] Sets the creator royalty percentage.
     * @param _newRoyaltyPercentage The new royalty in basis points (e.g., 750 for 7.5%).
     */
    function setRoyaltyPercentage(uint256 _newRoyaltyPercentage) public onlyOwner {
        require(_newRoyaltyPercentage <= 2000, "HyperMarket: Royalty cannot exceed 20%"); // Sanity check
        creatorRoyaltyPercentage = _newRoyaltyPercentage;
        emit CreatorRoyaltyChanged(_newRoyaltyPercentage);
    }

    /**
     * @notice [ADMIN] Sets the address that receives platform fees.
     * @param _newRecipient The new recipient address.
     */
    function setFeeRecipient(address _newRecipient) public onlyOwner {
        require(_newRecipient != address(0), "HyperMarket: Recipient cannot be zero address");
        feeRecipient = _newRecipient;
    }

    /**
     * @dev Internal function to handle the financial settlement and NFT transfer of a sale.
     * @param tokenId The ID of the token being sold.
     * @param buyer The address of the new owner.
     * @param seller The address of the seller.
     * @param price The total sale price.
     * @param paymentToken The token used for the sale.
     */
    function _handleSale(uint256 tokenId, address buyer, address seller, uint256 price, address paymentToken) internal {
        address creator = tokenCreators[tokenId];

        uint256 platformFee = (price * platformFeePercentage) / 10000;
        uint256 creatorRoyalty = (price * creatorRoyaltyPercentage) / 10000;
        uint256 sellerProceeds = price - platformFee - creatorRoyalty;
        
        // Credit balances for withdrawal
        pendingWithdrawals[seller][paymentToken] += sellerProceeds;
        if (platformFee > 0) {
            pendingWithdrawals[feeRecipient][paymentToken] += platformFee;
        }
        if (creatorRoyalty > 0 && creator != address(0)) {
            pendingWithdrawals[creator][paymentToken] += creatorRoyalty;
        }
        
        // Transfer NFT from contract (escrow) to buyer
        _transfer(address(this), buyer, tokenId);

        emit Sold(tokenId, seller, buyer, price, paymentToken);
    }

    /**
     * @dev Hook that is called before any token transfer.
     *      Ensures that listed tokens cannot be transferred except by the marketplace logic.
     */
    function _beforeTokenTransfer(address from, address to, uint256 tokenId, uint256 batchSize) internal override(ERC721, ERC721Enumerable) {
        super._beforeTokenTransfer(from, to, tokenId, batchSize);
        
        // Allow transfers initiated by the contract itself (e.g., sales, unlistings)
        if (from == address(this) || to == address(this)) {
            return;
        }
        
        // Disallow transfers of listed tokens by the owner
        require(listings[tokenId].price == 0, "HyperMarket: Token is listed and cannot be transferred");
    }

    /**
     * @dev See {IERC165-supportsInterface}.
     */
    function supportsInterface(bytes4 interfaceId) public view override(ERC721, ERC721Enumerable) returns (bool) {
        return super.supportsInterface(interfaceId);
    }
}