// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/**
 * @title FutureToken
 * @dev A simple ERC20 token that can be minted only by its owner.
 * For this presale, the owner will be the HyperIDO contract.
 */
contract FutureToken is ERC20, Ownable {
    /**
     * @dev Sets the initial owner of the token contract.
     * @param initialOwner The address to be set as the initial owner.
     */
    constructor(address initialOwner) ERC20("FUTURE", "FUT") Ownable(initialOwner) {}

    /**
     * @dev Creates `amount` tokens and assigns them to `to`, increasing the total supply.
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
 * @author Your Name
 * @dev A smart contract for a presale (IDO) of the FUTURE token.
 * It handles whitelisted contributions, soft/hard caps, refunds, and a linear token vesting schedule.
 * The contract deploys its own ERC20 token upon creation.
 */
contract HyperIDO is Ownable, ReentrancyGuard {
    // --- State Variables ---

    // Token and Presale Configuration
    FutureToken public immutable idoToken;
    uint256 public constant RATE = 10000; // 10,000 FUTURE tokens per 1 ETH
    uint256 public constant MIN_CONTRIBUTION = 0.1 ether;
    uint256 public constant MAX_CONTRIBUTION = 10 ether;
    uint256 public constant SOFT_CAP = 50 ether;
    uint256 public constant HARD_CAP = 500 ether;
    uint256 public constant PRESALE_DURATION = 30 days;

    // Vesting Configuration
    uint256 public constant TGE_PERCENT = 20; // 20% released immediately at TGE
    uint256 public constant VESTING_DURATION = 6 * 30 days; // 80% vests over 6 months

    // Presale Timeline & State
    uint256 public immutable startTime;
    uint256 public immutable endTime;
    uint256 public vestingStartTime;
    uint256 public totalEthRaised;

    /**
     * @dev Represents the current state of the presale.
     * - Active: Contributions are being accepted.
     * - Succeeded: Soft cap reached and finalized. Token claiming is enabled.
     * - Failed: Soft cap not reached and finalized. Refunds are enabled.
     */
    enum PresaleState { Active, Succeeded, Failed }
    PresaleState public presaleState;

    // User Data
    mapping(address => uint256) public contributions;
    mapping(address => uint256) public claimedAmount;
    mapping(address => bool) public isWhitelisted;

    // --- Events ---

    /**
     * @dev Emitted when a user contributes ETH to the presale.
     * @param contributor The address of the contributor.
     * @param ethAmount The amount of ETH contributed in wei.
     * @param tokenAmount The amount of FUTURE tokens purchased.
     */
    event Contributed(address indexed contributor, uint256 ethAmount, uint256 tokenAmount);

    /**
     * @dev Emitted when a user claims their vested tokens.
     * @param beneficiary The address receiving the tokens.
     * @param amount The amount of FUTURE tokens claimed.
     */
    event Claimed(address indexed beneficiary, uint256 amount);

    /**
     * @dev Emitted when a user receives a refund after a failed presale.
     * @param contributor The address receiving the refund.
     * @param amount The amount of ETH refunded in wei.
     */
    event Refunded(address indexed contributor, uint256 amount);

    /**
     * @dev Emitted when the presale is finalized by the owner.
     * @param totalRaised The total amount of ETH raised in wei.
     * @param success Whether the presale was successful (soft cap reached).
     */
    event PresaleFinalized(uint256 totalRaised, bool success);

    // --- Modifiers ---

    /**
     * @dev Modifier to check if the presale is in a specific state.
     * @param _state The required state to execute the function.
     */
    modifier inState(PresaleState _state) {
        require(presaleState == _state, "HyperIDO: Invalid presale state");
        _;
    }

    // --- Constructor ---

    /**
     * @dev Deploys the contract, creates the FUTURE token, and starts the presale.
     * The deployer of this contract becomes the owner.
     * The HyperIDO contract itself becomes the owner of the new FUTURE token contract,
     * allowing it to mint tokens.
     */
    constructor() Ownable(msg.sender) {
        idoToken = new FutureToken(address(this));
        startTime = block.timestamp;
        endTime = block.timestamp + PRESALE_DURATION;
        presaleState = PresaleState.Active;
    }

    // --- Whitelist Management ---

    /**
     * @dev Adds or removes a list of addresses from the whitelist. Only callable by the owner.
     * @param _users The array of addresses to modify.
     * @param _status The whitelist status to set (true for whitelisted, false for removed).
     */
    function setWhitelist(address[] calldata _users, bool _status) external onlyOwner {
        for (uint i = 0; i < _users.length; i++) {
            isWhitelisted[_users[i]] = _status;
        }
    }

    // --- Core Presale Functions ---

    /**
     * @dev Accepts ETH contributions from whitelisted users during the active presale period.
     */
    function contribute() external payable nonReentrant inState(PresaleState.Active) {
        require(block.timestamp <= endTime, "HyperIDO: Presale has ended");
        require(isWhitelisted[msg.sender], "HyperIDO: Not whitelisted");
        
        uint256 amount = msg.value;
        require(amount >= MIN_CONTRIBUTION, "HyperIDO: Amount is below minimum contribution");
        require(contributions[msg.sender] + amount <= MAX_CONTRIBUTION, "HyperIDO: Exceeds maximum contribution per wallet");
        require(totalEthRaised + amount <= HARD_CAP, "HyperIDO: Contribution would exceed hard cap");

        contributions[msg.sender] += amount;
        totalEthRaised += amount;

        emit Contributed(msg.sender, amount, amount * RATE);
    }
    
    /**
     * @dev Fallback function to accept ETH contributions via simple transfers.
     */
    receive() external payable {
        contribute();
    }

    /**
     * @dev Finalizes the presale after it has ended. Only callable by the owner.
     * This function determines if the presale succeeded or failed based on the soft cap
     * and transitions the contract state accordingly.
     */
    function finalizePresale() external onlyOwner {
        require(block.timestamp > endTime, "HyperIDO: Presale not yet ended");
        require(presaleState == PresaleState.Active, "HyperIDO: Presale already finalized");

        bool success = totalEthRaised >= SOFT_CAP;
        if (success) {
            presaleState = PresaleState.Succeeded;
            vestingStartTime = block.timestamp;
            uint256 totalTokensToMint = totalEthRaised * RATE;
            idoToken.mint(address(this), totalTokensToMint);
        } else {
            presaleState = PresaleState.Failed;
        }
        emit PresaleFinalized(totalEthRaised, success);
    }

    // --- Token Claiming and Refunds ---

    /**
     * @dev Allows users to claim their purchased tokens according to the vesting schedule.
     * Can only be called after a successful presale finalization.
     */
    function claimTokens() external nonReentrant inState(PresaleState.Succeeded) {
        uint256 claimableAmount = getReleasableAmount(msg.sender);
        require(claimableAmount > 0, "HyperIDO: No tokens available to claim");

        // Checks-Effects-Interactions Pattern
        claimedAmount[msg.sender] += claimableAmount;
        
        // Interaction
        bool sent = idoToken.transfer(msg.sender, claimableAmount);
        require(sent, "HyperIDO: Token transfer failed");

        emit Claimed(msg.sender, claimableAmount);
    }

    /**
     * @dev Allows users to get a full refund of their contribution if the presale failed.
     */
    function refund() external nonReentrant inState(PresaleState.Failed) {
        uint256 contributionAmount = contributions[msg.sender];
        require(contributionAmount > 0, "HyperIDO: No contribution to refund");

        // Checks-Effects-Interactions Pattern
        contributions[msg.sender] = 0;

        // Interaction
        (bool success, ) = msg.sender.call{value: contributionAmount}("");
        require(success, "HyperIDO: Refund transfer failed");

        emit Refunded(msg.sender, contributionAmount);
    }

    // --- Admin Functions ---

    /**
     * @dev Allows the owner to withdraw all raised ETH if the presale was successful.
     */
    function withdrawFunds() external onlyOwner inState(PresaleState.Succeeded) {
        (bool success, ) = owner().call{value: address(this).balance}("");
        require(success, "HyperIDO: ETH withdrawal failed");
    }

    /**
     * @dev Allows the owner to withdraw any mistakenly sent ERC20 tokens from this contract.
     * This function prevents locking of other assets. It cannot be used to withdraw the IDO token.
     * @param _tokenAddress The address of the ERC20 token to withdraw.
     */
    function emergencyWithdrawTokens(address _tokenAddress) external onlyOwner {
        require(_tokenAddress != address(idoToken), "HyperIDO: Cannot withdraw the IDO token");
        IERC20 token = IERC20(_tokenAddress);
        uint256 balance = token.balanceOf(address(this));
        require(balance > 0, "HyperIDO: No tokens of this type to withdraw");
        
        bool sent = token.transfer(owner(), balance);
        require(sent, "HyperIDO: Token withdrawal failed");
    }

    // --- View Functions ---

    /**
     * @dev Calculates the amount of tokens a user can release at the current time based on the vesting schedule.
     * @param _user The address of the user.
     * @return The amount of claimable tokens.
     */
    function getReleasableAmount(address _user) public view returns (uint256) {
        if (presaleState != PresaleState.Succeeded) {
            return 0;
        }

        uint256 totalTokens = contributions[_user] * RATE;
        if (totalTokens == 0) {
            return 0;
        }

        // Calculate TGE (immediately available) portion
        uint256 tgeAmount = (totalTokens * TGE_PERCENT) / 100;
        
        // Calculate the portion subject to linear vesting
        uint256 vestingPortion = totalTokens - tgeAmount;
        
        uint256 vestedAmount = 0;
        uint256 timeElapsed = block.timestamp > vestingStartTime ? block.timestamp - vestingStartTime : 0;

        if (timeElapsed >= VESTING_DURATION) {
            vestedAmount = vestingPortion; // Full amount vested
        } else {
            // Linear vesting calculation
            vestedAmount = (vestingPortion * timeElapsed) / VESTING_DURATION;
        }

        uint256 totalReleasable = tgeAmount + vestedAmount;
        uint256 alreadyClaimed = claimedAmount[_user];
        
        if (totalReleasable <= alreadyClaimed) {
            return 0;
        }
        
        return totalReleasable - alreadyClaimed;
    }
}