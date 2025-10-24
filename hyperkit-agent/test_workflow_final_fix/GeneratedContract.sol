// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/**
 * @title TestToken
 * @author Your Name
 * @notice A simple ERC20 token for testing purposes, incorporating standard OpenZeppelin features.
 * @dev This contract includes minting, burning, pausing, and ownership functionalities.
 * It is built upon OpenZeppelin's secure and audited components.
 * It uses Solidity 0.8+ with built-in overflow/underflow checks.
 */
contract TestToken is ERC20, ERC20Burnable, Ownable, Pausable, ReentrancyGuard {

    /**
     * @notice Emitted when the contract is paused.
     */
    event Paused(address account);

    /**
     * @notice Emitted when the contract is unpaused.
     */
    event Unpaused(address account);

    /**
     * @notice Sets up the token with a name, symbol, initial supply, and owner.
     * @param name_ The name of the token (e.g., "Test Token").
     * @param symbol_ The symbol of the token (e.g., "TEST").
     * @param initialSupply The total amount of tokens to mint to the deployer upon creation.
     *        It should be provided with decimals in mind (e.g., for 18 decimals, 1 token is 1 * 10**18).
     * @param owner The address that will be set as the contract owner.
     */
    constructor(
        string memory name_,
        string memory symbol_,
        uint256 initialSupply,
        address owner
    ) ERC20(name_, symbol_) Ownable(owner) {
        if (initialSupply > 0) {
            _mint(owner, initialSupply);
        }
    }

    /**
     * @dev Hook that is called before any token transfer, including minting and burning.
     * It ensures that token transfers cannot occur while the contract is paused.
     * Overrides the function from ERC20.
     */
    function _update(address from, address to, uint256 value)
        internal
        override(ERC20, Pausable)
    {
        super._update(from, to, value);
    }

    /**
     * @notice Creates `amount` new tokens and assigns them to the `to` address.
     * @dev Can only be called by the contract owner.
     * The contract must not be paused for this operation to succeed.
     * Emits a {Transfer} event with `from` set to the zero address.
     * @param to The address to mint the tokens to.
     * @param amount The number of tokens to mint.
     */
    function mint(address to, uint256 amount) public onlyOwner nonReentrant {
        // The `_update` hook handles the `whenNotPaused` check
        _mint(to, amount);
    }

    /**
     * @notice Pauses all token transfers, including mints and burns.
     * @dev Can only be called by the contract owner.
     * This is an emergency stop mechanism.
     * Emits a {Paused} event.
     */
    function pause() public onlyOwner {
        _pause();
        emit Paused(msg.sender);
    }

    /**
     * @notice Unpauses the contract, allowing token transfers to resume.
     * @dev Can only be called by the contract owner.
     * Emits an {Unpaused} event.
     */
    function unpause() public onlyOwner {
        _unpause();
        emit Unpaused(msg.sender);
    }
}