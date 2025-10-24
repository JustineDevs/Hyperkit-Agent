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
 * @dev This contract implements a standard ERC20 token with additional features:
 * - Ownable: A single owner has administrative control, such as minting new tokens or pausing the contract.
 * - Pausable: The owner can pause all token transfers in case of an emergency.
 * - Burnable: Token holders can burn (destroy) their own tokens.
 * - Minting: The owner can mint new tokens to any address.
 * This contract is built upon OpenZeppelin's battle-tested and audited components.
 */
contract SimpleERC20 is ERC20, ERC20Burnable, ERC20Pausable, Ownable {

    /**
     * @notice Initializes the contract, setting up the token's properties and initial state.
     * @param name The name of the token (e.g., "My Token").
     * @param symbol The symbol of the token (e.g., "MTK").
     * @param initialOwner The address that will be granted ownership of the contract.
     * @param initialSupply The amount of tokens to mint and assign to the initialOwner upon creation.
     *                      The amount should be provided in the smallest unit (e.g., wei), without decimals.
     */
    constructor(
        string memory name,
        string memory symbol,
        address initialOwner,
        uint256 initialSupply
    )
        ERC20(name, symbol)
        Ownable(initialOwner)
    {
        if (initialSupply > 0) {
            _mint(initialOwner, initialSupply);
        }
    }

    /**
     * @notice Pauses all token transfers.
     * @dev This function can only be called by the contract owner. It is a security measure to halt
     *      all token movements in case of a detected vulnerability or threat.
     *      Emits a {Paused} event.
     *      Requirements:
     *      - The contract must not be already paused.
     *      - The caller must be the owner.
     */
    function pause() public onlyOwner {
        _pause();
    }

    /**
     * @notice Unpauses the token transfers, restoring normal operation.
     * @dev This function can only be called by the contract owner.
     *      Emits an {Unpaused} event.
     *      Requirements:
     *      - The contract must be currently paused.
     *      - The caller must be the owner.
     */
    function unpause() public onlyOwner {
        _unpause();
    }

    /**
     * @notice Creates `amount` new tokens and assigns them to the `to` address.
     * @dev This function can only be called by the contract owner. It increases the total supply of the token.
     *      Emits a {Transfer} event with the `from` address as the zero address.
     *      Requirements:
     *      - The `to` address cannot be the zero address.
     *      - The caller must be the owner.
     * @param to The address that will receive the newly minted tokens.
     * @param amount The amount of tokens to mint, in the smallest unit.
     */
    function mint(address to, uint256 amount) public onlyOwner {
        _mint(to, amount);
    }

    /**
     * @dev Internal hook that is called before any token transfer, including minting and burning.
     *      This override combines the functionalities of ERC20 and ERC20Pausable.
     *      It ensures that token transfers are blocked when the contract is paused.
     *      This is the standard way to integrate Pausable with ERC20 in OpenZeppelin Contracts v5.0+.
     */
    function _update(address from, address to, uint256 value)
        internal
        override(ERC20, ERC20Pausable)
    {
        super._update(from, to, value);
    }
}