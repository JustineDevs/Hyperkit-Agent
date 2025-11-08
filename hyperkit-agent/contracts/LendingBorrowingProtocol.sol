pragma solidity ^0.8.24;

import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Address.sol";

contract LendingBorrowingProtocol is Ownable, ReentrancyGuard {
    struct Loan {
        uint256 amount;
        uint256 interestRate;
        uint256 duration;
        uint256 startTime;
        bool isActive;
    }

    mapping(address => Loan) private loans;
    event LoanCreated(address indexed borrower, uint256 amount, uint256 interestRate, uint256 duration);
    event LoanRepaid(address indexed borrower, uint256 amount);
    event LoanDefaulted(address indexed borrower);

    constructor(address _owner) Ownable(_owner) ReentrancyGuard() {}

    function createLoan(uint256 _amount, uint256 _interestRate, uint256 _duration) external nonReentrant {
        require(loans[msg.sender].isActive == false, "Existing loan must be repaid first");
        require(_amount > 0, "Loan amount must be greater than 0");
        require(_interestRate > 0, "Interest rate must be greater than 0");
        require(_duration > 0, "Duration must be greater than 0");

        loans[msg.sender] = Loan({
            amount: _amount,
            interestRate: _interestRate,
            duration: _duration,
            startTime: block.timestamp,
            isActive: true
        });

        emit LoanCreated(msg.sender, _amount, _interestRate, _duration);
    }

    function repayLoan() external payable nonReentrant {
        Loan storage loan = loans[msg.sender];
        require(loan.isActive, "No active loan to repay");
        
        uint256 repaymentAmount = loan.amount + (loan.amount * loan.interestRate / 100);
        require(msg.value >= repaymentAmount, "Insufficient funds for repayment");

        loan.isActive = false;
        Address.sendValue(payable(owner()), msg.value);

        emit LoanRepaid(msg.sender, msg.value);
    }

    function checkLoanStatus() external view returns (Loan memory) {
        return loans[msg.sender];
    }

    function markLoanDefaulted() external onlyOwner {
        Loan storage loan = loans[msg.sender];
        require(loan.isActive, "No active loan to default");
        loan.isActive = false;

        emit LoanDefaulted(msg.sender);
    }
}