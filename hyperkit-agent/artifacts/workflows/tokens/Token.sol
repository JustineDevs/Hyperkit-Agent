// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

/**
 * @title SimpleERC20
 * @author Your Name
 * @notice A basic ERC20 token with minting, burning, and pausable features.
 * @dev This contract uses OpenZeppelin's battle-tested contracts to ensure security.
 * It includes:
 * - ERC20: The standard token implementation.
 * - ERC20Burnable: Allows users to burn their own tokens via the `burn` and `burnFrom` functions.
 * - Ownable: Restricts sensitive functions like minting and pausing to the owner.
 * - Pausable: Allows the owner to halt all token transfers in an emergency.
 */
contract SimpleERC20 is ERC20, ERC20Burnable, Ownable, Pausable {
    /**
     * @notice Constructs the ERC20 token.
     * @param name The name of the token (e.g., "MyToken").
     * @param symbol The symbol of the token (e.g., "MTK").
     * @param initialOwner The address that will be set as the owner of the contract.
     * The owner has exclusive rights to mint new tokens and to pause/unpause the contract.
     * @param initialSupply The total amount of tokens to be minted and sent to the `initialOwner`
     * upon deployment. For a token with 18 decimals, to mint 1,000,000 tokens, this value
     * should be `1000000 * 10**18`.
     */
    constructor(
        string memory name,
        string memory symbol,
        address initialOwner,
        uint256 initialSupply
    ) ERC20(name, symbol) Ownable(initialOwner) {
        if (initialSupply > 0) {
            _mint(initialOwner, initialSupply);
        }
    }

    /**
     * @notice Halts all token transfers.
     * @dev Can only be called by the contract owner.
     * Emits a {Paused} event.
     * See {Pausable-_pause}.
     */
    function pause() public onlyOwner {
        _pause();
    }

    /**
     * @notice Resumes token transfers after they have been paused.
     * @dev Can only be called by the contract owner.
     * Emits an {Unpaused} event.
     * See {Pausable-_unpause}.
     */
    function unpause() public onlyOwner {
        _unpause();
    }

    /**
     * @notice Creates `amount` new tokens and assigns them to the `to` address.
     * @dev Can only be called by the contract owner.
     * Emits a {Transfer} event with the `from` address set to the zero address.
     * @param to The address that will receive the minted tokens.
     * @param amount The amount of tokens to mint.
     */
    function mint(address to, uint256 amount) public onlyOwner {
        _mint(to, amount);
    }

    /**
     * @dev Internal hook that is called before any token transfer, including minting and burning.
     * This override ensures that token transfers are not possible while the contract is paused.
     * It calls the parent implementation after checking the paused state.
     * See {ERC20-_update} and {Pausable}.
     */
    function _update(address from, address to, uint256 value)
        internal
        override(ERC20, ERC20Burnable)
    {
        require(!paused(), "ERC20Pausable: token transfer while paused");
        super._update(from, to, value);
    }
}