pragma solidity ^0.8.0;

import '@openzeppelin/contracts/access/Ownable.sol';
import '@openzeppelin/contracts/utils/ReentrancyGuard.sol';
import '@openzeppelin/contracts/token/ERC20/ERC20.sol';
import '@openzeppelin/contracts/utils/Address.sol';

/**
 * @title ContractGenerationPrompts
 * @dev This contract implements a standard ERC20 token with access controls and security measures.
 */
contract ContractGenerationPrompts is ERC20, Ownable, ReentrancyGuard {
    uint256 private _cap;

    event CapUpdated(uint256 newCap);

    /**
     * @dev Sets the values for {name} and {symbol}, initializes the cap, and assigns the initial balance to the owner.
     * The initial balance is set to 0, and the cap is initialized via constructor.
     *
     * @param _owner The address of the contract owner.
     * @param name_ The name of the token.
     * @param symbol_ The symbol of the token.
     * @param cap_ The maximum supply of the token.
     */
    constructor(address _owner, string memory name_, string memory symbol_, uint256 cap_) 
        ERC20(name_, symbol_) 
        Ownable(_owner) 
    {
        require(cap_ > 0, "Cap must be greater than 0");
        _cap = cap_;
    }

    /**
     * @dev Returns the maximum supply cap for the token.
     */
    function cap() public view returns (uint256) {
        return _cap;
    }

    /**
     * @dev Mints new tokens to the specified address. 
     * The amount minted cannot exceed the cap.
     *
     * @param account The address to mint tokens to.
     * @param amount The number of tokens to be minted.
     */
    function mint(address account, uint256 amount) external onlyOwner nonReentrant {
        require(totalSupply() + amount <= _cap, "Minting exceeds cap");
        _mint(account, amount);
    }

    /**
     * @dev Updates the cap.
     * This function can only be called by the owner of the contract.
     *
     * @param newCap The new maximum supply cap for the token.
     */
    function updateCap(uint256 newCap) external onlyOwner {
        require(newCap >= totalSupply(), "New cap must be greater than or equal to total supply");
        _cap = newCap;
        emit CapUpdated(newCap);
    }

    /**
     * @dev Internal function to perform custom logic before transferring tokens.
     * Can be overridden for additional checks/logic.
     *
     * @param from The address to transfer from.
     * @param to The address to transfer to.
     * @param amount The amount to be transferred.
     */
    function _beforeTokenTransfer(address from, address to, uint256 amount) internal virtual override {
        super._beforeTokenTransfer(from, to, amount);
    }
}