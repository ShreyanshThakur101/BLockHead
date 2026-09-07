"""
Mempool transaction manager for the Blockchain Engine.
Holds unconfirmed pending transactions prior to block proposing/packaging.
"""

import math
from typing import List, Dict, Any, Iterable
from backend.blockchain.models import Transaction
from backend.blockchain.hashing import calculate_transaction_id


class Mempool:
    def __init__(self):
        self.pending_transactions: Dict[str, Transaction] = {}

    def add_transaction(self, tx: Transaction) -> str:
        """Add a transaction to the pending mempool queue with strict validation."""
        if not tx.sender or not isinstance(tx.sender, str) or not tx.sender.strip():
            raise ValueError("Transaction sender must be a non-empty string.")

        if not tx.recipient or not isinstance(tx.recipient, str) or not tx.recipient.strip():
            raise ValueError("Transaction recipient must be a non-empty string.")

        if not math.isfinite(tx.amount) or tx.amount <= 0:
            raise ValueError("Transaction amount must be a positive, finite number.")

        if not tx.tx_id:
            tx.tx_id = calculate_transaction_id(tx)

        self.pending_transactions[tx.tx_id] = tx
        return tx.tx_id

    def get_pending(self, limit: int = 10) -> List[Transaction]:
        """Fetch pending transactions up to specified limit."""
        txs = list(self.pending_transactions.values())
        return txs[:max(0, limit)]

    def clear_transactions(self, tx_ids: Iterable[str]):
        """Remove confirmed transactions from mempool."""
        for tx_id in tx_ids:
            self.pending_transactions.pop(tx_id, None)

    def count(self) -> int:
        return len(self.pending_transactions)

    def to_list(self) -> List[Dict[str, Any]]:
        return [tx.to_dict() for tx in self.pending_transactions.values()]
