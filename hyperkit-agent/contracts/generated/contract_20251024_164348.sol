// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/math/Math.sol";

interface IHyperSwapCallee {
    function hyperSwapCall(address sender, uint256 amount0, uint256 amount1, bytes calldata data) external;
}

/**
 * @title HyperSwap Liquidity Pool
 * @author Your Name
 * @notice A Uniswap V2-style Automated Market Maker (AMM) for a specific USDC/LINK pair on Metis.
 * @dev This contract manages liquidity, facilitates swaps with a 0.3% fee, and provides TWAP oracle data.
 * It includes flash swap capabilities and reentrancy protection.
 * The contract itself is the LP token (ERC20).
 */
contract HyperSwap is ERC20, ReentrancyGuard, Ownable {
    // --- ERC20 Storage ---
    // ERC20 variables like `balanceOf`, `totalSupply`, `allowance` are inherited.

    // --- AMM Storage ---

    // @dev Minimum liquidity to be locked permanently to prevent certain attacks.
    uint256 public constant MINIMUM_LIQUIDITY = 10**3;
    
    // @dev The two tokens in the liquidity pool.
    // On Metis Mainnet:
    // USDC: 0xEA32A96608495e54156Ae48931A7c20f0dcc1a24
    // LINK: 0xb1d56AD1DE5293ea24C7123b395d2C32414787b4
    address public immutable token0;
    address public immutable token1;

    // @dev Reserves of token0 and token1, packed into a single storage slot.
    uint112 private reserve0;
    uint112 private reserve1;
    // @dev Timestamp of the last block where reserves were updated, used for TWAP.
    uint32 private blockTimestampLast;

    // --- Oracle Storage ---

    // @dev Cumulative prices used for time-weighted average price (TWAP) oracles.
    uint256 public price0CumulativeLast;
    uint256 public price1CumulativeLast;

    // --- Fee Storage ---

    // @dev The last product of reserves, used for calculating protocol fees.
    uint256 public kLast;
    // @dev Address to which protocol fees are sent. Can be updated by the owner.
    address public feeTo;

    // --- Events ---

    event Mint(address indexed sender, uint256 amount0, uint256 amount1);
    event Burn(address indexed sender, uint256 amount0, uint256 amount1, address indexed to);
    event Swap(
        address indexed sender,
        uint256 amount0In,
        uint256 amount1In,
        uint256 amount0Out,
        uint256 amount1Out,
        address indexed to
    );
    event Sync(uint112 reserve0, uint112 reserve1);

    // --- Constructor ---

    /**
     * @notice Initializes the HyperSwap pool.
     * @param _token0 Address of the first token (e.g., USDC).
     * @param _token1 Address of the second token (e.g., LINK).
     * @param _owner The initial owner of the contract.
     */
    constructor(address _token0, address _token1, address _owner) ERC20("HyperSwap LP Token", "HS-LP") Ownable(_owner) {
        require(_token0 != address(0) && _token1 != address(0), "HyperSwap: ZERO_ADDRESS");
        require(_token0 != _token1, "HyperSwap: IDENTICAL_ADDRESSES");
        // Ensure a consistent ordering of tokens
        (token0, token1) = _token0 < _token1 ? (_token0, _token1) : (_token1, _token0);
    }

    // --- Internal Logic ---

    /**
     * @dev Updates reserves and, if necessary, the TWAP oracle data.
     * This function is called at the end of any state-changing function.
     * It follows the checks-effects-interactions pattern.
     */
    function _update(uint256 balance0, uint256 balance1, uint112 _reserve0, uint112 _reserve1) private {
        require(balance0 <= type(uint112).max && balance1 <= type(uint112).max, "HyperSwap: OVERFLOW");
        
        uint32 blockTimestamp = uint32(block.timestamp % 2**32);
        uint32 timeElapsed = blockTimestamp - blockTimestampLast;

        // Update TWAP oracle if time has passed
        if (timeElapsed > 0 && _reserve0 != 0 && _reserve1 != 0) {
            // *Never* overflows because `timeElapsed` is capped at 2**32-1 and `_reserve` is capped at 2**112-1.
            // The result is capped at 2**256-1.
            price0CumulativeLast += uint256(UQ112x112.encode(_reserve1)) * timeElapsed / _reserve0;
            price1CumulativeLast += uint256(UQ112x112.encode(_reserve0)) * timeElapsed / _reserve1;
        }

        reserve0 = uint112(balance0);
        reserve1 = uint112(balance1);
        blockTimestampLast = blockTimestamp;

        emit Sync(reserve0, reserve1);
    }

    /**
     * @dev If `feeTo` is set, this function calculates and mints protocol fees.
     * Protocol fees are 1/3 of the total 0.3% trading fee.
     * This is done by minting new LP tokens to the `feeTo` address.
     * @return feeOn True if a fee was collected, false otherwise.
     */
    function _mintFee(uint112 _reserve0, uint112 _reserve1) private returns (bool feeOn) {
        feeOn = feeTo != address(0);
        uint256 _kLast = kLast; // gas savings

        if (feeOn) {
            if (_kLast != 0) {
                uint256 rootK = Math.sqrt(uint256(_reserve0) * _reserve1);
                uint256 rootKLast = Math.sqrt(_kLast);
                if (rootK > rootKLast) {
                    uint256 numerator = totalSupply * (rootK - rootKLast);
                    // Protocol fee is 0.1% of volume, which is 1/3 of the total 0.3% fee.
                    // The denominator reflects this 1/3 protocol share (vs 1/6 in Uniswap V2).
                    uint256 denominator = (rootK * 2) + rootKLast;
                    uint256 liquidity = numerator / denominator;
                    if (liquidity > 0) _mint(feeTo, liquidity);
                }
            }
        } else if (_kLast != 0) {
            kLast = 0;
        }
    }

    // --- Read-Only Functions ---

    /**
     * @notice Returns the current reserves and the timestamp of the last update.
     * @return _reserve0 The reserve of token0.
     * @return _reserve1 The reserve of token1.
     * @return _blockTimestampLast The timestamp of the last reserve update.
     */
    function getReserves() public view returns (uint112 _reserve0, uint112 _reserve1, uint32 _blockTimestampLast) {
        _reserve0 = reserve0;
        _reserve1 = reserve1;
        _blockTimestampLast = blockTimestampLast;
    }

    /**
     * @notice Given an input amount of one token, returns the maximum output amount of the other token.
     * @dev Takes the 0.3% trading fee into account.
     * @param amountIn The amount of the input token.
     * @param tokenIn The address of the input token.
     * @return amountOut The calculated amount of the output token.
     */
    function getAmountOut(uint256 amountIn, address tokenIn) public view returns (uint256 amountOut) {
        require(amountIn > 0, "HyperSwap: INSUFFICIENT_INPUT_AMOUNT");
        require(tokenIn == token0 || tokenIn == token1, "HyperSwap: INVALID_TOKEN");

        uint256 reserveIn;
        uint256 reserveOut;
        if (tokenIn == token0) {
            (reserveIn, reserveOut) = (reserve0, reserve1);
        } else {
            (reserveIn, reserveOut) = (reserve1, reserve0);
        }

        uint256 amountInWithFee = amountIn * 997; // 1000 - 3 (0.3% fee)
        uint256 numerator = amountInWithFee * reserveOut;
        uint256 denominator = (reserveIn * 1000) + amountInWithFee;
        amountOut = numerator / denominator;
    }

    // --- State-Changing Functions ---

    /**
     * @notice Adds liquidity to the pool.
     * @dev Calculates the optimal amount of tokens to add based on the current reserve ratio.
     * Mints LP tokens to the 'to' address.
     * @param amount0Desired The desired amount of token0 to add.
     * @param amount1Desired The desired amount of token1 to add.
     * @param amount0Min The minimum amount of token0 to add, for slippage protection.
     * @param amount1Min The minimum amount of token1 to add, for slippage protection.
     * @param to The address that will receive the LP tokens.
     * @param deadline A timestamp after which the transaction will be reverted.
     * @return amount0 The actual amount of token0 added.
     * @return amount1 The actual amount of token1 added.
     * @return liquidity The amount of LP tokens minted.
     */
    function addLiquidity(
        uint256 amount0Desired,
        uint256 amount1Desired,
        uint256 amount0Min,
        uint256 amount1Min,
        address to,
        uint256 deadline
    ) external nonReentrant returns (uint256 amount0, uint256 amount1, uint256 liquidity) {
        require(deadline >= block.timestamp, "HyperSwap: EXPIRED");

        (uint112 _reserve0, uint112 _reserve1, ) = getReserves(); // gas savings

        // First liquidity provider sets the initial price
        if (_reserve0 == 0 && _reserve1 == 0) {
            amount0 = amount0Desired;
            amount1 = amount1Desired;
        } else {
            uint256 amount1Optimal = (amount0Desired * _reserve1) / _reserve0;
            if (amount1Optimal <= amount1Desired) {
                require(amount1Optimal >= amount1Min, "HyperSwap: INSUFFICIENT_B_AMOUNT");
                amount0 = amount0Desired;
                amount1 = amount1Optimal;
            } else {
                uint256 amount0Optimal = (amount1Desired * _reserve0) / _reserve1;
                require(amount0Optimal >= amount0Min, "HyperSwap: INSUFFICIENT_A_AMOUNT");
                amount0 = amount0Optimal;
                amount1 = amount1Desired;
            }
        }

        uint256 _totalSupply = totalSupply;
        if (_totalSupply == 0) {
            liquidity = Math.sqrt(amount0 * amount1) - MINIMUM_LIQUIDITY;
            _mint(address(0), MINIMUM_LIQUIDITY); // Permanently lock initial liquidity
        } else {
            liquidity = Math.min((amount0 * _totalSupply) / _reserve0, (amount1 * _totalSupply) / _reserve1);
        }
        
        require(liquidity > 0, "HyperSwap: INSUFFICIENT_LIQUIDITY_MINTED");

        // Mint protocol fee if applicable
        _mintFee(_reserve0, _reserve1);
        
        // Mint LP tokens to the provider
        _mint(to, liquidity);
        
        // Transfer tokens from the provider to this contract
        _safeTransferFrom(token0, msg.sender, address(this), amount0);
        _safeTransferFrom(token1, msg.sender, address(this), amount1);

        uint256 balance0 = IERC20(token0).balanceOf(address(this));
        uint256 balance1 = IERC20(token1).balanceOf(address(this));
        _update(balance0, balance1, _reserve0, _reserve1);
        
        // Update kLast after state change for fee calculation
        if (feeTo != address(0)) {
            kLast = uint256(reserve0) * reserve1;
        }
        
        emit Mint(msg.sender, amount0, amount1);
    }
    
    /**
     * @notice Removes liquidity from the pool.
     * @dev Burns LP tokens and sends the corresponding a mounts of token0 and token1 to the 'to' address.
     * @param liquidity The amount of LP tokens to burn.
     * @param amount0Min The minimum amount of token0 to receive, for slippage protection.
     * @param amount1Min The minimum amount of token1 to receive, for slippage protection.
     * @param to The address that will receive the underlying tokens.
     * @param deadline A timestamp after which the transaction will be reverted.
     * @return amount0 The actual amount of token0 received.
     * @return amount1 The actual amount of token1 received.
     */
    function removeLiquidity(
        uint256 liquidity,
        uint256 amount0Min,
        uint256 amount1Min,
        address to,
        uint256 deadline
    ) external nonReentrant returns (uint256 amount0, uint256 amount1) {
        require(deadline >= block.timestamp, "HyperSwap: EXPIRED");
        require(balanceOf[msg.sender] >= liquidity, "HyperSwap: INSUFFICIENT_LIQUIDITY");

        (uint112 _reserve0, uint112 _reserve1, ) = getReserves(); // gas savings
        uint256 _totalSupply = totalSupply;
        
        amount0 = (liquidity * _reserve0) / _totalSupply;
        amount1 = (liquidity * _reserve1) / _totalSupply;
        
        require(amount0 >= amount0Min, "HyperSwap: INSUFFICIENT_A_AMOUNT");
        require(amount1 >= amount1Min, "HyperSwap: INSUFFICIENT_B_AMOUNT");

        // Mint protocol fee if applicable
        _mintFee(_reserve0, _reserve1);

        // Burn LP tokens from the provider
        _burn(msg.sender, liquidity);
        
        // Transfer tokens from this contract to the provider
        _safeTransfer(token0, to, amount0);
        _safeTransfer(token1, to, amount1);

        uint256 balance0 = IERC20(token0).balanceOf(address(this));
        uint256 balance1 = IERC20(token1).balanceOf(address(this));
        _update(balance0, balance1, _reserve0, _reserve1);

        // Update kLast after state change for fee calculation
        if (feeTo != address(0)) {
            kLast = uint256(reserve0) * reserve1;
        }
        
        emit Burn(msg.sender, amount0, amount1, to);
    }

    /**
     * @notice Swaps an exact amount of an input token for as much as possible of an output token.
     * @dev Supports flash swaps. If `data.length > 0`, it will attempt to call the 'to' address.
     * @param amount0Out The amount of token0 to send out.
     * @param amount1Out The amount of token1 to send out.
     * @param to The address to receive the output tokens.
     * @param data Optional data to pass to the callee for flash swaps.
     */
    function swap(uint256 amount0Out, uint256 amount1Out, address to, bytes calldata data) external nonReentrant {
        require(amount0Out > 0 || amount1Out > 0, "HyperSwap: INSUFFICIENT_OUTPUT_AMOUNT");
        (uint112 _reserve0, uint112 _reserve1, ) = getReserves(); // gas savings
        require(amount0Out < _reserve0 && amount1Out < _reserve1, "HyperSwap: INSUFFICIENT_LIQUIDITY");

        uint256 balance0;
        uint256 balance1;
        { // scope to avoid stack too deep errors
            address _token0 = token0;
            address _token1 = token1;
            require(to != _token0 && to != _token1, "HyperSwap: INVALID_TO");

            if (amount0Out > 0) _safeTransfer(_token0, to, amount0Out);
            if (amount1Out > 0) _safeTransfer(_token1, to, amount1Out);
            if (data.length > 0) IHyperSwapCallee(to).hyperSwapCall(msg.sender, amount0Out, amount1Out, data);

            balance0 = IERC20(_token0).balanceOf(address(this));
            balance1 = IERC20(_token1).balanceOf(address(this));
        }

        uint256 amount0In = balance0 > _reserve0 - amount0Out ? balance0 - (_reserve0 - amount0Out) : 0;
        uint256 amount1In = balance1 > _reserve1 - amount1Out ? balance1 - (_reserve1 - amount1Out) : 0;
        require(amount0In > 0 || amount1In > 0, "HyperSwap: INSUFFICIENT_INPUT_AMOUNT");

        { // scope for fee calculation
            uint256 balance0Adjusted = (balance0 * 1000) - (amount0In * 3);
            uint256 balance1Adjusted = (balance1 * 1000) - (amount1In * 3);
            require(
                balance0Adjusted * balance1Adjusted >= uint256(_reserve0) * _reserve1 * (1000**2),
                "HyperSwap: K"
            );
        }

        _update(balance0, balance1, _reserve0, _reserve1);
        emit Swap(msg.sender, amount0In, amount1In, amount0Out, amount1Out, to);
    }
    
    /**
     * @notice A user-friendly swap function.
     * @dev Swaps an exact amount of input tokens for a minimum amount of output tokens.
     * @param tokenIn The address of the input token.
     * @param amountIn The amount of input tokens to swap.
     * @param minAmountOut The minimum amount of output tokens to receive, for slippage protection.
     * @param to The address to receive the output tokens.
     * @param deadline A timestamp after which the transaction will be reverted.
     */
    function swap(
        address tokenIn,
        uint256 amountIn,
        uint256 minAmountOut,
        address to,
        uint256 deadline
    ) external nonReentrant {
        require(deadline >= block.timestamp, "HyperSwap: EXPIRED");

        uint256 amountOut = getAmountOut(amountIn, tokenIn);
        require(amountOut >= minAmountOut, "HyperSwap: INSUFFICIENT_OUTPUT_AMOUNT");

        (address tokenOut, uint amount0Out, uint amount1Out) = tokenIn == token0 
            ? (token1, 0, amountOut) 
            : (token0, amountOut, 0);

        _safeTransferFrom(tokenIn, msg.sender, address(this), amountIn);
        swap(amount0Out, amount1Out, to, new bytes(0));
    }

    // --- Owner Functions ---

    /**
     * @notice Sets the address that will receive protocol fees.
     * @dev Only the contract owner can call this function.
     * @param _feeTo The new address for fee collection.
     */
    function setFeeTo(address _feeTo) external onlyOwner {
        feeTo = _feeTo;
    }
    
    // --- Utility Functions ---

    /**
     * @dev Helper function to safely transfer tokens from this contract.
     */
    function _safeTransfer(address token, address to, uint256 value) private {
        (bool success, bytes memory data) = token.call(abi.encodeWithSelector(IERC20.transfer.selector, to, value));
        require(success && (data.length == 0 || abi.decode(data, (bool))), 'HyperSwap: TRANSFER_FAILED');
    }

    /**
     * @dev Helper function to safely transfer tokens to this contract.
     */
    function _safeTransferFrom(address token, address from, address to, uint256 value) private {
        (bool success, bytes memory data) = token.call(abi.encodeWithSelector(IERC20.transferFrom.selector, from, to, value));
        require(success && (data.length == 0 || abi.decode(data, (bool))), 'HyperSwap: TRANSFER_FROM_FAILED');
    }
}

/**
 * @title UQ112x112
 * @dev A library for handling UQ112x112 numbers, used for TWAP oracles.
 * This is a simplified version for demonstration.
 */
library UQ112x112 {
    uint224 constant Q112 = 2**112;

    // encode a uint112 as a UQ112x112
    function encode(uint112 y) internal pure returns (uint224 z) {
        z = uint224(y) * Q112;
    }
}