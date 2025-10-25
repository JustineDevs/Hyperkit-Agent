// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

/**
 * @title SimpleERC20
 * @author Your Name
 * @notice A basic, production-ready ERC20 token with minting, burning, and pausing capabilities.
 * @dev This contract uses OpenZeppelin's battle-tested libraries to ensure security and standard compliance.
 * - ERC20: The standard token implementation.
 * - ERC20Burnable: Allows users to burn their own tokens, reducing the total supply.
 * - Ownable: Restricts administrative functions (e.g., minting, pausing) to a single owner address.
 * - Pausable: Allows the owner to halt all token transfers in case of an emergency.
 * The contract deployer is set as the initial owner.
 */
contract SimpleERC20 is ERC20, ERC20Burnable, Ownable, Pausable {

    /**
     * @notice Sets the token name, symbol, and mints an initial supply to the contract deployer.
     * @dev The deployer of the contract will be the initial owner.
     * @param name_ The name of the token (e.g., "My Token").
     * @param symbol_ The symbol of the token (e.g., "MTK").
     * @param initialSupply The amount of tokens to mint to the owner upon deployment, specified in whole tokens (not wei).
     */
    constructor(
        string memory name_,
        string memory symbol_,
        uint256 initialSupply
    ) ERC20(name_, symbol_) Ownable(msg.sender) {
        if (initialSupply > 0) {
            // The initial supply is multiplied by 10**decimals() to account for the token's decimal places.
            // ERC20's decimals() function returns 18 by default.
            _mint(msg.sender, initialSupply * (10 ** decimals()));
        }
    }

    /**
     * @notice Pauses all token transfers, including minting and burning.
     * @dev This function can only be called by the owner. It is a critical safety feature
     * to halt trading in case of a discovered vulnerability or emergency.
     * Emits a {Paused} event.
     * See {Pausable-_pause}.
     */
    function pause() public onlyOwner {
        _pause();
    }

    /**
     * @notice Resumes token transfers after they have been paused.
     * @dev This function can only be called by the owner.
     * Emits an {Unpaused} event.
     * See {Pausable-_unpause}.
     */
    function unpause() public onlyOwner {
        _unpause();
    }

    /**
     * @notice Creates `amount` new tokens and assigns them to the `to` address.
     * @dev This function can only be called by the owner, allowing for a controlled supply increase.
     * The amount is specified in the smallest unit (wei).
     * Emits a {Transfer} event with the `from` address as the zero address.
     * @param to The address that will receive the minted tokens.
     * @param amount The amount of tokens to mint, in wei (e.g., amount * 10**18).
     */
    function mint(address to, uint256 amount) public onlyOwner {
        _mint(to, amount);
    }

    /**
     * @dev Hook that is called before any token transfer, including minting and burning.
     * @notice This override ensures that token transfers are not possible while the contract is paused.
     * It enforces the `whenNotPaused` state for all token movements.
     */
    function _beforeTokenTransfer(address from, address to, uint256 amount)
        internal
        whenNotPaused
        override(ERC20)
    {
        super._beforeTokenTransfer(from, to, amount);
    }
}