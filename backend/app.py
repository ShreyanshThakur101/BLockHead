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
from backend.auth import (
    hash_password,
    verify_password,
    generate_token,
    verify_token,
    get_current_user,
    require_auth,
    require_admin,
    seed_default_users
)

public_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "public"))
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
static_dir = public_dir if os.path.exists(public_dir) else frontend_dir

app = Flask(__name__, static_folder=static_dir, static_url_path="")
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'blockchain_sim_secret_key_2026')
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*")

# Global singleton Blockchain instance (Pure Proof of Stake with Database persistence)
blockchain_engine = Blockchain()
seed_default_users(blockchain_engine.db)


@app.route('/')
def index():
    """Serve the 2D visualizer web frontend."""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/health', methods=['GET'])
@app.route('/health', methods=['GET'])
def health_check():
    """Return health status of the blockchain simulation server."""
    return jsonify({
        "success": True,
        "status": "healthy",
        "service": "blockchain-pos-simulator"
    }), 200


@app.route('/api/chain', methods=['GET'])
@app.route('/chain', methods=['GET'])
def get_chain():
    """Return full blockchain state, blocks, validation status, and configuration."""
    return jsonify({
        "success": True,
        "data": blockchain_engine.to_dict()
    })


# ==============================================================================
# AUTHENTICATION & RBAC ENDPOINTS
# ==============================================================================

@app.route('/api/auth/register', methods=['POST'])
@app.route('/auth/register', methods=['POST'])
def auth_register():
    """Register a new user with chosen role (admin or viewer)."""
    req = request.get_json(silent=True) or {}
    username = str(req.get('username', '')).strip()
    password = str(req.get('password', '')).strip()
    role = str(req.get('role', 'viewer')).strip().lower()
    
    if not username or len(username) < 3:
        return jsonify({"success": False, "error": "Username must be at least 3 characters."}), 400
    if not password or len(password) < 6:
        return jsonify({"success": False, "error": "Password must be at least 6 characters."}), 400
    if role not in ['admin', 'viewer']:
        role = 'viewer'
        
    if blockchain_engine.db.get_user(username):
        return jsonify({"success": False, "error": f"Username '{username}' is already taken."}), 409
        
    pwd_hash, salt = hash_password(password)
    ok = blockchain_engine.db.create_user(username, pwd_hash, salt, role=role)
    if not ok:
        return jsonify({"success": False, "error": "Failed to register user."}), 500
        
    token = generate_token(username, role)
    return jsonify({
        "success": True,
        "message": f"Registered successfully as {role}.",
        "token": token,
        "user": {
            "username": username,
            "role": role
        }
    }), 201


@app.route('/api/auth/login', methods=['POST'])
@app.route('/auth/login', methods=['POST'])
def auth_login():
    """Sign in existing user and return bearer token with role."""
    req = request.get_json(silent=True) or {}
    username = str(req.get('username', '')).strip()
    password = str(req.get('password', '')).strip()
    
    if not username or not password:
        return jsonify({"success": False, "error": "Username and password are required."}), 400
        
    user_record = blockchain_engine.db.get_user(username)
    if not user_record or not verify_password(password, user_record['password_hash'], user_record['salt']):
        return jsonify({"success": False, "error": "Invalid username or password."}), 401
        
    token = generate_token(user_record['username'], user_record['role'])
    return jsonify({
        "success": True,
        "message": "Login successful.",
        "token": token,
        "user": {
            "username": user_record['username'],
            "role": user_record['role']
        }
    }), 200


@app.route('/api/auth/me', methods=['GET'])
@app.route('/auth/me', methods=['GET'])
def auth_me():
    """Return currently authenticated user profile and permissions."""
    user = get_current_user()
    if not user:
        return jsonify({
            "success": True,
            "authenticated": False,
            "user": None
        }), 200
    return jsonify({
        "success": True,
        "authenticated": True,
        "user": user
    }), 200


@app.route('/api/mine', methods=['POST'])
@app.route('/api/forge', methods=['POST'])
@app.route('/mine', methods=['POST'])
@app.route('/forge', methods=['POST'])
@require_admin
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
@app.route('/tamper/<int:index>', methods=['POST'])
@require_admin
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
@app.route('/reseal/<int:index>', methods=['POST'])
@app.route('/remine/<int:index>', methods=['POST'])
@require_admin
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
@app.route('/validate', methods=['GET'])
def validate_chain():
    """Return chain validation status report."""
    validation = blockchain_engine.is_chain_valid()
    return jsonify({
        "success": True,
        "validation": validation.to_dict()
    })


@app.route('/api/consensus', methods=['GET', 'POST'])
@app.route('/consensus', methods=['GET', 'POST'])
def get_consensus():
    """Return current consensus configuration (Proof of Stake)."""
    return jsonify({
        "success": True,
        "consensus_mode": "pos",
        "chain_state": blockchain_engine.to_dict()
    }), 200


@app.route('/api/mempool', methods=['GET', 'POST'])
@app.route('/mempool', methods=['GET', 'POST'])
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
@app.route('/validators', methods=['GET', 'POST'])
def handle_validators():
    """Manage PoS validator registry."""
    if request.method == 'GET':
        return jsonify({
            "success": True,
            "validators": [v.to_dict() for v in blockchain_engine.validators.values()]
        })

    # Mutation actions (add, slash, update) require Admin privileges
    user = get_current_user()
    if not user or user.get("role") != "admin":
        return jsonify({
            "success": False,
            "error": "Forbidden: Managing validators requires Admin privileges. Please sign in as admin."
        }), 403

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
