"""
Authentication & Role-Based Access Control (RBAC) module.
Handles PBKDF2 password hashing, HMAC-signed session tokens,
and route-protection decorators.
"""

import os
import time
import json
import base64
import hmac
import hashlib
import secrets
from functools import wraps
from typing import Optional, Dict, Any, Tuple
from flask import request, jsonify

SECRET_KEY = os.environ.get('SECRET_KEY', 'blockchain_sim_auth_secret_2026')


def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """Hash password using PBKDF2-HMAC-SHA256."""
    if not salt:
        salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()
    return pwd_hash, salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Verify password against stored hash."""
    calc_hash, _ = hash_password(password, salt)
    return hmac.compare_digest(calc_hash, stored_hash)


def generate_token(username: str, role: str) -> str:
    """Generate tamper-proof HMAC-SHA256 signed bearer token."""
    payload = {
        "u": username,
        "r": role,
        "exp": int(time.time()) + (86400 * 7)  # 7 days validity
    }
    raw_payload = base64.urlsafe_b64encode(json.dumps(payload).encode('utf-8')).decode('utf-8').rstrip('=')
    signature = hmac.new(
        SECRET_KEY.encode('utf-8'),
        raw_payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return f"{raw_payload}.{signature}"


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Validate bearer token signature and expiration."""
    if not token or '.' not in token:
        return None
    try:
        raw_payload, signature = token.split('.', 1)
        expected_sig = hmac.new(
            SECRET_KEY.encode('utf-8'),
            raw_payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_sig):
            return None
            
        # Add padding back if necessary
        rem = len(raw_payload) % 4
        padded = raw_payload + ('=' * (4 - rem) if rem > 0 else '')
        payload = json.loads(base64.urlsafe_b64decode(padded.encode('utf-8')).decode('utf-8'))
        
        if time.time() > payload.get('exp', 0):
            return None  # Token expired
            
        return {
            "username": payload.get('u'),
            "role": payload.get('r')
        }
    except Exception:
        return None


def get_current_user() -> Optional[Dict[str, Any]]:
    """Extract and verify user from Authorization header."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    token = auth_header[7:].strip()
    return verify_token(token)


def require_auth(allowed_roles=None):
    """Decorator to enforce authentication and optional role restrictions."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if not user:
                return jsonify({
                    "success": False,
                    "error": "Authentication required. Please sign in."
                }), 401
                
            if allowed_roles and user.get("role") not in allowed_roles:
                return jsonify({
                    "success": False,
                    "error": f"Forbidden: Action requires one of {allowed_roles} roles. Your role is '{user.get('role')}'."
                }), 403
                
            request.user = user
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_admin(f):
    """Decorator to restrict access strictly to Admin role."""
    return require_auth(allowed_roles=['admin'])(f)


def seed_default_users(db_manager):
    """Ensure default demo admin and viewer accounts exist."""
    # 1. Admin: admin / admin123
    if not db_manager.get_user('admin'):
        h, s = hash_password('admin123')
        db_manager.create_user('admin', h, s, role='admin')
        
    # 2. Viewer: viewer / viewer123
    if not db_manager.get_user('viewer'):
        h, s = hash_password('viewer123')
        db_manager.create_user('viewer', h, s, role='viewer')