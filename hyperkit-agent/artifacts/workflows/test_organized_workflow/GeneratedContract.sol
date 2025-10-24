// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

/**
 * @title SimpleERC20
 * @author Your Name
 * @notice A basic, production-ready ERC20 token with minting, burning, and pausable features.
 * @dev This contract leverages OpenZeppelin's battle-tested implementations for ERC20,
 * Ownable (for access control), Pausable (for emergency stops), and ERC20Burnable (for user-initiated burns).
 * The owner has the exclusive right to mint new tokens and to pause or unpause the contract.
 * All transfers, including mints and burns, are halted when the contract is paused.
 */
contract SimpleERC20 is ERC20, ERC20Burnable, Ownable, Pausable {

    /**
     * @notice Constructs the ERC20 token and assigns ownership.
     * @param initialOwner The address that will receive ownership of the contract.
     * @param name The name of the token (e.g., "My Token").
     * @param symbol The symbol of the token (e.g., "MTK").
     * @param initialSupply The total amount of tokens to mint on deployment. This value should include decimals.
     * For a token with 18 decimals, to mint 1,000,000 tokens, this value should be 1000000 * 10**18.
     */
    constructor(
        address initialOwner,
        string memory name,
        string memory symbol,
        uint256 initialSupply
    ) ERC20(name, symbol) Ownable(initialOwner) {
        if (initialSupply > 0) {
            _mint(initialOwner, initialSupply);
        }
    }

    /**
     * @dev Hook that is called before any token transfer, including minting and burning.
     * This override ensures that all token movements are blocked when the contract is paused.
     * This is the central point of control for the pausable functionality.
     */
    function _update(address from, address to, uint256 value)
        internal
        override
    {
        _requireNotPaused();
        super._update(from, to, value);
    }

    /**
     * @notice Pauses all token transfers, minting, and burning.
     * @dev Can only be called by the contract owner. Emits a {Paused} event.
     * Requirements:
     * - The contract must not be already paused.
     */
    function pause() public onlyOwner {
        _pause();
    }

    /**
     * @notice Resumes all token transfers, minting, and burning.
     * @dev Can only be called by the contract owner. Emits an {Unpaused} event.
     * Requirements:
     * - The contract must be currently paused.
     */
    function unpause() public onlyOwner {
        _unpause();
    }

    /**
     * @notice Creates `amount` new tokens and assigns them to the `to` address.
     * @dev Can only be called by the contract owner. The contract must not be paused
     * (enforced by the _update hook). Emits a {Transfer} event with the `from` address
     * as the zero address.
     * @param to The address that will receive the minted tokens.
     * @param amount The amount of tokens to mint (should include decimals).
     */
    function mint(address to, uint256 amount) public onlyOwner {
        _mint(to, amount);
    }
}