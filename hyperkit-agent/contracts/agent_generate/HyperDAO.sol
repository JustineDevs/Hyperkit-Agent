// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Pausable.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Snapshot.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/**
 * @title HyperDAO (HDAO) Token
 * @author Your Name <your.email@example.com>
 * @notice A production-ready ERC20 token with advanced features including role-based access control,
 * pausable transfers, snapshot capabilities for governance, and token vesting schedules.
 * @dev This contract uses OpenZeppelin's battle-tested libraries for security and standard compliance.
 * It integrates ERC20, Burnable, Pausable, Snapshot, AccessControl, and ReentrancyGuard features.
 * Access roles are:
 *  - DEFAULT_ADMIN_ROLE: Can grant and revoke roles.
 *  - MINTER_ROLE: Can mint new tokens.
 *  - PAUSER_ROLE: Can pause and unpause the token transfers.
 *  - VESTING_ADMIN_ROLE: Can create new vesting schedules.
 */
contract HyperDAO is ERC20, ERC20Burnable, ERC20Pausable, AccessControl, ERC20Snapshot, ReentrancyGuard {

    // --- Roles ---

    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");
    bytes32 public constant VESTING_ADMIN_ROLE = keccak256("VESTING_ADMIN_ROLE");

    // --- Vesting ---

    /**
     * @dev Represents a vesting schedule for a beneficiary.
     * @param beneficiary The address receiving the vested tokens.
     * @param startTimestamp The Unix timestamp when the vesting period begins.
     * @param cliffTimestamp The Unix timestamp until which no tokens can be released.
     * @param durationSeconds The total duration of the vesting period in seconds.
     * @param totalAmount The total number of tokens to be vested.
     * @param releasedAmount The number of tokens that have already been released.
     */
    struct VestingSchedule {
        address beneficiary;
        uint64 startTimestamp;
        uint64 cliffTimestamp;
        uint64 durationSeconds;
        uint256 totalAmount;
        uint256 releasedAmount;
    }

    mapping(bytes32 => VestingSchedule) private _vestingSchedules;
    uint256 private _vestingNonce;

    // --- Errors ---

    error InvalidBeneficiary();
    error InvalidVestingAmount();
    error InvalidVestingDuration();
    error InvalidVestingCliff();
    error VestingScheduleNotFound();
    error CliffNotReached();
    error NoTokensToRelease();
    error InsufficientBalance(uint256 required, uint256 available);

    // --- Events ---

    /**
     * @notice Emitted when a new vesting schedule is created.
     * @param scheduleId The unique identifier for the vesting schedule.
     * @param beneficiary The address of the token recipient.
     * @param totalAmount The total amount of tokens being vested.
     * @param startTimestamp The start time of the vesting period.
     * @param cliffTimestamp The cliff time of the vesting period.
     * @param durationSeconds The duration of the vesting period.
     */
    event VestingScheduleCreated(
        bytes32 indexed scheduleId,
        address indexed beneficiary,
        uint256 totalAmount,
        uint64 startTimestamp,
        uint64 cliffTimestamp,
        uint64 durationSeconds
    );

    /**
     * @notice Emitted when vested tokens are released.
     * @param scheduleId The unique identifier for the vesting schedule.
     * @param beneficiary The address of the token recipient.
     * @param amount The amount of tokens released.
     */
    event VestedTokensReleased(bytes32 indexed scheduleId, address indexed beneficiary, uint256 amount);


    // --- Constructor ---

    /**
     * @notice Sets the token name and symbol, and grants initial roles to the deployer.
     * @dev The deployer receives DEFAULT_ADMIN_ROLE, MINTER_ROLE, PAUSER_ROLE, and VESTING_ADMIN_ROLE.
     */
    constructor() ERC20("HyperDAO", "HDAO") {
        address deployer = msg.sender;
        _grantRole(DEFAULT_ADMIN_ROLE, deployer);
        _grantRole(MINTER_ROLE, deployer);
        _grantRole(PAUSER_ROLE, deployer);
        _grantRole(VESTING_ADMIN_ROLE, deployer);
    }


    // --- Overridden Hooks ---

    /**
     * @dev See {ERC20-_beforeTokenTransfer}.
     * This override combines the hooks from ERC20Pausable and ERC20Snapshot.
     */
    function _beforeTokenTransfer(address from, address to, uint256 amount)
        internal
        override(ERC20, ERC20Pausable, ERC20Snapshot)
    {
        super._beforeTokenTransfer(from, to, amount);
    }

    /**
     * @dev See {ERC20-_afterTokenTransfer}.
     * This override is required by ERC20Snapshot.
     */
    function _afterTokenTransfer(address from, address to, uint256 amount)
        internal
        override(ERC20, ERC20Snapshot)
    {
        super._afterTokenTransfer(from, to, amount);
    }


    // --- Core Functions ---

    /**
     * @notice Pauses all token transfers.
     * @dev Can only be called by an account with the PAUSER_ROLE.
     * Emits a {Paused} event.
     */
    function pause() public virtual {
        _checkRole(PAUSER_ROLE);
        _pause();
    }

    /**
     * @notice Unpauses all token transfers.
     * @dev Can only be called by an account with the PAUSER_ROLE.
     * Emits an {Unpaused} event.
     */
    function unpause() public virtual {
        _checkRole(PAUSER_ROLE);
        _unpause();
    }

    /**
     * @notice Creates `amount` new tokens and assigns them to `to`.
     * @dev Can only be called by an account with the MINTER_ROLE.
     * Emits a {Transfer} event with `from` set to the zero address.
     * @param to The address that will receive the minted tokens.
     * @param amount The number of tokens to mint.
     */
    function mint(address to, uint256 amount) public virtual {
        _checkRole(MINTER_ROLE);
        _mint(to, amount);
    }


    // --- Vesting Functions ---

    /**
     * @notice Creates a new token vesting schedule.
     * @dev Requires the VESTING_ADMIN_ROLE. The caller must have enough tokens to fund the schedule.
     * The tokens are transferred from the caller to this contract to be held in escrow.
     * @param beneficiary The address that will receive the vested tokens.
     * @param startTimestamp The Unix timestamp for the start of the vesting period.
     * @param cliffTimestamp The Unix timestamp for the cliff. Must be >= startTimestamp.
     * @param durationSeconds The total duration of the vesting period in seconds from the start time.
     * @param amount The total amount of tokens to be vested.
     * @return scheduleId The unique ID for the newly created vesting schedule.
     */
    function createVestingSchedule(
        address beneficiary,
        uint64 startTimestamp,
        uint64 cliffTimestamp,
        uint64 durationSeconds,
        uint256 amount
    ) public returns (bytes32) {
        _checkRole(VESTING_ADMIN_ROLE);

        if (beneficiary == address(0)) revert InvalidBeneficiary();
        if (amount == 0) revert InvalidVestingAmount();
        if (durationSeconds == 0) revert InvalidVestingDuration();
        if (cliffTimestamp < startTimestamp) revert InvalidVestingCliff();
        if (balanceOf(msg.sender) < amount) revert InsufficientBalance(amount, balanceOf(msg.sender));

        // Generate a unique schedule ID
        bytes32 scheduleId = keccak256(abi.encodePacked(beneficiary, amount, startTimestamp, _vestingNonce));
        _vestingNonce++;

        // Store the schedule
        _vestingSchedules[scheduleId] = VestingSchedule({
            beneficiary: beneficiary,
            startTimestamp: startTimestamp,
            cliffTimestamp: cliffTimestamp,
            durationSeconds: durationSeconds,
            totalAmount: amount,
            releasedAmount: 0
        });

        // Lock the tokens in the contract
        _transfer(msg.sender, address(this), amount);

        emit VestingScheduleCreated(
            scheduleId,
            beneficiary,
            amount,
            startTimestamp,
            cliffTimestamp,
            durationSeconds
        );

        return scheduleId;
    }

    /**
     * @notice Releases tokens that have vested according to a specific schedule.
     * @dev This function is non-reentrant. It can be called by anyone, but tokens are
     * only sent to the schedule's beneficiary.
     * @param scheduleId The ID of the vesting schedule.
     */
    function releaseVestedTokens(bytes32 scheduleId) public nonReentrant {
        VestingSchedule storage schedule = _vestingSchedules[scheduleId];
        if (schedule.beneficiary == address(0)) revert VestingScheduleNotFound();

        uint256 releasableAmount = _computeReleasableAmount(schedule);
        if (releasableAmount == 0) revert NoTokensToRelease();
        
        // Checks-Effects-Interactions Pattern
        schedule.releasedAmount += releasableAmount;

        _transfer(address(this), schedule.beneficiary, releasableAmount);

        emit VestedTokensReleased(scheduleId, schedule.beneficiary, releasableAmount);
    }

    /**
     * @notice Calculates the amount of tokens that can be released for a given schedule at the current time.
     * @param scheduleId The ID of the vesting schedule.
     * @return The amount of tokens that are vested and can be released now.
     */
    function getReleasableAmount(bytes32 scheduleId) public view returns (uint256) {
        VestingSchedule storage schedule = _vestingSchedules[scheduleId];
        if (schedule.beneficiary == address(0)) return 0;

        return _computeReleasableAmount(schedule);
    }

    /**
     * @notice Retrieves the details of a specific vesting schedule.
     * @param scheduleId The ID of the vesting schedule.
     * @return The VestingSchedule struct associated with the ID.
     */
    function getVestingSchedule(bytes32 scheduleId) public view returns (VestingSchedule memory) {
        VestingSchedule storage schedule = _vestingSchedules[scheduleId];
        if (schedule.beneficiary == address(0)) revert VestingScheduleNotFound();
        return schedule;
    }


    // --- Internal Vesting Logic ---

    /**
     * @dev Internal function to compute the releasable amount for a vesting schedule.
     * @param schedule The vesting schedule to compute the releasable amount for.
     * @return The amount of tokens available for release.
     */
    function _computeReleasableAmount(VestingSchedule storage schedule) private view returns (uint256) {
        if (block.timestamp < schedule.cliffTimestamp) {
            return 0;
        }

        uint256 vestedAmount;
        if (block.timestamp >= schedule.startTimestamp + schedule.durationSeconds) {
            vestedAmount = schedule.totalAmount;
        } else {
            // Linear vesting calculation
            uint256 timeElapsed = block.timestamp - schedule.startTimestamp;
            vestedAmount = (schedule.totalAmount * timeElapsed) / schedule.durationSeconds;
        }

        return vestedAmount - schedule.releasedAmount;
    }
}