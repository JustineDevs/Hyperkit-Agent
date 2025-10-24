// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

/**
 * @title TestToken5
 * @author Your Name
 * @notice A simple, production-ready ERC20 token with a fixed supply.
 * @dev This contract implements a standard ERC20 token with features like pausable transfers,
 * burnable tokens, and ownership control, leveraging OpenZeppelin's secure contracts.
 * The initial supply of 1,000,000 tokens is minted to the contract deployer.
 */
contract TestToken5 is ERC20, ERC20Burnable, Ownable, Pausable {

    /**
     * @notice Constructor to create the TestToken5.
     * @param initialOwner The address that will receive the initial supply and contract ownership.
     */
    constructor(address initialOwner)
        ERC20("TestToken5", "TT5")
        Ownable(initialOwner)
    {
        uint256 initialSupply = 1_000_000 * (10**decimals());
        _mint(initialOwner, initialSupply);
    }

    /**
     * @dev Pauses all token transfers.
     * @notice This function can only be called by the owner. It halts all token movements,
     * including transfers and approvals, as an emergency stop mechanism.
     * Emits a {Paused} event.
     */
    function pause() public onlyOwner {
        _pause();
    }

    /**
     * @dev Unpauses all token transfers.
     * @notice This function can only be called by the owner. It resumes all token movements
     * after the contract was previously paused.
     * Emits an {Unpaused} event.
     */
    function unpause() public onlyOwner {
        _unpause();
    }

    /**
     * @dev Hook that is called before any token transfer.
     * @notice This internal function is overridden to incorporate the Pausable functionality.
     * It ensures that token transfers cannot occur while the contract is paused.
     * This affects `transfer`, `transferFrom`, `mint`, and `burn`.
     * @param from The address from which tokens are being transferred.
     * @param to The address to which tokens are being transferred.
     * @param amount The amount of tokens being transferred.
     */
    function _update(address from, address to, uint256 amount)
        internal
        override
        whenNotPaused
    {
        super._update(from, to, amount);
    }
}