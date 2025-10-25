// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

/**
 * @title SimpleToken
 * @dev A basic ERC20 token implementation with minting, burning, and pausable capabilities.
 * This contract uses OpenZeppelin's battle-tested libraries for security and standard compliance.
 * - 'ERC20' for the core token functionality.
 * - 'ERC20Burnable' to allow users to burn their own tokens.
 * - 'Ownable' for access control, restricting sensitive functions like minting and pausing to the owner.
 * - 'Pausable' to halt token transfers in case of an emergency.
 *
 * The contract owner is set during deployment and can be transferred later.
 * The owner has the exclusive right to mint new tokens and to pause/unpause the contract.
 * All token transfers, including minting and burning, are disabled when the contract is paused.
 */
contract SimpleToken is ERC20, ERC20Burnable, Ownable, Pausable {

    /**
     * @dev Initializes the contract, sets the token name, symbol, and the initial owner.
     * @param initialOwner The address that will be set as the contract owner.
     */
    constructor(address initialOwner) ERC20("Simple Token", "STKN") Ownable(initialOwner) {
        // The Ownable constructor sets the initial owner to the provided address.
        // The ERC20 constructor sets the name and symbol.
    }

    /**
     * @dev Pauses all token transfers.
     * Can only be called by the owner.
     * Emits a {Paused} event.
     *
     * Requirements:
     * - The contract must not be already paused.
     */
    function pause() public onlyOwner {
        _pause();
    }

    /**
     * @dev Unpauses all token transfers.
     * Can only be called by the owner.
     * Emits an {Unpaused} event.
     *
     * Requirements:
     * - The contract must be paused.
     */
    function unpause() public onlyOwner {
        _unpause();
    }

    /**
     * @dev Creates `amount` tokens and assigns them to `to`, increasing the total supply.
     * Can only be called by the owner.
     * The contract must not be paused for minting to occur.
     * Emits a {Transfer} event with `from` set to the zero address.
     *
     * @param to The address that will receive the minted tokens.
     * @param amount The amount of tokens to mint.
     *
     * Requirements:
     * - `to` cannot be the zero address.
     */
    function mint(address to, uint256 amount) public onlyOwner {
        _mint(to, amount);
    }

    /**
     * @dev Hook that is called before any token transfer, including minting and burning.
     * Overridden to apply the `whenNotPaused` modifier, ensuring that token transfers
     * are not possible while the contract is paused.
     * This override combines the logic from both ERC20 and Pausable contracts.
     */
    function _update(address from, address to, uint256 value)
        internal
        override(ERC20, Pausable)
    {
        super._update(from, to, value);
    }
}