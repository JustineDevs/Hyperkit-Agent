pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/utils/structs/EnumerableSet.sol";


// --- Interfaces ---
interface IBridge {
    function burn(address _to, uint256 _amount, uint256 _nonce, bytes calldata _signature) external;
    function claim(address _to, uint256 _amount, uint256 _nonce, bytes calldata _signature) external;
}


// --- Events ---
event BridgeInitiated(address indexed sender, uint256 amount, uint256 nonce);
event BridgeClaimed(address indexed receiver, uint256 amount, uint256 nonce, address indexed validator);
event GovernanceAction(string action, address[] targets, uint256 value, bytes[] data);
event Paused(address account);
event Unpaused(address account);
event DailyMintCapChanged(uint256 newCap);
event ValidatorAdded(address validator);
event ValidatorRemoved(address validator);


// --- Errors ---
error InvalidSignature();
error InvalidNonce();
error DailyMintCapExceeded();
error NotValidator();
error AlreadyBridged();
error Unauthorized();
error InvalidProposalState();


contract CrossChainToken is ERC20, Ownable, Pausable {
    using EnumerableSet for EnumerableSet.AddressSet;

    // --- State Variables ---
    uint8 public constant VERSION = 1;
    uint256 public dailyMintCap; // Daily mint cap
    uint256 public dailyMinted; // Amount minted today
    uint256 public lastMintReset; // Timestamp of the last daily mint reset
    uint256 private _nonceCounter; // Nonce tracking
    mapping(uint256 => bool) public usedNonces; // Track used nonces
    EnumerableSet.AddressSet private _validators; // Set of valid bridge validators
    address[] public validatorList;
    address public immutable multisig; // Multi-signature contract address
    uint256 public constant requiredSignatures = 3;


    // --- Constructor ---
    constructor(
        string memory _name,
        string memory _symbol,
        uint256 _initialSupply,
        address _multisig,
        uint256 _dailyMintCap,
        address[] memory _initialValidators
    ) ERC20(_name, _symbol) Ownable(msg.sender) {
        _mint(msg.sender, _initialSupply);
        multisig = _multisig;
        dailyMintCap = _dailyMintCap;
        lastMintReset = block.timestamp;

        // Initialize validators
        for (uint256 i = 0; i < _initialValidators.length; i++) {
            _addValidator(_initialValidators[i]);
        }
    }


    // --- Modifiers ---
    modifier onlyValidator() {
        if (!_validators.contains(msg.sender)) {
            revert NotValidator();
        }
        _;
    }

    modifier onlyMultisig() {
        if (msg.sender != multisig) {
            revert Unauthorized();
        }
        _;
    }

    // --- Core Bridge Functions ---

    /**
     * @dev Burns tokens on the source chain, initiating a bridge transfer.
     * @param _amount The amount of tokens to burn.
     */
    function burn(uint256 _amount) external {
        require(_amount > 0, "Amount must be greater than 0");
        _burn(msg.sender, _amount);
        uint256 nonce = _nonceCounter;
        _nonceCounter++;
        emit BridgeInitiated(msg.sender, _amount, nonce);
    }


    /**
     * @dev Claims tokens on the destination chain based on a signed message.
     * @param _to The address to mint tokens to.
     * @param _amount The amount of tokens to mint.
     * @param _nonce The unique nonce of the bridge transfer.
     * @param _signature The signature from the validators.
     */
    function claim(address _to, uint256 _amount, uint256 _nonce, bytes calldata _signature) external {
        require(_amount > 0, "Amount must be greater than 0");
        require(!usedNonces[_nonce], "Nonce already used");
        _validateAndMint(_to, _amount, _nonce, _signature);
    }



    /**
     * @dev Batch claims tokens on the destination chain based on a list of signed messages.
     * @param _claims An array of claim data.  Each element is a struct containing claim details.
     */
    function batchClaim(ClaimData[] calldata _claims) external {
        for (uint256 i = 0; i < _claims.length; i++) {
            ClaimData memory claim = _claims[i];
            require(claim.amount > 0, "Amount must be greater than 0");
            require(!usedNonces[claim.nonce], "Nonce already used");
        }

        for (uint256 i = 0; i < _claims.length; i++) {
            ClaimData memory claim = _claims[i];
            _validateAndMint(claim.to, claim.amount, claim.nonce, claim.signature);
        }
    }


    /**
     * @dev Internal function to validate the signature and mint tokens.
     * @param _to The address to mint tokens to.
     * @param _amount The amount of tokens to mint.
     * @param _nonce The unique nonce of the bridge transfer.
     * @param _signature The signature from the validators.
     */
    function _validateAndMint(address _to, uint256 _amount, uint256 _nonce, bytes calldata _signature) private {

        bytes32 messageHash = keccak256(abi.encodePacked(address(this), _to, _amount, _nonce));
        bytes32 ethSignedMessageHash = keccak256(abi.encodePacked("\x19Ethereum Signed Message:\n32", messageHash));
        address recoveredAddress = _recoverSigner(ethSignedMessageHash, _signature);
        require(_validators.contains(recoveredAddress), "Invalid signature from invalid validator");

        _mint(_to, _amount);
        usedNonces[_nonce] = true;
        dailyMinted = (dailyMinted + _amount);
        emit BridgeClaimed(_to, _amount, _nonce, recoveredAddress);
    }

    // --- Helper function for signature recovery (uses single signer in this example, but it's extensible) ---
    function _recoverSigner(bytes32 _messageHash, bytes calldata _signature) private view returns (address) {
        (uint8 v, bytes32 r, bytes32 s) = _splitSignature(_signature);
        return ecrecover(_messageHash, v, r, s);
    }


    // Function to split a signature into its components
    function _splitSignature(bytes memory sig) private pure returns (uint8 v, bytes32 r, bytes32 s) {
        require(sig.length == 65, "Invalid signature length");
        assembly {
            r := mload(add(sig, 32))
            s := mload(add(sig, 64))
            v := byte(0, mload(add(sig, 96)))
        }
    }



    // --- Governance Functions (via MultiSig) ---

    /**
     * @dev Pauses the contract.  Callable only via MultiSig.
     */
    function pause() external onlyMultisig {
        _pause();
        emit Paused(msg.sender);
    }

    /**
     * @dev Unpauses the contract. Callable only via MultiSig.
     */
    function unpause() external onlyMultisig {
        _unpause();
        emit Unpaused(msg.sender);
    }

    /**
     * @dev Sets the daily mint cap. Callable only via MultiSig.
     * @param _newCap The new daily mint cap.
     */
    function setDailyMintCap(uint256 _newCap) external onlyMultisig {
        dailyMintCap = _newCap;
        emit DailyMintCapChanged(_newCap);
    }


    /**
     * @dev Adds a validator. Callable only via MultiSig.
     * @param _validator The address of the validator to add.
     */
    function addValidator(address _validator) external onlyMultisig {
        _addValidator(_validator);
        emit ValidatorAdded(_validator);
    }


    /**
     * @dev Removes a validator. Callable only via MultiSig.
     * @param _validator The address of the validator to remove.
     */
    function removeValidator(address _validator) external onlyMultisig {
        _removeValidator(_validator);
        emit ValidatorRemoved(_validator);
    }

    /**
     * @dev Executes a generic governance action. Callable only via MultiSig.
     * @param _targets An array of target addresses.
     * @param _values An array of values for each target.
     * @param _data An array of calldata for each target.
     */
    function executeGovernanceAction(address[] calldata _targets, uint256[] calldata _values, bytes[] calldata _data) external onlyMultisig {
        require(_targets.length == _values.length && _targets.length == _data.length, "Invalid array lengths");
        for (uint256 i = 0; i < _targets.length; i++) {
            (bool success, ) = _targets[i].call{value: _values[i]}(_data[i]);
            require(success, "Governance action failed");
        }
        emit GovernanceAction("Execute", _targets, 0, _data); // No values passed in event
    }



    // --- Internal helper functions for governance actions ---
    function _addValidator(address _validator) internal {
        require(_validator != address(0), "Invalid validator address");
        require(!_validators.contains(_validator), "Validator already added");
        (_validators + _validator);
        validatorList.push(_validator);
    }

    function _removeValidator(address _validator) internal {
        require(_validator != address(0), "Invalid validator address");
        require(_validators.contains(_validator), "Validator not found");
        _validators.remove(_validator);

        for (uint256 i = 0; i < validatorList.length; i++) {
            if (validatorList[i] == _validator) {
                validatorList[i] = validatorList[validatorList.length - 1]; // Replace with the last element
                validatorList.pop();
                break;
            }
        }
    }


    // --- View Functions ---
    /**
     * @dev Returns the remaining mintable tokens for the current day.
     * @return The remaining tokens.
     */
    function getRemainingMint() external view returns (uint256) {
        if (block.timestamp > lastMintReset) {
            return (dailyMintCap - dailyMinted);
        }
        return (dailyMintCap - dailyMinted); // Consider dailyMinted to be 0 at the start of the day
    }

    // --- Utility Functions ---
    function resetDailyMint() external {
        if (block.timestamp > lastMintReset) {
            dailyMinted = 0;
            lastMintReset = block.timestamp;
        }
    }

    function isValidator(address _address) external view returns (bool) {
        return _validators.contains(_address);
    }


    // --- Structs ---
    struct ClaimData {
        address to;
        uint256 amount;
        uint256 nonce;
        bytes signature;
    }

    // --- Fallback & Receive ---
    receive() external payable {}
    fallback() external payable {}
}