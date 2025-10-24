// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Snapshot.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/**
 * @title GamingEcosystemToken
 * @author Your Name/Company
 * @notice An advanced ERC20 token for a gaming ecosystem, featuring role-based access control,
 * pausable transfers, burnable tokens, and snapshot capabilities for governance.
 * @dev This contract integrates multiple OpenZeppelin modules to provide a secure and
 * feature-rich token.
 * - AccessControl: For managing roles like minters, pausers, and admins.
 * - Pausable: To halt token transfers in case of an emergency.
 * - ERC20Burnable: To allow users to burn their own tokens.
 * - ERC20Snapshot: To enable governance mechanisms by recording token balances at specific times.
 * - ReentrancyGuard: To protect against reentrancy attacks on sensitive functions.
 */
contract GamingEcosystemToken is ERC20, ERC20Burnable, ERC20Snapshot, AccessControl, Pausable, ReentrancyGuard {
    // --- Roles ---
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");
    bytes32 public constant SNAPSHOT_ROLE = keccak256("SNAPSHOT_ROLE");
    // DEFAULT_ADMIN_ROLE is inherited from AccessControl

    // --- Custom Errors ---
    error GamingEcosystemToken__MustHaveMinterRole();
    error GamingEcosystemToken__MustHavePauserRole();
    error GamingEcosystemToken__MustHaveSnapshotRole();
    error GamingEcosystemToken__ContractIsPaused();

    /**
     * @notice Constructor to deploy the GamingEcosystemToken.
     * @param name The name of the token.
     * @param symbol The symbol of the token.
     * @param initialAdmin The address that will be granted the initial admin, minter, pauser, and snapshot roles.
     */
    constructor(
        string memory name,
        string memory symbol,
        address initialAdmin
    ) ERC20(name, symbol) {
        if (initialAdmin == address(0)) {
            revert("GamingEcosystemToken: initial admin cannot be the zero address");
        }
        _grantRole(DEFAULT_ADMIN_ROLE, initialAdmin);
        _grantRole(MINTER_ROLE, initialAdmin);
        _grantRole(PAUSER_ROLE, initialAdmin);
        _grantRole(SNAPSHOT_ROLE, initialAdmin);
    }

    /**
     * @notice Creates a new snapshot and returns its id.
     * @dev The snapshot mechanism is useful for governance, allowing for voting based on
     * token balances at a specific block. Can only be called by an account with the SNAPSHOT_ROLE.
     * @return The id of the new snapshot.
     */
    function snapshot() public nonReentrant returns (uint256) {
        if (!hasRole(SNAPSHOT_ROLE, _msgSender())) {
            revert GamingEcosystemToken__MustHaveSnapshotRole();
        }
        return _snapshot();
    }

    /**
     * @notice Pauses all token transfers.
     * @dev This is an emergency stop mechanism. Can only be called by an account with the PAUSER_ROLE.
     * Emits a {Paused} event.
     */
    function pause() public {
        if (!hasRole(PAUSER_ROLE, _msgSender())) {
            revert GamingEcosystemToken__MustHavePauserRole();
        }
        _pause();
    }

    /**
     * @notice Unpauses all token transfers.
     * @dev Resumes normal token operations after a pause. Can only be called by an account with the PAUSER_ROLE.
     * Emits an {Unpaused} event.
     */
    function unpause() public {
        if (!hasRole(PAUSER_ROLE, _msgSender())) {
            revert GamingEcosystemToken__MustHavePauserRole();
        }
        _unpause();
    }

    /**
     * @notice Creates `amount` new tokens and assigns them to `to`.
     * @dev This function is used to increase the total supply of the token. Can only be
     * called by an account with the MINTER_ROLE.
     * Emits a {Transfer} event with `from` set to the zero address.
     * @param to The address that will receive the minted tokens.
     * @param amount The amount of tokens to mint.
     */
    function mint(address to, uint256 amount) public nonReentrant {
        if (!hasRole(MINTER_ROLE, _msgSender())) {
            revert GamingEcosystemToken__MustHaveMinterRole();
        }
        _mint(to, amount);
    }

    /**
     * @dev Overridden hook that is called before any token transfer, including minting and burning.
     * It ensures that transfers cannot occur while the contract is paused.
     * It also calls the super function to handle snapshot updates.
     */
    function _beforeTokenTransfer(address from, address to, uint256 amount)
        internal
        override(ERC20, ERC20Snapshot)
    {
        if (paused()) {
            revert GamingEcosystemToken__ContractIsPaused();
        }
        super._beforeTokenTransfer(from, to, amount);
    }
}