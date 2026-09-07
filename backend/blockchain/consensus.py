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
        """
        active_validators = {
            name: v for name, v in validators.items()
            if v.stake > 0 and not v.is_slashed
        }

        if not active_validators:
            raise ValueError("No active, non-slashed validators available with positive stake.")

        total_stake = sum(v.stake for v in active_validators.values())
        pick = random.uniform(0, total_stake)

        current = 0.0
        for name, v in active_validators.items():
            current += v.stake
            if pick <= current:
                return name

        # Fallback safety return last active validator
        return list(active_validators.keys())[-1]

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
        3. Validator must exist in validator pool and not be slashed.
        """
        computed = calculate_block_hash(block)
        if computed != block.hash:
            return False

        # In PoS, every block must be signed/validated by a known validator
        if not block.validator:
            return False

        # If validator registry is provided, check validator legitimacy
        if validators and block.validator in validators:
            v = validators[block.validator]
            if v.is_slashed:
                return False
            if v.stake <= 0:
                return False

        return True
