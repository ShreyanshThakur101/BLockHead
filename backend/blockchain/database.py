"""
Database persistence layer for Blockchain Simulator.
Supports zero-configuration local SQLite storage and cloud PostgreSQL (Supabase/Neon/Vercel Postgres)
via DATABASE_URL environment variable.
"""

import os
import sys
import json
import sqlite3
import threading
import time
from typing import List, Dict, Optional, Any
from urllib.parse import urlparse

from backend.blockchain.models import Block, Validator, Transaction


class DatabaseManager:
    def __init__(self, db_url: Optional[str] = None):
        self.lock = threading.RLock()
        self.db_url = db_url or os.environ.get('DATABASE_URL')
        self.is_postgres = False
        self.sqlite_path = None
        
        if self.db_url and self.db_url.endswith('.db'):
            self.sqlite_path = self.db_url
        elif self.db_url and ('postgres://' in self.db_url or 'postgresql://' in self.db_url):
            self.is_postgres = True
        else:
            db_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            preferred_path = os.path.join(db_dir, 'blockchain.db')
            try:
                with open(preferred_path + '.test', 'w') as f:
                    f.write('1')
                os.remove(preferred_path + '.test')
                self.sqlite_path = preferred_path
            except Exception:
                self.sqlite_path = '/tmp/blockchain.db'

        self.init_schema()

    def _get_connection(self):
        if self.is_postgres:
            try:
                import pg8000.native
                parsed = urlparse(self.db_url)
                user = parsed.username
                password = parsed.password
                host = parsed.hostname
                port = parsed.port or 5432
                database = parsed.path.lstrip('/')
                
                conn = pg8000.native.Connection(
                    user=user,
                    password=password,
                    host=host,
                    port=port,
                    database=database,
                    ssl_context=True
                )
                return conn
            except Exception as e:
                print(f'[DatabaseManager] Postgres connection error: {e}. Falling back to SQLite.')
                self.is_postgres = False
                self.sqlite_path = '/tmp/blockchain.db' if not self.sqlite_path else self.sqlite_path
                return sqlite3.connect(self.sqlite_path, check_same_thread=False)
        else:
            conn = sqlite3.connect(self.sqlite_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            return conn

    def init_schema(self):
        with self.lock:
            conn = self._get_connection()
            try:
                if self.is_postgres:
                    conn.run('''
                        CREATE TABLE IF NOT EXISTS users (
                            id SERIAL PRIMARY KEY,
                            username VARCHAR(100) UNIQUE NOT NULL,
                            password_hash VARCHAR(256) NOT NULL,
                            salt VARCHAR(64) NOT NULL,
                            role VARCHAR(32) NOT NULL DEFAULT 'viewer',
                            created_at DOUBLE PRECISION NOT NULL
                        );
                        CREATE TABLE IF NOT EXISTS blocks (
                            block_index INTEGER PRIMARY KEY,
                            hash VARCHAR(128) NOT NULL,
                            previous_hash VARCHAR(128) NOT NULL,
                            timestamp DOUBLE PRECISION NOT NULL,
                            validator VARCHAR(100) NOT NULL,
                            data TEXT NOT NULL,
                            transactions_json TEXT NOT NULL DEFAULT '[]',
                            merkle_root VARCHAR(128) NOT NULL,
                            validation_time DOUBLE PRECISION NOT NULL DEFAULT 0.0
                        );
                        CREATE TABLE IF NOT EXISTS validators (
                            name VARCHAR(100) PRIMARY KEY,
                            stake DOUBLE PRECISION NOT NULL,
                            is_slashed BOOLEAN NOT NULL DEFAULT FALSE
                        );
                        CREATE TABLE IF NOT EXISTS mempool (
                            id VARCHAR(100) PRIMARY KEY,
                            sender VARCHAR(100) NOT NULL,
                            recipient VARCHAR(100) NOT NULL,
                            amount DOUBLE PRECISION NOT NULL,
                            timestamp DOUBLE PRECISION NOT NULL
                        );
                    ''')
                else:
                    cursor = conn.cursor()
                    cursor.executescript('''
                        CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT UNIQUE NOT NULL,
                            password_hash TEXT NOT NULL,
                            salt TEXT NOT NULL,
                            role TEXT NOT NULL DEFAULT 'viewer',
                            created_at REAL NOT NULL
                        );
                        CREATE TABLE IF NOT EXISTS blocks (
                            block_index INTEGER PRIMARY KEY,
                            hash TEXT NOT NULL,
                            previous_hash TEXT NOT NULL,
                            timestamp REAL NOT NULL,
                            validator TEXT NOT NULL,
                            data TEXT NOT NULL,
                            transactions_json TEXT NOT NULL DEFAULT '[]',
                            merkle_root TEXT NOT NULL,
                            validation_time REAL NOT NULL DEFAULT 0.0
                        );
                        CREATE TABLE IF NOT EXISTS validators (
                            name TEXT PRIMARY KEY,
                            stake REAL NOT NULL,
                            is_slashed INTEGER NOT NULL DEFAULT 0
                        );
                        CREATE TABLE IF NOT EXISTS mempool (
                            id TEXT PRIMARY KEY,
                            sender TEXT NOT NULL,
                            recipient TEXT NOT NULL,
                            amount REAL NOT NULL,
                            timestamp REAL NOT NULL
                        );
                    ''')
                    conn.commit()
            finally:
                conn.close()

    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        with self.lock:
            conn = self._get_connection()
            try:
                if self.is_postgres:
                    rows = conn.run('SELECT username, password_hash, salt, role, created_at FROM users WHERE username = :u', u=username)
                    if rows:
                        r = rows[0]
                        return {'username': r[0], 'password_hash': r[1], 'salt': r[2], 'role': r[3], 'created_at': r[4]}
                else:
                    cursor = conn.cursor()
                    cursor.execute('SELECT username, password_hash, salt, role, created_at FROM users WHERE username = ?', (username,))
                    r = cursor.fetchone()
                    if r:
                        return {'username': r['username'], 'password_hash': r['password_hash'], 'salt': r['salt'], 'role': r['role'], 'created_at': r['created_at']}
                return None
            finally:
                conn.close()

    def create_user(self, username: str, password_hash: str, salt: str, role: str = 'viewer') -> bool:
        with self.lock:
            conn = self._get_connection()
            now = time.time()
            try:
                if self.is_postgres:
                    conn.run('INSERT INTO users (username, password_hash, salt, role, created_at) VALUES (:u, :p, :s, :r, :c) ON CONFLICT (username) DO NOTHING',
                             u=username, p=password_hash, s=salt, r=role, c=now)
                else:
                    cursor = conn.cursor()
                    cursor.execute('INSERT OR IGNORE INTO users (username, password_hash, salt, role, created_at) VALUES (?, ?, ?, ?, ?)',
                                   (username, password_hash, salt, role, now))
                    conn.commit()
                return True
            except Exception as e:
                print(f'[DatabaseManager] Error creating user: {e}')
                return False
            finally:
                conn.close()

    def load_blocks(self) -> List[Block]:
        with self.lock:
            conn = self._get_connection()
            blocks = []
            try:
                if self.is_postgres:
                    rows = conn.run('SELECT block_index, hash, previous_hash, timestamp, validator, data, transactions_json, merkle_root, validation_time FROM blocks ORDER BY block_index ASC')
                    for r in rows:
                        txs_raw = json.loads(r[6]) if r[6] else []
                        txs = [Transaction.from_dict(t) for t in txs_raw]
                        b = Block(index=r[0], hash=r[1], previous_hash=r[2], timestamp=r[3], validator=r[4], data=r[5], transactions=txs, merkle_root=r[7], validation_time=r[8])
                        blocks.append(b)
                else:
                    cursor = conn.cursor()
                    cursor.execute('SELECT block_index, hash, previous_hash, timestamp, validator, data, transactions_json, merkle_root, validation_time FROM blocks ORDER BY block_index ASC')
                    for r in cursor.fetchall():
                        txs_raw = json.loads(r['transactions_json']) if r['transactions_json'] else []
                        txs = [Transaction.from_dict(t) for t in txs_raw]
                        b = Block(index=r['block_index'], hash=r['hash'], previous_hash=r['previous_hash'], timestamp=r['timestamp'], validator=r['validator'], data=r['data'], transactions=txs, merkle_root=r['merkle_root'], validation_time=r['validation_time'])
                        blocks.append(b)
                return blocks
            finally:
                conn.close()

    def save_block(self, block: Block):
        with self.lock:
            conn = self._get_connection()
            txs_json = json.dumps([tx.to_dict() for tx in block.transactions])
            try:
                if self.is_postgres:
                    conn.run('''
                        INSERT INTO blocks (block_index, hash, previous_hash, timestamp, validator, data, transactions_json, merkle_root, validation_time)
                        VALUES (:idx, :h, :ph, :ts, :val, :d, :txs, :mr, :vt)
                        ON CONFLICT (block_index) DO UPDATE SET
                            hash = EXCLUDED.hash,
                            previous_hash = EXCLUDED.previous_hash,
                            timestamp = EXCLUDED.timestamp,
                            validator = EXCLUDED.validator,
                            data = EXCLUDED.data,
                            transactions_json = EXCLUDED.transactions_json,
                            merkle_root = EXCLUDED.merkle_root,
                            validation_time = EXCLUDED.validation_time
                    ''', idx=block.index, h=block.hash, ph=block.previous_hash, ts=block.timestamp,
                         val=block.validator, d=block.data, txs=txs_json, mr=block.merkle_root, vt=block.validation_time)
                else:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO blocks (block_index, hash, previous_hash, timestamp, validator, data, transactions_json, merkle_root, validation_time)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(block_index) DO UPDATE SET
                            hash=excluded.hash,
                            previous_hash=excluded.previous_hash,
                            timestamp=excluded.timestamp,
                            validator=excluded.validator,
                            data=excluded.data,
                            transactions_json=excluded.transactions_json,
                            merkle_root=excluded.merkle_root,
                            validation_time=excluded.validation_time
                    ''', (block.index, block.hash, block.previous_hash, block.timestamp,
                          block.validator, block.data, txs_json, block.merkle_root, block.validation_time))
                    conn.commit()
            finally:
                conn.close()

    def replace_blocks(self, blocks: List[Block]):
        with self.lock:
            conn = self._get_connection()
            try:
                if self.is_postgres:
                    conn.run('DELETE FROM blocks')
                else:
                    conn.execute('DELETE FROM blocks')
                    conn.commit()
                for b in blocks:
                    self.save_block(b)
            finally:
                conn.close()

    def load_validators(self) -> Dict[str, Validator]:
        with self.lock:
            conn = self._get_connection()
            validators = {}
            try:
                if self.is_postgres:
                    rows = conn.run('SELECT name, stake, is_slashed FROM validators')
                    for r in rows:
                        validators[r[0]] = Validator(name=r[0], stake=float(r[1]), is_slashed=bool(r[2]))
                else:
                    cursor = conn.cursor()
                    cursor.execute('SELECT name, stake, is_slashed FROM validators')
                    for r in cursor.fetchall():
                        validators[r['name']] = Validator(name=r['name'], stake=float(r['stake']), is_slashed=bool(r['is_slashed']))
                return validators
            finally:
                conn.close()

    def save_validator(self, validator: Validator):
        with self.lock:
            conn = self._get_connection()
            try:
                if self.is_postgres:
                    conn.run('''
                        INSERT INTO validators (name, stake, is_slashed)
                        VALUES (:n, :s, :sl)
                        ON CONFLICT (name) DO UPDATE SET
                            stake = EXCLUDED.stake,
                            is_slashed = EXCLUDED.is_slashed
                    ''', n=validator.name, s=validator.stake, sl=validator.is_slashed)
                else:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO validators (name, stake, is_slashed)
                        VALUES (?, ?, ?)
                        ON CONFLICT(name) DO UPDATE SET
                            stake=excluded.stake,
                            is_slashed=excluded.is_slashed
                    ''', (validator.name, validator.stake, 1 if validator.is_slashed else 0))
                    conn.commit()
            finally:
                conn.close()

    def load_mempool(self) -> List[Transaction]:
        with self.lock:
            conn = self._get_connection()
            txs = []
            try:
                if self.is_postgres:
                    rows = conn.run('SELECT id, sender, recipient, amount, timestamp FROM mempool ORDER BY timestamp ASC')
                    for r in rows:
                        txs.append(Transaction(tx_id=r[0], sender=r[1], recipient=r[2], amount=float(r[3]), timestamp=float(r[4])))
                else:
                    cursor = conn.cursor()
                    cursor.execute('SELECT id, sender, recipient, amount, timestamp FROM mempool ORDER BY timestamp ASC')
                    for r in cursor.fetchall():
                        txs.append(Transaction(tx_id=r['id'], sender=r['sender'], recipient=r['recipient'], amount=float(r['amount']), timestamp=float(r['timestamp'])))
                return txs
            finally:
                conn.close()

    def add_mempool_tx(self, tx: Transaction):
        with self.lock:
            conn = self._get_connection()
            tx_id = tx.tx_id or f'{tx.sender}_{tx.recipient}_{tx.timestamp}'
            try:
                if self.is_postgres:
                    conn.run('INSERT INTO mempool (id, sender, recipient, amount, timestamp) VALUES (:id, :s, :r, :a, :ts) ON CONFLICT (id) DO NOTHING',
                             id=tx_id, s=tx.sender, r=tx.recipient, a=tx.amount, ts=tx.timestamp)
                else:
                    cursor = conn.cursor()
                    cursor.execute('INSERT OR IGNORE INTO mempool (id, sender, recipient, amount, timestamp) VALUES (?, ?, ?, ?, ?)',
                                   (tx_id, tx.sender, tx.recipient, tx.amount, tx.timestamp))
                    conn.commit()
            finally:
                conn.close()

    def clear_mempool(self):
        with self.lock:
            conn = self._get_connection()
            try:
                if self.is_postgres:
                    conn.run('DELETE FROM mempool')
                else:
                    conn.execute('DELETE FROM mempool')
                    conn.commit()
            finally:
                conn.close()