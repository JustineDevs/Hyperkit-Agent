// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

/**
 * @title SimpleToken
 * @author Your Name
 * @notice A basic ERC20 token with minting, burning, and pausable features.
 * @dev This contract uses OpenZeppelin's battle-tested libraries for ERC20,
 *      Ownable access control, Burnable functionality, and Pausable emergency stop mechanism.
 *      It follows standard security practices for a production-ready token.
 */
contract SimpleToken is ERC20, ERC20Burnable, Ownable, Pausable {

    /**
     * @notice Constructs the ERC20 token.
     * @param name_ The name of the token.
     * @param symbol_ The symbol of the token.
     * @param initialOwner The address that will initially own the contract and have minting/pausing rights.
     */
    constructor(
        string memory name_,
        string memory symbol_,
        address initialOwner
    ) ERC20(name_, symbol_) Ownable(initialOwner) {
        // The Ownable constructor sets the deployer as the initial owner.
    }

    /**
     * @notice Mints new tokens and assigns them to a specified address.
     * @dev Can only be called by the contract owner.
     *      The contract must not be paused.
     *      Emits a {Transfer} event with `from` set to the zero address.
     * @param to The address that will receive the minted tokens.
     * @param amount The amount of tokens to mint.
     */
    function mint(address to, uint256 amount) public onlyOwner whenNotPaused {
        require(to != address(0), "ERC20: mint to the zero address");
        _mint(to, amount);
    }

    /**
     * @notice Pauses all token transfers.
     * @dev Can only be called by the contract owner.
     *      Emits a {Paused} event.
     */
    function pause() public onlyOwner {
        _pause();
    }

    /**
     * @notice Unpauses all token transfers.
     * @dev Can only be called by the contract owner.
     *      Emits an {Unpaused} event.
     */
    function unpause() public onlyOwner {
        _unpause();
    }

    /**
     * @dev Hook that is called before any token transfer, including minting and burning.
     *      Overrides the function in ERC20 and Pausable to ensure that token transfers
     *      are not possible when the contract is paused.
     * @param from The address from which tokens are being transferred.
     * @param to The address to which tokens are being transferred.
     * @param amount The amount of tokens being transferred.
     */
    function _beforeTokenTransfer(address from, address to, uint256 amount)
        internal
        override(ERC20, Pausable)
    {
        super._beforeTokenTransfer(from, to, amount);
    }
}