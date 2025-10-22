// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/**
 * @title SimpleMintableToken
 * @author Your Name
 * @notice A simple ERC20 token with a minting capability restricted to the owner.
 * @dev This contract uses OpenZeppelin's ERC20, Ownable, and ReentrancyGuard contracts
 *      to provide a secure and standard implementation.
 */
contract SimpleMintableToken is ERC20, Ownable, ReentrancyGuard {
    /**
     * @notice Thrown when attempting to mint zero tokens.
     */
    error MintAmountIsZero();

    /**
     * @dev Sets the values for {name} and {symbol}.
     * The `owner` is set to the deploying address by the `Ownable` constructor.
     * @param name_ The name of the token.
     * @param symbol_ The symbol of the token.
     */
    constructor(string memory name_, string memory symbol_) ERC20(name_, symbol_) Ownable(msg.sender) {}

    /**
     * @notice Creates `amount` new tokens and assigns them to `to`.
     * @dev This function can only be called by the contract owner.
     *      It is protected against reentrancy attacks, although the risk is minimal
     *      in this simple implementation.
     *      Emits a {Transfer} event with `from` set to the zero address.
     * @param to The address that will receive the minted tokens.
     * @param amount The amount of tokens to mint.
     */
    function mint(address to, uint256 amount) public onlyOwner nonReentrant {
        if (amount == 0) {
            revert MintAmountIsZero();
        }
        _mint(to, amount);
    }
}