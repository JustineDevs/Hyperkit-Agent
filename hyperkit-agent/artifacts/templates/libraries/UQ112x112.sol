// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title UQ112x112
 * @dev Library for handling Q112.112 fixed point numbers
 */
library UQ112x112 {
    uint224 constant Q112 = 2**112;
    
    /**
     * @notice Encode a uint112 as a UQ112x112
     * @param y Input value
     * @return z Encoded value
     */
    function encode(uint112 y) internal pure returns (uint224 z) {
        z = uint224(y) * Q112; // never overflows
    }
    
    /**
     * @notice Divide a UQ112x112 by a uint112, returning a UQ112x112
     * @param x Dividend
     * @param y Divisor
     * @return z Result
     */
    function uqdiv(uint224 x, uint112 y) internal pure returns (uint224 z) {
        z = x / uint224(y);
    }
}
