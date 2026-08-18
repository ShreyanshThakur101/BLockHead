"""
Core Blockchain engine managing the chain of blocks, consensus mode,
tamper simulation, re-mining, validator set, and full chain validation.
"""

import time
from typing import List, Dict, Optional, Any, Union
from backend.blockchain.models import Block, Transaction, Validator, ChainValidationResult
from backend.blockchain.hashing import calculate_block_hash, build_merkle_root
from backend.blockchain.consensus import ProofOfWorkStrategy, ProofOfStakeStrategy, ConsensusStrategy
from backend.blockchain.mempool import Mempool


class Blockchain:
    def __init__(self, consensus_mode: str = "pow", difficulty: int = 4):
        self.blocks: List[Block] = []
        self.mempool = Mempool()
        self.validators: Dict[str, Validator] = {}
        self.consensus_mode = consensus_mode.lower()

        # Initialize default validators for PoS simulation
        self._init_default_validators()

        # Initialize consensus strategy
        self.pow_strategy = ProofOfWorkStrategy(difficulty=difficulty)
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
            nonce=0,
            validator="Genesis_Authority"
        )
        # Seal genesis block
        genesis.hash = calculate_block_hash(genesis)
        self.blocks.append(genesis)

    @property
    def current_strategy(self) -> ConsensusStrategy:
        if self.consensus_mode == "pos":
            return self.pos_strategy
        return self.pow_strategy

    def set_consensus_mode(self, mode: str, difficulty: Optional[int] = None):
        mode = mode.lower()
        if mode not in ["pow", "pos"]:
            raise ValueError("Invalid consensus mode. Must be 'pow' or 'pos'.")
        self.consensus_mode = mode

        if difficulty is not None and mode == "pow":
            self.pow_strategy.set_difficulty(difficulty)

    def set_pow_difficulty(self, difficulty: int):
        self.pow_strategy.set_difficulty(difficulty)

    def add_validator(self, name: str, stake: float) -> Validator:
        if stake <= 0:
            raise ValueError("Validator stake must be greater than zero.")
        v = Validator(name=name, stake=stake)
        self.validators[name] = v
        return v

    def update_validator_stake(self, name: str, stake: float) -> Validator:
        if name not in self.validators:
            raise KeyError(f"Validator '{name}' not found.")
        if stake < 0:
            raise ValueError("Stake cannot be negative.")
        self.validators[name].stake = stake
        return self.validators[name]

    def slash_validator(self, name: str) -> Validator:
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
        progress_callback=None
    ) -> Block:
        """
        Build, seal, and append a new block to the chain.
        Pulls transactions from parameter or mempool.
        Runs active consensus (PoW mining or PoS validator selection).
        """
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
            merkle_root=merkle_root,
            nonce=0
        )

        # Execute consensus algorithm to seal block
        if self.consensus_mode == "pow":
            sealed_block = self.pow_strategy.execute(new_block, progress_callback=progress_callback)
        else:
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
        WITHOUT re-computing hash or noncing, breaking the chain validation.
        """
        if index <= 0 or index >= len(self.blocks):
            raise IndexError(f"Cannot tamper block index {index}. Valid index range: 1..{len(self.blocks)-1}")

        target = self.blocks[index]
        target.data = new_data
        # Note: target.hash is NOT updated here intentionally to trigger validation failure
        return target

    def remine_block(self, index: int, progress_callback=None) -> Block:
        """
        Re-mines / re-seals a single block at `index`.
        Illustrates that fixing one block does not repair down-stream links.
        """
        if index <= 0 or index >= len(self.blocks):
            raise IndexError(f"Cannot re-mine block index {index}. Valid range: 1..{len(self.blocks)-1}")

        block = self.blocks[index]
        # Re-attach to previous block's current stored hash pointer
        block.previous_hash = self.blocks[index - 1].hash
        block.timestamp = time.time()

        if self.consensus_mode == "pow":
            resealed = self.pow_strategy.execute(block, progress_callback=progress_callback)
        else:
            resealed = self.pos_strategy.execute(block, validators=self.validators)

        self.blocks[index] = resealed
        return resealed

    def is_chain_valid(self) -> ChainValidationResult:
        """
        Full chain validation loop checking:
        1. Current block's calculated hash == stored hash.
        2. Current block's previous_hash == actual previous block hash.
        3. Current block satisfies consensus strategy rules.
        """
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

            # 3. Verify consensus rules
            if self.consensus_mode == "pow":
                if not self.pow_strategy.validate_block(current, previous):
                    return ChainValidationResult(
                        is_valid=False,
                        broken_at_index=i,
                        reason=f"Block #{i} fails Proof of Work difficulty target rule."
                    )
            else:
                if not self.pos_strategy.validate_block(current, previous, validators=self.validators):
                    return ChainValidationResult(
                        is_valid=False,
                        broken_at_index=i,
                        reason=f"Block #{i} fails Proof of Stake validator validation rule."
                    )

        return ChainValidationResult(
            is_valid=True,
            broken_at_index=None,
            reason="Chain is 100% valid. All hashes, links, and consensus rules verified."
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize complete state for API clients."""
        validation = self.is_chain_valid()
        return {
            "consensus_mode": self.consensus_mode,
            "pow_difficulty": self.pow_strategy.difficulty,
            "chain_length": len(self.blocks),
            "validation": validation.to_dict(),
            "mempool_count": self.mempool.count(),
            "validators": [v.to_dict() for v in self.validators.values()],
            "blocks": [b.to_dict() for b in self.blocks]
        }
