// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Capped.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";

/**
 * @title GameToken
 * @author Expert Solidity Developer
 * @notice A secure and feature-rich ERC20 token for gaming applications.
 * @dev This contract implements a fungible token with role-based access control,
 * a maximum supply cap, minting/burning capabilities, and an emergency pause mechanism.
 * It is built using OpenZeppelin's battle-tested libraries to ensure security and
 * adherence to standards.
 */
contract GameToken is ERC20, ERC20Burnable, ERC20Capped, AccessControl, Pausable {
    /**
     * @dev Role identifier for addresses that are allowed to mint new tokens.
     */
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    
    /**
     * @dev Role identifier for addresses that are allowed to pause and unpause token transfers.
     */
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");

    /**
     * @dev Sets up the token with a name, symbol, initial supply, max supply, and admin.
     * The `initialAdmin` will be granted the DEFAULT_ADMIN_ROLE, MINTER_ROLE, and PAUSER_ROLE.
     *
     * @param name The name of the token (e.g., "Game Gold").
     * @param symbol The symbol of the token (e.g., "GG").
     * @param initialSupply The amount of tokens to mint to the admin upon deployment.
     * @param maxSupply The maximum total supply (cap) for the token.
     * @param initialAdmin The address that will be granted all administrative roles.
     */
    constructor(
        string memory name,
        string memory symbol,
        uint256 initialSupply,
        uint256 maxSupply,
        address initialAdmin
    ) ERC20(name, symbol) ERC20Capped(maxSupply) {
        require(initialAdmin != address(0), "GameToken: initial admin is the zero address");
        require(initialSupply <= maxSupply, "GameToken: initial supply exceeds max supply");

        // Grant the deployer the default admin role, which allows them to grant and revoke roles.
        _grantRole(DEFAULT_ADMIN_ROLE, initialAdmin);
        // Grant the minter and pauser roles to the initial admin.
        _grantRole(MINTER_ROLE, initialAdmin);
        _grantRole(PAUSER_ROLE, initialAdmin);

        if (initialSupply > 0) {
            _mint(initialAdmin, initialSupply);
        }
    }

    /**
     * @notice Pauses all token transfers.
     * @dev Can only be called by an account with the PAUSER_ROLE.
     * Emits a {Paused} event.
     */
    function pause() external onlyRole(PAUSER_ROLE) {
        _pause();
    }

    /**
     * @notice Unpauses all token transfers.
     * @dev Can only be called by an account with the PAUSER_ROLE.
     * Emits an {Unpaused} event.
     */
    function unpause() external onlyRole(PAUSER_ROLE) {
        _unpause();
    }

    /**
     * @notice Creates `amount` new tokens and assigns them to `to`.
     * @dev Can only be called by an account with the MINTER_ROLE.
     * Emits a {Transfer} event with `from` set to the zero address.
     * Requirements:
     * - `to` cannot be the zero address.
     * - The total supply must not exceed the cap.
     * @param to The address that will receive the minted tokens.
     * @param amount The amount of tokens to mint.
     */
    function mint(address to, uint256 amount) external onlyRole(MINTER_ROLE) {
        _mint(to, amount);
    }

    /**
     * @dev Overrides the internal `_update` function to apply pausing and capping logic.
     * This function is called before all token transfers, including minting and burning.
     * The `whenNotPaused` modifier from `Pausable` prevents transfers when the contract is paused.
     * The logic from `ERC20Capped` is included by calling `super._update`.
     */
    function _update(address from, address to, uint256 value) internal override(ERC20, ERC20Capped) whenNotPaused {
        super._update(from, to, value);
    }
}