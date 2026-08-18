"""
Hashing and Merkle tree utilities for the Blockchain Simulation engine.
Ensures deterministic SHA-256 hash generation regardless of environment.
"""

import hashlib
import json
from typing import List
from backend.blockchain.models import Block, Transaction


def calculate_sha256(content: str) -> str:
    """Compute SHA-256 hex digest for a given string."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def calculate_transaction_id(tx: Transaction) -> str:
    """Compute unique deterministic hash for a transaction."""
    tx_dict = {
        "sender": tx.sender,
        "recipient": tx.recipient,
        "amount": round(float(tx.amount), 6),
        "timestamp": round(float(tx.timestamp), 6)
    }
    serialized = json.dumps(tx_dict, sort_keys=True)
    return calculate_sha256(serialized)


def build_merkle_root(transactions: List[Transaction]) -> str:
    """
    Build a Merkle Tree root hash from a list of transactions.
    If no transactions exist, returns an empty string.
    If 1 transaction exists, returns its tx_id hash.
    Otherwise recursively pairs up hashes until a single root hash remains.
    """
    if not transactions:
        return ""

    # Ensure transaction IDs exist
    hashes = []
    for tx in transactions:
        tx_id = tx.tx_id or calculate_transaction_id(tx)
        hashes.append(tx_id)

    # Build Merkle tree
    while len(hashes) > 1:
        # If odd number of hashes, duplicate the last hash to complete the pair
        if len(hashes) % 2 != 0:
            hashes.append(hashes[-1])

        next_level = []
        for i in range(0, len(hashes), 2):
            combined = hashes[i] + hashes[i + 1]
            next_level.append(calculate_sha256(combined))
        hashes = next_level

    return hashes[0]


def calculate_block_hash(block: Block) -> str:
    """
    Compute canonical SHA-256 hash of a block.
    Uses sorted JSON dictionary serialization to guarantee 100% deterministic hash output.
    """
    merkle_root = block.merkle_root
    if block.transactions and not merkle_root:
        merkle_root = build_merkle_root(block.transactions)

    block_dict = {
        "index": int(block.index),
        "timestamp": round(float(block.timestamp), 6),
        "previous_hash": str(block.previous_hash),
        "data": str(block.data),
        "merkle_root": str(merkle_root),
        "nonce": int(block.nonce),
        "validator": str(block.validator or "")
    }

    serialized = json.dumps(block_dict, sort_keys=True)
    return calculate_sha256(serialized)
