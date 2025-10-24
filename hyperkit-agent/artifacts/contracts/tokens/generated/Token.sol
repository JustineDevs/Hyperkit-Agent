// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {ERC20Burnable} from "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";
import {Pausable} from "@openzeppelin/contracts/security/Pausable.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/**
 * @title TestToken19
 * @author Your Name
 * @notice A simple ERC20 token with a fixed supply, pausable functionality,
 * and burnable features, built using OpenZeppelin contracts.
 * @dev This contract mints an initial supply of 1,000,000 tokens to the deployer.
 * The contract owner can pause and unpause token transfers.
 * Any token holder can burn their own tokens.
 */
contract TestToken19 is ERC20, ERC20Burnable, Ownable, Pausable, ReentrancyGuard {
    /**
     * @notice The total number of tokens to be minted at deployment.
     * @dev The value is 1,000,000 tokens with 18 decimals.
     */
    uint256 public constant INITIAL_SUPPLY = 1_000_000 * 10**18;

    /**
     * @dev An error indicating an invalid address (e.g., address(0)).
     */
    error TestToken19__InvalidAddress();

    /**
     * @dev An event emitted when the contract is paused.
     * @param account The account that triggered the pause.
     */
    event Paused(address account);

    /**
     * @dev An event emitted when the contract is unpaused.
     * @param account The account that triggered the unpause.
     */
    event Unpaused(address account);

    /**
     * @notice Constructs the TestToken19 contract.
     * @param initialOwner The address that will receive the initial supply and contract ownership.
     */
    constructor(address initialOwner) ERC20("TestToken19", "TT19") Ownable(initialOwner) {
        if (initialOwner == address(0)) {
            revert TestToken19__InvalidAddress();
        }
        _mint(initialOwner, INITIAL_SUPPLY);
    }

    /**
     * @notice Pauses all token transfers.
     * @dev Can only be called by the contract owner.
     * Emits a {Paused} event.
     * @custom:security See {Pausable-_pause}.
     */
    function pause() public onlyOwner nonReentrant {
        _pause();
        emit Paused(msg.sender);
    }

    /**
     * @notice Unpauses all token transfers.
     * @dev Can only be called by the contract owner.
     * Emits an {Unpaused} event.
     * @custom:security See {Pausable-_unpause}.
     */
    function unpause() public onlyOwner nonReentrant {
        _unpause();
        emit Unpaused(msg.sender);
    }

    /**
     * @dev Overrides the internal OpenZeppelin `_update` function to enforce the `whenNotPaused`
     * modifier on all token movements (transfers, mints, and burns). This is a more
     * gas-efficient and comprehensive approach than overriding each individual function.
     */
    function _update(address from, address to, uint256 value) internal override(ERC20, ERC20Pausable) whenNotPaused {
        super._update(from, to, value);
    }
}