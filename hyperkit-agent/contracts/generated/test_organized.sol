// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Pausable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title SimpleERC20
 * @author Your Name
 * @notice A secure and production-ready ERC20 token contract.
 * @dev This contract implements a basic ERC20 token with additional features:
 * - Minting new tokens (restricted to the owner).
 * - Burning tokens (users can burn their own tokens).
 * - Pausable functionality (owner can pause/unpause all token transfers in emergencies).
 * - Ownership control for administrative functions.
 * It is built using OpenZeppelin's battle-tested contracts to ensure security and
 * adherence to standards.
 */
contract SimpleERC20 is ERC20, ERC20Burnable, ERC20Pausable, Ownable {

    /**
     * @notice Constructor to initialize the ERC20 token, its owner, name, and symbol.
     * @param name The name of the token (e.g., "MyToken").
     * @param symbol The symbol of the token (e.g., "MTK").
     * @param initialOwner The address that will be granted ownership of this contract.
     */
    constructor(
        string memory name,
        string memory symbol,
        address initialOwner
    ) ERC20(name, symbol) Ownable(initialOwner) {
        // The ERC20 name, symbol, and contract owner are set in the parent constructors.
    }

    /**
     * @notice Creates `amount` new tokens and assigns them to the `to` address.
     * @dev This function can only be called by the contract owner. It is subject to
     * the pausable functionality; minting is not possible when the contract is paused.
     * Emits a {Transfer} event with `from` set to the zero address.
     * @param to The address that will receive the minted tokens.
     * @param amount The quantity of tokens to mint.
     */
    function mint(address to, uint256 amount) public onlyOwner {
        _mint(to, amount);
    }

    /**
     * @notice Pauses all token transfers, including minting and burning.
     * @dev This is an emergency stop mechanism. It can only be called by the owner.
     * See {Pausable-_pause}.
     * Emits a {Paused} event.
     * Requirements:
     * - The contract must not be paused.
     */
    function pause() public onlyOwner {
        _pause();
    }

    /**
     * @notice Unpauses the token, resuming all transfers, minting, and burning.
     * @dev Can only be called by the owner. See {Pausable-_unpause}.
     * Emits an {Unpaused} event.
     * Requirements:
     * - The contract must be paused.
     */
    function unpause() public onlyOwner {
        _unpause();
    }

    /**
     * @dev Overrides the internal _update function from ERC20 to integrate the pausable check.
     * This hook ensures that all token movements (transfers, mints, burns) are blocked
     * when the contract is in a paused state. This is a requirement when combining
     * ERC20 with Pausable.
     */
    function _update(address from, address to, uint256 value)
        internal
        override(ERC20, ERC20Pausable)
    {
        super._update(from, to, value);
    }
}