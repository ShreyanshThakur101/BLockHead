"""
Flask Web REST API and WebSockets server for the Proof of Stake (PoS) Blockchain Engine.
Exposes control endpoints for block proposing, tampering, re-sealing,
mempool management, and validator registry manipulation.
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import sys
import os
import math

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.blockchain import Blockchain, Transaction

frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
app = Flask(__name__, static_folder=frontend_dir, static_url_path="")
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'blockchain_sim_secret_key_2026')
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*")

# Global singleton Blockchain instance (Pure Proof of Stake)
blockchain_engine = Blockchain()


@app.route('/')
def index():
    """Serve the 2D visualizer web frontend."""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/health', methods=['GET'])
def health_check():
    """Return health status of the blockchain simulation server."""
    return jsonify({
        "success": True,
        "status": "healthy",
        "service": "blockchain-pos-simulator"
    }), 200


@app.route('/api/chain', methods=['GET'])
def get_chain():
    """Return full blockchain state, blocks, validation status, and configuration."""
    return jsonify({
        "success": True,
        "data": blockchain_engine.to_dict()
    })


@app.route('/api/mine', methods=['POST'])
@app.route('/api/forge', methods=['POST'])
def forge_block():
    """Propose and seal a new block using Proof of Stake validator selection."""
    req = request.get_json(silent=True) or {}
    data_payload = str(req.get("data", ""))[:50000]  # Cap payload size for safety
    validator_name = req.get("validator")
    if validator_name:
        validator_name = str(validator_name).strip() or None

    try:
        new_block = blockchain_engine.add_block(
            data=data_payload,
            validator_name=validator_name
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
    """Simulate cyber attack on a block's data payload without re-sealing."""
    req = request.get_json(silent=True) or {}
    new_data = str(req.get("data", "TAMPERED DATA PAYLOAD"))[:50000]

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


@app.route('/api/reseal/<int:index>', methods=['POST'])
@app.route('/api/remine/<int:index>', methods=['POST'])
def reseal_block(index: int):
    """Re-seal a specific single block using PoS."""
    req = request.get_json(silent=True) or {}
    validator_name = req.get("validator")
    if validator_name:
        validator_name = str(validator_name).strip() or None

    try:
        resealed_block = blockchain_engine.reseal_block(index=index, validator_name=validator_name)
        validation = blockchain_engine.is_chain_valid()
        response_payload = {
            "success": True,
            "resealed_index": index,
            "remined_index": index,
            "block": resealed_block.to_dict(),
            "validation": validation.to_dict(),
            "chain_state": blockchain_engine.to_dict()
        }
        socketio.emit('block_resealed', response_payload)
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


@app.route('/api/consensus', methods=['GET', 'POST'])
def get_consensus():
    """Return current consensus configuration (Proof of Stake)."""
    return jsonify({
        "success": True,
        "consensus_mode": "pos",
        "chain_state": blockchain_engine.to_dict()
    }), 200


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
    req = request.get_json(silent=True) or {}
    raw_sender = req.get("sender", "")
    raw_recipient = req.get("recipient", "")
    raw_amount = req.get("amount")

    try:
        sender = str(raw_sender).strip()
        recipient = str(raw_recipient).strip()
        if not sender:
            sender = "Anonymous"
        if not recipient:
            recipient = "Anonymous"

        if raw_amount is None:
            raise ValueError("Transaction amount is required.")
        amount = float(raw_amount)
        if not math.isfinite(amount) or amount <= 0:
            raise ValueError("Amount must be a positive finite number.")

        tx = Transaction(sender=sender, recipient=recipient, amount=amount)
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

    req = request.get_json(silent=True) or {}
    action = str(req.get("action", "add")).lower()
    raw_name = req.get("name")
    raw_stake = req.get("stake", 0.0)

    if not raw_name or not str(raw_name).strip():
        return jsonify({"success": False, "error": "Validator name is required."}), 400

    name = str(raw_name).strip()

    try:
        if action == "slash":
            v = blockchain_engine.slash_validator(name)
        elif action == "update":
            try:
                stake = float(raw_stake)
            except (ValueError, TypeError):
                return jsonify({"success": False, "error": "Stake must be a valid number."}), 400
            v = blockchain_engine.update_validator_stake(name, stake)
        else:
            try:
                stake = float(raw_stake)
            except (ValueError, TypeError):
                return jsonify({"success": False, "error": "Stake must be a valid number."}), 400
            v = blockchain_engine.add_validator(name, stake)

        response_payload = {
            "success": True,
            "validator": v.to_dict(),
            "validators": [val.to_dict() for val in blockchain_engine.validators.values()]
        }
        socketio.emit('validators_updated', response_payload)
        return jsonify(response_payload), 200

    except KeyError as ke:
        return jsonify({"success": False, "error": str(ke).strip("'")}), 404
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
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    print(f"[SERVER] Blockchain Simulation Server running on http://{host}:{port}")
    socketio.run(app, host=host, port=port, debug=debug)
