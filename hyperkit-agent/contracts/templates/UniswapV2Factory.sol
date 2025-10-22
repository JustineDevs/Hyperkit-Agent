// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "./interfaces/IUniswapV2Factory.sol";
import "./interfaces/IUniswapV2Pair.sol";

/**
 * @title UniswapV2Factory
 * @dev Factory contract for creating Uniswap V2 pairs
 * @notice This contract creates and manages Uniswap V2 trading pairs
 * @author HyperKit Agent
 */
contract UniswapV2Factory is IUniswapV2Factory, Ownable, ReentrancyGuard {
    /// @notice Fee to setter address
    address public feeTo;
    
    /// @notice Fee setter address
    address public feeToSetter;
    
    /// @notice Protocol fee denominator
    uint256 public constant FEE_DENOMINATOR = 10000;
    
    /// @notice Protocol fee numerator (default 0.3%)
    uint256 public protocolFeeNumerator = 30;
    
    /// @notice Mapping from token pair to pair address
    mapping(address => mapping(address => address)) public getPair;
    
    /// @notice Array of all pairs
    address[] public allPairs;
    
    /// @notice Mapping to check if address is a pair
    mapping(address => bool) public isPair;
    
    /// @notice Pair creation code hash
    bytes32 public immutable pairCodeHash;
    
    /// @notice Maximum number of pairs allowed
    uint256 public maxPairs = 1000;
    
    /// @notice Pair creation fee (in wei)
    uint256 public pairCreationFee = 0;
    
    /// @notice Events
    event PairCreated(address indexed token0, address indexed token1, address pair, uint256);
    event FeeToUpdated(address indexed oldFeeTo, address indexed newFeeTo);
    event FeeToSetterUpdated(address indexed oldFeeToSetter, address indexed newFeeToSetter);
    event ProtocolFeeUpdated(uint256 oldNumerator, uint256 newNumerator);
    event PairCreationFeeUpdated(uint256 oldFee, uint256 newFee);
    event MaxPairsUpdated(uint256 oldMax, uint256 newMax);
    
    /// @notice Errors
    error IdenticalAddresses();
    error ZeroAddress();
    error PairExists();
    error PairNotExists();
    error MaxPairsExceeded();
    error InvalidFeeNumerator();
    error OnlyFeeToSetter();
    error OnlyPair();
    error InvalidFeeToSetter();
    
    /**
     * @dev Constructor
     * @param _feeToSetter Address that can set feeTo
     */
    constructor(address _feeToSetter) {
        if (_feeToSetter == address(0)) revert ZeroAddress();
        feeToSetter = _feeToSetter;
        pairCodeHash = keccak256(type(UniswapV2Pair).creationCode);
    }
    
    /**
     * @notice Get the number of pairs
     * @return Number of pairs
     */
    function allPairsLength() external view returns (uint256) {
        return allPairs.length;
    }
    
    /**
     * @notice Create a pair for two tokens
     * @param tokenA First token address
     * @param tokenB Second token address
     * @return pair Address of the created pair
     */
    function createPair(address tokenA, address tokenB) 
        external 
        payable 
        nonReentrant 
        returns (address pair) 
    {
        if (tokenA == tokenB) revert IdenticalAddresses();
        if (tokenA == address(0) || tokenB == address(0)) revert ZeroAddress();
        
        // Ensure tokenA < tokenB for consistent pair ordering
        (address token0, address token1) = tokenA < tokenB ? (tokenA, tokenB) : (tokenB, tokenA);
        
        if (token0 == address(0)) revert ZeroAddress();
        if (getPair[token0][token1] != address(0)) revert PairExists();
        
        if (allPairs.length >= maxPairs) revert MaxPairsExceeded();
        
        // Check pair creation fee
        if (msg.value < pairCreationFee) {
            revert("Insufficient pair creation fee");
        }
        
        // Create pair contract
        bytes32 salt = keccak256(abi.encodePacked(token0, token1));
        pair = address(new UniswapV2Pair{salt: salt}());
        
        // Initialize pair
        IUniswapV2Pair(pair).initialize(token0, token1);
        
        // Update mappings
        getPair[token0][token1] = pair;
        getPair[token1][token0] = pair; // Populate reverse mapping
        allPairs.push(pair);
        isPair[pair] = true;
        
        emit PairCreated(token0, token1, pair, allPairs.length);
        
        // Refund excess payment
        if (msg.value > pairCreationFee) {
            payable(msg.sender).transfer(msg.value - pairCreationFee);
        }
    }
    
    /**
     * @notice Set the fee recipient address
     * @param _feeTo New fee recipient address
     */
    function setFeeTo(address _feeTo) external {
        if (msg.sender != feeToSetter) revert OnlyFeeToSetter();
        address oldFeeTo = feeTo;
        feeTo = _feeTo;
        emit FeeToUpdated(oldFeeTo, _feeTo);
    }
    
    /**
     * @notice Set the fee setter address
     * @param _feeToSetter New fee setter address
     */
    function setFeeToSetter(address _feeToSetter) external {
        if (msg.sender != feeToSetter) revert OnlyFeeToSetter();
        if (_feeToSetter == address(0)) revert InvalidFeeToSetter();
        address oldFeeToSetter = feeToSetter;
        feeToSetter = _feeToSetter;
        emit FeeToSetterUpdated(oldFeeToSetter, _feeToSetter);
    }
    
    /**
     * @notice Set the protocol fee numerator
     * @param _protocolFeeNumerator New protocol fee numerator
     */
    function setProtocolFeeNumerator(uint256 _protocolFeeNumerator) external onlyOwner {
        if (_protocolFeeNumerator > FEE_DENOMINATOR) revert InvalidFeeNumerator();
        uint256 oldNumerator = protocolFeeNumerator;
        protocolFeeNumerator = _protocolFeeNumerator;
        emit ProtocolFeeUpdated(oldNumerator, _protocolFeeNumerator);
    }
    
    /**
     * @notice Set the pair creation fee
     * @param _pairCreationFee New pair creation fee
     */
    function setPairCreationFee(uint256 _pairCreationFee) external onlyOwner {
        uint256 oldFee = pairCreationFee;
        pairCreationFee = _pairCreationFee;
        emit PairCreationFeeUpdated(oldFee, _pairCreationFee);
    }
    
    /**
     * @notice Set the maximum number of pairs
     * @param _maxPairs New maximum number of pairs
     */
    function setMaxPairs(uint256 _maxPairs) external onlyOwner {
        uint256 oldMax = maxPairs;
        maxPairs = _maxPairs;
        emit MaxPairsUpdated(oldMax, _maxPairs);
    }
    
    /**
     * @notice Get pair address for two tokens
     * @param tokenA First token address
     * @param tokenB Second token address
     * @return pair Address of the pair
     */
    function getPairAddress(address tokenA, address tokenB) external view returns (address pair) {
        (address token0, address token1) = tokenA < tokenB ? (tokenA, tokenB) : (tokenB, tokenA);
        return getPair[token0][token1];
    }
    
    /**
     * @notice Check if a pair exists for two tokens
     * @param tokenA First token address
     * @param tokenB Second token address
     * @return exists True if pair exists
     */
    function pairExists(address tokenA, address tokenB) external view returns (bool exists) {
        (address token0, address token1) = tokenA < tokenB ? (tokenA, tokenB) : (tokenB, tokenA);
        return getPair[token0][token1] != address(0);
    }
    
    /**
     * @notice Get all pairs in a range
     * @param start Starting index
     * @param end Ending index
     * @return pairs Array of pair addresses
     */
    function getPairsInRange(uint256 start, uint256 end) 
        external 
        view 
        returns (address[] memory pairs) 
    {
        require(start <= end, "Invalid range");
        require(end < allPairs.length, "End index out of bounds");
        
        uint256 length = end - start + 1;
        pairs = new address[](length);
        
        for (uint256 i = 0; i < length; i++) {
            pairs[i] = allPairs[start + i];
        }
    }
    
    /**
     * @notice Emergency function to pause pair creation
     */
    function emergencyPause() external onlyOwner {
        _pause();
    }
    
    /**
     * @notice Emergency function to unpause pair creation
     */
    function emergencyUnpause() external onlyOwner {
        _unpause();
    }
    
    /**
     * @notice Withdraw accumulated fees
     */
    function withdrawFees() external onlyOwner {
        uint256 balance = address(this).balance;
        if (balance > 0) {
            payable(owner()).transfer(balance);
        }
    }
    
    /**
     * @notice Get factory information
     * @return _feeTo Current fee recipient
     * @return _feeToSetter Current fee setter
     * @return _protocolFeeNumerator Current protocol fee numerator
     * @return _pairCreationFee Current pair creation fee
     * @return _maxPairs Current maximum pairs
     * @return _totalPairs Current total pairs
     */
    function getFactoryInfo() external view returns (
        address _feeTo,
        address _feeToSetter,
        uint256 _protocolFeeNumerator,
        uint256 _pairCreationFee,
        uint256 _maxPairs,
        uint256 _totalPairs
    ) {
        return (
            feeTo,
            feeToSetter,
            protocolFeeNumerator,
            pairCreationFee,
            maxPairs,
            allPairs.length
        );
    }
}
