"""
Direct RPC Contract Data Fetcher
Fetches smart contract data from blockchain without explorer APIs
"""

from web3 import Web3
from eth_utils import encode_hex, decode_hex
import requests
import json
import re
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)

class ContractDataFetcher:
    """Fetch contract data directly from RPC without explorer API"""
    
    def __init__(self, rpc_url: str):
        """
        Initialize fetcher with RPC endpoint
        
        Args:
            rpc_url: Blockchain RPC URL (e.g., https://hyperion-testnet.metisdevops.link)
        """
        self.web3 = Web3(Web3.HTTPProvider(rpc_url))
        self.rpc_url = rpc_url
        
        if not self.web3.is_connected():
            raise ConnectionError(f"Cannot connect to RPC: {rpc_url}")
        
        logger.info(f"Connected to blockchain at {rpc_url}")
    
    def get_contract_bytecode(self, address: str) -> str:
        """
        Fetch deployed contract bytecode
        
        Args:
            address: Contract address (0x...)
        
        Returns:
            Bytecode as hex string
        """
        try:
            checksum_address = Web3.to_checksum_address(address)
            bytecode = self.web3.eth.get_code(checksum_address)
            return bytecode.hex()
        except Exception as e:
            logger.error(f"Error fetching bytecode: {e}")
            return ""
    
    def get_contract_balance(self, address: str) -> float:
        """Get contract ETH/native token balance"""
        try:
            checksum_address = Web3.to_checksum_address(address)
            balance_wei = self.web3.eth.get_balance(checksum_address)
            balance_eth = self.web3.from_wei(balance_wei, 'ether')
            return float(balance_eth)
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return 0.0
    
    def get_transaction_count(self, address: str) -> int:
        """Get number of transactions (nonce)"""
        try:
            checksum_address = Web3.to_checksum_address(address)
            return self.web3.eth.get_transaction_count(checksum_address)
        except Exception as e:
            logger.error(f"Error fetching tx count: {e}")
            return 0
    
    def extract_function_signatures(self, bytecode: str) -> List[str]:
        """
        Extract function selectors from bytecode
        
        Function selectors are first 4 bytes of keccak256(function_signature)
        Example: transfer(address,uint256) → 0xa9059cbb
        """
        try:
            # Remove 0x prefix
            if bytecode.startswith('0x'):
                bytecode = bytecode[2:]
            
            # Look for PUSH4 opcodes (0x63) followed by 4-byte selectors
            selectors = set()
            
            # Pattern: 63 XX XX XX XX (PUSH4 selector)
            pattern = r'63([0-9a-fA-F]{8})'
            matches = re.findall(pattern, bytecode)
            
            for match in matches:
                selectors.add('0x' + match)
            
            return list(selectors)
        except Exception as e:
            logger.error(f"Error extracting signatures: {e}")
            return []
    
    def lookup_function_signature(self, selector: str) -> Optional[str]:
        """
        Look up function signature from 4byte.directory
        
        Args:
            selector: 4-byte function selector (0xa9059cbb)
        
        Returns:
            Function signature string or None
        """
        try:
            # Remove 0x prefix if present
            if selector.startswith('0x'):
                selector = selector[2:]
            
            # Query 4byte.directory API
            url = f"https://www.4byte.directory/api/v1/signatures/?hex_signature=0x{selector}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('results'):
                    return data['results'][0]['text_signature']
            
            return None
        except Exception as e:
            logger.warning(f"Could not lookup signature {selector}: {e}")
            return None
    
    def get_storage_at(self, address: str, position: int) -> str:
        """
        Read contract storage slot
        
        Args:
            address: Contract address
            position: Storage slot number (0, 1, 2...)
        
        Returns:
            Storage value as hex string
        """
        try:
            checksum_address = Web3.to_checksum_address(address)
            storage = self.web3.eth.get_storage_at(checksum_address, position)
            return storage.hex()
        except Exception as e:
            logger.error(f"Error reading storage: {e}")
            return "0x"
    
    def get_creation_transaction(self, address: str, start_block: int = 0) -> Optional[Dict]:
        """
        Find contract creation transaction (slow, scans blocks)
        
        Args:
            address: Contract address
            start_block: Block to start searching from
        
        Returns:
            Transaction dict or None
        """
        try:
            checksum_address = Web3.to_checksum_address(address)
            current_block = self.web3.eth.block_number
            
            # Scan recent blocks (last 10000)
            for block_num in range(max(start_block, current_block - 10000), current_block + 1):
                block = self.web3.eth.get_block(block_num, full_transactions=True)
                
                for tx in block['transactions']:
                    # Check if transaction creates contract at this address
                    if tx.get('to') is None:  # Contract creation
                        receipt = self.web3.eth.get_transaction_receipt(tx['hash'])
                        if receipt.get('contractAddress') == checksum_address:
                            return {
                                'hash': tx['hash'].hex(),
                                'from': tx['from'],
                                'block_number': block_num,
                                'timestamp': block['timestamp']
                            }
            
            return None
        except Exception as e:
            logger.error(f"Error finding creation tx: {e}")
            return None
    
    def analyze_contract(self, address: str) -> Dict:
        """
        Complete contract analysis without explorer API
        
        Returns comprehensive contract metadata
        """
        logger.info(f"Analyzing contract: {address}")
        
        analysis = {
            "address": address,
            "network": self.rpc_url,
            "exists": False,
            "bytecode": "",
            "bytecode_length": 0,
            "balance": 0.0,
            "transaction_count": 0,
            "function_selectors": [],
            "function_signatures": [],
            "storage_slots": {},
            "creation_info": None
        }
        
        try:
            # 1. Check if contract exists
            bytecode = self.get_contract_bytecode(address)
            if not bytecode or bytecode == "0x":
                logger.warning(f"No bytecode found at {address}")
                return analysis
            
            analysis["exists"] = True
            analysis["bytecode"] = bytecode
            analysis["bytecode_length"] = len(bytecode) // 2  # Convert hex to bytes
            
            # 2. Get balance
            analysis["balance"] = self.get_contract_balance(address)
            
            # 3. Get transaction count
            analysis["transaction_count"] = self.get_transaction_count(address)
            
            # 4. Extract function selectors
            selectors = self.extract_function_signatures(bytecode)
            analysis["function_selectors"] = selectors
            
            # 5. Lookup function signatures (first 10)
            signatures = []
            for selector in selectors[:10]:
                sig = self.lookup_function_signature(selector)
                if sig:
                    signatures.append({
                        "selector": selector,
                        "signature": sig
                    })
            
            analysis["function_signatures"] = signatures
            
            # 6. Sample storage slots (first 5)
            storage = {}
            for i in range(5):
                value = self.get_storage_at(address, i)
                if value and value != "0x" + "00" * 32:
                    storage[f"slot_{i}"] = value
            
            analysis["storage_slots"] = storage
            
            logger.info(f"Contract analysis complete: {len(selectors)} functions found")
            return analysis
        
        except Exception as e:
            logger.error(f"Error analyzing contract: {e}")
            analysis["error"] = str(e)
            return analysis


class MultiNetworkContractFetcher:
    """Manage contract fetchers for multiple networks"""
    
    NETWORKS = {
        "hyperion": "https://hyperion-testnet.metisdevops.link",
        "lazai": "https://rpc.lazai.network/testnet",
        "metis": "https://andromeda.metis.io",
        "polygon": "https://polygon-rpc.com",
        "ethereum": "https://mainnet.infura.io/v3/YOUR_KEY"
    }
    
    def __init__(self):
        self.fetchers = {}
    
    def get_fetcher(self, network: str) -> ContractDataFetcher:
        """Get or create fetcher for network"""
        if network not in self.fetchers:
            rpc_url = self.NETWORKS.get(network)
            if not rpc_url:
                raise ValueError(f"Unknown network: {network}")
            
            self.fetchers[network] = ContractDataFetcher(rpc_url)
        
        return self.fetchers[network]
    
    def analyze_contract_on_network(self, address: str, network: str) -> Dict:
        """Analyze contract on specific network"""
        fetcher = self.get_fetcher(network)
        return fetcher.analyze_contract(address)


# ============================================================================
# INTEGRATION WITH AUDIT COMMAND
# ============================================================================

def fetch_contract_from_blockchain(address: str, network: str) -> tuple:
    """
    Fetch contract data from blockchain without explorer API
    
    Returns:
        (source_code_or_bytecode, metadata)
    """
    try:
        fetcher_manager = MultiNetworkContractFetcher()
        analysis = fetcher_manager.analyze_contract_on_network(address, network)
        
        if not analysis.get("exists"):
            raise ValueError(f"No contract found at {address} on {network}")
        
        # Use bytecode as source (for analysis)
        bytecode = analysis["bytecode"]
        
        # Build metadata
        metadata = {
            "type": "on_chain_analysis",
            "address": address,
            "network": network,
            "bytecode_length": analysis["bytecode_length"],
            "balance": analysis["balance"],
            "tx_count": analysis["transaction_count"],
            "functions_detected": len(analysis["function_selectors"]),
            "function_signatures": analysis["function_signatures"],
            "verified": False,  # Cannot verify without explorer
            "analysis_method": "direct_rpc"
        }
        
        return bytecode, metadata
    
    except Exception as e:
        logger.error(f"Error fetching from blockchain: {e}")
        raise
