// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/**
 * @title HyperToken
 * @author Your Name
 * @notice A secure and production-ready ERC20 token with minting, burning, and pausable features.
 * @dev This contract uses OpenZeppelin's battle-tested libraries for core ERC20 functionality,
 * access control, security, and pausable emergency-stop capabilities. Access to administrative
 * functions like minting and pausing is restricted to the owner.
 */
contract HyperToken is ERC20, ERC20Burnable, Ownable, Pausable, ReentrancyGuard {

    /**
     * @notice Sets the token name, symbol, and initial owner.
     * @dev Mints an initial supply of 1,000,000 tokens to the contract deployer.
     * The `initialOwner` address will be set as the contract owner.
     * @param initialOwner The address that will receive ownership of the contract.
     */
    constructor(address initialOwner) ERC20("HyperToken", "HYPR") Ownable(initialOwner) {
        _mint(initialOwner, 1_000_000 * 10**decimals());
    }

    /**
     * @notice Creates `amount` new tokens and assigns them to the `to` address.
     * @dev This function can only be called by the contract owner. It is protected
     * against reentrancy attacks and cannot be called when the contract is paused.
     * Emits a {Transfer} event with `from` set to the zero address.
     * @param to The address that will receive the minted tokens.
     * @param amount The amount of tokens to mint.
     */
    function mint(address to, uint256 amount) public onlyOwner whenNotPaused nonReentrant {
        require(to != address(0), "ERC20: mint to the zero address");
        _mint(to, amount);
    }

    /**
     * @notice Pauses all token transfers, minting, and burning.
     * @dev This function can only be called by the contract owner. It's an emergency
     * stop mechanism. Emits a {Paused} event.
     */
    function pause() public onlyOwner {
        _pause();
    }

    /**
     * @notice Unpauses the contract, resuming all token transfers, minting, and burning.
     * @dev This function can only be called by the contract owner.
     * Emits an {Unpaused} event.
     */
    function unpause() public onlyOwner {
        _unpause();
    }

    /**
     * @dev Hook that is called before any token transfer, including minting and burning.
     * It combines the pausing logic from `Pausable` with the core ERC20 transfer logic,
     * ensuring that no token movements can occur while the contract is paused.
     *
     * Requirements:
     * - When `from` and `to` are both non-zero, `from`'s `amount` of tokens
     * will be transferred to `to`.
     * - When `from` is zero, `amount` tokens will be minted for `to`.
     * - When `to` is zero, `from`'s `amount` tokens will be burned.
     * - `from` and `to` are never both zero.
     * - The contract must not be paused.
     */
    function _update(address from, address to, uint256 value) internal override(ERC20, Pausable) {
        super._update(from, to, value);
    }
}