// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "./interfaces/IUniswapV2Pair.sol";
import "./interfaces/IUniswapV2Factory.sol";
import "./interfaces/IERC20.sol";
import "./libraries/Math.sol";
import "./libraries/UQ112x112.sol";

/**
 * @title UniswapV2Pair
 * @dev Uniswap V2 Pair contract for token trading
 * @notice This contract handles the core trading logic for a token pair
 * @author HyperKit Agent
 */
contract UniswapV2Pair is IUniswapV2Pair, ERC20, ReentrancyGuard {
    using UQ112x112 for uint224;
    
    /// @notice Minimum liquidity that must be locked
    uint256 public constant MINIMUM_LIQUIDITY = 10**3;
    
    /// @notice Factory contract address
    address public factory;
    
    /// @notice Token0 address
    address public token0;
    
    /// @notice Token1 address
    address public token1;
    
    /// @notice Reserve0 amount
    uint112 private reserve0;
    
    /// @notice Reserve1 amount
    uint112 private reserve1;
    
    /// @notice Block timestamp of last update
    uint32 private blockTimestampLast;
    
    /// @notice Price0 cumulative last
    uint256 public price0CumulativeLast;
    
    /// @notice Price1 cumulative last
    uint256 public price1CumulativeLast;
    
    /// @notice K last (reserve0 * reserve1)
    uint256 public kLast;
    
    /// @notice Permit typehash
    bytes32 public constant PERMIT_TYPEHASH = keccak256("Permit(address owner,address spender,uint256 value,uint256 nonce,uint256 deadline)");
    
    /// @notice Domain separator for permit
    bytes32 public DOMAIN_SEPARATOR;
    
    /// @notice Nonces for permit
    mapping(address => uint256) public nonces;
    
    /// @notice Events
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
    
    /// @notice Errors
    error InsufficientLiquidityMinted();
    error InsufficientLiquidityBurned();
    error InsufficientOutputAmount();
    error ExcessiveInputAmount();
    error InsufficientLiquidity();
    error InvalidK();
    error Unauthorized();
    error InvalidDeadline();
    error InvalidSignature();
    error IdenticalAddresses();
    error ZeroAddress();
    
    /**
     * @dev Constructor
     */
    constructor() ERC20("Uniswap V2", "UNI-V2") {
        factory = msg.sender;
        
        uint256 chainId;
        assembly {
            chainId := chainid()
        }
        DOMAIN_SEPARATOR = keccak256(
            abi.encode(
                keccak256("EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"),
                keccak256(bytes(name())),
                keccak256(bytes("1")),
                chainId,
                address(this)
            )
        );
    }
    
    /**
     * @notice Initialize the pair
     * @param _token0 First token address
     * @param _token1 Second token address
     */
    function initialize(address _token0, address _token1) external {
        if (msg.sender != factory) revert Unauthorized();
        if (_token0 == _token1) revert IdenticalAddresses();
        if (_token0 == address(0) || _token1 == address(0)) revert ZeroAddress();
        
        token0 = _token0;
        token1 = _token1;
    }
    
    /**
     * @notice Get reserves
     * @return _reserve0 Reserve0 amount
     * @return _reserve1 Reserve1 amount
     * @return _blockTimestampLast Block timestamp of last update
     */
    function getReserves() public view returns (uint112 _reserve0, uint112 _reserve1, uint32 _blockTimestampLast) {
        _reserve0 = reserve0;
        _reserve1 = reserve1;
        _blockTimestampLast = blockTimestampLast;
    }
    
    /**
     * @notice Update reserves
     * @param balance0 Balance of token0
     * @param balance1 Balance of token1
     * @param _reserve0 Reserve0 amount
     * @param _reserve1 Reserve1 amount
     */
    function _update(uint256 balance0, uint256 balance1, uint112 _reserve0, uint112 _reserve1) private {
        require(balance0 <= type(uint112).max && balance1 <= type(uint112).max, "UniswapV2: OVERFLOW");
        uint32 blockTimestamp = uint32(block.timestamp % 2**32);
        uint32 timeElapsed = blockTimestamp - blockTimestampLast;
        
        if (timeElapsed > 0 && _reserve0 != 0 && _reserve1 != 0) {
            price0CumulativeLast += uint256(UQ112x112.encode(_reserve1).uqdiv(_reserve0)) * timeElapsed;
            price1CumulativeLast += uint256(UQ112x112.encode(_reserve0).uqdiv(_reserve1)) * timeElapsed;
        }
        
        reserve0 = uint112(balance0);
        reserve1 = uint112(balance1);
        blockTimestampLast = blockTimestamp;
        emit Sync(reserve0, reserve1);
    }
    
    /**
     * @notice Mint liquidity tokens
     * @param to Address to receive tokens
     * @return liquidity Amount of liquidity tokens minted
     */
    function mint(address to) external nonReentrant returns (uint256 liquidity) {
        (uint112 _reserve0, uint112 _reserve1,) = getReserves();
        uint256 balance0 = IERC20(token0).balanceOf(address(this));
        uint256 balance1 = IERC20(token1).balanceOf(address(this));
        uint256 amount0 = balance0 - _reserve0;
        uint256 amount1 = balance1 - _reserve1;
        
        bool feeOn = _mintFee(_reserve0, _reserve1);
        uint256 _totalSupply = totalSupply();
        
        if (_totalSupply == 0) {
            liquidity = Math.sqrt(amount0 * amount1) - MINIMUM_LIQUIDITY;
            _mint(address(0), MINIMUM_LIQUIDITY); // permanently lock the first MINIMUM_LIQUIDITY tokens
        } else {
            liquidity = Math.min(amount0 * _totalSupply / _reserve0, amount1 * _totalSupply / _reserve1);
        }
        
        if (liquidity == 0) revert InsufficientLiquidityMinted();
        _mint(to, liquidity);
        
        _update(balance0, balance1, _reserve0, _reserve1);
        if (feeOn) kLast = uint256(reserve0) * reserve1;
        
        emit Mint(msg.sender, amount0, amount1);
    }
    
    /**
     * @notice Burn liquidity tokens
     * @param to Address to receive underlying tokens
     * @return amount0 Amount of token0 returned
     * @return amount1 Amount of token1 returned
     */
    function burn(address to) external nonReentrant returns (uint256 amount0, uint256 amount1) {
        (uint112 _reserve0, uint112 _reserve1,) = getReserves();
        address _token0 = token0;
        address _token1 = token1;
        uint256 balance0 = IERC20(_token0).balanceOf(address(this));
        uint256 balance1 = IERC20(_token1).balanceOf(address(this));
        uint256 liquidity = balanceOf(address(this));
        
        bool feeOn = _mintFee(_reserve0, _reserve1);
        uint256 _totalSupply = totalSupply();
        amount0 = liquidity * balance0 / _totalSupply;
        amount1 = liquidity * balance1 / _totalSupply;
        
        if (amount0 == 0 || amount1 == 0) revert InsufficientLiquidityBurned();
        _burn(address(this), liquidity);
        
        _safeTransfer(_token0, to, amount0);
        _safeTransfer(_token1, to, amount1);
        balance0 = IERC20(_token0).balanceOf(address(this));
        balance1 = IERC20(_token1).balanceOf(address(this));
        
        _update(balance0, balance1, _reserve0, _reserve1);
        if (feeOn) kLast = uint256(reserve0) * reserve1;
        
        emit Burn(msg.sender, amount0, amount1, to);
    }
    
    /**
     * @notice Swap tokens
     * @param amount0Out Amount of token0 to output
     * @param amount1Out Amount of token1 to output
     * @param to Address to receive output tokens
     * @param data Additional data
     */
    function swap(uint256 amount0Out, uint256 amount1Out, address to, bytes calldata data) external nonReentrant {
        if (amount0Out == 0 && amount1Out == 0) revert InsufficientOutputAmount();
        (uint112 _reserve0, uint112 _reserve1,) = getReserves();
        if (amount0Out >= _reserve0 || amount1Out >= _reserve1) revert InsufficientLiquidity();
        
        uint256 balance0;
        uint256 balance1;
        {
            address _token0 = token0;
            address _token1 = token1;
            if (to == _token0 || to == _token1) revert Unauthorized();
            if (amount0Out > 0) _safeTransfer(_token0, to, amount0Out);
            if (amount1Out > 0) _safeTransfer(_token1, to, amount1Out);
            if (data.length > 0) IUniswapV2Callee(to).uniswapV2Call(msg.sender, amount0Out, amount1Out, data);
            balance0 = IERC20(_token0).balanceOf(address(this));
            balance1 = IERC20(_token1).balanceOf(address(this));
        }
        
        uint256 amount0In = balance0 > _reserve0 - amount0Out ? balance0 - (_reserve0 - amount0Out) : 0;
        uint256 amount1In = balance1 > _reserve1 - amount1Out ? balance1 - (_reserve1 - amount1Out) : 0;
        if (amount0In == 0 && amount1In == 0) revert InsufficientOutputAmount();
        
        {
            uint256 balance0Adjusted = balance0 * 1000 - amount0In * 3;
            uint256 balance1Adjusted = balance1 * 1000 - amount1In * 3;
            if (balance0Adjusted * balance1Adjusted < uint256(_reserve0) * _reserve1 * 1000**2) revert InvalidK();
        }
        
        _update(balance0, balance1, _reserve0, _reserve1);
        emit Swap(msg.sender, amount0In, amount1In, amount0Out, amount1Out, to);
    }
    
    /**
     * @notice Sync reserves
     */
    function sync() external nonReentrant {
        _update(IERC20(token0).balanceOf(address(this)), IERC20(token1).balanceOf(address(this)), reserve0, reserve1);
    }
    
    /**
     * @notice Skim excess tokens
     * @param to Address to receive excess tokens
     */
    function skim(address to) external nonReentrant {
        address _token0 = token0;
        address _token1 = token1;
        _safeTransfer(_token0, to, IERC20(_token0).balanceOf(address(this)) - reserve0);
        _safeTransfer(_token1, to, IERC20(_token1).balanceOf(address(this)) - reserve1);
    }
    
    /**
     * @notice Mint fee if applicable
     * @param _reserve0 Reserve0 amount
     * @param _reserve1 Reserve1 amount
     * @return feeOn True if fee was minted
     */
    function _mintFee(uint112 _reserve0, uint112 _reserve1) private returns (bool feeOn) {
        address feeTo = IUniswapV2Factory(factory).feeTo();
        feeOn = feeTo != address(0);
        uint256 _kLast = kLast;
        if (feeOn) {
            if (_kLast != 0) {
                uint256 rootK = Math.sqrt(uint256(_reserve0) * _reserve1);
                uint256 rootKLast = Math.sqrt(_kLast);
                if (rootK > rootKLast) {
                    uint256 numerator = totalSupply() * (rootK - rootKLast);
                    uint256 denominator = rootK * 5 + rootKLast;
                    uint256 liquidity = numerator / denominator;
                    if (liquidity > 0) _mint(feeTo, liquidity);
                }
            }
        } else if (_kLast != 0) {
            kLast = 0;
        }
    }
    
    /**
     * @notice Safe transfer helper
     * @param token Token address
     * @param to Recipient address
     * @param value Amount to transfer
     */
    function _safeTransfer(address token, address to, uint256 value) private {
        (bool success, bytes memory data) = token.call(abi.encodeWithSelector(0xa9059cbb, to, value));
        require(success && (data.length == 0 || abi.decode(data, (bool))), "UniswapV2: TRANSFER_FAILED");
    }
    
    /**
     * @notice Permit function for gasless approvals
     * @param owner Token owner
     * @param spender Spender address
     * @param value Amount to approve
     * @param deadline Deadline for permit
     * @param v Signature v
     * @param r Signature r
     * @param s Signature s
     */
    function permit(address owner, address spender, uint256 value, uint256 deadline, uint8 v, bytes32 r, bytes32 s) external {
        if (block.timestamp > deadline) revert InvalidDeadline();
        bytes32 structHash = keccak256(abi.encode(PERMIT_TYPEHASH, owner, spender, value, nonces[owner]++, deadline));
        bytes32 hash = keccak256(abi.encodePacked("\x19\x01", DOMAIN_SEPARATOR, structHash));
        address signer = ecrecover(hash, v, r, s);
        if (signer == address(0) || signer != owner) revert InvalidSignature();
        _approve(owner, spender, value);
    }
}

interface IUniswapV2Callee {
    function uniswapV2Call(address sender, uint256 amount0, uint256 amount1, bytes calldata data) external;
}
