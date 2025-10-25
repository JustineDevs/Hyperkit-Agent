// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Pausable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title TestToken
 * @author Smart Contract Generator
 * @notice A secure, production-ready ERC20 token named 'TestToken' (TEST).
 * @dev This contract implements a standard ERC20 token with a fixed supply of 1,000,000 tokens.
 * It integrates OpenZeppelin's secure, community-vetted implementations for ERC20,
 * ownership control (Ownable), pausable token transfers (Pausable), and user-initiated
 * token burning (Burnable).
 */
contract TestToken is ERC20, ERC20Burnable, ERC20Pausable, Ownable {
    /**
     * @notice Initializes the contract, sets the token name, symbol, and initial owner.
     * @dev Mints the total supply of 1,000,000 tokens to the `initialOwner`.
     * The `initialOwner` is also granted ownership of the contract, which allows
     * them to call privileged functions like `pause` and `unpause`.
     * @param initialOwner The address to receive the entire initial supply and contract ownership.
     */
    constructor(address initialOwner)
        ERC20("TestToken", "TEST")
        Ownable(initialOwner)
    {
        // The total supply is 1,000,000 tokens.
        // Since ERC20 decimals are typically 18, we multiply by 10**18.
        uint256 initialSupply = 1_000_000 * 10**decimals();
        _mint(initialOwner, initialSupply);
    }

    /**
     * @notice Pauses all token transfers, approvals, and burns.
     * @dev This function can only be called by the contract owner. It serves as an
     * emergency stop mechanism. Emits a {Paused} event.
     * Requirements:
     * - The contract must not be already paused.
     * - The caller must be the owner.
     */
    function pause() public onlyOwner {
        _pause();
    }

    /**
     * @notice Resumes all token transfers, approvals, and burns.
     * @dev This function can only be called by the contract owner to lift a previously
     * triggered pause. Emits an {Unpaused} event.
     * Requirements:
     * - The contract must be paused.
     * - The caller must be the owner.
     */
    function unpause() public onlyOwner {
        _unpause();
    }

    /**
     * @dev Overrides the internal `_update` function from ERC20 to apply the `whenNotPaused`
     * modifier from the ERC20Pausable extension. This is the core mechanism that ensures
     * all state-changing token operations (transfers, mints, burns) are halted when
     * the contract is paused.
     *
     * This override is required by the Solidity compiler because `_update` is defined in both
     * parent contracts (`ERC20` and `ERC20Pausable`).
     *
     * See {ERC20-_update} and {Pausable-whenNotPaused}.
     */
    function _update(address from, address to, uint256 value)
        internal
        override(ERC20, ERC20Pausable)
    {
        super._update(from, to, value);
    }
}