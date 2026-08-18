"""
Consensus mechanisms (Proof of Work and Proof of Stake) for the Blockchain Engine.
Implements Strategy pattern to allow seamless consensus mode swapping.
"""

from abc import ABC, abstractmethod
import random
import time
from typing import Dict, Optional, Callable
from backend.blockchain.models import Block, Validator
from backend.blockchain.hashing import calculate_block_hash


class ConsensusStrategy(ABC):
    @abstractmethod
    def execute(self, block: Block, **kwargs) -> Block:
        """Process and seal block according to consensus rules."""
        pass

    @abstractmethod
    def validate_block(self, block: Block, prev_block: Optional[Block], **kwargs) -> bool:
        """Validate if block adheres to consensus strategy rules."""
        pass


class ProofOfWorkStrategy(ConsensusStrategy):
    def __init__(self, difficulty: int = 4):
        self.difficulty = difficulty

    def set_difficulty(self, difficulty: int):
        if difficulty < 1 or difficulty > 8:
            raise ValueError("Difficulty must be between 1 and 8 leading zeros.")
        self.difficulty = difficulty

    def execute(self, block: Block, progress_callback: Optional[Callable[[int, int, str], None]] = None, **kwargs) -> Block:
        """
        Mines a block using Proof of Work.
        Increments nonce until block hash starts with `difficulty` leading zeros.
        """
        target = "0" * self.difficulty
        block.nonce = 0
        start_time = time.time()

        while True:
            block.hash = calculate_block_hash(block)

            if block.hash.startswith(target):
                block.mining_time = time.time() - start_time
                return block

            block.nonce += 1

            # Emit progress update every 5000 hashes if callback provided
            if progress_callback and block.nonce % 5000 == 0:
                progress_callback(block.index, block.nonce, block.hash)

    def validate_block(self, block: Block, prev_block: Optional[Block], **kwargs) -> bool:
        target = "0" * self.difficulty
        # Check hash matching and leading zeros requirement
        computed = calculate_block_hash(block)
        if computed != block.hash:
            return False
        if not block.hash.startswith(target):
            return False
        return True


class ProofOfStakeStrategy(ConsensusStrategy):
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

        # Fallback safety return last validator
        return list(active_validators.keys())[-1]

    def execute(self, block: Block, validators: Dict[str, Validator] = None, validator_name: Optional[str] = None, **kwargs) -> Block:
        """
        Seals a block using Proof of Stake selection.
        Calculates hash instantly without mining iterations.
        """
        start_time = time.time()
        if not validator_name and validators:
            validator_name = self.select_validator(validators)

        block.validator = validator_name or "SystemValidator"
        block.nonce = 0  # No nonce needed in PoS
        block.hash = calculate_block_hash(block)
        block.mining_time = time.time() - start_time
        return block

    def validate_block(self, block: Block, prev_block: Optional[Block], validators: Dict[str, Validator] = None, **kwargs) -> bool:
        computed = calculate_block_hash(block)
        if computed != block.hash:
            return False

        # In PoS, block must identify a validator
        if not block.validator:
            return False

        # If validator registry is provided, check validator existence and non-slashed status
        if validators and block.validator in validators:
            v = validators[block.validator]
            if v.is_slashed:
                return False

        return True
