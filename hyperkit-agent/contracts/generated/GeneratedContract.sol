// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Pausable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title SimpleToken
 * @author Your Name
 * @notice A simple, secure, and production-ready ERC20 token.
 * @dev This contract implements a standard ERC20 token with minting, burning, and pausable functionalities.
 * It uses OpenZeppelin contracts for security and standard compliance.
 * Access control for sensitive functions like minting and pausing is managed by Ownable.
 */
contract SimpleToken is ERC20, ERC20Burnable, ERC20Pausable, Ownable {

    /**
     * @notice Constructs the SimpleToken contract.
     * @param initialOwner The address that will be set as the initial owner of the contract.
     * The owner has exclusive rights to mint new tokens and to pause/unpause the contract.
     */
    constructor(address initialOwner)
        ERC20("Simple Token", "STKN")
        Ownable(initialOwner)
    {}

    /**
     * @notice Pauses all token transfers.
     * @dev This function can only be called by the owner. It triggers the `_pause` function
     * from the Pausable contract, setting the contract state to paused.
     * Emits a {Paused} event.
     * Requirements:
     * - The contract must not be already paused.
     */
    function pause() public onlyOwner {
        _pause();
    }

    /**
     * @notice Unpauses the token, resuming all token transfers.
     * @dev This function can only be called by the owner. It triggers the `_unpause` function
     * from the Pausable contract, setting the contract state to unpaused.
     * Emits an {Unpaused} event.
     * Requirements:
     * - The contract must be currently paused.
     */
    function unpause() public onlyOwner {
        _unpause();
    }

    /**
     * @notice Creates `amount` new tokens and assigns them to the `to` address.
     * @dev This function can only be called by the owner. It increases the total supply.
     * Emits a {Transfer} event with `from` set to the zero address.
     * @param to The address that will receive the minted tokens.
     * @param amount The amount of tokens to mint.
     * Requirements:
     * - `to` cannot be the zero address.
     */
    function mint(address to, uint256 amount) public onlyOwner {
        // The check for `to != address(0)` is already handled by OpenZeppelin's _mint function.
        // We keep it here for explicit clarity and as a defense-in-depth measure.
        require(to != address(0), "SimpleToken: cannot mint to the zero address");
        _mint(to, amount);
    }

    /**
     * @dev Overrides the internal `_update` function from ERC20 to integrate pausable functionality.
     * This hook is called before any token transfer, including minting and burning.
     * It ensures that token transfers are not possible while the contract is paused.
     * See {ERC20-_update}.
     * Requirements:
     * - The contract must not be paused.
     */
    function _update(address from, address to, uint256 value)
        internal
        override(ERC20, ERC20Pausable)
    {
        super._update(from, to, value);
    }
}