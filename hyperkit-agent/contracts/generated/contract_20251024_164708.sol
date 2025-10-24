// SPDX-License-Identifier: MIT
pragma solidity ^0.8.18;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";

/**
 * @title FUTUREToken
 * @dev The ERC20 token being sold in the HyperIDO presale.
 * The HyperIDO contract will deploy this token and be its initial owner.
 */
contract FUTUREToken is ERC20, Ownable {
    constructor() ERC20("FUTURE", "FUT") {}

    /**
     * @dev Creates a new supply of tokens and assigns them to an account.
     * Can only be called by the owner.
     * @param to The address that will receive the minted tokens.
     * @param amount The amount of tokens to mint.
     */
    function mint(address to, uint256 amount) public onlyOwner {
        _mint(to, amount);
    }
}


/**
 * @title HyperIDO
 * @dev A smart contract for conducting a presale (Initial DEX Offering) for the FUTURE token.
 * It handles contributions in ETH, manages a soft and hard cap, and includes a vesting schedule for the tokens.
 * Features include whitelisting, refunds for failed sales, and secure fund withdrawal.
 */
contract HyperIDO is Ownable, ReentrancyGuard {
    using SafeMath for uint256;

    //- Events -//

    /**
     * @dev Emitted when a user contributes ETH to the presale.
     * @param contributor The address of the contributor.
     * @param ethAmount The amount of ETH contributed.
     * @param tokenAmount The amount of FUTURE tokens purchased.
     */
    event Contributed(address indexed contributor, uint256 ethAmount, uint256 tokenAmount);

    /**
     * @dev Emitted when a user claims their FUTURE tokens.
     * @param beneficiary The address of the user claiming tokens.
     * @param tokenAmount The amount of FUTURE tokens claimed.
     */
    event Claimed(address indexed beneficiary, uint256 tokenAmount);

    /**
     * @dev Emitted when a user receives a refund after a failed presale.
     * @param contributor The address of the contributor receiving the refund.
     * @param ethAmount The amount of ETH refunded.
     */
    event Refunded(address indexed contributor, uint256 ethAmount);

    /**
     * @dev Emitted when the presale is finalized (either successful or failed).
     * @param totalRaised The total amount of ETH raised.
     * @param success True if the soft cap was reached, false otherwise.
     */
    event PresaleFinalized(uint256 totalRaised, bool success);


    //- Custom Errors -//
    error PresaleNotOpen();
    error PresaleHasEnded();
    error NotWhitelisted();
    error ContributionTooSmall();
    error UserCapExceeded();
    error HardCapExceeded();
    error PresaleNotFinalized();
    error PresaleNotSuccessful();
    error PresaleDidNotFail();
    error NothingToClaim();
    error NothingToRefund();
    error NoFundsToWithdraw();
    error AlreadyFinalized();
    error TokenOwnershipAlreadyTransferred();


    //- State Variables -//

    /// @notice The ERC20 token being sold in this presale.
    FUTUREToken public immutable idoToken;

    // --- Presale Configuration ---
    /// @notice The number of FUTURE tokens per 1 ETH.
    uint256 public constant RATE = 10000;
    /// @notice The minimum contribution amount in ETH.
    uint256 public constant MIN_PURCHASE = 0.1 ether;
    /// @notice The maximum total contribution per wallet in ETH.
    uint256 public constant MAX_PURCHASE_PER_WALLET = 10 ether;
    /// @notice The minimum amount of ETH to be raised for the presale to be successful.
    uint256 public constant SOFT_CAP = 50 ether;
    /// @notice The maximum amount of ETH that can be raised.
    uint256 public constant HARD_CAP = 500 ether;

    // --- Timing ---
    /// @notice The timestamp when the presale starts.
    uint256 public immutable startTime;
    /// @notice The timestamp when the presale ends.
    uint256 public immutable endTime;
    /// @notice The duration of the presale (30 days).
    uint256 public constant PRESALE_DURATION = 30 days;

    // --- Vesting Configuration ---
    /// @notice The percentage of tokens released at the Token Generation Event (TGE).
    uint256 public constant TGE_PERCENT = 20; // 20%
    /// @notice The duration of the linear vesting period (6 months).
    uint256 public constant VESTING_DURATION = 6 * 30 days;

    // --- State Tracking ---
    /// @notice The total amount of ETH raised so far.
    uint256 public totalEthRaised;
    /// @notice Mapping from contributor address to their total ETH contribution.
    mapping(address => uint256) public contributions;
    /// @notice Mapping from user address to the amount of tokens they have claimed.
    mapping(address => uint256) public claimedTokens;
    /// @notice Mapping for whitelisted contributor addresses.
    mapping(address => bool) public whitelist;
    /// @notice Flag to indicate if the presale has been finalized.
    bool private isFinalized;
    /// @notice Flag to indicate if token ownership has been transferred.
    bool private tokenOwnershipTransferred;


    //- Constructor -//
    constructor() {
        idoToken = new FUTUREToken();
        startTime = block.timestamp;
        endTime = block.timestamp + PRESALE_DURATION;

        // Mint the total possible supply for the hard cap to this contract
        uint256 maxTokenSupply = HARD_CAP * RATE;
        idoToken.mint(address(this), maxTokenSupply);

        // Make this presale contract the owner of the token contract
        // to control minting and future administrative actions.
        idoToken.transferOwnership(address(this));
    }


    //- Whitelist Management -//

    /**
     * @dev Adds a list of addresses to the whitelist.
     * @param _addresses The addresses to add.
     */
    function addToWhitelist(address[] calldata _addresses) external onlyOwner {
        for (uint256 i = 0; i < _addresses.length; i++) {
            whitelist[_addresses[i]] = true;
        }
    }

    /**
     * @dev Removes a list of addresses from the whitelist.
     * @param _addresses The addresses to remove.
     */
    function removeFromWhitelist(address[] calldata _addresses) external onlyOwner {
        for (uint256 i = 0; i < _addresses.length; i++) {
            whitelist[_addresses[i]] = false;
        }
    }


    //- Core Functions -//

    /**
     * @dev Accepts ETH contributions from whitelisted users during the presale period.
     */
    function acceptContributions() external payable nonReentrant {
        if (block.timestamp < startTime || block.timestamp > endTime) revert PresaleNotOpen();
        if (!whitelist[msg.sender]) revert NotWhitelisted();
        if (msg.value < MIN_PURCHASE) revert ContributionTooSmall();

        uint256 newTotalContribution = contributions[msg.sender] + msg.value;
        if (newTotalContribution > MAX_PURCHASE_PER_WALLET) revert UserCapExceeded();

        uint256 newTotalRaised = totalEthRaised + msg.value;
        if (newTotalRaised > HARD_CAP) revert HardCapExceeded();

        // Effects
        contributions[msg.sender] = newTotalContribution;
        totalEthRaised = newTotalRaised;

        // Interactions
        uint256 tokenAmount = msg.value * RATE;
        emit Contributed(msg.sender, msg.value, tokenAmount);
    }

    /**
     * @dev Allows users to claim their purchased tokens according to the vesting schedule.
     * Can only be called after the presale has ended successfully.
     */
    function claimTokens() external nonReentrant {
        if (block.timestamp <= endTime) revert PresaleNotFinalized();
        if (totalEthRaised < SOFT_CAP) revert PresaleNotSuccessful();

        uint256 totalTokensOwed = contributions[msg.sender].mul(RATE);
        if (totalTokensOwed == 0) revert NothingToClaim();

        uint256 claimableAmount = _calculateClaimableTokens(msg.sender, totalTokensOwed);
        uint256 alreadyClaimed = claimedTokens[msg.sender];

        uint256 tokensToClaim = claimableAmount - alreadyClaimed;
        if (tokensToClaim == 0) revert NothingToClaim();

        // Effects
        claimedTokens[msg.sender] = alreadyClaimed.add(tokensToClaim);

        // Interactions
        idoToken.transfer(msg.sender, tokensToClaim);
        emit Claimed(msg.sender, tokensToClaim);
    }

    /**
     * @dev Allows users to get a refund if the soft cap was not met.
     * Can only be called after the presale period has ended.
     */
    function refund() external nonReentrant {
        if (block.timestamp <= endTime) revert PresaleNotFinalized();
        if (totalEthRaised >= SOFT_CAP) revert PresaleDidNotFail();

        uint256 refundAmount = contributions[msg.sender];
        if (refundAmount == 0) revert NothingToRefund();

        // Effects
        contributions[msg.sender] = 0;

        // Interactions
        (bool success, ) = msg.sender.call{value: refundAmount}("");
        require(success, "Refund transfer failed");
        emit Refunded(msg.sender, refundAmount);
    }


    //- Admin Functions -//

    /**
     * @dev Allows the owner to withdraw the raised ETH if the presale was successful.
     */
    function emergencyWithdraw() external onlyOwner nonReentrant {
        if (block.timestamp <= endTime) revert PresaleNotFinalized();
        if (totalEthRaised < SOFT_CAP) revert PresaleNotSuccessful();
        
        uint256 balance = address(this).balance;
        if (balance == 0) revert NoFundsToWithdraw();
        
        (bool success, ) = owner().call{value: balance}("");
        require(success, "Withdrawal failed");
    }

    /**
     * @dev Finalizes the presale after it ends. If successful, burns unsold tokens.
     * If failed, allows the owner to reclaim all minted IDO tokens.
     * This is a one-time function that can only be called by the owner.
     */
    function finalizePresale() external onlyOwner {
        if (block.timestamp <= endTime) revert PresaleNotFinalized();
        if (isFinalized) revert AlreadyFinalized();

        isFinalized = true;

        if (totalEthRaised >= SOFT_CAP) {
            uint256 tokensSold = totalEthRaised * RATE;
            uint256 totalTokensMinted = HARD_CAP * RATE;
            uint256 unsoldTokens = totalTokensMinted - tokensSold;

            if (unsoldTokens > 0) {
                // Transfer unsold tokens to a dead address as a burn mechanism
                idoToken.transfer(address(0x000000000000000000000000000000000000dEaD), unsoldTokens);
            }
            emit PresaleFinalized(totalEthRaised, true);
        } else {
            // If the sale fails, the owner can reclaim all the minted FUTURE tokens.
            uint256 totalTokensMinted = HARD_CAP * RATE;
            if (totalTokensMinted > 0) {
                idoToken.transfer(owner(), totalTokensMinted);
            }
            emit PresaleFinalized(totalEthRaised, false);
        }
    }
    
    /**
     * @dev Transfers the ownership of the created FUTURE token to a new owner.
     * This should be done after the presale is completely over.
     * This is a critical step for decentralizing the token's control away from the IDO contract.
     * Can only be called once.
     */
    function transferTokenOwnership(address newOwner) external onlyOwner {
        if (tokenOwnershipTransferred) revert TokenOwnershipAlreadyTransferred();
        if(newOwner == address(0)) revert Ownable__NewOwnerIsZeroAddress();
        tokenOwnershipTransferred = true;
        idoToken.transferOwnership(newOwner);
    }


    //- View/Pure Functions -//

    /**
     * @dev Calculates the amount of tokens a user can claim at the current time.
     * @param _user The address of the user.
     * @return The number of tokens the user is eligible to claim now.
     */
    function getClaimableAmount(address _user) external view returns (uint256) {
        if (block.timestamp <= endTime || totalEthRaised < SOFT_CAP) {
            return 0;
        }
        uint256 totalTokensOwed = contributions[_user].mul(RATE);
        if (totalTokensOwed == 0) {
            return 0;
        }
        
        uint256 claimable = _calculateClaimableTokens(_user, totalTokensOwed);
        uint256 alreadyClaimed = claimedTokens[_user];
        
        return claimable > alreadyClaimed ? claimable - alreadyClaimed : 0;
    }

    /**
     * @dev Internal function to calculate total claimable tokens based on vesting schedule.
     * @param _user The user's address.
     * @param _totalTokensOwed The total amount of tokens purchased by the user.
     * @return The cumulative amount of tokens that should have been released by now.
     */
    function _calculateClaimableTokens(address _user, uint256 _totalTokensOwed) internal view returns (uint256) {
        // Suppress unused variable warning
        _user;

        uint256 vestingStartTime = endTime;
        
        // Before vesting starts, only TGE is claimable
        if (block.timestamp <= vestingStartTime) {
            return _totalTokensOwed.mul(TGE_PERCENT).div(100);
        }

        // After vesting period ends, all tokens are claimable
        uint256 vestingEndTime = vestingStartTime + VESTING_DURATION;
        if (block.timestamp >= vestingEndTime) {
            return _totalTokensOwed;
        }

        // During the vesting period
        uint256 tgeAmount = _totalTokensOwed.mul(TGE_PERCENT).div(100);
        uint256 vestingTokens = _totalTokensOwed - tgeAmount;
        uint256 timeElapsed = block.timestamp - vestingStartTime;
        uint256 vestedAmount = vestingTokens.mul(timeElapsed).div(VESTING_DURATION);

        return tgeAmount + vestedAmount;
    }
}