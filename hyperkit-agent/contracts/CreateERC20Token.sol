pragma solidity ^0.8.0;

import '@openzeppelin/contracts/token/ERC20/ERC20.sol';
import '@openzeppelin/contracts/access/Ownable.sol';
import '@openzeppelin/contracts/utils/ReentrancyGuard.sol';
import '@openzeppelin/contracts/utils/Address.sol';

/**
 * @title CreateERC20Token
 * @dev This contract implements an ERC20 token with ownership and reentrancy protection.
 */
contract CreateERC20Token is ERC20, Ownable, ReentrancyGuard {
    
    /**
     * @dev Emitted when new tokens are minted.
     */
    event Minted(address indexed to, uint256 amount);

    /**
     * @dev Throws if the caller is not the owner.
     */
    modifier onlyOwner() {
        require(msg.sender == owner(), "Caller is not the owner");
        _;
    }

    /**
     * @param _owner The address of the owner of the contract.
     * @param name The name of the token.
     * @param symbol The symbol of the token.
     * @param initialSupply The initial supply of tokens.
     */
    constructor(address _owner, string memory name, string memory symbol, uint256 initialSupply)
        ERC20(name, symbol) 
        Ownable(_owner) 
    {
        _mint(_owner, initialSupply);
    }

    /**
     * @dev Mints new tokens to the specified address.
     * @param to The address to mint tokens to.
     * @param amount The amount of tokens to mint.
     */
    function mint(address to, uint256 amount) external onlyOwner nonReentrant {
        _mint(to, amount);
        emit Minted(to, amount);
    }

    /**
     * @dev Overrides the _beforeTokenTransfer hook to include custom logic.
     * @param from The address sending the tokens.
     * @param to The address receiving the tokens.
     * @param amount The amount of tokens being transferred.
     */
    function _beforeTokenTransfer(address from, address to, uint256 amount) internal override {
        super._beforeTokenTransfer(from, to, amount);
    }
}