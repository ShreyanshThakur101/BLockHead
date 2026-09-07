"""
Dataclasses and data models for the Blockchain Simulation engine.
Ensures clean, typed, and serializable data structures for blocks, transactions, validators,
and validation results.
"""

from dataclasses import dataclass, field
import time
from typing import List, Optional, Dict, Any


@dataclass
class Transaction:
    sender: str
    recipient: str
    amount: float
    timestamp: float = field(default_factory=time.time)
    signature: Optional[str] = None
    tx_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert transaction to a deterministic dictionary."""
        return {
            "tx_id": self.tx_id or "",
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": round(float(self.amount), 6),
            "timestamp": round(float(self.timestamp), 6),
            "signature": self.signature or ""
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Transaction":
        return cls(
            sender=data.get("sender", ""),
            recipient=data.get("recipient", ""),
            amount=float(data.get("amount", 0.0)),
            timestamp=float(data.get("timestamp", time.time())),
            signature=data.get("signature"),
            tx_id=data.get("tx_id")
        )


@dataclass
class Validator:
    name: str
    stake: float
    is_slashed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "stake": round(float(self.stake), 6),
            "is_slashed": self.is_slashed
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Validator":
        return cls(
            name=data["name"],
            stake=float(data.get("stake", 0.0)),
            is_slashed=bool(data.get("is_slashed", False))
        )


@dataclass
class Block:
    index: int
    timestamp: float
    previous_hash: str
    data: str = ""
    transactions: List[Transaction] = field(default_factory=list)
    merkle_root: str = ""
    validator: str = "System"
    hash: str = ""
    validation_time: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert block instance to dictionary for API responses and hashing."""
        return {
            "index": self.index,
            "timestamp": round(float(self.timestamp), 6),
            "previous_hash": self.previous_hash,
            "data": self.data,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "merkle_root": self.merkle_root,
            "validator": self.validator or "",
            "hash": self.hash,
            "validation_time": round(float(self.validation_time), 4)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Block":
        txs = [Transaction.from_dict(tx) for tx in data.get("transactions", [])]
        return cls(
            index=int(data["index"]),
            timestamp=float(data["timestamp"]),
            previous_hash=str(data["previous_hash"]),
            data=str(data.get("data", "")),
            transactions=txs,
            merkle_root=str(data.get("merkle_root", "")),
            validator=data.get("validator", "System"),
            hash=str(data.get("hash", "")),
            validation_time=float(data.get("validation_time", data.get("mining_time", 0.0)))
        )


@dataclass
class ChainValidationResult:
    is_valid: bool
    broken_at_index: Optional[int]
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "broken_at_index": self.broken_at_index,
            "reason": self.reason
        }
