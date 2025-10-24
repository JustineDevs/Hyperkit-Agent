// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IUniswapV3Factory {
    function getPool(address tokenA, address tokenB, uint24 fee) external view returns (address pool);
    function allPools(uint256 index) external view returns (address pool);
    function allPoolsLength() external view returns (uint256);
    function owner() external view returns (address);
    function feeAmountTickSpacing() external view returns (uint24);
    
    event PoolCreated(
        address indexed token0,
        address indexed token1,
        uint24 indexed fee,
        int24 tickSpacing,
        address pool
    );
}
