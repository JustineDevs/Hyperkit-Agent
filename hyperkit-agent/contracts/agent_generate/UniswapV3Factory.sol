// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "./interfaces/IUniswapV3Factory.sol";
import "./interfaces/IUniswapV3Pool.sol";

contract UniswapV3Factory is IUniswapV3Factory {
    mapping(address => mapping(address => mapping(uint24 => address))) public override getPool;
    address[] public override allPools;
    
    address public override owner;
    uint24 public override feeAmountTickSpacing;
    
    event PoolCreated(
        address indexed token0,
        address indexed token1,
        uint24 indexed fee,
        int24 tickSpacing,
        address pool
    );
    
    constructor() {
        owner = msg.sender;
        feeAmountTickSpacing = 500; // 0.05%
    }
    
    function createPool(
        address tokenA,
        address tokenB,
        uint24 fee
    ) external override returns (address pool) {
        require(tokenA != tokenB, "Same token");
        (address token0, address token1) = tokenA < tokenB ? (tokenA, tokenB) : (tokenB, tokenA);
        require(token0 != address(0), "Zero address");
        require(getPool[token0][token1][fee] == address(0), "Pool exists");
        
        pool = address(new UniswapV3Pool());
        getPool[token0][token1][fee] = pool;
        getPool[token1][token0][fee] = pool;
        allPools.push(pool);
        
        emit PoolCreated(token0, token1, fee, feeAmountTickSpacing, pool);
    }
    
    function allPoolsLength() external view override returns (uint256) {
        return allPools.length;
    }
}
