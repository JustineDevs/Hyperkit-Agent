// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title TestToken22
 * @author Smart Contract Expert
 * @notice A secure, production-ready ERC20 token with a fixed supply of 1,000,000.
 * @dev This contract implements the ERC20 standard using OpenZeppelin's battle-tested
 * libraries. It includes Ownable for access control, Pausable for emergency stops,
 * and ERC20Burnable to allow users to burn their own tokens. The total supply is
 * minted to the initial owner upon deployment.
 */
contract TestToken22 is ERC20, ERC20Burnable, Pausable, Ownable {
    /**
     * @notice The total number of tokens to be minted at deployment.
     * @dev 1,000,000 tokens with 18 decimal places.
     */
    uint256 public constant INITIAL_SUPPLY = 1_000_000 * 10**18;

    /**
     * @notice Initializes the contract, sets the token name, symbol, and mints the total supply.
     * @dev The entire initial supply is minted to the `initialOwner` address provided during deployment.
     *      This address also becomes the contract owner, with privileges to pause or unpause the contract.
     * @param initialOwner The address that will receive the initial supply and contract ownership.
     */
    constructor(address initialOwner)
        ERC20("TestToken22", "TT22")
        Ownable(initialOwner)
    {
        if (initialOwner == address(0)) {
            revert OwnableInvalidOwner(address(0));
        }
        _mint(initialOwner, INITIAL_SUPPLY);
    }

    /**
     * @notice Pauses all token transfers, approvals, and burns.
     * @dev This function can only be called by the contract owner. It is a security measure
     *      to halt all token activity in case of an emergency. Emits a {Paused} event.
     *      Throws if called by any account other than the owner.
     */
    function pause() public onlyOwner {
        _pause();
    }

    /**
     * @notice Resumes token transfers, approvals, and burns after they have been paused.
     * @dev This function can only be called by the contract owner. Emits an {Unpaused} event.
     *      Throws if called by any account other than the owner.
     */
    function unpause() public onlyOwner {
        _unpause();
    }

    /**
     * @dev Hook that is called before any token transfer, including minting and burning.
     *      It ensures that token operations cannot occur while the contract is paused.
     * @notice This internal function overrides the OpenZeppelin base function to add the
     *      pausable check, effectively protecting all transfer-related functions
     *      ({transfer}, {transferFrom}, {burn}, etc.).
     * @param from The address tokens are being sent from.
     * @param to The address tokens are being sent to.
     * @param amount The amount of tokens being transferred.
     */
    function _beforeTokenTransfer(address from, address to, uint256 amount)
        internal
        whenNotPaused
        override
    {
        super._beforeTokenTransfer(from, to, amount);
    }
}