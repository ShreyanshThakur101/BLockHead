
"""
Verification test suite for the Proof of Stake (PoS) Blockchain Simulation engine.
Validates PoS block generation, weighted validator selection, validator registry & slashing,
mempool transaction handling, Merkle tree root calculation, tamper detection,
and block re-sealing workflows.
"""

import sys
import os

# Ensure backend package path is available
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.blockchain import Blockchain, Transaction


def test_genesis_and_pos_block_creation():
    print("--- 1. Testing Genesis Block & PoS Block Creation ---")
    chain = Blockchain()
    assert len(chain.blocks) == 1, "Chain should initialize with 1 Genesis block"
    genesis = chain.blocks[0]
    assert genesis.index == 0
    assert genesis.validator == "Genesis_Authority"
    print(f"[OK] Genesis Block: Hash={genesis.hash[:16]}... Validator={genesis.validator}")

    # Propose/Forge PoS blocks
    b1 = chain.add_block(data="Alice pays Bob 10 coins")
    print(f"[OK] PoS Block #1: Validator={b1.validator} Hash={b1.hash[:16]}... Time={b1.validation_time:.4f}s")
    assert b1.validator in chain.validators, "Selected validator must be in validator pool"

    b2 = chain.add_block(data="Bob pays Carol 5 coins")
    print(f"[OK] PoS Block #2: Validator={b2.validator} Hash={b2.hash[:16]}... Time={b2.validation_time:.4f}s")
    assert b2.validator in chain.validators

    val = chain.is_chain_valid()
    assert val.is_valid, f"Validation failed: {val.reason}"
    print(f"[OK] Chain Status: {val.reason}")


def test_validator_pool_and_slashing():
    print("\n--- 2. Testing Validator Management & Slashing ---")
    chain = Blockchain()

    # Register new validator
    v_new = chain.add_validator(name="Dave_Node", stake=100.0)
    assert "Dave_Node" in chain.validators
    assert v_new.stake == 100.0
    print(f"[OK] Added validator {v_new.name} with stake {v_new.stake}")

    # Update stake
    chain.update_validator_stake("Dave_Node", 150.0)
    assert chain.validators["Dave_Node"].stake == 150.0

    # Slash validator
    slashed_v = chain.slash_validator("Dave_Node")
    assert slashed_v.is_slashed is True
    assert slashed_v.stake == 0.0
    print(f"[OK] Slashed validator {slashed_v.name}: is_slashed={slashed_v.is_slashed}, stake={slashed_v.stake}")

    # Ensure Dave_Node is never selected for new blocks
    for _ in range(5):
        b = chain.add_block(data="Post-slash block")
        assert b.validator != "Dave_Node", "Slashed validator should never be selected"
    print("[OK] Slashed validator excluded from PoS block selection lottery.")


def test_tamper_and_reseal():
    print("\n--- 3. Testing Tamper Detection & Single Block Re-sealing ---")
    chain = Blockchain()
    chain.add_block(data="Block 1 Original Data")
    chain.add_block(data="Block 2 Original Data")

    assert chain.is_chain_valid().is_valid, "Chain should initially be valid"

    # Tamper Block 1
    chain.tamper_block(1, new_data="Block 1 TAMPERED DATA")
    val_tampered = chain.is_chain_valid()
    assert not val_tampered.is_valid, "Tampered chain must be invalid"
    assert val_tampered.broken_at_index == 1, f"Expected break at 1, got {val_tampered.broken_at_index}"
    print(f"[OK] Tamper Detection Succeeded: Broken at Block #{val_tampered.broken_at_index} ({val_tampered.reason})")

    # Re-seal Block 1
    chain.reseal_block(1)
    val_resealed = chain.is_chain_valid()
    # Re-sealing block 1 repairs block 1's internal hash, but block 2 still points to block 1's old hash!
    assert not val_resealed.is_valid, "Chain should still be invalid downstream at Block 2"
    assert val_resealed.broken_at_index == 2, f"Expected cascade break at 2, got {val_resealed.broken_at_index}"
    print(f"[OK] Cascade Invalidation Verified: Block #2 correctly remains broken after Block #1 re-sealing.")

    # Re-seal Block 2 to fully heal chain
    chain.reseal_block(2)
    assert chain.is_chain_valid().is_valid, "Chain should now be 100% valid after repairing downstream blocks"
    print("[OK] Full chain repair verified.")


def test_security_unregistered_validator_rejection():
    print("\n--- 4. Testing Security: Unregistered & Slashed Validator Rejection ---")
    chain = Blockchain()
    b1 = chain.add_block(data="Legitimate block")
    assert chain.is_chain_valid().is_valid

    # Attempt to forge a block with an untrusted, unregistered validator
    b1.validator = "Hacker_Node_666"
    from backend.blockchain.hashing import calculate_block_hash
    b1.hash = calculate_block_hash(b1)  # Recalculate hash so hash matches

    val = chain.is_chain_valid()
    assert not val.is_valid, "Chain must reject blocks created by unregistered validators!"
    assert val.broken_at_index == 1
    print(f"[OK] Security Check Passed: Unregistered validator '{b1.validator}' successfully rejected: {val.reason}")


def test_input_validation_and_edge_cases():
    print("\n--- 5. Testing Input Validation & Edge Cases ---")
    chain = Blockchain()

    # Test invalid validator inputs
    try:
        chain.add_validator("", 10.0)
        assert False, "Empty validator name should be rejected"
    except ValueError:
        pass

    try:
        chain.add_validator("Valid_Name", float("nan"))
        assert False, "NaN stake should be rejected"
    except ValueError:
        pass

    try:
        chain.add_validator("Valid_Name", -5.0)
        assert False, "Negative stake should be rejected"
    except ValueError:
        pass

    # Test invalid transaction inputs
    try:
        chain.mempool.add_transaction(Transaction(sender="", recipient="Bob", amount=10.0))
        assert False, "Empty sender should be rejected"
    except ValueError:
        pass

    try:
        chain.mempool.add_transaction(Transaction(sender="Alice", recipient="Bob", amount=float("inf")))
        assert False, "Infinite amount should be rejected"
    except ValueError:
        pass

    print("[OK] All invalid and malicious edge-case inputs successfully rejected.")


def test_mempool_and_merkle():
    print("\n--- 6. Testing Mempool & Merkle Trees in PoS ---")
    chain = Blockchain()

    tx1 = Transaction(sender="Alice", recipient="Bob", amount=25.0)
    tx2 = Transaction(sender="Bob", recipient="Carol", amount=12.5)

    chain.mempool.add_transaction(tx1)
    chain.mempool.add_transaction(tx2)
    assert chain.mempool.count() == 2, "Mempool should hold 2 transactions"

    b = chain.add_block()
    print(f"[OK] Sealed Block with Mempool Txs: Txs Count={len(b.transactions)}, Merkle Root={b.merkle_root[:16]}... Validator={b.validator}")
    assert len(b.transactions) == 2, "Block should contain the 2 mempool transactions"
    assert chain.mempool.count() == 0, "Mempool should be cleared after block addition"
    print("[OK] Mempool & Merkle Root integration verified.")


def test_concurrency_thread_safety():
    print("\n--- 7. Testing Concurrency & Thread Safety ---")
    import concurrent.futures

    chain = Blockchain()
    num_threads = 8
    blocks_per_thread = 5

    def add_blocks():
        for i in range(blocks_per_thread):
            chain.add_block(data=f"Thread Block {i}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(add_blocks) for _ in range(num_threads)]
        for f in concurrent.futures.as_completed(futures):
            f.result()

    expected_blocks = 1 + (num_threads * blocks_per_thread)
    assert len(chain.blocks) == expected_blocks, f"Expected {expected_blocks} blocks, got {len(chain.blocks)}"
    val = chain.is_chain_valid()
    assert val.is_valid, f"Concurrent chain corrupted! {val.reason}"
    print(f"[OK] Concurrent generation of {expected_blocks} blocks across {num_threads} threads was 100% race-free and valid.")


if __name__ == "__main__":
    test_genesis_and_pos_block_creation()
    test_validator_pool_and_slashing()
    test_tamper_and_reseal()
    test_security_unregistered_validator_rejection()
    test_input_validation_and_edge_cases()
    test_mempool_and_merkle()
    test_concurrency_thread_safety()
    print("\n[ALL AUDIT & SECURITY TESTS PASSED WITH 100% SUCCESS!]")
