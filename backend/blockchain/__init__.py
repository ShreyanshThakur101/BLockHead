"""
Blockchain Simulation Domain Package Exports.
Provides clean access to models, consensus mechanisms, hashing, mempool, and chain engine.
"""

from backend.blockchain.models import Block, Transaction, Validator, ChainValidationResult
from backend.blockchain.hashing import calculate_block_hash, calculate_sha256, build_merkle_root
from backend.blockchain.consensus import ProofOfWorkStrategy, ProofOfStakeStrategy
from backend.blockchain.mempool import Mempool
from backend.blockchain.chain import Blockchain

__all__ = [
    "Block",
    "Transaction",
    "Validator",
    "ChainValidationResult",
    "calculate_block_hash",
    "calculate_sha256",
    "build_merkle_root",
    "ProofOfWorkStrategy",
    "ProofOfStakeStrategy",
    "Mempool",
    "Blockchain"
]
