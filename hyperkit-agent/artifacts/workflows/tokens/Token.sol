// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {ERC20Burnable} from "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import {ERC20Pausable} from "@openzeppelin/contracts/token/ERC20/extensions/ERC20Pausable.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title TestToken
 * @author Your Name
 * @notice A secure and production-ready ERC20 token contract.
 * @dev This contract implements a standard ERC20 token with additional features:
 * - Minting new tokens (restricted to the owner).
 * - Burning tokens (callable by any token holder for their own tokens).
 * - Pausable functionality (emergency stop mechanism controlled by the owner).
 * - Ownable access control.
 * - Reentrancy protection on state-changing functions.
 * It is built using OpenZeppelin's battle-tested contracts.
 */
contract TestToken is ERC20, ERC20Burnable, ERC20Pausable, Ownable, ReentrancyGuard {
    /**
     * @notice Thrown when a zero amount is provided for a mint operation.
     */
    error MintAmountIsZero();

    /**
     * @dev Initializes the contract, setting the token name, symbol, and owner.
     * The deployer of the contract is set as the initial owner.
     * @param initialOwner The address that will receive ownership of the contract.
     */
    constructor(address initialOwner) ERC20("TestToken", "TTK") Ownable(initialOwner) {}

    /**
     * @notice Mints a specified `amount` of tokens to a `to` address.
     * @dev This function can only be called by the contract owner.
     * Emits a {Transfer} event with the `from` address as the zero address.
     * Reverts if `to` is the zero address or `amount` is zero.
     * @param to The address that will receive the minted tokens.
     * @param amount The amount of tokens to mint (in wei).
     */
    function mint(address to, uint256 amount) public onlyOwner nonReentrant {
        if (amount == 0) {
            revert MintAmountIsZero();
        }
        _mint(to, amount);
    }

    /**
     * @notice Pauses all token transfers, minting, and burning.
     * @dev This function can only be called by the contract owner.
     * Useful as an emergency stop mechanism in case of a vulnerability.
     * Emits a {Paused} event.
     */
    function pause() public onlyOwner {
        _pause();
    }

    /**
     * @notice Unpauses the token, resuming all transfers, minting, and burning.
     * @dev This function can only be called by the contract owner.
     * Emits an {Unpaused} event.
     */
    function unpause() public onlyOwner {
        _unpause();
    }

    /**
     * @dev Overrides the internal `_update` function to integrate Pausable functionality.
     * This hook ensures that token transfers (including mints and burns) are blocked
     * when the contract is paused.
     * @param from The address sending tokens.
     * @param to The address receiving tokens.
     * @param value The amount of tokens being transferred.
     */
    function _update(address from, address to, uint256 value) internal override(ERC20, ERC20Pausable) {
        super._update(from, to, value);
    }
}