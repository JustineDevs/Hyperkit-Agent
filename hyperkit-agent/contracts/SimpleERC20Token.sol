pragma solidity ^0.8.0;

import '@openzeppelin/contracts/access/Ownable.sol';
import '@openzeppelin/contracts/utils/ReentrancyGuard.sol';
import '@openzeppelin/contracts/token/ERC20/ERC20.sol';

/**
 * @title SimpleERC20Token
 * @dev A simple ERC20 token with ownership and reentrancy protection.
 */
contract SimpleERC20Token is Ownable, ReentrancyGuard, ERC20 {
    
    /**
     * @dev Constructor that gives the deployer all initial tokens.
     * @param _owner The owner of the token contract.
     * @param _name The name of the token.
     * @param _symbol The symbol of the token.
     * @param _initialSupply The initial supply of the token.
     */
    constructor(
        address _owner,
        string memory _name,
        string memory _symbol,
        uint256 _initialSupply
    ) 
        Ownable(_owner)
        ERC20(_name, _symbol) 
    {
        _mint(_owner, _initialSupply);
    }

    /**
     * @dev Mint new tokens to a specified address.
     * @param account The address to mint tokens to.
     * @param amount The amount of tokens to mint.
     */
    function mint(address account, uint256 amount) external onlyOwner nonReentrant {
        _mint(account, amount);
    }

    /**
     * @dev Burn tokens from a specified address.
     * @param account The address to burn tokens from.
     * @param amount The amount of tokens to burn.
     */
    function burn(address account, uint256 amount) external onlyOwner nonReentrant {
        _burn(account, amount);
    }
}