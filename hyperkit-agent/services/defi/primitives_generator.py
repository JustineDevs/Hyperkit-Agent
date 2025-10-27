"""
DeFi Primitives Generator
Generates common DeFi contract patterns using Alith SDK
"""

import logging
from typing import Dict, List, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class DeFiPrimitive(Enum):
    STAKING = "staking"
    SWAP = "swap"
    VAULT = "vault"
    LENDING = "lending"
    GOVERNANCE = "governance"

class DeFiPrimitivesGenerator:
    """Generates DeFi primitive contracts"""
    
    def __init__(self):
        self.templates = {
            DeFiPrimitive.STAKING: self._generate_staking_template,
            DeFiPrimitive.SWAP: self._generate_swap_template,
            DeFiPrimitive.VAULT: self._generate_vault_template,
            DeFiPrimitive.LENDING: self._generate_lending_template,
            DeFiPrimitive.GOVERNANCE: self._generate_governance_template
        }
    
    async def generate_primitive(self, primitive_type: DeFiPrimitive, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a DeFi primitive contract
        
        Args:
            primitive_type: Type of DeFi primitive
            config: Configuration for the primitive
            
        Returns:
            Generated contract code and metadata
        """
        try:
            logger.info(f"Generating {primitive_type.value} primitive")
            
            if primitive_type not in self.templates:
                raise ValueError(f"Unsupported DeFi primitive: {primitive_type}")
            
            # Generate the contract
            contract_code = await self.templates[primitive_type](config)
            
            # Generate metadata
            metadata = self._generate_metadata(primitive_type, config)
            
            return {
                "status": "success",
                "primitive_type": primitive_type.value,
                "contract_code": contract_code,
                "metadata": metadata,
                "config": config
            }
            
        except Exception as e:
            logger.error(f"Failed to generate {primitive_type.value} primitive: {e}")
            return {
                "status": "error",
                "error": str(e),
                "primitive_type": primitive_type.value
            }
    
    async def _generate_staking_template(self, config: Dict[str, Any]) -> str:
        """Generate staking contract template"""
        token_address = config.get("token_address", "address(0)")
        reward_token = config.get("reward_token", "address(0)")
        reward_rate = config.get("reward_rate", "100")  # tokens per second
        lock_period = config.get("lock_period", "7 days")
        
        return f"""// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

/**
 * @title StakingContract
 * @notice Flexible staking contract with reward distribution
 * @dev Supports multiple tokens and time-lock functionality
 */
contract StakingContract is ReentrancyGuard, Ownable, Pausable {{
    using SafeERC20 for IERC20;
    
    // State variables
    IERC20 public immutable stakingToken;
    IERC20 public immutable rewardToken;
    
    uint256 public rewardRate; // tokens per second
    uint256 public lockPeriod; // in seconds
    uint256 public totalStaked;
    uint256 public lastUpdateTime;
    uint256 public rewardPerTokenStored;
    
    // User staking info
    struct Staker {{
        uint256 amount;
        uint256 rewardDebt;
        uint256 stakedAt;
        uint256 lastClaimed;
    }}
    
    mapping(address => Staker) public stakers;
    
    // Events
    event Staked(address indexed user, uint256 amount);
    event Unstaked(address indexed user, uint256 amount);
    event RewardClaimed(address indexed user, uint256 amount);
    event RewardRateUpdated(uint256 newRate);
    
    constructor(
        address _stakingToken,
        address _rewardToken,
        uint256 _rewardRate,
        uint256 _lockPeriod
    ) {{
        stakingToken = IERC20(_stakingToken);
        rewardToken = IERC20(_rewardToken);
        rewardRate = _rewardRate;
        lockPeriod = _lockPeriod;
        lastUpdateTime = block.timestamp;
    }}
    
    // Modifiers
    modifier updateReward(address account) {{
        rewardPerTokenStored = rewardPerToken();
        lastUpdateTime = lastTimeRewardApplicable();
        if (account != address(0)) {{
            stakers[account].rewardDebt = earned(account);
            stakers[account].lastClaimed = block.timestamp;
        }}
        _;
    }}
    
    // View functions
    function lastTimeRewardApplicable() public view returns (uint256) {{
        return block.timestamp;
    }}
    
    function rewardPerToken() public view returns (uint256) {{
        if (totalStaked == 0) {{
            return rewardPerTokenStored;
        }}
        return rewardPerTokenStored + 
               (lastTimeRewardApplicable() - lastUpdateTime) * rewardRate * 1e18 / totalStaked;
    }}
    
    function earned(address account) public view returns (uint256) {{
        Staker memory staker = stakers[account];
        return staker.amount * rewardPerToken() / 1e18 - staker.rewardDebt;
    }}
    
    // Staking functions
    function stake(uint256 amount) external nonReentrant whenNotPaused updateReward(msg.sender) {{
        require(amount > 0, "Amount must be greater than 0");
        
        stakingToken.safeTransferFrom(msg.sender, address(this), amount);
        
        stakers[msg.sender].amount += amount;
        totalStaked += amount;
        stakers[msg.sender].stakedAt = block.timestamp;
        
        emit Staked(msg.sender, amount);
    }}
    
    function unstake(uint256 amount) external nonReentrant updateReward(msg.sender) {{
        require(amount > 0, "Amount must be greater than 0");
        require(stakers[msg.sender].amount >= amount, "Insufficient staked amount");
        require(
            block.timestamp >= stakers[msg.sender].stakedAt + lockPeriod,
            "Tokens are still locked"
        );
        
        stakers[msg.sender].amount -= amount;
        totalStaked -= amount;
        
        stakingToken.safeTransfer(msg.sender, amount);
        
        emit Unstaked(msg.sender, amount);
    }}
    
    function claimReward() external nonReentrant updateReward(msg.sender) {{
        uint256 reward = earned(msg.sender);
        require(reward > 0, "No rewards to claim");
        
        stakers[msg.sender].rewardDebt = stakers[msg.sender].amount * rewardPerToken() / 1e18;
        
        rewardToken.safeTransfer(msg.sender, reward);
        
        emit RewardClaimed(msg.sender, reward);
    }}
    
    // Admin functions
    function setRewardRate(uint256 _rewardRate) external onlyOwner {{
        rewardRate = _rewardRate;
        emit RewardRateUpdated(_rewardRate);
    }}
    
    function setLockPeriod(uint256 _lockPeriod) external onlyOwner {{
        lockPeriod = _lockPeriod;
    }}
    
    function pause() external onlyOwner {{
        _pause();
    }}
    
    function unpause() external onlyOwner {{
        _unpause();
    }}
    
    function emergencyWithdraw() external onlyOwner {{
        uint256 balance = rewardToken.balanceOf(address(this));
        rewardToken.safeTransfer(owner(), balance);
    }}
}}"""
    
    async def _generate_swap_template(self, config: Dict[str, Any]) -> str:
        """Generate AMM swap contract template"""
        return """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title SimpleAMM
 * @notice Basic Automated Market Maker implementation
 * @dev Constant product formula (x * y = k)
 */
contract SimpleAMM is ReentrancyGuard, Ownable {
    using SafeERC20 for IERC20;
    
    IERC20 public tokenA;
    IERC20 public tokenB;
    
    uint256 public reserveA;
    uint256 public reserveB;
    uint256 public totalSupply;
    
    mapping(address => uint256) public balanceOf;
    
    uint256 public constant MINIMUM_LIQUIDITY = 10**3;
    
    event AddLiquidity(address indexed user, uint256 amountA, uint256 amountB);
    event RemoveLiquidity(address indexed user, uint256 amountA, uint256 amountB);
    event Swap(address indexed user, address tokenIn, uint256 amountIn, uint256 amountOut);
    
    constructor(address _tokenA, address _tokenB) {
        tokenA = IERC20(_tokenA);
        tokenB = IERC20(_tokenB);
    }
    
    function addLiquidity(uint256 amountA, uint256 amountB) external nonReentrant {
        require(amountA > 0 && amountB > 0, "Amounts must be greater than 0");
        
        tokenA.safeTransferFrom(msg.sender, address(this), amountA);
        tokenB.safeTransferFrom(msg.sender, address(this), amountB);
        
        uint256 liquidity;
        if (totalSupply == 0) {
            liquidity = sqrt(amountA * amountB) - MINIMUM_LIQUIDITY;
        } else {
            liquidity = min(amountA * totalSupply / reserveA, amountB * totalSupply / reserveB);
        }
        
        require(liquidity > 0, "Insufficient liquidity minted");
        
        balanceOf[msg.sender] += liquidity;
        totalSupply += liquidity;
        
        reserveA += amountA;
        reserveB += amountB;
        
        emit AddLiquidity(msg.sender, amountA, amountB);
    }
    
    function removeLiquidity(uint256 liquidity) external nonReentrant {
        require(liquidity > 0, "Liquidity must be greater than 0");
        require(balanceOf[msg.sender] >= liquidity, "Insufficient liquidity");
        
        uint256 amountA = liquidity * reserveA / totalSupply;
        uint256 amountB = liquidity * reserveB / totalSupply;
        
        balanceOf[msg.sender] -= liquidity;
        totalSupply -= liquidity;
        
        reserveA -= amountA;
        reserveB -= amountB;
        
        tokenA.safeTransfer(msg.sender, amountA);
        tokenB.safeTransfer(msg.sender, amountB);
        
        emit RemoveLiquidity(msg.sender, amountA, amountB);
    }
    
    function swap(address tokenIn, uint256 amountIn) external nonReentrant {
        require(amountIn > 0, "Amount must be greater than 0");
        
        bool isTokenA = tokenIn == address(tokenA);
        require(isTokenA || tokenIn == address(tokenB), "Invalid token");
        
        uint256 amountOut;
        if (isTokenA) {
            amountOut = getAmountOut(amountIn, reserveA, reserveB);
            tokenA.safeTransferFrom(msg.sender, address(this), amountIn);
            tokenB.safeTransfer(msg.sender, amountOut);
            reserveA += amountIn;
            reserveB -= amountOut;
        } else {
            amountOut = getAmountOut(amountIn, reserveB, reserveA);
            tokenB.safeTransferFrom(msg.sender, address(this), amountIn);
            tokenA.safeTransfer(msg.sender, amountOut);
            reserveB += amountIn;
            reserveA -= amountOut;
        }
        
        emit Swap(msg.sender, tokenIn, amountIn, amountOut);
    }
    
    function getAmountOut(uint256 amountIn, uint256 reserveIn, uint256 reserveOut) 
        public pure returns (uint256) {
        uint256 amountInWithFee = amountIn * 997;
        uint256 numerator = amountInWithFee * reserveOut;
        uint256 denominator = reserveIn * 1000 + amountInWithFee;
        return numerator / denominator;
    }
    
    function sqrt(uint256 y) internal pure returns (uint256 z) {
        if (y > 3) {
            z = y;
            uint256 x = y / 2 + 1;
            while (x < z) {
                z = x;
                x = (y / x + x) / 2;
            }
        } else if (y != 0) {
            z = 1;
        }
    }
    
    function min(uint256 x, uint256 y) internal pure returns (uint256) {
        return x < y ? x : y;
    }
}"""
    
    async def _generate_vault_template(self, config: Dict[str, Any]) -> str:
        """Generate yield vault contract template"""
        return """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

/**
 * @title YieldVault
 * @notice Yield-generating vault with strategy execution
 * @dev Supports multiple strategies and fee management
 */
contract YieldVault is ReentrancyGuard, Ownable, Pausable {
    using SafeERC20 for IERC20;
    
    IERC20 public immutable asset;
    
    uint256 public totalAssets;
    uint256 public totalSupply;
    uint256 public managementFee = 200; // 2% annually
    uint256 public performanceFee = 2000; // 20%
    
    mapping(address => uint256) public balanceOf;
    mapping(address => uint256) public lastDepositTime;
    
    uint256 public constant MAX_FEE = 10000; // 100%
    uint256 public constant SECONDS_PER_YEAR = 365 days;
    
    event Deposit(address indexed user, uint256 amount, uint256 shares);
    event Withdraw(address indexed user, uint256 amount, uint256 shares);
    event StrategyExecuted(uint256 profit, uint256 fee);
    event FeesUpdated(uint256 managementFee, uint256 performanceFee);
    
    constructor(address _asset) {
        asset = IERC20(_asset);
    }
    
    function deposit(uint256 amount) external nonReentrant whenNotPaused {
        require(amount > 0, "Amount must be greater than 0");
        
        asset.safeTransferFrom(msg.sender, address(this), amount);
        
        uint256 shares = convertToShares(amount);
        balanceOf[msg.sender] += shares;
        totalSupply += shares;
        totalAssets += amount;
        lastDepositTime[msg.sender] = block.timestamp;
        
        emit Deposit(msg.sender, amount, shares);
    }
    
    function withdraw(uint256 shares) external nonReentrant {
        require(shares > 0, "Shares must be greater than 0");
        require(balanceOf[msg.sender] >= shares, "Insufficient shares");
        
        uint256 amount = convertToAssets(shares);
        balanceOf[msg.sender] -= shares;
        totalSupply -= shares;
        totalAssets -= amount;
        
        asset.safeTransfer(msg.sender, amount);
        
        emit Withdraw(msg.sender, amount, shares);
    }
    
    function convertToShares(uint256 assets) public view returns (uint256) {
        if (totalSupply == 0) return assets;
        return assets * totalSupply / totalAssets;
    }
    
    function convertToAssets(uint256 shares) public view returns (uint256) {
        if (totalSupply == 0) return shares;
        return shares * totalAssets / totalSupply;
    }
    
    function executeStrategy() external onlyOwner {
        // TODO: Implement actual strategy execution
        uint256 profit = 0; // Placeholder
        uint256 fee = profit * performanceFee / MAX_FEE;
        
        if (fee > 0) {
            asset.safeTransfer(owner(), fee);
        }
        
        emit StrategyExecuted(profit, fee);
    }
    
    function setFees(uint256 _managementFee, uint256 _performanceFee) external onlyOwner {
        require(_managementFee <= MAX_FEE, "Management fee too high");
        require(_performanceFee <= MAX_FEE, "Performance fee too high");
        
        managementFee = _managementFee;
        performanceFee = _performanceFee;
        
        emit FeesUpdated(_managementFee, _performanceFee);
    }
    
    function pause() external onlyOwner {
        _pause();
    }
    
    function unpause() external onlyOwner {
        _unpause();
    }
}"""
    
    async def _generate_lending_template(self, config: Dict[str, Any]) -> str:
        """Generate lending protocol template"""
        return """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title LendingProtocol
 * @notice Simple lending protocol with collateral
 * @dev Supports multiple assets and interest calculation
 */
contract LendingProtocol is ReentrancyGuard, Ownable {
    using SafeERC20 for IERC20;
    
    struct Loan {
        address borrower;
        address collateralToken;
        address loanToken;
        uint256 collateralAmount;
        uint256 loanAmount;
        uint256 interestRate;
        uint256 createdAt;
        bool active;
    }
    
    mapping(address => mapping(address => uint256)) public collateral;
    mapping(uint256 => Loan) public loans;
    mapping(address => bool) public supportedTokens;
    mapping(address => uint256) public interestRates;
    
    uint256 public nextLoanId;
    uint256 public liquidationThreshold = 8000; // 80%
    uint256 public constant MAX_LTV = 10000; // 100%
    
    event DepositCollateral(address indexed user, address token, uint256 amount);
    event WithdrawCollateral(address indexed user, address token, uint256 amount);
    event CreateLoan(uint256 indexed loanId, address borrower, uint256 amount);
    event RepayLoan(uint256 indexed loanId, uint256 amount);
    event LiquidateLoan(uint256 indexed loanId);
    
    function depositCollateral(address token, uint256 amount) external nonReentrant {
        require(supportedTokens[token], "Token not supported");
        require(amount > 0, "Amount must be greater than 0");
        
        IERC20(token).safeTransferFrom(msg.sender, address(this), amount);
        collateral[msg.sender][token] += amount;
        
        emit DepositCollateral(msg.sender, token, amount);
    }
    
    function withdrawCollateral(address token, uint256 amount) external nonReentrant {
        require(collateral[msg.sender][token] >= amount, "Insufficient collateral");
        
        collateral[msg.sender][token] -= amount;
        IERC20(token).safeTransfer(msg.sender, amount);
        
        emit WithdrawCollateral(msg.sender, token, amount);
    }
    
    function createLoan(
        address loanToken,
        uint256 loanAmount,
        address collateralToken,
        uint256 collateralAmount
    ) external nonReentrant {
        require(supportedTokens[loanToken], "Loan token not supported");
        require(supportedTokens[collateralToken], "Collateral token not supported");
        require(collateral[msg.sender][collateralToken] >= collateralAmount, "Insufficient collateral");
        
        uint256 ltv = (loanAmount * MAX_LTV) / collateralAmount;
        require(ltv <= liquidationThreshold, "Loan-to-value too high");
        
        loans[nextLoanId] = Loan({
            borrower: msg.sender,
            collateralToken: collateralToken,
            loanToken: loanToken,
            collateralAmount: collateralAmount,
            loanAmount: loanAmount,
            interestRate: interestRates[loanToken],
            createdAt: block.timestamp,
            active: true
        });
        
        collateral[msg.sender][collateralToken] -= collateralAmount;
        IERC20(loanToken).safeTransfer(msg.sender, loanAmount);
        
        emit CreateLoan(nextLoanId, msg.sender, loanAmount);
        nextLoanId++;
    }
    
    function repayLoan(uint256 loanId, uint256 amount) external nonReentrant {
        Loan storage loan = loans[loanId];
        require(loan.borrower == msg.sender, "Not the borrower");
        require(loan.active, "Loan not active");
        
        IERC20(loan.loanToken).safeTransferFrom(msg.sender, address(this), amount);
        
        if (amount >= loan.loanAmount) {
            loan.active = false;
            collateral[msg.sender][loan.collateralToken] += loan.collateralAmount;
            emit RepayLoan(loanId, amount);
        }
    }
    
    function liquidateLoan(uint256 loanId) external nonReentrant {
        Loan storage loan = loans[loanId];
        require(loan.active, "Loan not active");
        
        // TODO: Implement liquidation logic
        loan.active = false;
        
        emit LiquidateLoan(loanId);
    }
    
    function addSupportedToken(address token, uint256 interestRate) external onlyOwner {
        supportedTokens[token] = true;
        interestRates[token] = interestRate;
    }
    
    function setLiquidationThreshold(uint256 threshold) external onlyOwner {
        require(threshold <= MAX_LTV, "Threshold too high");
        liquidationThreshold = threshold;
    }
}"""
    
    async def _generate_governance_template(self, config: Dict[str, Any]) -> str:
        """Generate governance contract template"""
        return """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/governance/Governor.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorSettings.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorCountingSimple.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorVotes.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorVotesQuorumFraction.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorTimelockControl.sol";

/**
 * @title GovernanceContract
 * @notice Token-based governance system
 * @dev Uses OpenZeppelin Governor with timelock
 */
contract GovernanceContract is 
    Governor,
    GovernorSettings,
    GovernorCountingSimple,
    GovernorVotes,
    GovernorVotesQuorumFraction,
    GovernorTimelockControl
{
    constructor(
        IVotes _token,
        TimelockController _timelock,
        uint256 _votingDelay,
        uint256 _votingPeriod,
        uint256 _proposalThreshold,
        uint256 _quorumPercentage
    )
        Governor("GovernanceContract")
        GovernorSettings(_votingDelay, _votingPeriod, _proposalThreshold)
        GovernorVotes(_token)
        GovernorVotesQuorumFraction(_quorumPercentage)
        GovernorTimelockControl(_timelock)
    {}
    
    function votingDelay() public pure override(IGovernor, GovernorSettings) returns (uint256) {
        return super.votingDelay();
    }
    
    function votingPeriod() public pure override(IGovernor, GovernorSettings) returns (uint256) {
        return super.votingPeriod();
    }
    
    function proposalThreshold() public pure override(Governor, GovernorSettings) returns (uint256) {
        return super.proposalThreshold();
    }
}"""
    
    def _generate_metadata(self, primitive_type: DeFiPrimitive, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate metadata for the primitive"""
        return {
            "primitive_type": primitive_type.value,
            "version": "4.2.0",
            "features": self._get_primitive_features(primitive_type),
            "dependencies": self._get_primitive_dependencies(primitive_type),
            "security_notes": self._get_security_notes(primitive_type),
            "deployment_notes": self._get_deployment_notes(primitive_type)
        }
    
    def _get_primitive_features(self, primitive_type: DeFiPrimitive) -> List[str]:
        """Get features for a primitive type"""
        features_map = {
            DeFiPrimitive.STAKING: [
                "Flexible staking pools",
                "Reward distribution",
                "Time-lock functionality",
                "Multi-token support",
                "Emergency pause"
            ],
            DeFiPrimitive.SWAP: [
                "AMM implementation",
                "Liquidity management",
                "Slippage protection",
                "Price oracles",
                "Fee collection"
            ],
            DeFiPrimitive.VAULT: [
                "Yield generation",
                "Strategy execution",
                "Fee management",
                "Emergency withdrawal",
                "Performance tracking"
            ],
            DeFiPrimitive.LENDING: [
                "Collateral management",
                "Interest calculation",
                "Liquidation system",
                "Multi-asset support",
                "Risk management"
            ],
            DeFiPrimitive.GOVERNANCE: [
                "Proposal creation",
                "Voting mechanisms",
                "Timelock execution",
                "Emergency procedures",
                "Quorum management"
            ]
        }
        return features_map.get(primitive_type, [])
    
    def _get_primitive_dependencies(self, primitive_type: DeFiPrimitive) -> List[str]:
        """Get dependencies for a primitive type"""
        return [
            "@openzeppelin/contracts/token/ERC20/IERC20.sol",
            "@openzeppelin/contracts/security/ReentrancyGuard.sol",
            "@openzeppelin/contracts/access/Ownable.sol"
        ]
    
    def _get_security_notes(self, primitive_type: DeFiPrimitive) -> List[str]:
        """Get security notes for a primitive type"""
        return [
            "Use OpenZeppelin's battle-tested implementations",
            "Implement proper access controls",
            "Add reentrancy guards for external calls",
            "Validate all inputs and check for zero addresses",
            "Consider pausable functionality for emergency stops"
        ]
    
    def _get_deployment_notes(self, primitive_type: DeFiPrimitive) -> List[str]:
        """Get deployment notes for a primitive type"""
        return [
            "Deploy with proper constructor arguments",
            "Set appropriate roles and permissions",
            "Configure initial parameters carefully",
            "Test thoroughly on testnet before mainnet",
            "Consider upgradeability patterns if needed"
        ]

# Global instance
defi_primitives_generator = DeFiPrimitivesGenerator()
