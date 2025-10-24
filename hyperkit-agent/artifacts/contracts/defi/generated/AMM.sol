// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

// Interface for the flash swap callback
interface IHyperSwapCallee {
    /// @notice Called by the HyperSwap pool to execute the flash swap.
    /// @param sender The address that initiated the flash swap.
    /// @param amount0 The amount of token0 borrowed.
    /// @param amount1 The amount of token1 borrowed.
    /// @param data Arbitrary data sent by the initiator.
    function hyperSwapCall(address sender, uint256 amount0, uint256 amount1, bytes calldata data) external;
}

/**
 * @title HyperSwap Liquidity Pool
 * @author Your Name
 * @notice A secure, production-ready Uniswap-style AMM liquidity pool contract.
 * @dev Implements a constant product (x*y=k) AMM with LP tokens, trading fees,
 * flash swaps, and a time-weighted average price (TWAP) oracle.
 * This contract is designed for a specific pair of ERC20 tokens, e.g., USDC/LINK on Metis.
 * The protocol fee is 1/3 of the total 0.3% trade fee (i.e., 0.1%).
 */
contract HyperSwap is ERC20, ReentrancyGuard {
    // --- Constants ---

    /// @dev The minimum liquidity amount to be minted to the first liquidity provider.
    uint256 public constant MINIMUM_LIQUIDITY = 10**3;
    /// @dev The denominator for the fee calculation, 10000 = 100%. 30 corresponds to 0.3%.
    uint256 public constant FEE_DENOMINATOR = 10000;
    /// @dev The numerator for the trade fee. 30/10000 = 0.3%.
    uint256 public constant FEE_NUMERATOR = 30;
    /// @dev The denominator for the protocol fee split. The protocol fee is 1/3 of the total fee.
    uint256 public constant PROTOCOL_FEE_SHARE_DIVISOR = 3;

    // --- State Variables ---

    /// @notice The first token of the trading pair.
    address public immutable token0;
    /// @notice The second token of the trading pair.
    address public immutable token1;

    /// @notice The reserve of token0 in the pool.
    uint112 private reserve0;
    /// @notice The reserve of token1 in the pool.
    uint112 private reserve1;
    /// @notice The timestamp of the last block in which the reserves were updated.
    uint32 private blockTimestampLast;

    /// @notice The cumulative price of token0, used for TWAP calculation.
    uint256 public price0CumulativeLast;
    /// @notice The cumulative price of token1, used for TWAP calculation.
    uint256 public price1CumulativeLast;

    /// @dev The product of reserves `k = reserve0 * reserve1` from the last fee minting.
    uint256 public kLast;

    /// @notice The address that can set the `feeTo` address.
    address public feeToSetter;
    /// @notice The address to which protocol fees are sent.
    address public feeTo;

    // --- Events ---

    /// @notice Emitted when liquidity is added to the pool.
    /// @param sender The address that added the liquidity.
    /// @param amount0 The amount of token0 added.
    /// @param amount1 The amount of token1 added.
    event Mint(address indexed sender, uint256 amount0, uint256 amount1);

    /// @notice Emitted when liquidity is removed from the pool.
    /// @param sender The address that initiated the removal.
    /// @param to The address that received the tokens.
    /// @param amount0 The amount of token0 removed.
    /// @param amount1 The amount of token1 removed.
    event Burn(address indexed sender, address indexed to, uint256 amount0, uint256 amount1);

    /// @notice Emitted on every swap.
    /// @param sender The address that initiated the swap.
    /// @param to The address that received the swapped tokens.
    /// @param amount0In The amount of token0 sent to the pool.
    /// @param amount1In The amount of token1 sent to the pool.
    /// @param amount0Out The amount of token0 sent from the pool.
    /// @param amount1Out The amount of token1 sent from the pool.
    event Swap(
        address indexed sender,
        address indexed to,
        uint256 amount0In,
        uint256 amount1In,
        uint256 amount0Out,
        uint256 amount1Out
    );

    /// @notice Emitted after every state change to update off-chain clients.
    /// @param reserve0 The new reserve of token0.
    /// @param reserve1 The new reserve of token1.
    event Sync(uint112 reserve0, uint112 reserve1);


    // --- Modifiers ---

    /// @dev A lock to prevent reentrancy into the _update function.
    uint256 private unlocked = 1;
    modifier lock() {
        require(unlocked == 1, "HyperSwap: LOCKED");
        unlocked = 0;
        _;
        unlocked = 1;
    }

    // --- Constructor ---

    /**
     * @notice Initializes the HyperSwap pool.
     * @param _tokenA The address of the first ERC20 token.
     * @param _tokenB The address of the second ERC20 token.
     */
    constructor(address _tokenA, address _tokenB) ERC20("HyperSwap LP Token", "HS-LP") {
        require(_tokenA != address(0) && _tokenB != address(0), "HyperSwap: ZERO_ADDRESS");
        require(_tokenA != _tokenB, "HyperSwap: IDENTICAL_ADDRESSES");
        
        // Ensure canonical ordering of tokens
        (token0, token1) = _tokenA < _tokenB ? (_tokenA, _tokenB) : (_tokenB, _tokenA);
        feeToSetter = msg.sender;
    }

    // --- Core Logic ---

    /**
     * @dev Internal function to update reserves, TWAP, and mint protocol fees.
     * @param _balance0 The current balance of token0.
     * @param _balance1 The current balance of token1.
     * @param _reserve0 The previous reserve of token0.
     * @param _reserve1 The previous reserve of token1.
     */
    function _update(uint256 _balance0, uint256 _balance1, uint112 _reserve0, uint112 _reserve1) private {
        require(_balance0 <= type(uint112).max && _balance1 <= type(uint112).max, "HyperSwap: OVERFLOW");
        
        uint32 blockTimestamp = uint32(block.timestamp % 2**32);
        uint32 timeElapsed = blockTimestamp - blockTimestampLast;

        if (timeElapsed > 0 && _reserve0 != 0 && _reserve1 != 0) {
            // Update cumulative prices for TWAP
            // Fixed point UQ112x112 encoding
            price0CumulativeLast += uint256(UQ112x112.encode(_reserve1)) * timeElapsed / _reserve0;
            price1CumulativeLast += uint256(UQ112x112.encode(_reserve0)) * timeElapsed / _reserve1;
        }

        reserve0 = uint112(_balance0);
        reserve1 = uint112(_balance1);
        blockTimestampLast = blockTimestamp;

        emit Sync(reserve0, reserve1);
    }

    /**
     * @dev Mints protocol fees if `feeTo` is set.
     * @param _reserve0 The reserve of token0 before the current transaction.
     * @param _reserve1 The reserve of token1 before the current transaction.
     * @return feeOn True if fees were minted, false otherwise.
     */
    function _mintFee(uint112 _reserve0, uint112 _reserve1) private returns (bool feeOn) {
        feeOn = feeTo != address(0);
        if (feeOn) {
            if (kLast > 0) {
                uint256 rootK = Babylonian.sqrt(uint256(_reserve0) * _reserve1);
                uint256 rootKLast = Babylonian.sqrt(kLast);
                if (rootK > rootKLast) {
                    uint256 numerator = totalSupply() * (rootK - rootKLast);
                    uint256 denominator = (rootK * (PROTOCOL_FEE_SHARE_DIVISOR - 1)) + rootKLast;
                    uint256 liquidity = numerator / denominator;
                    if (liquidity > 0) {
                        _mint(feeTo, liquidity);
                    }
                }
            }
        } else if (kLast > 0) {
            kLast = 0;
        }
        kLast = uint256(reserve0) * reserve1;
    }

    // --- External Functions ---

    /**
     * @notice Returns the current reserves and the last update timestamp.
     * @return _reserve0 The reserve of token0.
     * @return _reserve1 The reserve of token1.
     * @return _blockTimestampLast The timestamp of the last update.
     */
    function getReserves() external view returns (uint112 _reserve0, uint112 _reserve1, uint32 _blockTimestampLast) {
        _reserve0 = reserve0;
        _reserve1 = reserve1;
        _blockTimestampLast = blockTimestampLast;
    }

    /**
     * @notice Calculates the output amount for a given input amount.
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
        
        uint256 amountInWithFee = amountIn * (FEE_DENOMINATOR - FEE_NUMERATOR);
        uint256 numerator = amountInWithFee * reserveOut;
        uint256 denominator = (reserveIn * FEE_DENOMINATOR) + amountInWithFee;
        amountOut = numerator / denominator;
    }

    /**
     * @notice Adds liquidity to the pool.
     * @param to The address to receive the LP tokens.
     * @param amountADesired The desired amount of tokenA to add.
     * @param amountBDesired The desired amount of tokenB to add.
     * @param amountAMin The minimum amount of tokenA to add (slippage protection).
     * @param amountBMin The minimum amount of tokenB to add (slippage protection).
     * @return amountA The actual amount of tokenA added.
     * @return amountB The actual amount of tokenB added.
     * @return liquidity The amount of LP tokens minted.
     */
    function addLiquidity(
        address to,
        uint256 amountADesired,
        uint256 amountBDesired,
        uint256 amountAMin,
        uint256 amountBMin
    ) external nonReentrant returns (uint256 amountA, uint256 amountB, uint256 liquidity) {
        (uint112 _reserve0, uint112 _reserve1,) = getReserves();
        if (_reserve0 == 0 && _reserve1 == 0) {
            (amountA, amountB) = (amountADesired, amountBDesired);
            liquidity = Babylonian.sqrt(amountA * amountB) - MINIMUM_LIQUIDITY;
            _mint(address(0), MINIMUM_LIQUIDITY); // Lock minimum liquidity
        } else {
            uint256 amountBOptimal = (amountADesired * _reserve1) / _reserve0;
            if (amountBOptimal <= amountBDesired) {
                require(amountBOptimal >= amountBMin, "HyperSwap: INSUFFICIENT_B_AMOUNT");
                (amountA, amountB) = (amountADesired, amountBOptimal);
            } else {
                uint256 amountAOptimal = (amountBDesired * _reserve0) / _reserve1;
                require(amountAOptimal <= amountADesired, "HyperSwap: INSUFFICIENT_A_AMOUNT_LOGIC_ERROR");
                require(amountAOptimal >= amountAMin, "HyperSwap: INSUFFICIENT_A_AMOUNT");
                (amountA, amountB) = (amountAOptimal, amountBDesired);
            }
            uint256 _totalSupply = totalSupply();
            liquidity = Math.min((amountA * _totalSupply) / _reserve0, (amountB * _totalSupply) / _reserve1);
        }
        require(amountA >= amountAMin && amountB >= amountBMin, "HyperSwap: SLIPPAGE");
        require(liquidity > 0, "HyperSwap: INSUFFICIENT_LIQUIDITY_MINTED");

        // --- Effects ---
        _mint(to, liquidity);
        _update(
            IERC20(token0).balanceOf(address(this)) + amountA,
            IERC20(token1).balanceOf(address(this)) + amountB,
            _reserve0,
            _reserve1
        );
        if (feeTo != address(0)) {
           _mintFee(_reserve0, _reserve1);
        }

        // --- Interactions ---
        _safeTransferFrom(token0, msg.sender, address(this), amountA);
        _safeTransferFrom(token1, msg.sender, address(this), amountB);

        emit Mint(msg.sender, amountA, amountB);
    }

    /**
     * @notice Removes liquidity from the pool.
     * @param to The address to receive the withdrawn tokens.
     * @param liquidity The amount of LP tokens to burn.
     * @param amount0Min The minimum amount of token0 to receive (slippage protection).
     * @param amount1Min The minimum amount of token1 to receive (slippage protection).
     * @return amount0 The amount of token0 returned.
     * @return amount1 The amount of token1 returned.
     */
    function removeLiquidity(
        address to,
        uint256 liquidity,
        uint256 amount0Min,
        uint256 amount1Min
    ) external nonReentrant returns (uint256 amount0, uint256 amount1) {
        require(liquidity > 0, "HyperSwap: ZERO_LIQUIDITY");
        (uint112 _reserve0, uint112 _reserve1,) = getReserves();
        uint256 _balance0 = IERC20(token0).balanceOf(address(this));
        uint256 _balance1 = IERC20(token1).balanceOf(address(this));
        uint256 _totalSupply = totalSupply();
        
        amount0 = (liquidity * _balance0) / _totalSupply;
        amount1 = (liquidity * _balance1) / _totalSupply;
        
        require(amount0 >= amount0Min, "HyperSwap: INSUFFICIENT_A_AMOUNT");
        require(amount1 >= amount1Min, "HyperSwap: INSUFFICIENT_B_AMOUNT");

        // --- Effects ---
        _burn(msg.sender, liquidity);
        _update(_balance0 - amount0, _balance1 - amount1, _reserve0, _reserve1);
        if (feeTo != address(0)) {
            _mintFee(_reserve0, _reserve1);
        }

        // --- Interactions ---
        _safeTransfer(token0, to, amount0);
        _safeTransfer(token1, to, amount1);

        emit Burn(msg.sender, to, amount0, amount1);
    }

    /**
     * @notice Swaps an exact amount of input tokens for an amount of output tokens.
     * @param amountIn The exact amount of tokens to send.
     * @param amountOutMin The minimum amount of output tokens to receive (slippage protection).
     * @param path The trading path (must contain 2 tokens: input and output).
     * @param to The address to receive the swapped tokens.
     */
    function swap(
        uint256 amountIn,
        uint256 amountOutMin,
        address[] calldata path,
        address to
    ) external nonReentrant {
        require(path.length == 2, "HyperSwap: INVALID_PATH");
        require(path[0] == token0 || path[0] == token1, "HyperSwap: INVALID_PATH_TOKEN");
        require(path[1] == token0 || path[1] == token1, "HyperSwap: INVALID_PATH_TOKEN");
        require(path[0] != path[1], "HyperSwap: IDENTICAL_PATH_TOKENS");
        
        (uint112 _reserve0, uint112 _reserve1,) = getReserves();

        // Calculate output amount
        uint256 amountOut = getAmountOut(amountIn, path[0]);
        require(amountOut >= amountOutMin, "HyperSwap: INSUFFICIENT_OUTPUT_AMOUNT");

        // Determine amounts for event and update
        (uint amount0In, uint amount1In, uint amount0Out, uint amount1Out) = 
            path[0] == token0 ? (amountIn, 0, 0, amountOut) : (0, amountIn, amountOut, 0);

        // --- Effects ---
        _update(
            _reserve0 + amount0In - amount0Out,
            _reserve1 + amount1In - amount1Out,
            _reserve0,
            _reserve1
        );

        // --- Interactions ---
        _safeTransferFrom(path[0], msg.sender, address(this), amountIn);
        _safeTransfer(path[1], to, amountOut);
        
        emit Swap(msg.sender, to, amount0In, amount1In, amount0Out, amount1Out);
    }

    /**
     * @notice Borrows tokens, executes a callback, and expects repayment with a fee.
     * @param to The address that will receive the tokens and execute the callback.
     * @param amount0Out The amount of token0 to borrow.
     * @param amount1Out The amount of token1 to borrow.
     * @param data Arbitrary data to be passed to the callback.
     */
    function flashSwap(address to, uint256 amount0Out, uint256 amount1Out, bytes calldata data) external nonReentrant lock {
        require(amount0Out > 0 || amount1Out > 0, "HyperSwap: ZERO_OUTPUT");
        (uint112 _reserve0, uint112 _reserve1,) = getReserves();
        require(amount0Out < _reserve0 && amount1Out < _reserve1, "HyperSwap: INSUFFICIENT_LIQUIDITY");

        // --- Optimistically transfer tokens ---
        if (amount0Out > 0) _safeTransfer(token0, to, amount0Out);
        if (amount1Out > 0) _safeTransfer(token1, to, amount1Out);

        // --- Execute callback ---
        IHyperSwapCallee(to).hyperSwapCall(msg.sender, amount0Out, amount1Out, data);

        // --- Verify repayment ---
        uint256 balance0 = IERC20(token0).balanceOf(address(this));
        uint256 balance1 = IERC20(token1).balanceOf(address(this));

        uint256 amount0In = balance0 > _reserve0 - amount0Out ? balance0 - (_reserve0 - amount0Out) : 0;
        uint256 amount1In = balance1 > _reserve1 - amount1Out ? balance1 - (_reserve1 - amount1Out) : 0;
        require(amount0In > 0 || amount1In > 0, "HyperSwap: NO_REPAYMENT");

        uint256 fee0 = 0;
        uint256 fee1 = 0;
        if (amount0Out > 0) fee0 = (amount0Out * FEE_NUMERATOR) / (FEE_DENOMINATOR - FEE_NUMERATOR) + 1;
        if (amount1Out > 0) fee1 = (amount1Out * FEE_NUMERATOR) / (FEE_DENOMINATOR - FEE_NUMERATOR) + 1;
        
        require(amount0In >= fee0, "HyperSwap: INSUFFICIENT_FEE_0");
        require(amount1In >= fee1, "HyperSwap: INSUFFICIENT_FEE_1");

        // --- Effects ---
        _update(balance0, balance1, _reserve0, _reserve1);

        emit Swap(msg.sender, to, amount0In, amount1In, amount0Out, amount1Out);
    }

    // --- Admin Functions ---

    /**
     * @notice Sets the address that will receive protocol fees.
     * @param _feeTo The new fee recipient address.
     */
    function setFeeTo(address _feeTo) external {
        require(msg.sender == feeToSetter, "HyperSwap: FORBIDDEN");
        feeTo = _feeTo;
    }

    /**
     * @notice Sets the address that can change the fee recipient.
     * @param _feeToSetter The new fee setter address.
     */
    function setFeeToSetter(address _feeToSetter) external {
        require(msg.sender == feeToSetter, "HyperSwap: FORBIDDEN");
        feeToSetter = _feeToSetter;
    }

    // --- Internal Helpers ---

    function _safeTransfer(address token, address to, uint256 value) private {
        (bool success, bytes memory data) = token.call(abi.encodeWithSelector(IERC20.transfer.selector, to, value));
        require(success && (data.length == 0 || abi.decode(data, (bool))), "HyperSwap: TRANSFER_FAILED");
    }

    function _safeTransferFrom(address token, address from, address to, uint256 value) private {
        (bool success, bytes memory data) = token.call(abi.encodeWithSelector(IERC20.transferFrom.selector, from, to, value));
        require(success && (data.length == 0 || abi.decode(data, (bool))), "HyperSwap: TRANSFER_FROM_FAILED");
    }
}

// --- Libraries ---

/**
 * @title Math
 * @author Uniswap Labs
 * @notice Small math helper library.
 */
library Math {
    function min(uint256 x, uint256 y) internal pure returns (uint256 z) {
        z = x < y ? x : y;
    }
}

/**
 * @title Babylonian
 * @author Uniswap Labs
 * @notice A library for calculating square roots of uint256.
 */
library Babylonian {
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
}

/**
 * @title UQ112x112
 * @author Uniswap Labs
 * @notice A library for handling Q112.112-format fixed-point numbers.
 */
library UQ112x112 {
    uint224 constant Q112 = 2**112;

    // encode a uint112 as a UQ112x112
    function encode(uint112 y) internal pure returns (uint224 z) {
        z = uint224(y) * Q112;
    }
}