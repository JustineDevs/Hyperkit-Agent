pragma solidity ^0.8.0;

import '@openzeppelin/contracts/utils/ReentrancyGuard.sol';
import '@openzeppelin/contracts/access/Ownable.sol';
import '@openzeppelin/contracts/token/ERC20/ERC20.sol';
import '@openzeppelin/contracts/utils/Address.sol';

/**
 * @title MyERC20Token
 * @dev Implementation of a standard ERC20 token with access control and reentrancy guard.
 */
contract MyERC20Token is ERC20, Ownable, ReentrancyGuard {
    uint256 private immutable _maxSupply;

    event Mint(address indexed to, uint256 amount);
    event Burn(address indexed from, uint256 amount);

    /**
     * @dev Sets the values for {name} and {symbol}, and initializes the max supply.
     * @param _name Name of the token.
     * @param _symbol Symbol of the token.
     * @param maxSupply Maximum supply of the token.
     * @param _owner Initial owner of the contract.
     */
    constructor(string memory _name, string memory _symbol, uint256 maxSupply, address _owner) 
        ERC20(_name, _symbol) 
        Ownable(_owner) 
    {
        _maxSupply = maxSupply;
    }

    /**
     * @dev Mints `amount` tokens to the specified address, only callable by the owner.
     * @param to Address to receive the minted tokens.
     * @param amount Amount of tokens to mint.
     */
    function mint(address to, uint256 amount) external onlyOwner nonReentrant {
        require(totalSupply() + amount <= _maxSupply, "Minting exceeds max supply");
        _mint(to, amount);
        emit Mint(to, amount);
    }

    /**
     * @dev Burns `amount` tokens from the caller's address.
     * @param amount Amount of tokens to burn.
     */
    function burn(uint256 amount) external nonReentrant {
        _burn(msg.sender, amount);
        emit Burn(msg.sender, amount);
    }

    /**
     * @dev Overrides the _beforeTokenTransfer hook from ERC20 for custom logic if needed.
     * @param from Address of the originating account.
     * @param to Address of the receiving account.
     * @param amount Amount of tokens to transfer.
     */
    function _beforeTokenTransfer(address from, address to, uint256 amount) internal virtual override {
        super._beforeTokenTransfer(from, to, amount);
        // Custom logic can go here
    }

    /**
     * @dev Returns the maximum supply of the token.
     */
    function maxSupply() external view returns (uint256) {
        return _maxSupply;
    }
}