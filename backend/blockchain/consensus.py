"""
Proof of Stake (PoS) consensus mechanism for the Blockchain Engine.
Handles weighted random validator selection (lottery) based on active stake,
block sealing, and cryptographic validation.
"""

import random
import time
from typing import Dict, Optional
from backend.blockchain.models import Block, Validator
from backend.blockchain.hashing import calculate_block_hash


class ProofOfStakeStrategy:
    """
    Proof of Stake Consensus Strategy.
    Validators are selected proportionally to their active stake (weighted random lottery).
    Block generation is immediate and requires no computationally wasteful hashing loops.
    """

    def select_validator(self, validators: Dict[str, Validator]) -> str:
        """
        Weighted random selection (lottery) based on active validator stake.
        Uses Python's optimized C-level random.choices implementation.
        """
        active_validators = [
            (name, v.stake) for name, v in validators.items()
            if v.stake > 0 and not v.is_slashed
        ]

        if not active_validators:
            raise ValueError("No active, non-slashed validators available with positive stake.")

        names, weights = zip(*active_validators)
        return random.choices(names, weights=weights, k=1)[0]

    def execute(
        self,
        block: Block,
        validators: Optional[Dict[str, Validator]] = None,
        validator_name: Optional[str] = None,
        **kwargs
    ) -> Block:
        """
        Seals a block using Proof of Stake selection.
        Calculates hash instantly without mining iterations.
        """
        start_time = time.time()
        if not validator_name and validators:
            validator_name = self.select_validator(validators)

        block.validator = validator_name or "Genesis_Authority"
        block.hash = calculate_block_hash(block)
        block.validation_time = time.time() - start_time
        return block

    def validate_block(
        self,
        block: Block,
        prev_block: Optional[Block] = None,
        validators: Optional[Dict[str, Validator]] = None,
        **kwargs
    ) -> bool:
        """
        Validate block according to Proof of Stake consensus rules:
        1. Block's stored hash must match freshly computed SHA-256 hash.
        2. Block must have an assigned validator.
        3. For non-genesis blocks, validator must exist in registry, not be slashed, and have positive stake.
        """
        computed = calculate_block_hash(block)
        if computed != block.hash:
            return False

        if not block.validator:
            return False

        # Genesis block (Index 0) has special genesis authority
        if block.index == 0:
            return True

        # If validator registry is provided, enforce that validator exists,
        # is not slashed, and holds active stake > 0
        if validators is not None:
            if block.validator not in validators:
                return False
            v = validators[block.validator]
            if v.is_slashed or v.stake <= 0:
                return False

        return True
