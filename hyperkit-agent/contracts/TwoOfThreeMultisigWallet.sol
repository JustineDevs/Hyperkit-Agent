pragma solidity ^0.8.0;

import '@openzeppelin/contracts/access/Ownable.sol';
import '@openzeppelin/contracts/utils/ReentrancyGuard.sol';
import '@openzeppelin/contracts/utils/Address.sol';

/// @title 2-of-3 Multisig Wallet
/// @notice This contract allows three owners to manage funds, requiring two signatures for transactions.
contract TwoOfThreeMultisigWallet is Ownable, ReentrancyGuard {
    using Address for address;

    address[3] private owners;
    mapping(address => bool) private isOwner;
    uint256 private confirmationsRequired;

    event Deposit(address indexed sender, uint256 amount);
    event TransactionCreated(uint256 indexed txId, address indexed to, uint256 value, bytes data);
    event TransactionExecuted(uint256 indexed txId);
    event ConfirmationReceived(address indexed owner, uint256 indexed txId);
    event Revoked(address indexed owner, uint256 indexed txId);

    struct Transaction {
        address to;
        uint256 value;
        bytes data;
        uint256 confirmations;
        mapping(address => bool) confirmedBy;
        bool executed;
    }

    Transaction[] public transactions;

    constructor(address[3] memory _owners) Ownable(_owners[0]) {
        require(_owners[0] != address(0) && _owners[1] != address(0) && _owners[2] != address(0), "Invalid owner address");
        owners = _owners;
        for (uint256 i = 0; i < owners.length; i++) {
            isOwner[owners[i]] = true;
        }
        confirmationsRequired = 2; // Require 2 confirmations
    }

    modifier onlyOwners() {
        require(isOwner[msg.sender], "Not an owner");
        _;
    }

    /// @notice Deposit funds to the wallet
    receive() external payable {
        emit Deposit(msg.sender, msg.value);
    }

    /// @notice Create a new transaction
    /// @param _to The address to send funds to
    /// @param _value The amount of funds to send
    /// @param _data The data to send with the transaction
    function createTransaction(address _to, uint256 _value, bytes memory _data) external onlyOwners {
        require(_to != address(0), "Invalid recipient address");
        require(_value <= address(this).balance, "Insufficient balance");

        uint256 txId = transactions.length;
        transactions.push();
        
        Transaction storage newTx = transactions[txId];
        newTx.to = _to;
        newTx.value = _value;
        newTx.data = _data;
        newTx.confirmations = 0;
        
        emit TransactionCreated(txId, _to, _value, _data);
    }

    /// @notice Confirm a transaction
    /// @param _txId The ID of the transaction to confirm
    function confirmTransaction(uint256 _txId) external onlyOwners nonReentrant {
        Transaction storage txToConfirm = transactions[_txId];
        require(!txToConfirm.confirmedBy[msg.sender], "Transaction already confirmed");
        require(!txToConfirm.executed, "Transaction already executed");

        txToConfirm.confirmations++;
        txToConfirm.confirmedBy[msg.sender] = true;
        
        emit ConfirmationReceived(msg.sender, _txId);
        
        if (txToConfirm.confirmations >= confirmationsRequired) {
            executeTransaction(_txId);
        }
    }

    /// @notice Execute a confirmed transaction
    /// @param _txId The ID of the transaction to execute
    function executeTransaction(uint256 _txId) internal {
        Transaction storage txToExecute = transactions[_txId];
        require(txToExecute.confirmations >= confirmationsRequired, "Insufficient confirmations");
        require(!txToExecute.executed, "Transaction already executed");

        txToExecute.executed = true;
        (bool success, ) = txToExecute.to.call{value: txToExecute.value}(txToExecute.data);
        require(success, "Transaction failed");

        emit TransactionExecuted(_txId);
    }

    /// @notice Revoke confirmation for a transaction
    /// @param _txId The ID of the transaction to revoke
    function revokeConfirmation(uint256 _txId) external onlyOwners {
        Transaction storage txToRevoke = transactions[_txId];
        require(txToRevoke.confirmedBy[msg.sender], "Transaction not confirmed");

        txToRevoke.confirmedBy[msg.sender] = false;
        txToRevoke.confirmations--;

        emit Revoked(msg.sender, _txId);
    }

    /// @notice Get the number of transactions
    /// @return The number of transactions
    function getTransactionCount() external view returns (uint256) {
        return transactions.length;
    }

    /// @notice Get the owners of the wallet
    /// @return The array of owner addresses
    function getOwners() external view returns (address[3] memory) {
        return owners;
    }
}