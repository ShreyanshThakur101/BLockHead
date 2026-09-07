"""
Verification test suite for the Proof of Stake (PoS) Blockchain Simulation engine.
Validates PoS block generation, weighted validator selection, validator registry & slashing,
mempool transaction handling, Merkle tree root calculation, tamper detection,
block re-sealing workflows, database persistence, and authentication/RBAC.
"""

import sys
import os
import uuid
import time
import math
import concurrent.futures

# Ensure backend package path is available
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.blockchain import Blockchain, Transaction
from backend.blockchain.database import DatabaseManager
from backend.auth import (
    hash_password,
    verify_password,
    generate_token,
    verify_token,
    seed_default_users
)


def get_fresh_chain():
    """Create an isolated test blockchain with a unique SQLite database."""
    db_name = f"test_{uuid.uuid4().hex[:8]}.db"
    db = DatabaseManager(db_name)
    chain = Blockchain(db=db)
    return chain, db_name


def cleanup_db(db_name):
    if db_name and os.path.exists(db_name):
        try:
            os.remove(db_name)
        except Exception:
            pass


def test_genesis_and_pos_block_creation():
    print("--- 1. Testing Genesis Block & PoS Block Creation ---")
    chain, db_name = get_fresh_chain()
    try:
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
    finally:
        cleanup_db(db_name)


def test_validator_pool_and_slashing():
    print("\n--- 2. Testing Validator Management & Slashing ---")
    chain, db_name = get_fresh_chain()
    try:
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
    finally:
        cleanup_db(db_name)


def test_tamper_and_reseal():
    print("\n--- 3. Testing Tamper Detection & Single Block Re-sealing ---")
    chain, db_name = get_fresh_chain()
    try:
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
    finally:
        cleanup_db(db_name)


def test_security_unregistered_validator_rejection():
    print("\n--- 4. Testing Security: Unregistered & Slashed Validator Rejection ---")
    chain, db_name = get_fresh_chain()
    try:
        b1 = chain.add_block(data="Legitimate block")
        assert chain.is_chain_valid().is_valid

        # Attack: Attacker modifies block validator to an unregistered node
        b1.validator = "Hacker_Node_666"
        from backend.blockchain.hashing import calculate_block_hash
        b1.hash = calculate_block_hash(b1)  # Hash is cryptographically valid, but consensus rule broken!

        val = chain.is_chain_valid()
        assert not val.is_valid, "Block with unregistered validator MUST fail validation!"
        assert "fails Proof of Stake validator validation rule" in val.reason
        print(f"[OK] Security Check Passed: Unregistered validator 'Hacker_Node_666' successfully rejected: {val.reason}")
    finally:
        cleanup_db(db_name)


def test_input_validation_and_edge_cases():
    print("\n--- 5. Testing Input Validation & Edge Cases ---")
    chain, db_name = get_fresh_chain()
    try:
        # Invalid stake: NaN / Infinity / Negative
        try:
            chain.add_validator("BadNode", float("nan"))
            assert False, "Should reject NaN stake"
        except ValueError:
            pass

        try:
            chain.add_validator("BadNode", -50.0)
            assert False, "Should reject negative stake"
        except ValueError:
            pass

        try:
            chain.add_validator("", 100.0)
            assert False, "Should reject empty validator name"
        except ValueError:
            pass

        # Mempool validation: NaN amount
        try:
            chain.mempool.add_transaction(Transaction("Alice", "Bob", float("nan")))
            assert False, "Should reject NaN amount transaction"
        except ValueError:
            pass

        # Mempool validation: negative amount
        try:
            chain.mempool.add_transaction(Transaction("Alice", "Bob", -10.0))
            assert False, "Should reject negative amount transaction"
        except ValueError:
            pass

        print("[OK] All invalid and malicious edge-case inputs successfully rejected.")
    finally:
        cleanup_db(db_name)


def test_mempool_and_merkle():
    print("\n--- 6. Testing Mempool & Merkle Trees in PoS ---")
    chain, db_name = get_fresh_chain()
    try:
        chain.mempool.add_transaction(Transaction("Alice", "Bob", 12.5))
        chain.mempool.add_transaction(Transaction("Bob", "Charlie", 3.0))
        assert chain.mempool.count() == 2

        # Block proposal includes mempool transactions
        b_tx = chain.add_block(data="Block with mempool txs")
        assert len(b_tx.transactions) == 2
        assert b_tx.merkle_root != ""
        assert chain.mempool.count() == 0  # Cleared after block inclusion
        print(f"[OK] Sealed Block with Mempool Txs: Txs Count={len(b_tx.transactions)}, Merkle Root={b_tx.merkle_root[:16]}... Validator={b_tx.validator}")

        val = chain.is_chain_valid()
        assert val.is_valid
        print("[OK] Mempool & Merkle Root integration verified.")
    finally:
        cleanup_db(db_name)


def test_concurrency_thread_safety():
    print("\n--- 7. Testing Concurrency & Thread Safety ---")
    chain, db_name = get_fresh_chain()
    try:
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
    finally:
        cleanup_db(db_name)


def test_database_persistence():
    print("\n--- 8. Testing Database Persistence Across Restarts ---")
    db_name = f"test_persist_{uuid.uuid4().hex[:8]}.db"
    try:
        # Phase 1: Initialize blockchain, create blocks, add validator
        db1 = DatabaseManager(db_name)
        chain1 = Blockchain(db=db1)
        b1 = chain1.add_block(data="Persistent Block 1")
        b2 = chain1.add_block(data="Persistent Block 2")
        v_pers = chain1.add_validator(name="Persistent_Node", stake=77.0)
        assert len(chain1.blocks) == 3
        assert "Persistent_Node" in chain1.validators

        # Phase 2: Simulate complete server reboot (new Blockchain instance reading from same DB)
        db2 = DatabaseManager(db_name)
        chain2 = Blockchain(db=db2)
        assert len(chain2.blocks) == 3, f"Expected 3 blocks after restart, got {len(chain2.blocks)}"
        assert chain2.blocks[1].data == "Persistent Block 1"
        assert chain2.blocks[2].data == "Persistent Block 2"
        assert chain2.blocks[1].hash == b1.hash
        assert chain2.blocks[2].hash == b2.hash
        assert "Persistent_Node" in chain2.validators
        assert chain2.validators["Persistent_Node"].stake == 77.0
        val = chain2.is_chain_valid()
        assert val.is_valid, f"Restored chain must be valid: {val.reason}"
        print("[OK] Database persistence verified: blocks and validators survive server restart intact.")
    finally:
        cleanup_db(db_name)


def test_authentication_and_rbac():
    print("\n--- 9. Testing Authentication, PBKDF2 Hashing & RBAC ---")
    db_name = f"test_auth_{uuid.uuid4().hex[:8]}.db"
    try:
        db = DatabaseManager(db_name)
        seed_default_users(db)

        # 1. Default user accounts
        admin_u = db.get_user('admin')
        viewer_u = db.get_user('viewer')
        assert admin_u is not None, "Admin user must exist"
        assert viewer_u is not None, "Viewer user must exist"
        assert admin_u['role'] == 'admin'
        assert viewer_u['role'] == 'viewer'
        assert verify_password('admin123', admin_u['password_hash'], admin_u['salt'])
        assert verify_password('viewer123', viewer_u['password_hash'], viewer_u['salt'])
        assert not verify_password('wrongpass', admin_u['password_hash'], admin_u['salt'])
        print("[OK] Default accounts seeded & PBKDF2 password verification confirmed.")

        # 2. Cryptographic session tokens
        admin_token = generate_token('admin', 'admin')
        viewer_token = generate_token('viewer', 'viewer')

        admin_claims = verify_token(admin_token)
        assert admin_claims is not None
        assert admin_claims['username'] == 'admin' and admin_claims['role'] == 'admin'

        viewer_claims = verify_token(viewer_token)
        assert viewer_claims is not None
        assert viewer_claims['username'] == 'viewer' and viewer_claims['role'] == 'viewer'

        assert verify_token('invalid.token') is None
        print("[OK] Cryptographic session tokens and role verification confirmed.")
    finally:
        cleanup_db(db_name)


if __name__ == "__main__":
    test_genesis_and_pos_block_creation()
    test_validator_pool_and_slashing()
    test_tamper_and_reseal()
    test_security_unregistered_validator_rejection()
    test_input_validation_and_edge_cases()
    test_mempool_and_merkle()
    test_concurrency_thread_safety()
    test_database_persistence()
    test_authentication_and_rbac()
    print("\n[ALL AUDIT, SECURITY, PERSISTENCE & AUTH TESTS PASSED WITH 100% SUCCESS!]")