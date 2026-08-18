"""
Mempool transaction manager for the Blockchain Engine.
Holds unconfirmed pending transactions prior to block mining/packaging.
"""

from typing import List, Dict, Any
from backend.blockchain.models import Transaction
from backend.blockchain.hashing import calculate_transaction_id


class Mempool:
    def __init__(self):
        self.pending_transactions: Dict[str, Transaction] = {}

    def add_transaction(self, tx: Transaction) -> str:
        """Add a transaction to the pending mempool queue."""
        if not tx.tx_id:
            tx.tx_id = calculate_transaction_id(tx)

        if tx.amount <= 0:
            raise ValueError("Transaction amount must be greater than zero.")

        self.pending_transactions[tx.tx_id] = tx
        return tx.tx_id

    def get_pending(self, limit: int = 10) -> List[Transaction]:
        """Fetch pending transactions up to specified limit."""
        txs = list(self.pending_transactions.values())
        return txs[:limit]

    def clear_transactions(self, tx_ids: List[str]):
        """Remove confirmed transactions from mempool."""
        for tx_id in tx_ids:
            self.pending_transactions.pop(tx_id, None)

    def count(self) -> int:
        return len(self.pending_transactions)

    def to_list(self) -> List[Dict[str, Any]]:
        return [tx.to_dict() for tx in self.pending_transactions.values()]
