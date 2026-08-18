
"""
Verification test suite for the Blockchain Simulation engine.
Validates PoW mining, PoS validator selection, mempool handling, tamper detection,
and re-mining workflows cleanly.
"""

import sys
import os

# Ensure backend package path is available
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.blockchain import Blockchain, Transaction


def test_pow_mining_and_validation():
    print("--- 1. Testing Proof of Work (PoW) Mining & Validation ---")
    chain = Blockchain(consensus_mode="pow", difficulty=3)
    
    # Add blocks
    b1 = chain.add_block(data="Alice pays Bob 10 coins")
    print(f"Mined Block #1: Hash={b1.hash[:16]}... Nonce={b1.nonce} Time={b1.mining_time:.4f}s")
    
    b2 = chain.add_block(data="Bob pays Carol 5 coins")
    print(f"Mined Block #2: Hash={b2.hash[:16]}... Nonce={b2.nonce} Time={b2.mining_time:.4f}s")
    
    val = chain.is_chain_valid()
    assert val.is_valid, f"Validation failed: {val.reason}"
    print(f"[OK] Initial Chain Status: {val.reason}")

    # Tamper test
    print("\n--- 2. Testing Tamper Detection ---")
    chain.tamper_block(1, new_data="Alice pays Bob 1000 coins (TAMPERED!)")
    val_tampered = chain.is_chain_valid()
    assert not val_tampered.is_valid, "Tampered chain should be marked invalid!"
    assert val_tampered.broken_at_index == 1, f"Expected broken at 1, got {val_tampered.broken_at_index}"
    print(f"[OK] Tamper Detection Success: Flagged broken at Block #{val_tampered.broken_at_index} - {val_tampered.reason}")

    # Re-mine test
    print("\n--- 3. Testing Single Block Re-mining ---")
    chain.remine_block(1)
    # Note: re-mining block 1 fixes block 1, but block 2 still has previous_hash pointing to old block 1 hash!
    val_remined = chain.is_chain_valid()
    print(f"Status after re-mining Block #1: Valid={val_remined.is_valid}, BrokenAt={val_remined.broken_at_index}")
    assert val_remined.broken_at_index == 2, "Re-mining Block 1 should leave Block 2 broken due to link pointer mismatch!"
    print("[OK] Cascade re-mine dependency verified (Block #2 correctly remains broken).")


def test_pos_staking():
    print("\n--- 4. Testing Proof of Stake (PoS) Mode ---")
    chain = Blockchain(consensus_mode="pos")
    
    b1 = chain.add_block(data="PoS Transaction 1")
    print(f"PoS Block #1: Selected Validator={b1.validator}, Hash={b1.hash[:16]}...")
    
    b2 = chain.add_block(data="PoS Transaction 2")
    print(f"PoS Block #2: Selected Validator={b2.validator}, Hash={b2.hash[:16]}...")
    
    val = chain.is_chain_valid()
    assert val.is_valid, f"PoS Chain validation failed: {val.reason}"
    print(f"[OK] PoS Chain Status: {val.reason}")


def test_mempool():
    print("\n--- 5. Testing Mempool & Merkle Trees ---")
    chain = Blockchain(consensus_mode="pow", difficulty=2)
    
    tx1 = Transaction(sender="Alice", recipient="Bob", amount=25.0)
    tx2 = Transaction(sender="Bob", recipient="Carol", amount=12.5)
    
    chain.mempool.add_transaction(tx1)
    chain.mempool.add_transaction(tx2)
    assert chain.mempool.count() == 2, "Mempool should hold 2 transactions"
    
    b = chain.add_block()
    print(f"Mined Block with Mempool Txs: Txs Count={len(b.transactions)}, Merkle Root={b.merkle_root[:16]}...")
    assert len(b.transactions) == 2, "Block should contain the 2 mempool transactions"
    assert chain.mempool.count() == 0, "Mempool should be cleared after block mining"
    print("[OK] Mempool & Merkle Root integration verified.")


if __name__ == "__main__":
    test_pow_mining_and_validation()
    test_pos_staking()
    test_mempool()
    print("\n[ALL TESTS PASSED SUCCESSFULLY!]")
