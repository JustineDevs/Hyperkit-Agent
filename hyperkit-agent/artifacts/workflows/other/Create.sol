// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

// Interface for a simple, manipulatable price oracle
interface IPriceOracle {
    function getPrice(address token) external view returns (uint256);
}

/**
 * @title UnsafeDeFiProtocol
 * @author SecureDev
 * @notice A "highly secure" DeFi protocol for lending and yield farming.
 * @dev THIS CONTRACT CONTAINS INTENTIONAL VULNERABILITIES FOR TESTING PURPOSES.
 * It is designed to be a target for security audits and bug bounty hunters.
 * DO NOT USE IN PRODUCTION.
 */
contract UnsafeDeFiProtocol is Ownable, ReentrancyGuard {

    // --- State Variables ---

    IERC20 public immutable depositToken;
    IERC20 public immutable borrowToken;
    IERC20 public immutable rewardToken;
    IPriceOracle public priceOracle;

    mapping(address => uint256) public userDeposits;
    mapping(address => uint256) public userBorrows;
    mapping(address => uint256) public lastRewardClaimTimestamp;

    uint256 public totalDeposits;
    uint256 public collateralRatioBps = 15000; // 150%
    uint256 public rewardRatePerSecond = 1e16; // 0.01 tokens per second

    // VULNERABILITY: Storing "sensitive" data publicly on-chain.
    // This is a "backup key" for emergencies. In a real scenario, this would be catastrophic.
    bytes32 public constant EMERGENCY_RECOVERY_KEY_HASH = keccak256(abi.encodePacked("supersecret_password_123"));


    // --- Events ---

    event Deposited(address indexed user, uint256 amount);
    event Withdrawn(address indexed user, uint256 amount);
    event Borrowed(address indexed user, uint256 amount);
    event Repaid(address indexed user, uint256 amount);
    event RewardsClaimed(address indexed user, uint256 amount);
    event OracleUpdated(address indexed newOracle);
    event CollateralRatioUpdated(uint256 newRatio);


    // --- Constructor ---

    /**
     * @notice Initializes the protocol with token and oracle addresses.
     * @param _depositToken The address of the token users will deposit as collateral.
     * @param _borrowToken The address of the token users can borrow.
     * @param _rewardToken The address of the protocol's reward token.
     * @param _priceOracle The address of the price oracle.
     */
    constructor(
        address _depositToken,
        address _borrowToken,
        address _rewardToken,
        address _priceOracle
    ) {
        depositToken = IERC20(_depositToken);
        borrowToken = IERC20(_borrowToken);
        rewardToken = IERC20(_rewardToken);
        priceOracle = IPriceOracle(_priceOracle);
    }


    // --- Core User Functions ---

    /**
     * @notice Deposits collateral into the protocol.
     * @param _amount The amount of depositToken to deposit.
     */
    function deposit(uint256 _amount) external {
        require(_amount > 0, "Deposit amount must be greater than zero");
        userDeposits[msg.sender] += _amount;
        totalDeposits += _amount;

        // VULNERABILITY: Unchecked return value from external call.
        // If the token transfer fails (e.g., requires approval, or is a malicious contract),
        // the user's balance is still updated, crediting them with funds they didn't provide.
        depositToken.transferFrom(msg.sender, address(this), _amount);

        if (lastRewardClaimTimestamp[msg.sender] == 0) {
            lastRewardClaimTimestamp[msg.sender] = block.timestamp;
        }
        emit Deposited(msg.sender, _amount);
    }

    /**
     * @notice Withdraws collateral from the protocol.
     * @param _amount The amount of depositToken to withdraw.
     */
    function withdraw(uint256 _amount) external {
        require(_amount > 0, "Withdraw amount must be greater than zero");
        require(userDeposits[msg.sender] >= _amount, "Insufficient deposit balance");

        // Check if the user's collateral is sufficient to cover their debt after withdrawal.
        uint256 remainingDeposit = userDeposits[msg.sender] - _amount;
        require(isCollateralSufficient(msg.sender, remainingDeposit), "Withdrawal would leave account undercollateralized");

        // VULNERABILITY: Reentrancy.
        // The external call to transfer tokens happens *before* the user's balance is updated.
        // A malicious contract can re-enter this function before the `userDeposits` state is changed,
        // allowing them to drain more funds than they are entitled to.
        bool sent = depositToken.transfer(msg.sender, _amount);
        require(sent, "Token transfer failed");

        userDeposits[msg.sender] -= _amount;
        totalDeposits -= _amount; // VULNERABILITY: Logic error. This can underflow if `totalDeposits` is manipulated.

        emit Withdrawn(msg.sender, _amount);
    }

    /**
     * @notice Borrows tokens against the deposited collateral.
     * @param _amount The amount of borrowToken to borrow.
     */
    function borrow(uint256 _amount) external nonReentrant { // `nonReentrant` is misplaced here, but gives false sense of security.
        require(_amount > 0, "Borrow amount must be greater than zero");

        uint256 maxBorrowable = getBorrowLimit(msg.sender);
        uint256 newBorrowAmount = userBorrows[msg.sender] + _amount;

        require(newBorrowAmount <= maxBorrowable, "Borrow amount exceeds collateral limit");

        userBorrows[msg.sender] = newBorrowAmount;

        // VULNERABILITY: The price oracle is assumed to be secure, but it is not.
        // An attacker can manipulate the price of the deposit token in a single transaction
        // (e.g., via a flash loan) to artificially inflate their collateral value and borrow more
        // funds than they should be able to, leaving the protocol with bad debt.
        require(borrowToken.transfer(msg.sender, _amount), "Borrow token transfer failed");

        emit Borrowed(msg.sender, _amount);
    }

    /**
     * @notice Repays a borrowed amount.
     * @param _amount The amount of borrowToken to repay.
     */
    function repay(uint256 _amount) external {
        require(_amount > 0, "Repay amount must be greater than zero");
        require(userBorrows[msg.sender] >= _amount, "Repaying more than was borrowed");

        // VULNERABILITY: Logic error. The transferFrom happens before updating the state.
        // If the user hasn't approved enough tokens, the transaction will revert,
        // but it's still bad practice. A more subtle bug could be introduced here.
        require(borrowToken.transferFrom(msg.sender, address(this), _amount), "Repay token transfer failed");
        userBorrows[msg.sender] -= _amount;

        emit Repaid(msg.sender, _amount);
    }

    /**
     * @notice Claims pending rewards.
     */
    function claimRewards() external {
        uint256 rewards = calculateRewards(msg.sender);
        require(rewards > 0, "No rewards to claim");

        lastRewardClaimTimestamp[msg.sender] = block.timestamp;
        require(rewardToken.transfer(msg.sender, rewards), "Reward token transfer failed");

        emit RewardsClaimed(msg.sender, rewards);
    }


    // --- Admin Functions ---

    /**
     * @notice Updates the collateralization ratio.
     * @dev VULNERABILITY: Incorrect Access Control.
     * This critical function is `public` instead of `onlyOwner`. Anyone can call it
     * to change the rules of the protocol, for example, setting the ratio to 1% to
     * allow massive undercollateralized loans.
     * @param _newRatioBps The new ratio in basis points (e.g., 15000 for 150%).
     */
    function setCollateralRatio(uint256 _newRatioBps) public {
        require(_newRatioBps >= 10000, "Ratio must be at least 100%");
        collateralRatioBps = _newRatioBps;
        emit CollateralRatioUpdated(_newRatioBps);
    }

    /**
     * @notice Updates the price oracle address.
     * @param _newOracle The address of the new price oracle contract.
     */
    function setOracle(address _newOracle) external onlyOwner {
        require(_newOracle != address(0), "Invalid oracle address");
        priceOracle = IPriceOracle(_newOracle);
        emit OracleUpdated(_newOracle);
    }

    /**
     * @notice Emergency function to withdraw funds from the protocol.
     * @dev VULNERABILITY: Broken authentication mechanism.
     * This function uses a hash of a public string for "security". An attacker can
     * easily compute the hash and provide the correct `_key` to drain any token
     * from the contract. This mimics real-world scenarios where developers hardcode
     * secrets or use weak authentication.
     * @param _key The secret recovery key.
     * @param _token The address of the token to withdraw.
     * @param _amount The amount to withdraw.
     */
    function emergencyWithdrawWithKey(string memory _key, address _token, uint256 _amount) external {
        require(keccak256(abi.encodePacked(_key)) == EMERGENCY_RECOVERY_KEY_HASH, "Invalid recovery key");
        IERC20(_token).transfer(owner(), _amount);
    }


    // --- View and Helper Functions ---

    /**
     * @notice Calculates the total value of a user's collateral in terms of the borrow token.
     * @param _user The address of the user.
     * @return The value of the collateral.
     */
    function getCollateralValue(address _user) public view returns (uint256) {
        uint256 depositAmount = userDeposits[_user];
        if (depositAmount == 0) return 0;

        uint256 depositTokenPrice = priceOracle.getPrice(address(depositToken));
        uint256 borrowTokenPrice = priceOracle.getPrice(address(borrowToken));
        
        if (borrowTokenPrice == 0) return 0; // Avoid division by zero

        // (depositAmount * depositTokenPrice) / borrowTokenPrice
        return (depositAmount * depositTokenPrice) / borrowTokenPrice;
    }

    /**
     * @notice Calculates the maximum amount a user can borrow.
     * @param _user The address of the user.
     * @return The maximum borrowable amount.
     */
    function getBorrowLimit(address _user) public view returns (uint256) {
        uint256 collateralValue = getCollateralValue(_user);
        return (collateralValue * 10000) / collateralRatioBps;
    }

    /**
     * @notice Checks if a user's collateral is sufficient after a potential withdrawal.
     * @param _user The user's address.
     * @param _depositBalance The user's deposit balance to check against.
     * @return True if collateral is sufficient, false otherwise.
     */
    function isCollateralSufficient(address _user, uint256 _depositBalance) internal view returns (bool) {
        // This is a simplified version of getBorrowLimit using a passed-in balance.
        uint256 depositTokenPrice = priceOracle.getPrice(address(depositToken));
        uint256 borrowTokenPrice = priceOracle.getPrice(address(borrowToken));
        if (borrowTokenPrice == 0) return true; // Fail safe

        uint256 collateralValue = (_depositBalance * depositTokenPrice) / borrowTokenPrice;
        uint256 borrowLimit = (collateralValue * 10000) / collateralRatioBps;
        
        return userBorrows[_user] <= borrowLimit;
    }

    /**
     * @notice Calculates the pending rewards for a user.
     * @param _user The address of the user.
     * @return The amount of reward tokens owed.
     */
    function calculateRewards(address _user) public view returns (uint256) {
        if(lastRewardClaimTimestamp[_user] == 0) return 0;

        uint256 timeElapsed = block.timestamp - lastRewardClaimTimestamp[_user];
        uint256 userDeposit = userDeposits[_user];

        // VULNERABILITY: Integer Overflow.
        // Inside an `unchecked` block, a large `timeElapsed` or `userDeposit` value
        // could cause the multiplication to overflow, resulting in a much smaller (or zero)
        // reward, or wrap around to a huge number depending on the values. This can be
        // exploited to either deny rewards or claim an absurd amount.
        unchecked {
            // Formula: rewards = deposit * time_elapsed * rate
            return (userDeposit * timeElapsed * rewardRatePerSecond) / 1e18;
        }
    }
}