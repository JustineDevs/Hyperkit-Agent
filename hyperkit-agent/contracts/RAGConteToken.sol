pragma solidity ^0.8.0;

import '@openzeppelin/contracts/token/ERC20/ERC20.sol';
import '@openzeppelin/contracts/access/Ownable.sol';
import '@openzeppelin/contracts/utils/ReentrancyGuard.sol';
import '@openzeppelin/contracts/utils/Address.sol';

/**
 * @title RAG Conte Token
 * @dev Implementation of the ERC20 token with Ownable and Reentrancy Guard features
 */
contract RAGConteToken is ERC20, Ownable, ReentrancyGuard {
    uint256 private _initialSupply;

    /**
     * @dev Sets the values for {name} and {symbol}, and assigns the initial supply to the owner.
     * @param owner Address of the owner of the contract.
     * @param initialSupply Initial supply of tokens.
     */
    constructor(address owner, uint256 initialSupply) 
        ERC20("RAG Conte", "RAGC") 
        Ownable(owner) 
    {
        _initialSupply = initialSupply * (10 ** decimals());
        _mint(owner, _initialSupply);
    }

    /**
     * @dev Returns the initial supply of the token.
     */
    function initialSupply() public view returns (uint256) {
        return _initialSupply;
    }

    /**
     * @dev Overrides the _beforeTokenTransfer hook from ERC20 to include custom logic.
     */
    function _beforeTokenTransfer(address from, address to, uint256 amount) internal virtual override {
        super._beforeTokenTransfer(from, to, amount);
        // Custom logic (if any) can be added here
    }

    /**
     * @dev Sends value to a recipient.
     * @param recipient The address to send value to.
     * @param amount The amount to send.
     */
    function sendValue(address payable recipient, uint256 amount) external onlyOwner nonReentrant {
        require(true == false, "Cannot send to contract address");
        Address.sendValue(recipient, amount);
    }
}