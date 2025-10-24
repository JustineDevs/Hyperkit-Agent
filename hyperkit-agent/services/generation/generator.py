"""
Smart Contract Generation Service
Uses AI to generate Solidity contracts from natural language prompts
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


class ContractGenerator:
    """
    Generates Solidity smart contracts using AI models.
    Supports multiple AI providers and template integration.
    """

    def __init__(self, api_key: str, provider: str = "openai"):
        """
        Initialize the contract generator.

        Args:
            api_key: API key for the AI provider
            provider: AI provider to use (openai, anthropic, google)
        """
        self.api_key = api_key
        self.provider = provider
        self.client = None
        self.templates = self._load_templates()

        # Initialize AI client based on provider
        self._initialize_client()

        logger.info(f"ContractGenerator initialized with {provider}")

    def _initialize_client(self):
        """Initialize the AI client based on the provider."""
        try:
            if self.provider == "openai":
                import openai

                self.client = openai.OpenAI(api_key=self.api_key)
            elif self.provider == "anthropic":
                import anthropic

                self.client = anthropic.Anthropic(api_key=self.api_key)
            elif self.provider == "google":
                import google.generativeai as genai

                genai.configure(api_key=self.api_key)
                self.client = genai.GenerativeModel(
                    "gemini-2.5-pro-preview-03-25"
                )  # Use working model
            elif self.provider == "deepseek":
                import openai

                self.client = openai.OpenAI(
                    api_key=self.api_key, base_url="https://api.deepseek.com"
                )
            elif self.provider == "xai":
                import openai

                self.client = openai.OpenAI(
                    api_key=self.api_key, base_url="https://api.x.ai/v1"
                )
            # GPT-OSS removed - using cloud-based providers only
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
        except ImportError as e:
            logger.error(f"Failed to import AI provider library: {e}")
            raise

    def _load_templates(self) -> Dict[str, str]:
        """Load contract templates for different contract types."""
        return {
            "token": """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

contract {CONTRACT_NAME} is ERC20, Ownable, ReentrancyGuard {{
    uint256 public constant MAX_SUPPLY = {MAX_SUPPLY};
    
    constructor() ERC20("{TOKEN_NAME}", "{TOKEN_SYMBOL}") {{
        _mint(msg.sender, {INITIAL_SUPPLY} * 10**decimals());
    }}
    
    function mint(address to, uint256 amount) public onlyOwner {{
        require(totalSupply() + amount <= MAX_SUPPLY, "Exceeds max supply");
        _mint(to, amount);
    }}
}}""",
            "nft": """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

contract {CONTRACT_NAME} is ERC721, Ownable, ReentrancyGuard {{
    uint256 public constant MAX_SUPPLY = {MAX_SUPPLY};
    uint256 private _tokenIdCounter;
    
    constructor() ERC721("{NFT_NAME}", "{NFT_SYMBOL}") {{
        _tokenIdCounter = 1;
    }}
    
    function mint(address to) public onlyOwner nonReentrant {{
        require(_tokenIdCounter <= MAX_SUPPLY, "Exceeds max supply");
        _safeMint(to, _tokenIdCounter);
        _tokenIdCounter++;
    }}
}}""",
            "defi_vault": """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract {CONTRACT_NAME} is ReentrancyGuard, Ownable {
    IERC20 public token;
    uint256 public totalDeposits;
    uint256 public totalRewards;
    uint256 public rewardRate;
    uint256 public lastUpdateTime;
    
    mapping(address => uint256) public deposits;
    mapping(address => uint256) public rewards;
    mapping(address => uint256) public userRewardPerTokenPaid;
    
    event Deposited(address indexed user, uint256 amount);
    event Withdrawn(address indexed user, uint256 amount);
    event RewardPaid(address indexed user, uint256 reward);
    
    constructor(address _token) {
        token = IERC20(_token);
    }
    
    function deposit(uint256 amount) external nonReentrant {
        require(amount > 0, "Amount must be > 0");
        token.transferFrom(msg.sender, address(this), amount);
        deposits[msg.sender] += amount;
        totalDeposits += amount;
        emit Deposited(msg.sender, amount);
    }
    
    function withdraw(uint256 amount) external nonReentrant {
        require(amount > 0, "Amount must be > 0");
        require(deposits[msg.sender] >= amount, "Insufficient balance");
        deposits[msg.sender] -= amount;
        totalDeposits -= amount;
        token.transfer(msg.sender, amount);
        emit Withdrawn(msg.sender, amount);
    }
    
    function claimRewards() external nonReentrant {
        uint256 reward = calculateReward(msg.sender);
        if (reward > 0) {
            rewards[msg.sender] = 0;
            token.transfer(msg.sender, reward);
            emit RewardPaid(msg.sender, reward);
        }
    }
}""",
            "staking_rewards": """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract {CONTRACT_NAME} is ReentrancyGuard, Ownable {
    IERC20 public stakingToken;
    IERC20 public rewardsToken;
    
    uint256 public periodFinish = 0;
    uint256 public rewardRate = 0;
    uint256 public rewardsDuration = 7 days;
    uint256 public lastUpdateTime;
    uint256 public rewardPerTokenStored;
    
    mapping(address => uint256) public userRewardPerTokenPaid;
    mapping(address => uint256) public rewards;
    mapping(address => uint256) private _balances;
    
    uint256 private _totalSupply;
    
    event Staked(address indexed user, uint256 amount);
    event Withdrawn(address indexed user, uint256 amount);
    event RewardPaid(address indexed user, uint256 reward);
    
    constructor(address _stakingToken, address _rewardsToken) {
        stakingToken = IERC20(_stakingToken);
        rewardsToken = IERC20(_rewardsToken);
    }
    
    function stake(uint256 amount) external nonReentrant {
        require(amount > 0, "Cannot stake 0");
        _totalSupply += amount;
        _balances[msg.sender] += amount;
        stakingToken.transferFrom(msg.sender, address(this), amount);
        emit Staked(msg.sender, amount);
    }
    
    function withdraw(uint256 amount) public nonReentrant {
        require(amount > 0, "Cannot withdraw 0");
        _totalSupply -= amount;
        _balances[msg.sender] -= amount;
        stakingToken.transfer(msg.sender, amount);
        emit Withdrawn(msg.sender, amount);
    }
    
    function getReward() public nonReentrant {
        uint256 reward = rewards[msg.sender];
        if (reward > 0) {
            rewards[msg.sender] = 0;
            rewardsToken.transfer(msg.sender, reward);
            emit RewardPaid(msg.sender, reward);
        }
    }
}""",
            "governance": """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/governance/Governor.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorSettings.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorCountingSimple.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorVotes.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorVotesQuorumFraction.sol";

contract {CONTRACT_NAME} is Governor, GovernorSettings, GovernorCountingSimple, GovernorVotes, GovernorVotesQuorumFraction {
    constructor(
        IVotes _token,
        uint256 _votingDelay,
        uint256 _votingPeriod,
        uint256 _quorumPercentage
    )
        Governor("{CONTRACT_NAME}")
        GovernorSettings(_votingDelay, _votingPeriod, 0)
        GovernorVotes(_token)
        GovernorVotesQuorumFraction(_quorumPercentage)
    {}
    
    function votingDelay() public view override(IGovernor, GovernorSettings) returns (uint256) {
        return super.votingDelay();
    }
    
    function votingPeriod() public view override(IGovernor, GovernorSettings) returns (uint256) {
        return super.votingPeriod();
    }
    
    function quorum(uint256 blockNumber) public view override(IGovernor, GovernorVotesQuorumFraction) returns (uint256) {
        return super.quorum(blockNumber);
    }
}""",
            "lending_protocol": """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract {CONTRACT_NAME} is ReentrancyGuard, Ownable {
    struct Loan {
        address borrower;
        address lender;
        address token;
        uint256 amount;
        uint256 interestRate;
        uint256 duration;
        uint256 startTime;
        bool active;
        bool repaid;
    }
    
    mapping(uint256 => Loan) public loans;
    mapping(address => uint256[]) public borrowerLoans;
    mapping(address => uint256[]) public lenderLoans;
    
    uint256 public loanCounter;
    uint256 public totalLent;
    uint256 public totalBorrowed;
    
    event LoanCreated(uint256 indexed loanId, address indexed borrower, address indexed lender, uint256 amount);
    event LoanRepaid(uint256 indexed loanId, uint256 amount);
    
    function createLoan(
        address lender,
        address token,
        uint256 amount,
        uint256 interestRate,
        uint256 duration
    ) external nonReentrant returns (uint256) {
        require(lender != address(0), "Invalid lender");
        require(amount > 0, "Amount must be > 0");
        require(duration > 0, "Duration must be > 0");
        
        uint256 loanId = loanCounter++;
        
        loans[loanId] = Loan({
            borrower: msg.sender,
            lender: lender,
            token: token,
            amount: amount,
            interestRate: interestRate,
            duration: duration,
            startTime: block.timestamp,
            active: true,
            repaid: false
        });
        
        borrowerLoans[msg.sender].push(loanId);
        lenderLoans[lender].push(loanId);
        
        totalBorrowed += amount;
        
        emit LoanCreated(loanId, msg.sender, lender, amount);
        
        return loanId;
    }
    
    function repayLoan(uint256 loanId) external nonReentrant {
        Loan storage loan = loans[loanId];
        require(loan.borrower == msg.sender, "Not the borrower");
        require(loan.active, "Loan not active");
        require(!loan.repaid, "Loan already repaid");
        
        uint256 interest = (loan.amount * loan.interestRate * loan.duration) / (365 days * 10000);
        uint256 totalAmount = loan.amount + interest;
        
        IERC20(loan.token).transferFrom(msg.sender, loan.lender, totalAmount);
        
        loan.repaid = true;
        loan.active = false;
        
        emit LoanRepaid(loanId, totalAmount);
    }
}""",
            "dex": """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract {CONTRACT_NAME} is ReentrancyGuard, Ownable {
    struct Pool {
        address tokenA;
        address tokenB;
        uint256 reserveA;
        uint256 reserveB;
        uint256 totalSupply;
        bool active;
    }
    
    mapping(bytes32 => Pool) public pools;
    mapping(address => mapping(address => uint256)) public liquidity;
    
    uint256 public constant FEE_RATE = 30; // 0.3%
    uint256 public constant FEE_DENOMINATOR = 10000;
    
    event PoolCreated(bytes32 indexed poolId, address indexed tokenA, address indexed tokenB);
    event LiquidityAdded(bytes32 indexed poolId, address indexed user, uint256 amountA, uint256 amountB);
    event Swap(bytes32 indexed poolId, address indexed user, address tokenIn, address tokenOut, uint256 amountIn, uint256 amountOut);
    
    function createPool(address tokenA, address tokenB) external onlyOwner returns (bytes32) {
        require(tokenA != tokenB, "Same token");
        require(tokenA != address(0) && tokenB != address(0), "Zero address");
        
        bytes32 poolId = keccak256(abi.encodePacked(tokenA, tokenB));
        require(!pools[poolId].active, "Pool exists");
        
        pools[poolId] = Pool({
            tokenA: tokenA,
            tokenB: tokenB,
            reserveA: 0,
            reserveB: 0,
            totalSupply: 0,
            active: true
        });
        
        emit PoolCreated(poolId, tokenA, tokenB);
        return poolId;
    }
    
    function addLiquidity(
        bytes32 poolId,
        uint256 amountA,
        uint256 amountB
    ) external nonReentrant {
        Pool storage pool = pools[poolId];
        require(pool.active, "Pool not active");
        
        IERC20(pool.tokenA).transferFrom(msg.sender, address(this), amountA);
        IERC20(pool.tokenB).transferFrom(msg.sender, address(this), amountB);
        
        uint256 liquidityAmount;
        if (pool.totalSupply == 0) {
            liquidityAmount = sqrt(amountA * amountB);
        } else {
            liquidityAmount = min(
                (amountA * pool.totalSupply) / pool.reserveA,
                (amountB * pool.totalSupply) / pool.reserveB
            );
        }
        
        pool.reserveA += amountA;
        pool.reserveB += amountB;
        pool.totalSupply += liquidityAmount;
        liquidity[msg.sender][poolId] += liquidityAmount;
        
        emit LiquidityAdded(poolId, msg.sender, amountA, amountB);
    }
    
    function swap(
        bytes32 poolId,
        address tokenIn,
        uint256 amountIn
    ) external nonReentrant {
        Pool storage pool = pools[poolId];
        require(pool.active, "Pool not active");
        
        address tokenOut = tokenIn == pool.tokenA ? pool.tokenB : pool.tokenA;
        require(tokenOut != address(0), "Invalid token");
        
        IERC20(tokenIn).transferFrom(msg.sender, address(this), amountIn);
        
        uint256 amountOut = getAmountOut(amountIn, tokenIn == pool.tokenA ? pool.reserveA : pool.reserveB, tokenIn == pool.tokenA ? pool.reserveB : pool.reserveA);
        
        if (tokenIn == pool.tokenA) {
            pool.reserveA += amountIn;
            pool.reserveB -= amountOut;
        } else {
            pool.reserveB += amountIn;
            pool.reserveA -= amountOut;
        }
        
        IERC20(tokenOut).transfer(msg.sender, amountOut);
        
        emit Swap(poolId, msg.sender, tokenIn, tokenOut, amountIn, amountOut);
    }
    
    function getAmountOut(uint256 amountIn, uint256 reserveIn, uint256 reserveOut) public pure returns (uint256) {
        uint256 amountInWithFee = amountIn * (FEE_DENOMINATOR - FEE_RATE);
        uint256 numerator = amountInWithFee * reserveOut;
        uint256 denominator = (reserveIn * FEE_DENOMINATOR) + amountInWithFee;
        return numerator / denominator;
    }
    
    function sqrt(uint256 x) internal pure returns (uint256) {
        if (x == 0) return 0;
        uint256 z = (x + 1) / 2;
        uint256 y = x;
        while (z < y) {
            y = z;
            z = (x / z + z) / 2;
        }
        return y;
    }
    
    function min(uint256 a, uint256 b) internal pure returns (uint256) {
        return a < b ? a : b;
    }
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

contract {CONTRACT_NAME} is Ownable, ReentrancyGuard, Pausable {{
    IERC20 public immutable asset;
    uint256 public totalAssets;
    uint256 public totalSupply;
    
    mapping(address => uint256) public balanceOf;
    
    event Deposit(address indexed user, uint256 amount);
    event Withdraw(address indexed user, uint256 amount);
    
    constructor(address _asset) {{
        asset = IERC20(_asset);
    }}
    
    function deposit(uint256 amount) external nonReentrant whenNotPaused {{
        require(amount > 0, "Amount must be greater than 0");
        
        asset.transferFrom(msg.sender, address(this), amount);
        balanceOf[msg.sender] += amount;
        totalAssets += amount;
        totalSupply += amount;
        
        emit Deposit(msg.sender, amount);
    }}
    
    function withdraw(uint256 amount) external nonReentrant {{
        require(amount <= balanceOf[msg.sender], "Insufficient balance");
        
        balanceOf[msg.sender] -= amount;
        totalAssets -= amount;
        totalSupply -= amount;
        
        asset.transfer(msg.sender, amount);
        
        emit Withdraw(msg.sender, amount);
    }}
}}""",
        }

    async def generate(self, prompt: str, context: str = "") -> str:
        """
        Generate a smart contract based on the prompt and context.

        Args:
            prompt: Natural language description of the contract
            context: Additional context from RAG system

        Returns:
            Generated Solidity contract code
        """
        try:
            # Determine contract type from prompt
            contract_type = self._determine_contract_type(prompt)

            # Create system prompt
            system_prompt = self._create_system_prompt(contract_type, context)

            # Generate contract using AI
            if self.provider in ["openai", "deepseek", "xai", "gpt-oss"]:
                contract_code = await self._generate_with_openai(system_prompt, prompt)
            elif self.provider == "anthropic":
                contract_code = await self._generate_with_anthropic(
                    system_prompt, prompt
                )
            elif self.provider == "google":
                contract_code = await self._generate_with_google(system_prompt, prompt)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")

            # Post-process the generated code
            contract_code = self._post_process_contract(contract_code, contract_type)

            logger.info(f"Generated {contract_type} contract successfully")
            return contract_code

        except Exception as e:
            logger.error(f"Contract generation failed: {e}")
            raise

    def _determine_contract_type(self, prompt: str) -> str:
        """Determine the type of contract based on the prompt."""
        prompt_lower = prompt.lower()

        if any(keyword in prompt_lower for keyword in ["token", "erc20", "fungible"]):
            return "token"
        elif any(
            keyword in prompt_lower for keyword in ["nft", "erc721", "non-fungible"]
        ):
            return "nft"
        elif any(
            keyword in prompt_lower for keyword in ["vault", "defi", "yield", "staking"]
        ):
            return "defi_vault"
        else:
            return "token"  # Default to token

    def _create_system_prompt(self, contract_type: str, context: str) -> str:
        """Create a system prompt for the AI model."""
        base_prompt = f"""
You are an expert Solidity developer specializing in {contract_type} contracts. 
Generate secure, production-ready smart contracts based on user requirements.

Key Requirements:
- Use Solidity ^0.8.0
- Import OpenZeppelin 5.0 libraries for security
- Follow best practices: checks-effects-interactions pattern
- Implement reentrancy guards where needed
- Use proper access control (Ownable, AccessControl)
- Include comprehensive error handling
- Add events for important state changes
- Use NatSpec documentation
- Ensure gas optimization

Security Best Practices:
- Validate all inputs
- Use SafeMath or built-in overflow protection
- Implement circuit breakers for emergency situations
- Use proper random number generation
- Avoid delegatecall with untrusted contracts
- Implement proper upgrade patterns if needed

Context from knowledge base:
{context}

Generate only the Solidity contract code, no explanations or markdown formatting.
"""
        return base_prompt

    async def _generate_with_openai(self, system_prompt: str, user_prompt: str) -> str:
        """Generate contract using OpenAI-compatible API."""
        # Select model based on provider
        model_map = {
            "openai": "gpt-3.5-turbo",  # Changed from gpt-4 to gpt-3.5-turbo
            "deepseek": "deepseek-chat",
            "xai": "grok-beta",
            "gpt-oss": "gpt-3.5-turbo",  # Changed from gpt-4 to gpt-3.5-turbo
        }
        model = model_map.get(self.provider, "gpt-4")

        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=4000,
        )
        return response.choices[0].message.content

    async def _generate_with_anthropic(
        self, system_prompt: str, user_prompt: str
    ) -> str:
        """Generate contract using Anthropic API."""
        response = self.client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=4000,
            temperature=0.3,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text

    async def _generate_with_google(self, system_prompt: str, user_prompt: str) -> str:
        """Generate contract using Google Gemini API."""
        full_prompt = f"{system_prompt}\n\nUser Request: {user_prompt}"
        response = self.client.generate_content(full_prompt)
        return response.text

    def _post_process_contract(self, contract_code: str, contract_type: str) -> str:
        """Post-process the generated contract code."""
        # Remove markdown formatting if present
        if contract_code.startswith("```solidity"):
            contract_code = contract_code.replace("```solidity", "").replace("```", "")

        # Ensure proper license identifier
        if "SPDX-License-Identifier" not in contract_code:
            contract_code = "// SPDX-License-Identifier: MIT\n" + contract_code

        # Add template-specific parameters if needed
        if contract_type in self.templates:
            # Extract parameters from the prompt and fill template
            # This is a simplified version - in practice, you'd use NLP to extract parameters
            contract_code = self._fill_template_parameters(contract_code, contract_type)

        return contract_code.strip()

    def _fill_template_parameters(self, contract_code: str, contract_type: str) -> str:
        """Fill template parameters with default values."""
        defaults = {
            "CONTRACT_NAME": "GeneratedContract",
            "TOKEN_NAME": "Generated Token",
            "TOKEN_SYMBOL": "GEN",
            "NFT_NAME": "Generated NFT",
            "NFT_SYMBOL": "GNFT",
            "MAX_SUPPLY": "1000000",
            "INITIAL_SUPPLY": "100000",
        }

        for param, value in defaults.items():
            contract_code = contract_code.replace(f"{{{param}}}", value)

        return contract_code

    def get_available_templates(self) -> List[str]:
        """Get list of available contract templates."""
        return list(self.templates.keys())

    def get_template(self, template_name: str) -> str:
        """Get a specific contract template."""
        return self.templates.get(template_name, "")


# Example usage
async def main():
    """Example usage of the ContractGenerator."""
    generator = ContractGenerator(api_key="your-api-key-here", provider="openai")

    prompt = "Create a simple ERC20 token with minting functionality"
    context = "Use OpenZeppelin contracts for security"

    try:
        contract_code = await generator.generate(prompt, context)
        print("Generated Contract:")
        print(contract_code)
    except Exception as e:
        print(f"Generation failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
