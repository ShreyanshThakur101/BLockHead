"""
Core Blockchain engine managing the chain of blocks, Proof of Stake consensus,
tamper simulation, re-sealing, validator set, and full chain validation.
"""

import time
import math
import threading
from typing import List, Dict, Optional, Any
from backend.blockchain.models import Block, Transaction, Validator, ChainValidationResult
from backend.blockchain.hashing import calculate_block_hash, build_merkle_root
from backend.blockchain.consensus import ProofOfStakeStrategy
from backend.blockchain.mempool import Mempool


class Blockchain:
    def __init__(self):
        self._lock = threading.RLock()
        self.blocks: List[Block] = []
        self.mempool = Mempool()
        self.validators: Dict[str, Validator] = {}
        self.consensus_mode = "pos"

        # Initialize default validators for PoS simulation
        self._init_default_validators()

        # Initialize consensus strategy
        self.pos_strategy = ProofOfStakeStrategy()

        # Create Genesis Block
        self._create_genesis_block()

    def _init_default_validators(self):
        """Setup initial default validator pool for Proof of Stake."""
        defaults = [
            Validator("Alice_Node", 50.0),
            Validator("Bob_Node", 30.0),
            Validator("Carol_Node", 20.0),
        ]
        for v in defaults:
            self.validators[v.name] = v

    def _create_genesis_block(self):
        """Generate hardcoded Genesis Block (Index 0)."""
        genesis = Block(
            index=0,
            timestamp=time.time(),
            previous_hash="0" * 64,
            data="Genesis Block",
            transactions=[],
            merkle_root="",
            validator="Genesis_Authority"
        )
        # Seal genesis block
        genesis.hash = calculate_block_hash(genesis)
        self.blocks.append(genesis)

    @property
    def current_strategy(self) -> ProofOfStakeStrategy:
        return self.pos_strategy

    def add_validator(self, name: str, stake: float) -> Validator:
        with self._lock:
            if not name or not isinstance(name, str) or not name.strip():
                raise ValueError("Validator name must be a non-empty string.")
            name = name.strip()
            if name in self.validators:
                raise ValueError(f"Validator '{name}' already exists.")
            if not math.isfinite(stake) or stake <= 0:
                raise ValueError("Validator stake must be a positive finite number.")

            v = Validator(name=name, stake=float(stake))
            self.validators[name] = v
            return v

    def update_validator_stake(self, name: str, stake: float) -> Validator:
        with self._lock:
            name = name.strip() if isinstance(name, str) else name
            if name not in self.validators:
                raise KeyError(f"Validator '{name}' not found.")
            if not math.isfinite(stake) or stake < 0:
                raise ValueError("Stake must be a non-negative finite number.")

            self.validators[name].stake = float(stake)
            return self.validators[name]

    def slash_validator(self, name: str) -> Validator:
        with self._lock:
            name = name.strip() if isinstance(name, str) else name
            if name not in self.validators:
                raise KeyError(f"Validator '{name}' not found.")

            v = self.validators[name]
            v.is_slashed = True
            v.stake = 0.0
            return v

    def add_block(
        self,
        data: str = "",
        transactions: Optional[List[Transaction]] = None,
        validator_name: Optional[str] = None,
        **kwargs
    ) -> Block:
        """
        Build, seal, and append a new block to the chain using PoS validator selection.
        Pulls transactions from parameter or mempool. Thread-safe.
        """
        with self._lock:
            last_block = self.blocks[-1]
            new_index = last_block.index + 1

            # Package transactions
            block_txs = transactions or self.mempool.get_pending(limit=10)
            merkle_root = build_merkle_root(block_txs) if block_txs else ""

            # Construct raw unsealed block
            new_block = Block(
                index=new_index,
                timestamp=time.time(),
                previous_hash=last_block.hash,
                data=data or (f"Block {new_index} Payload" if not block_txs else f"Batch of {len(block_txs)} Txs"),
                transactions=block_txs,
                merkle_root=merkle_root
            )

            # Execute Proof of Stake selection and seal block
            sealed_block = self.pos_strategy.execute(
                new_block,
                validators=self.validators,
                validator_name=validator_name
            )

            # Clear confirmed transactions from mempool
            if block_txs:
                confirmed_ids = [tx.tx_id for tx in block_txs if tx.tx_id]
                self.mempool.clear_transactions(confirmed_ids)

            self.blocks.append(sealed_block)
            return sealed_block

    def tamper_block(self, index: int, new_data: str) -> Block:
        """
        Simulates cyber attack / tamper by overwriting a block's data payload
        WITHOUT re-computing hash, breaking the chain validation.
        """
        with self._lock:
            if index <= 0 or index >= len(self.blocks):
                raise IndexError(f"Cannot tamper block index {index}. Valid index range: 1..{len(self.blocks)-1}")

            target = self.blocks[index]
            target.data = str(new_data)
            # Note: target.hash is NOT updated here intentionally to trigger validation failure
            return target

    def reseal_block(self, index: int, validator_name: Optional[str] = None, **kwargs) -> Block:
        """
        Re-seals a single block at `index` with PoS.
        Illustrates that fixing one block does not repair downstream links.
        """
        with self._lock:
            if index <= 0 or index >= len(self.blocks):
                raise IndexError(f"Cannot re-seal block index {index}. Valid range: 1..{len(self.blocks)-1}")

            block = self.blocks[index]
            # Re-attach to previous block's current stored hash pointer
            block.previous_hash = self.blocks[index - 1].hash
            block.timestamp = time.time()

            resealed = self.pos_strategy.execute(
                block,
                validators=self.validators,
                validator_name=validator_name or block.validator
            )

            self.blocks[index] = resealed
            return resealed

    def remine_block(self, index: int, **kwargs) -> Block:
        """Backward-compatible alias for reseal_block."""
        return self.reseal_block(index=index, **kwargs)

    def is_chain_valid(self) -> ChainValidationResult:
        """
        Full chain validation loop checking:
        1. Current block's calculated hash == stored hash.
        2. Current block's previous_hash == actual previous block hash.
        3. Current block satisfies Proof of Stake validator validity rules.
        """
        with self._lock:
            for i in range(1, len(self.blocks)):
                current = self.blocks[i]
                previous = self.blocks[i - 1]

                # 1. Verify hash match
                calculated_hash = calculate_block_hash(current)
                if current.hash != calculated_hash:
                    return ChainValidationResult(
                        is_valid=False,
                        broken_at_index=i,
                        reason=f"Block #{i} payload tampered! Stored hash '{current.hash[:10]}...' does not match calculated hash '{calculated_hash[:10]}...'."
                    )

                # 2. Verify previous_hash continuity
                if current.previous_hash != previous.hash:
                    return ChainValidationResult(
                        is_valid=False,
                        broken_at_index=i,
                        reason=f"Block #{i} previous_hash link broken! Points to '{current.previous_hash[:10]}...', but Block #{i-1} hash is '{previous.hash[:10]}...'."
                    )

                # 3. Verify Proof of Stake consensus rules
                if not self.pos_strategy.validate_block(current, previous, validators=self.validators):
                    return ChainValidationResult(
                        is_valid=False,
                        broken_at_index=i,
                        reason=f"Block #{i} fails Proof of Stake validator validation rule."
                    )

            return ChainValidationResult(
                is_valid=True,
                broken_at_index=None,
                reason="Chain is 100% valid. All hashes, links, and PoS consensus rules verified."
            )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize complete state for API clients. Thread-safe."""
        with self._lock:
            validation = self.is_chain_valid()
            return {
                "consensus_mode": "pos",
                "chain_length": len(self.blocks),
                "validation": validation.to_dict(),
                "mempool_count": self.mempool.count(),
                "validators": [v.to_dict() for v in self.validators.values()],
                "blocks": [b.to_dict() for b in self.blocks]
            }
