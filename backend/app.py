"""
Flask Web REST API and WebSockets server for the Blockchain Engine.
Exposes control endpoints for mining, tampering, re-mining, consensus mode switching,
mempool management, and validator registry manipulation.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.blockchain import Blockchain, Transaction

app = Flask(__name__)
app.config['SECRET_KEY'] = 'blockchain_sim_secret_key_2026'
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*")

# Global singleton Blockchain instance
blockchain_engine = Blockchain(consensus_mode="pow", difficulty=3)


@app.route('/api/chain', methods=['GET'])
def get_chain():
    """Return full blockchain state, blocks, validation status, and configuration."""
    return jsonify({
        "success": True,
        "data": blockchain_engine.to_dict()
    })


@app.route('/api/mine', methods=['POST'])
def mine_block():
    """Mine or select a new block."""
    req = request.get_json() or {}
    data_payload = req.get("data", "")
    validator_name = req.get("validator", None)

    def on_mining_progress(index: int, nonce: int, current_hash: str):
        # Emit WebSocket progress every 5000 iterations
        socketio.emit('mining_progress', {
            "index": index,
            "nonce": nonce,
            "hash": current_hash
        })

    try:
        new_block = blockchain_engine.add_block(
            data=data_payload,
            validator_name=validator_name,
            progress_callback=on_mining_progress
        )
        response_payload = {
            "success": True,
            "block": new_block.to_dict(),
            "chain_state": blockchain_engine.to_dict()
        }
        # Broadcast block addition to all connected UI clients
        socketio.emit('block_added', response_payload)
        return jsonify(response_payload), 201

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/api/tamper/<int:index>', methods=['POST'])
def tamper_block(index: int):
    """Simulate cyber attack on a block's data payload without re-mining."""
    req = request.get_json() or {}
    new_data = req.get("data", "TAMPERED DATA PAYLOAD")

    try:
        tampered_block = blockchain_engine.tamper_block(index=index, new_data=new_data)
        validation = blockchain_engine.is_chain_valid()
        response_payload = {
            "success": True,
            "tampered_index": index,
            "block": tampered_block.to_dict(),
            "validation": validation.to_dict(),
            "chain_state": blockchain_engine.to_dict()
        }
        socketio.emit('chain_tampered', response_payload)
        return jsonify(response_payload), 200

    except IndexError as ie:
        return jsonify({"success": False, "error": str(ie)}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/api/remine/<int:index>', methods=['POST'])
def remine_block(index: int):
    """Re-mine or re-seal a specific single block."""
    def on_mining_progress(idx: int, nonce: int, current_hash: str):
        socketio.emit('mining_progress', {
            "index": idx,
            "nonce": nonce,
            "hash": current_hash
        })

    try:
        remined_block = blockchain_engine.remine_block(index=index, progress_callback=on_mining_progress)
        validation = blockchain_engine.is_chain_valid()
        response_payload = {
            "success": True,
            "remined_index": index,
            "block": remined_block.to_dict(),
            "validation": validation.to_dict(),
            "chain_state": blockchain_engine.to_dict()
        }
        socketio.emit('block_remined', response_payload)
        return jsonify(response_payload), 200

    except IndexError as ie:
        return jsonify({"success": False, "error": str(ie)}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/api/validate', methods=['GET'])
def validate_chain():
    """Return chain validation status report."""
    validation = blockchain_engine.is_chain_valid()
    return jsonify({
        "success": True,
        "validation": validation.to_dict()
    })


@app.route('/api/consensus', methods=['POST'])
def set_consensus():
    """Swap consensus mode (pow / pos) or update PoW difficulty."""
    req = request.get_json() or {}
    mode = req.get("mode", blockchain_engine.consensus_mode)
    difficulty = req.get("difficulty", None)

    try:
        if difficulty is not None:
            difficulty = int(difficulty)
        blockchain_engine.set_consensus_mode(mode=mode, difficulty=difficulty)
        
        response_payload = {
            "success": True,
            "consensus_mode": blockchain_engine.consensus_mode,
            "pow_difficulty": blockchain_engine.pow_strategy.difficulty,
            "chain_state": blockchain_engine.to_dict()
        }
        socketio.emit('consensus_updated', response_payload)
        return jsonify(response_payload), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/api/mempool', methods=['GET', 'POST'])
def handle_mempool():
    """Get pending mempool transactions or submit a new transaction."""
    if request.method == 'GET':
        return jsonify({
            "success": True,
            "count": blockchain_engine.mempool.count(),
            "pending_transactions": blockchain_engine.mempool.to_list()
        })

    # POST submit new transaction
    req = request.get_json() or {}
    try:
        tx = Transaction(
            sender=req.get("sender", "Anonymous"),
            recipient=req.get("recipient", "Anonymous"),
            amount=float(req.get("amount", 0.0))
        )
        tx_id = blockchain_engine.mempool.add_transaction(tx)
        response_payload = {
            "success": True,
            "tx_id": tx_id,
            "tx": tx.to_dict(),
            "mempool_count": blockchain_engine.mempool.count()
        }
        socketio.emit('mempool_updated', response_payload)
        return jsonify(response_payload), 201

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/api/validators', methods=['GET', 'POST'])
def handle_validators():
    """Manage PoS validator registry."""
    if request.method == 'GET':
        return jsonify({
            "success": True,
            "validators": [v.to_dict() for v in blockchain_engine.validators.values()]
        })

    req = request.get_json() or {}
    action = req.get("action", "add")
    name = req.get("name")
    stake = req.get("stake", 0.0)

    try:
        if action == "slash":
            v = blockchain_engine.slash_validator(name)
        elif action == "update":
            v = blockchain_engine.update_validator_stake(name, float(stake))
        else:
            v = blockchain_engine.add_validator(name, float(stake))

        response_payload = {
            "success": True,
            "validator": v.to_dict(),
            "validators": [val.to_dict() for val in blockchain_engine.validators.values()]
        }
        socketio.emit('validators_updated', response_payload)
        return jsonify(response_payload), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# WebSocket Connection Handlers
@socketio.on('connect')
def handle_connect():
    emit('connection_response', {
        'status': 'connected',
        'chain_state': blockchain_engine.to_dict()
    })


if __name__ == '__main__':
    print("[SERVER] Blockchain Simulation Server running on http://127.0.0.1:5000")
    socketio.run(app, host='127.0.0.1', port=5000, debug=True)
