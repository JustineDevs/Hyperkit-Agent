// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";

/**
 * @title IWrappedToken
 * @dev Interface for a token that is mintable and burnable, controlled by the bridge.
 */
interface IWrappedToken is IERC20 {
    function mint(address to, uint256 amount) external;
    function burnFrom(address from, uint256 amount) external;
}

/**
 * @title CrossChainBridge
 * @author Your Name
 * @notice A contract to bridge an ERC20 token between Metis and Hyperion.
 * @dev This contract facilitates cross-chain transfers using a 3-of-5 validator multisig.
 *      On the source chain (Metis), it locks the original LINK token.
 *      On the destination chain (Hyperion), it mints/burns a wrapped version of the token.
 *      The process is reversed for bridging from Hyperion back to Metis.
 */
contract CrossChainBridge is Ownable, Pausable, ReentrancyGuard {
    using ECDSA for bytes32;

    // --- Events ---

    /**
     * @notice Emitted when a user initiates a transfer to the other chain.
     * @param from The address initiating the bridge transfer.
     * @param to The recipient address on the destination chain.
     * @param amount The gross amount of tokens being bridged.
     * @param amountAfterFee The net amount the recipient will receive.
     * @param nonce The sender-specific nonce for this transfer.
     * @param fromChainId The source chain ID.
     * @param toChainId The destination chain ID.
     */
    event BridgeInitiated(
        address indexed from,
        address to,
        uint256 amount,
        uint256 amountAfterFee,
        uint256 nonce,
        uint256 fromChainId,
        uint256 toChainId
    );

    /**
     * @notice Emitted when a user successfully claims their tokens on the destination chain.
     * @param from The original sender's address on the source chain.
     * @param to The recipient's address on the destination chain.
     * @param amount The net amount of tokens claimed.
     * @param nonce The nonce of the original bridge transaction.
     * @param fromChainId The source chain ID of the original transaction.
     */
    event BridgeClaimed(
        address indexed from,
        address indexed to,
        uint256 amount,
        uint256 nonce,
        uint256 fromChainId
    );

    /**
     * @notice Emitted when a new validator is added.
     * @param validator The address of the new validator.
     */
    event ValidatorAdded(address indexed validator);

    /**
     * @notice Emitted when a validator is removed.
     * @param validator The address of the removed validator.
     */
    event ValidatorRemoved(address indexed validator);

    /**
     * @notice Emitted when the bridge fee is updated.
     * @param newFeeBps The new fee in basis points.
     */
    event FeeUpdated(uint256 newFeeBps);

    // --- Custom Errors ---

    error ZeroAddress();
    error InvalidAmount();
    error ExceedsMaxLimit();
    error BelowMinLimit();
    error InvalidDestinationChain();
    error InsufficientSignatures();
    error AlreadyClaimed();
    error NotAValidator();
    error DuplicateSignature();
    error ValidatorAlreadyExists();
    error ValidatorNotFound();
    error MaxValidatorsReached();
    error NotEnoughValidators();
    error InvalidFee();
    error InsufficientAllowance();
    error InvalidSignature();

    // --- State Variables ---

    /// @notice The ERC20 token this bridge manages.
    IERC20 public immutable token;

    /// @notice The chain ID for Metis (e.g., 1088).
    uint256 public immutable metisChainId;

    /// @notice The chain ID for Hyperion (e.g., 133717).
    uint256 public immutable hyperionChainId;

    /// @notice Mapping to check if an address is a validator.
    mapping(address => bool) public isValidator;
    /// @notice Array of current validator addresses.
    address[] public validators;

    /// @notice The minimum number of validator signatures required to claim tokens.
    uint256 public constant REQUIRED_SIGNATURES = 3;
    /// @notice The maximum number of validators allowed in the set.
    uint256 public constant MAX_VALIDATORS = 5;

    /// @notice The bridge fee in basis points (e.g., 50 for 0.5%).
    uint256 public feeBps;
    /// @notice The maximum amount of tokens that can be bridged in a single transaction.
    uint256 public maxTransfer;
    /// @notice The minimum amount of tokens that can be bridged in a single transaction.
    uint256 public minTransfer;

    /// @notice Per-user nonce to prevent replay attacks on bridge initiation.
    mapping(address => uint256) public userNonces;
    /// @notice Mapping to track processed claims to prevent replay attacks.
    mapping(bytes32 => bool) public processedClaims;


    /**
     * @notice Sets up the bridge contract with initial parameters.
     * @param _token The address of the ERC20 token to bridge (LINK on Metis, Wrapped LINK on Hyperion).
     * @param _initialValidators An array of exactly 5 initial validator addresses.
     * @param _metisChainId The chain ID for the Metis network.
     * @param _hyperionChainId The chain ID for the Hyperion network.
     */
    constructor(
        address _token,
        address[] memory _initialValidators,
        uint256 _metisChainId,
        uint256 _hyperionChainId
    ) {
        if (_token == address(0)) revert ZeroAddress();
        if (_initialValidators.length != MAX_VALIDATORS) revert NotEnoughValidators();

        token = IERC20(_token);
        metisChainId = _metisChainId;
        hyperionChainId = _hyperionChainId;

        // Set initial parameters based on user request
        feeBps = 50; // 0.5%
        maxTransfer = 1_000_000 * 10**18;
        minTransfer = 100 * 10**18;

        for (uint256 i = 0; i < _initialValidators.length; i++) {
            address validator = _initialValidators[i];
            if (validator == address(0)) revert ZeroAddress();
            if (isValidator[validator]) revert ValidatorAlreadyExists();
            isValidator[validator] = true;
            validators.push(validator);
            emit ValidatorAdded(validator);
        }
    }

    /**
     * @notice Initiates a token transfer to the other chain.
     * @dev On Metis, this locks the user's LINK tokens in the contract.
     *      On Hyperion, this burns the user's wrapped LINK tokens.
     *      User must approve this contract to spend their tokens before calling.
     * @param _to The recipient address on the destination chain.
     * @param _amount The amount of tokens to bridge (in wei).
     * @param _destinationChainId The chain ID of the destination network.
     */
    function bridge(address _to, uint256 _amount, uint256 _destinationChainId)
        external
        whenNotPaused
        nonReentrant
    {
        if (_to == address(0)) revert ZeroAddress();
        if (_amount > maxTransfer) revert ExceedsMaxLimit();
        if (_amount < minTransfer) revert BelowMinLimit();

        uint256 sourceChainId = block.chainid;
        if (
            !((sourceChainId == metisChainId && _destinationChainId == hyperionChainId) ||
              (sourceChainId == hyperionChainId && _destinationChainId == metisChainId))
        ) {
            revert InvalidDestinationChain();
        }

        uint256 feeAmount = (_amount * feeBps) / 10000;
        if (feeAmount >= _amount) revert InvalidAmount();
        uint256 amountAfterFee = _amount - feeAmount;

        address from = msg.sender;
        uint256 nonce = userNonces[from]++;

        if (sourceChainId == metisChainId) {
            // Lock original LINK tokens
            if (token.allowance(from, address(this)) < _amount) revert InsufficientAllowance();
            token.transferFrom(from, address(this), _amount);
        } else { // On Hyperion
            // Burn wrapped LINK tokens
            if (token.allowance(from, address(this)) < _amount) revert InsufficientAllowance();
            IWrappedToken(address(token)).burnFrom(from, _amount);
        }

        emit BridgeInitiated(from, _to, _amount, amountAfterFee, nonce, sourceChainId, _destinationChainId);
    }

    /**
     * @notice Claims tokens on the destination chain using validator signatures.
     * @dev On Metis, this unlocks original LINK tokens. On Hyperion, this mints wrapped LINK tokens.
     * @param _from The original sender address on the source chain.
     * @param _to The recipient address on this destination chain.
     * @param _amount The original amount bridged (before fee).
     * @param _nonce The nonce of the bridge transaction from the source chain.
     * @param _sourceChainId The chain ID of the source chain.
     * @param _signatures An array of signatures from the validators.
     */
    function claim(
        address _from,
        address _to,
        uint256 _amount,
        uint256 _nonce,
        uint256 _sourceChainId,
        bytes[] calldata _signatures
    ) external whenNotPaused nonReentrant {
        if (_signatures.length < REQUIRED_SIGNATURES) revert InsufficientSignatures();

        bytes32 messageHash = getMessageHash(_from, _to, _amount, _nonce, _sourceChainId, block.chainid);
        if (processedClaims[messageHash]) revert AlreadyClaimed();

        mapping(address => bool) private hasSigned;
        uint256 validSignatureCount = 0;

        for (uint256 i = 0; i < _signatures.length; i++) {
            address signer = messageHash.toEthSignedMessageHash().recover(_signatures[i]);
            if (signer == address(0)) revert InvalidSignature();

            if (isValidator[signer] && !hasSigned[signer]) {
                hasSigned[signer] = true;
                validSignatureCount++;
            }
        }

        if (validSignatureCount < REQUIRED_SIGNATURES) revert InsufficientSignatures();

        processedClaims[messageHash] = true;

        uint256 feeAmount = (_amount * feeBps) / 10000;
        if (feeAmount >= _amount) revert InvalidAmount();
        uint256 amountToClaim = _amount - feeAmount;

        if (block.chainid == hyperionChainId) {
            // Mint wrapped LINK tokens
            IWrappedToken(address(token)).mint(_to, amountToClaim);
        } else { // On Metis
            // Unlock original LINK tokens
            token.transfer(_to, amountToClaim);
        }

        emit BridgeClaimed(_from, _to, amountToClaim, _nonce, _sourceChainId);
    }

    // --- Admin Functions ---

    /**
     * @notice Adds a new validator. Can only be called by the owner.
     * @param _validator The address of the new validator.
     */
    function addValidator(address _validator) external onlyOwner {
        if (_validator == address(0)) revert ZeroAddress();
        if (isValidator[_validator]) revert ValidatorAlreadyExists();
        if (validators.length >= MAX_VALIDATORS) revert MaxValidatorsReached();

        isValidator[_validator] = true;
        validators.push(_validator);
        emit ValidatorAdded(_validator);
    }

    /**
     * @notice Removes an existing validator. Can only be called by the owner.
     * @param _validator The address of the validator to remove.
     */
    function removeValidator(address _validator) external onlyOwner {
        if (!isValidator[_validator]) revert ValidatorNotFound();
        if (validators.length - 1 < REQUIRED_SIGNATURES) revert NotEnoughValidators();

        isValidator[_validator] = false;

        for (uint256 i = 0; i < validators.length; i++) {
            if (validators[i] == _validator) {
                validators[i] = validators[validators.length - 1];
                validators.pop();
                break;
            }
        }

        emit ValidatorRemoved(_validator);
    }

    /**
     * @notice Updates the bridge fee. Can only be called by the owner.
     * @param _newFeeBps The new fee in basis points. Must be less than 1000 (10%).
     */
    function updateFee(uint256 _newFeeBps) external onlyOwner {
        if (_newFeeBps >= 1000) revert InvalidFee(); // Max fee of 10%
        feeBps = _newFeeBps;
        emit FeeUpdated(_newFeeBps);
    }

    /**
     * @notice Pauses bridge operations (`bridge` and `claim`). Can only be called by the owner.
     */
    function pause() external onlyOwner {
        _pause();
    }

    /**
     * @notice Resumes bridge operations. Can only be called by the owner.
     */
    function unpause() external onlyOwner {
        _unpause();
    }

    /**
     * @notice Withdraws accumulated fees from the contract.
     * @dev Fees accumulate as leftover original tokens (e.g., LINK on Metis) in this contract.
     *      This function allows the owner to transfer them out.
     * @param _to The address to receive the withdrawn fees.
     */
    function withdrawFees(address _to) external onlyOwner {
        if (_to == address(0)) revert ZeroAddress();
        // This simple implementation withdraws the entire token balance of the contract.
        // It's effective on the "lock/unlock" side (Metis) where fees accumulate.
        uint256 balance = token.balanceOf(address(this));
        if (balance > 0) {
            token.transfer(_to, balance);
        }
    }

    // --- View Functions ---

    /**
     * @notice Constructs the hash of the message to be signed by validators.
     * @param _from The original sender address on the source chain.
     * @param _to The recipient address on the destination chain.
     * @param _amount The original amount bridged (before fee).
     * @param _nonce The nonce of the bridge transaction on the source chain.
     * @param _sourceChainId The chain ID of the source chain.
     * @param _destinationChainId The chain ID of the destination chain (current chain).
     * @return The EIP-191 compliant hash of the packed data.
     */
    function getMessageHash(
        address _from,
        address _to,
        uint256 _amount,
        uint256 _nonce,
        uint256 _sourceChainId,
        uint256 _destinationChainId
    ) public pure returns (bytes32) {
        return keccak256(
            abi.encodePacked(
                _from,
                _to,
                _amount,
                _nonce,
                _sourceChainId,
                _destinationChainId
            )
        );
    }

    /**
     * @notice Returns the list of current validator addresses.
     */
    function getValidators() external view returns (address[] memory) {
        return validators;
    }
}

/**
 * @title WrappedERC20
 * @author Your Name
 * @notice An ERC20 token for the destination chain (Hyperion).
 * @dev This token is mintable only by its owner (the bridge contract) and burnable by its holders.
 *      It should be deployed on Hyperion, and its ownership transferred to the bridge contract.
 */
contract WrappedERC20 is ERC20, ERC20Burnable, Ownable {
    /**
     * @notice Deploys the wrapped token contract.
     * @param name The name of the token (e.g., "Wrapped LINK on Hyperion").
     * @param symbol The symbol of the token (e.g., "hLINK").
     */
    constructor(string memory name, string memory symbol) ERC20(name, symbol) Ownable(msg.sender) {}

    /**
     * @notice Mints new tokens. Can only be called by the owner (the bridge).
     * @param to The address to receive the new tokens.
     * @param amount The amount of tokens to mint.
     */
    function mint(address to, uint256 amount) public virtual onlyOwner {
        _mint(to, amount);
    }

    /**
     * @notice Overrides the standard `burnFrom` to make it callable only by the owner.
     * @dev This ensures that only the bridge contract can initiate burns as part of the bridge-back process.
     * @param from The address whose tokens are to be burned.
     * @param amount The amount of tokens to burn.
     */
    function burnFrom(address from, uint256 amount) public override onlyOwner {
        _spendAllowance(from, owner(), amount);
        _burn(from, amount);
    }
}