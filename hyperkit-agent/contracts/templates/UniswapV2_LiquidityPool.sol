// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";

/**
 * @title UniswapV2LiquidityPool
 * @dev Simplified Uniswap V2-style liquidity pool implementation
 * @author HyperKit AI Agent
 */
contract UniswapV2LiquidityPool is ERC20, ERC20Burnable, Ownable, ReentrancyGuard {
    using SafeMath for uint256;
    
    // Token addresses
    address public tokenA;
    address public tokenB;
    
    // Pool reserves
    uint256 public reserveA;
    uint256 public reserveB;
    
    // Pool state
    uint256 public totalLiquidity;
    uint256 public constant MINIMUM_LIQUIDITY = 1000;
    
    // Fees (in basis points, 100 = 1%)
    uint256 public constant FEE_DENOMINATOR = 10000;
    uint256 public tradingFee = 30; // 0.3%
    uint256 public protocolFee = 5; // 0.05%
    
    // Events
    event LiquidityAdded(address indexed provider, uint256 amountA, uint256 amountB, uint256 liquidity);
    event LiquidityRemoved(address indexed provider, uint256 amountA, uint256 amountB, uint256 liquidity);
    event Swap(address indexed sender, uint256 amountIn, uint256 amountOut, address indexed to);
    event ReservesUpdated(uint256 reserveA, uint256 reserveB);
    
    constructor(
        string memory name,
        string memory symbol,
        address _tokenA,
        address _tokenB
    ) ERC20(name, symbol) {
        tokenA = _tokenA;
        tokenB = _tokenB;
    }
    
    /**
     * @dev Add liquidity to the pool
     * @param amountA Amount of token A to add
     * @param amountB Amount of token B to add
     * @param minLiquidity Minimum liquidity to receive
     * @return liquidity Amount of liquidity tokens minted
     */
    function addLiquidity(
        uint256 amountA,
        uint256 amountB,
        uint256 minLiquidity
    ) external nonReentrant returns (uint256 liquidity) {
        require(amountA > 0 && amountB > 0, "Amounts must be greater than 0");
        
        // Calculate liquidity to mint
        if (totalLiquidity == 0) {
            liquidity = sqrt(amountA.mul(amountB)).sub(MINIMUM_LIQUIDITY);
            _mint(address(0), MINIMUM_LIQUIDITY); // Lock minimum liquidity
        } else {
            uint256 liquidityA = amountA.mul(totalLiquidity).div(reserveA);
            uint256 liquidityB = amountB.mul(totalLiquidity).div(reserveB);
            liquidity = (liquidityA < liquidityB) ? liquidityA : liquidityB;
        }
        
        require(liquidity >= minLiquidity, "Insufficient liquidity minted");
        
        // Transfer tokens from user
        IERC20(tokenA).transferFrom(msg.sender, address(this), amountA);
        IERC20(tokenB).transferFrom(msg.sender, address(this), amountB);
        
        // Update reserves
        reserveA = reserveA.add(amountA);
        reserveB = reserveB.add(amountB);
        totalLiquidity = totalLiquidity.add(liquidity);
        
        // Mint liquidity tokens
        _mint(msg.sender, liquidity);
        
        emit LiquidityAdded(msg.sender, amountA, amountB, liquidity);
        emit ReservesUpdated(reserveA, reserveB);
    }
    
    /**
     * @dev Remove liquidity from the pool
     * @param liquidity Amount of liquidity tokens to burn
     * @param minAmountA Minimum amount of token A to receive
     * @param minAmountB Minimum amount of token B to receive
     * @return amountA Amount of token A received
     * @return amountB Amount of token B received
     */
    function removeLiquidity(
        uint256 liquidity,
        uint256 minAmountA,
        uint256 minAmountB
    ) external nonReentrant returns (uint256 amountA, uint256 amountB) {
        require(liquidity > 0, "Liquidity must be greater than 0");
        require(balanceOf(msg.sender) >= liquidity, "Insufficient liquidity tokens");
        
        // Calculate amounts to return
        amountA = liquidity.mul(reserveA).div(totalLiquidity);
        amountB = liquidity.mul(reserveB).div(totalLiquidity);
        
        require(amountA >= minAmountA && amountB >= minAmountB, "Insufficient amounts");
        
        // Burn liquidity tokens
        _burn(msg.sender, liquidity);
        
        // Update reserves
        reserveA = reserveA.sub(amountA);
        reserveB = reserveB.sub(amountB);
        totalLiquidity = totalLiquidity.sub(liquidity);
        
        // Transfer tokens to user
        IERC20(tokenA).transfer(msg.sender, amountA);
        IERC20(tokenB).transfer(msg.sender, amountB);
        
        emit LiquidityRemoved(msg.sender, amountA, amountB, liquidity);
        emit ReservesUpdated(reserveA, reserveB);
    }
    
    /**
     * @dev Swap tokens
     * @param tokenIn Address of input token
     * @param amountIn Amount of input token
     * @param minAmountOut Minimum amount of output token
     * @param to Address to receive output tokens
     * @return amountOut Amount of output token received
     */
    function swap(
        address tokenIn,
        uint256 amountIn,
        uint256 minAmountOut,
        address to
    ) external nonReentrant returns (uint256 amountOut) {
        require(tokenIn == tokenA || tokenIn == tokenB, "Invalid token");
        require(amountIn > 0, "Amount must be greater than 0");
        require(to != address(0), "Invalid recipient");
        
        // Calculate output amount
        uint256 amountInWithFee = amountIn.mul(FEE_DENOMINATOR.sub(tradingFee));
        uint256 numerator = amountInWithFee.mul(getReserve(tokenIn == tokenA ? tokenB : tokenA));
        uint256 denominator = getReserve(tokenIn).mul(FEE_DENOMINATOR).add(amountInWithFee);
        amountOut = numerator.div(denominator);
        
        require(amountOut >= minAmountOut, "Insufficient output amount");
        
        // Transfer input token from user
        IERC20(tokenIn).transferFrom(msg.sender, address(this), amountIn);
        
        // Update reserves
        if (tokenIn == tokenA) {
            reserveA = reserveA.add(amountIn);
            reserveB = reserveB.sub(amountOut);
        } else {
            reserveB = reserveB.add(amountIn);
            reserveA = reserveA.sub(amountOut);
        }
        
        // Transfer output token to user
        IERC20(tokenIn == tokenA ? tokenB : tokenA).transfer(to, amountOut);
        
        emit Swap(msg.sender, amountIn, amountOut, to);
        emit ReservesUpdated(reserveA, reserveB);
    }
    
    /**
     * @dev Get current reserves
     * @return _reserveA Reserve of token A
     * @return _reserveB Reserve of token B
     */
    function getReserves() external view returns (uint256 _reserveA, uint256 _reserveB) {
        return (reserveA, reserveB);
    }
    
    /**
     * @dev Get reserve of a specific token
     * @param token Token address
     * @return Reserve amount
     */
    function getReserve(address token) public view returns (uint256) {
        if (token == tokenA) return reserveA;
        if (token == tokenB) return reserveB;
        return 0;
    }
    
    /**
     * @dev Get amount out for a given amount in
     * @param tokenIn Input token address
     * @param amountIn Input amount
     * @return amountOut Output amount
     */
    function getAmountOut(address tokenIn, uint256 amountIn) external view returns (uint256 amountOut) {
        require(tokenIn == tokenA || tokenIn == tokenB, "Invalid token");
        
        uint256 amountInWithFee = amountIn.mul(FEE_DENOMINATOR.sub(tradingFee));
        uint256 numerator = amountInWithFee.mul(getReserve(tokenIn == tokenA ? tokenB : tokenA));
        uint256 denominator = getReserve(tokenIn).mul(FEE_DENOMINATOR).add(amountInWithFee);
        amountOut = numerator.div(denominator);
    }
    
    /**
     * @dev Get amount in for a given amount out
     * @param tokenIn Input token address
     * @param amountOut Output amount
     * @return amountIn Input amount
     */
    function getAmountIn(address tokenIn, uint256 amountOut) external view returns (uint256 amountIn) {
        require(tokenIn == tokenA || tokenIn == tokenB, "Invalid token");
        
        uint256 reserveIn = getReserve(tokenIn);
        uint256 reserveOut = getReserve(tokenIn == tokenA ? tokenB : tokenA);
        
        uint256 numerator = reserveIn.mul(amountOut).mul(FEE_DENOMINATOR);
        uint256 denominator = reserveOut.sub(amountOut).mul(FEE_DENOMINATOR.sub(tradingFee));
        amountIn = numerator.div(denominator).add(1);
    }
    
    /**
     * @dev Set trading fee (only owner)
     * @param newFee New trading fee in basis points
     */
    function setTradingFee(uint256 newFee) external onlyOwner {
        require(newFee <= 1000, "Fee too high"); // Max 10%
        tradingFee = newFee;
    }
    
    /**
     * @dev Set protocol fee (only owner)
     * @param newFee New protocol fee in basis points
     */
    function setProtocolFee(uint256 newFee) external onlyOwner {
        require(newFee <= 1000, "Fee too high"); // Max 10%
        protocolFee = newFee;
    }
    
    /**
     * @dev Calculate square root
     * @param x Number to calculate square root of
     * @return Square root
     */
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
    
    /**
     * @dev Emergency withdraw (only owner)
     * @param token Token address to withdraw
     * @param amount Amount to withdraw
     */
    function emergencyWithdraw(address token, uint256 amount) external onlyOwner {
        IERC20(token).transfer(owner(), amount);
    }
}
