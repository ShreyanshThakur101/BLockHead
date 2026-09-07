# Blockchain Simulation & Visualizer — Extended Memory & Progress Report

**Project Name:** Blockchain & Consensus 2D Simulation (PoW & PoS Engine)  
**Repository Path:** `C:\Projects\blockchain-sim`  
**Created:** 2026-08-17 22:28:53 IST  
**Last Updated:** 2026-08-17 22:28:53 IST  

---

## 1. Executive Summary & Purpose
This document serves as the **extended context memory and progress log** for the Blockchain Simulation project. It tracks historical development steps with exact timestamps, records architectural decisions, monitors active task statuses, and details the comprehensive top-down design blueprint for building a production-grade, highly maintainable, modular, and extensible blockchain engine and visualizer.

---

## 2. Chronological Progress Log

### 🕒 Timestamp: `2026-08-17 22:23:50 IST`
- **Action:** Project initialization and requirement analysis.
- **Details:** Read and analyzed `blockchain-pos-simulation-guide.md` and `blockchain-pow-simulation-guide.md`.
- **Outcome:** Identified system scope, key features (PoW mining, PoS staking, block hashing, chain validation, tamper detection, REST API, HTML5 Canvas 2D visualizer, WebSocket live updates).

### 🕒 Timestamp: `2026-08-17 22:24:00 IST`
- **Action:** Codebase structure inspection.
- **Details:** Inspected `backend/` and `frontend/` directories.
- **Findings:**
  - `backend/blockchain.py`: Contains a basic skeleton `block` class draft (needs full refactoring into modular clean architecture).
  - `backend/requirements.txt`: Virtual environment dependencies file present.
  - `frontend/index.html`, `main.js`, `style.css`: Initialized as empty placeholder files.

### 🕒 Timestamp: `2026-08-17 22:31:30 IST`
- **Action:** Implemented backend domain engine (`backend/blockchain/`).
- **Details:** Created dataclasses (`models.py`), SHA-256 & Merkle Tree generator (`hashing.py`), PoW & PoS consensus strategies (`consensus.py`), transaction mempool (`mempool.py`), and master `Blockchain` engine class (`chain.py`).

### 🕒 Timestamp: `2026-08-17 22:35:30 IST`
- **Action:** Automated backend test execution.
- **Outcome:** Verified PoW noncing, PoS weighted lottery validator selection, mempool tx packing, tamper detection, and single block re-mining. All tests passed with zero errors (`test_engine.py`).

### 🕒 Timestamp: `2026-08-17 22:36:10 IST`
- **Action:** Implemented Flask REST + SocketIO WebSockets server & 2D Frontend Visualizer.
- **Details:** Created `backend/app.py` with 9 REST endpoints and WebSocket events. Built dark glassmorphism web app with HTML5 Canvas 2D engine (`frontend/`), camera panning/zooming, animated link pointers, tamper alert drawer, mempool modal, and PoS validator management panel.

---

## 3. Project Status Matrix

| Module / Component | Status | Description |
|---|---|---|
| **Extended Memory (`progress_report.md`)** | 🟢 Complete | Memory context log & top-down blueprint maintained. |
| **Backend Core (`backend/blockchain/`)** | 🟢 Complete | Dataclasses, hashing, Merkle trees, chain engine. |
| **Consensus Engine (PoW & PoS)** | 🟢 Complete | Dynamic mode toggle, noncing loop & weighted lottery. |
| **Mempool & Transactions** | 🟢 Complete | Pending tx queue, auto block packaging, Merkle root. |
| **REST & WebSocket API (`app.py`)** | 🟢 Complete | Flask endpoints + Socket.IO real-time ticker stream. |
| **Frontend UI Layout (`index.html` & `style.css`)** | 🟢 Complete | Dark glassmorphism interface, modals & drawers. |
| **Canvas 2D Renderer (`main.js` & `canvas.js`)** | 🟢 Complete | High-DPI 60 FPS interactive stage with panning & zoom. |
| **Interactive Inspector & Controls** | 🟢 Complete | Tamper attack trigger, re-mine tool, validator pool. |

---

## 4. Key Architectural Principles
To ensure the system is **reliable, simple to maintain, easy to debug, self-explanatory, and modular**:

1. **Strict Separation of Concerns**: Core engine logic (`domain/`) is 100% decoupled from Web API framework (`Flask`/`Sockets`) and rendering logic (`Canvas`). The engine can run in CLI, automated unit tests, or web server modes without code modifications.
2. **Deterministic Data Contracts**: Immutable dataclasses / clean dictionary representations with sorted key JSON serialization to guarantee 100% reproducible hashes across platforms.
3. **Consensus Strategy Pattern**: Plug-and-play consensus algorithms via abstract base class (`ConsensusStrategy`), allowing seamless switching between **Proof of Work (PoW)** and **Proof of Stake (PoS)**, or adding new consensus models (e.g. Proof of Authority) easily.
4. **State Observer Pattern & Event Emitter**: The blockchain engine emits real-time events (`block_mined`, `validator_selected`, `chain_tampered`, `validation_result`) to push updates via WebSockets or log output seamlessly.
5. **Self-Documenting Code & Comprehensive Type Hints**: Standard Python type annotations (`typing`), clear docstrings, and informative error handling throughout.

---

## 5. Comprehensive Top-Down Architecture & Implementation Master Plan

```
========================================================================================
                                 TOP-DOWN PLANNING HIERARCHY
========================================================================================
 LEVEL 1: HUGE GOALS & TARGETS         ──▶ Production-grade, reliable dual PoW/PoS simulator
 LEVEL 2: SYSTEM FEATURES              ──▶ Hashing, Mining, Staking, Mempool, Tamper & Validation
 LEVEL 3: USER INTERFACE (UI)          ──▶ Glassmorphism, 2D Canvas stage, Inspector modal
 LEVEL 4: FILE-BY-FILE BREAKDOWN       ──▶ Decoupled backend package & frontend JS modules
 LEVEL 5: FUNCTION-BY-FUNCTION CONTRACT ──▶ Strict types, explicit inputs, outputs & error safety
 LEVEL 6: LINE-BY-LINE PSEUDOCODE      ──▶ Precise hashing, mining, staking & rendering logic
========================================================================================
```

---

### 🟢 LEVEL 1: HUGE GOALS & TARGETS

1. **Dual Consensus Engine (PoW + PoS)**: Seamlessly toggle between Proof of Work (computationally mined) and Proof of Stake (weighted lottery selected) in a single unified architecture.
2. **Uncompromising Reliability & Error Safety**:
   - Zero silent fails, zero unhandled exceptions, zero undefined state mutations.
   - Comprehensive input validation on all API endpoints and data models.
   - Deterministic SHA-256 hash generation independent of OS or Python version.
3. **Extreme Maintainability & Developer Experience**:
   - Modular clean architecture: Domain engine has **zero dependencies** on Web or UI logic.
   - Fully documented functions with clear docstrings, type annotations, and explicit error codes.
   - Easy to write unit tests for every individual module (`pytest` ready).
4. **Production-Ready Visual Experience**:
   - High performance 60 FPS HTML5 Canvas 2D visualizer.
   - Interactive camera panning and zooming across infinite horizontal block chains.
   - Real-time animated consensus states (mining counter, PoS validator wheel, tamper red alert cascade).

---

### 🟢 LEVEL 2: SYSTEM FEATURES & CAPABILITIES

#### 2.1 Core Blockchain & Cryptography Engine
- **Deterministic Block Hashing**: Uses SHA-256 with sorted JSON key encoding (`json.dumps(dict, sort_keys=True)`).
- **Merkle Tree Root Calculation**: Hashes individual transactions in a block into a binary Merkle tree to produce a tamper-proof block payload fingerprint.
- **Genesis Block Generation**: Standardized hardcoded initial block (`Index 0`, `prev_hash="0"*64`).
- **Chain Validation Engine**:
  - Validates `hash == compute_hash()`.
  - Validates `current.previous_hash == previous.hash`.
  - Validates proof of work target or proof of stake validator eligibility.
  - Pinpoints exact index where chain corruption begins (`broken_at_index`).

#### 2.2 Consensus Mechanisms
- **Proof of Work (PoW)**:
  - Configurable target difficulty (`1` to `6` leading zeros).
  - Iterative `nonce` increment search.
  - Real-time nonce progress callback emitting live hash attempts over WebSockets.
- **Proof of Stake (PoS)**:
  - Validator registry holding validator identities and staked coin balances.
  - Weighted random selection algorithm (`cumulative distribution uniform pick`).
  - Validator selection probability display.
  - Slashing simulation: penalize & ban misbehaving validators.

#### 2.3 Mempool & Transaction Management
- Pending transaction pool (`Mempool`) for receiving `{sender, recipient, amount, timestamp, signature}`.
- Block packaging: Automatically batch unconfirmed transactions into mined/selected blocks.

#### 2.4 Tamper & Attack Simulation
- **Surgical Tampering**: Modify payload of block `N` without updating subsequent blocks.
- **Cascading Failure Verification**: Visual notification showing how block `N` tampering breaks block `N+1`, `N+2`, etc.
- **Re-mining / Repair Tool**: Re-mine block `N` individually to illustrate that fixing one block does not repair down-stream links.

#### 2.5 Real-Time Communication
- WebSocket event broadcast stream for live mining status, real-time nonce updates, block creation events, and tamper notifications.

---

### 🟢 LEVEL 3: USER INTERFACE (UI) DESIGN & LAYOUT

```
+---------------------------------------------------------------------------------------+
|  [LOGO] Blockchain 2D Simulator | Mode: [ PoW | PoS ] | Health: [ VALID / TAMPERED ]   |
+---------------------------------------------------------------------------------------+
| CONTROLS: Difficulty [===|===] 4 | Staking Pool | [Mine New Block] [Validate Chain]   |
+---------------------------------------------------------------------------------------+
|                                                                                       |
|   CANVAS 2D STAGE (Horizontal Chain Scrolling & Interactive Drag)                     |
|                                                                                       |
|   +--------------+         +--------------+         +--------------+                  |
|   | Block #0     | ======> | Block #1     | ======> | Block #2 !   |                  |
|   | Hash: 0000a1 | (Link)  | Hash: 0000f2 | (Broken)| Hash: 9b8a31 | (Tampered Red!)  |
|   +--------------+         +--------------+         +--------------+                  |
|                                                                                       |
+---------------------------------------------------------------------------------------+
| DOCK PANELS:                                                                          |
| [Block Inspector Modal / Edit]  [Mempool / Create Tx]  [Validator Stake Board]       |
+---------------------------------------------------------------------------------------+
```

1. **Aesthetics & Theme**:
   - Dark mode background (`#0B0F19`), surface cards (`#1E293B`), borders (`#334155`).
   - Neon accent indicators: Valid Cyan (`#00F2FE`), Mining Gold (`#F59E0B`), Tampered Red (`#EF4444`).
   - Glassmorphism overlays (`backdrop-filter: blur(12px)`).

2. **Canvas 2D Rendering Components**:
   - **Block Nodes**: Rounded rectangular cards displaying Block Index, Shortened Hash, Nonce/Validator, Transaction Count, and Status Badge.
   - **Chain Link Connectors**: Smooth Bézier curves or lines with directional arrows. Green glow when valid, glowing red pulse when chain break is detected.
   - **Animation Layers**:
     - Mining Progress: Rotating glowing particle ring around pending block.
     - PoS Selection: Highlighted spinning selector over validator cards.
     - Block Arrival: Smooth spring physics slide-in from offscreen right.

3. **Interactive Control Panels**:
   - **Block Details Drawer**: Click block to view complete metadata, edit payload to simulate attack, re-mine button.
   - **Validator Management (PoS Mode)**: Sliders to adjust stakes, add new validator, view selection probabilities.
   - **Mempool Viewer**: Table of unconfirmed transactions with single-click auto-mine.

---

### 🟢 LEVEL 4: FILE-BY-FILE CONTENT & MODULE BREAKDOWN

```
blockchain-sim/
├── backend/
│   ├── app.py                      # Flask REST API + WebSocket Server & Route Handlers
│   ├── requirements.txt            # Dependencies (flask, flask-cors, flask-socketio)
│   └── blockchain/
│       ├── __init__.py             # Package exposure
│       ├── models.py               # Transaction, Block, Validator, ValidationResult dataclasses
│       ├── hashing.py              # SHA-256 deterministic hashing & Merkle tree builders
│       ├── consensus.py            # ConsensusStrategy ABC, ProofOfWorkStrategy, ProofOfStakeStrategy
│       ├── mempool.py              # Mempool transaction pool manager
│       └── chain.py                # Core Blockchain engine class
├── frontend/
│   ├── index.html                  # Semantic HTML5 UI skeleton
│   ├── style.css                   # CSS variable design system & glassmorphism styling
│   └── js/
│       ├── config.js               # API endpoints & theme color constants
│       ├── api.js                  # Fetch REST client & WebSocket manager
│       ├── canvas.js               # Canvas 2D engine, camera panning, block renderer
│       ├── ui.js                   # DOM event binding, modal handlers, control updates
│       └── main.js                 # App bootstrapper & initialization orchestrator
└── progress_report.md              # Extended Context Memory & Progress Log
```

---

### 🟢 LEVEL 5: FUNCTION-BY-FUNCTION CONTRACT SPECIFICATION

#### 📄 `backend/blockchain/models.py`
- `Transaction.to_dict() -> dict`: Serializes transaction to sorted dict.
- `Block.to_dict() -> dict`: Serializes block fields (including transactions list) to JSON-serializable dictionary.
- `Block.from_dict(data: dict) -> Block`: Reconstructs Block instance from dict.
- `Validator.to_dict() -> dict`: Serializes validator identity and stake info.

#### 📄 `backend/blockchain/hashing.py`
- `calculate_sha256(content: str) -> str`: Computes standard SHA-256 hex digest.
- `calculate_block_hash(block: Block) -> str`: Canonical JSON stringification (sorted keys) of `(index, timestamp, previous_hash, data_or_merkle_root, nonce, validator)` followed by SHA-256 computation.
- `build_merkle_root(transactions: List[Transaction]) -> str`: Recursively hashes paired transactions to construct Merkle root hash.

#### 📄 `backend/blockchain/consensus.py`
- `ConsensusStrategy(ABC)`:
  - `@abstractmethod validate_block(block: Block, prev_block: Optional[Block]) -> bool`
- `ProofOfWorkStrategy(ConsensusStrategy)`:
  - `mine(block: Block, difficulty: int, progress_callback=None) -> Block`: Runs nonce increment loop until `hash.startswith('0' * difficulty)`. Emits periodic progress updates.
  - `validate_block(block: Block, prev_block: Optional[Block]) -> bool`: Verifies leading zeros and hash match.
- `ProofOfStakeStrategy(ConsensusStrategy)`:
  - `select_validator(validators: Dict[str, Validator]) -> str`: Returns validator name based on weighted stake probability distribution.
  - `validate_block(block: Block, prev_block: Optional[Block]) -> bool`: Verifies block validator exists in registry and has active stake.

#### 📄 `backend/blockchain/mempool.py`
- `Mempool.add_transaction(tx: Transaction) -> bool`: Validates and queues incoming transaction.
- `Mempool.get_pending(limit: int) -> List[Transaction]`: Returns up to `limit` pending transactions.
- `Mempool.clear_transactions(tx_ids: List[str])`: Removes transactions included in a mined block.

#### 📄 `backend/blockchain/chain.py`
- `Blockchain.__init__(consensus_type: str = "pow", difficulty: int = 4)`: Initializes genesis block, mempool, validator set, and selected consensus strategy.
- `Blockchain.set_consensus_mode(mode: str, difficulty: int)`: Swaps active consensus strategy between PoW and PoS dynamically.
- `Blockchain.add_block(data_or_txs, validator_name: str = None) -> Block`: Pulls transactions or raw data, computes Merkle root, executes consensus (PoW mine or PoS select), and appends block.
- `Blockchain.tamper_block(index: int, new_data: str) -> Block`: Overwrites target block payload without recalculating nonce/hash to simulate cyber attack.
- `Blockchain.remine_block(index: int) -> Block`: Re-runs consensus on target block alone.
- `Blockchain.is_chain_valid() -> ChainValidationResult`: Iterates through chain from index 0 to N, verifying hashes, link pointers, and consensus criteria. Returns `{valid: bool, broken_at_index: Optional[int], reason: str}`.

#### 📄 `backend/app.py`
- `GET /api/chain`: Returns complete chain payload as JSON.
- `POST /api/mine`: Accepts `{ "data": "..." }`, triggers block mining, broadcasts new block via WebSocket.
- `POST /api/tamper/<int:index>`: Accepts `{ "data": "..." }`, triggers block tampering.
- `GET /api/validate`: Returns chain validation report.
- `POST /api/remine/<int:index>`: Re-mines specified block index.
- `POST /api/consensus`: Swaps consensus mode or updates difficulty/stakes.
- `GET/POST /api/mempool`: Read pending transactions or submit new transaction.
- WebSocket Events (`connect`, `disconnect`, `subscribe_mining`).

#### 📄 `frontend/js/canvas.js`
- `CanvasRenderer.init(canvasElement)`: Binds canvas context, sets up high-DPI resolution rendering.
- `CanvasRenderer.setChainData(chain, validationResult)`: Updates renderable block cache.
- `CanvasRenderer.draw()`: Main 60 FPS animation loop clearing canvas, applying camera translate/scale, rendering links, rendering block cards, drawing animation particles.
- `CanvasRenderer.handlePointerDown(x, y)` / `handlePointerMove` / `handlePointerUp`: Handles camera dragging/panning and block card selection click testing.

---

### 🟢 LEVEL 6: LINE-BY-LINE / PSEUDOCODE LOGIC BLUEPRINT

#### 🔹 Pseudocode 1: Deterministic Block Hashing (`hashing.py`)
```python
def calculate_block_hash(block: Block) -> str:
    # 1. Create clean dictionary of hash-relevant fields
    block_dict = {
        "index": block.index,
        "timestamp": round(block.timestamp, 6),
        "previous_hash": block.previous_hash,
        "merkle_root": block.merkle_root or "",
        "data": block.data if isinstance(block.data, str) else "",
        "nonce": block.nonce,
        "validator": block.validator or ""
    }
    # 2. Serialize to string with strictly sorted keys to guarantee cross-platform determinism
    serialized_str = json.dumps(block_dict, sort_keys=True)
    # 3. Return SHA-256 hex digest
    return hashlib.sha256(serialized_str.encode("utf-8")).hexdigest()
```

#### 🔹 Pseudocode 2: Proof of Work Mining Loop (`consensus.py`)
```python
def mine(self, block: Block, difficulty: int, progress_callback=None) -> Block:
    target_prefix = "0" * difficulty
    block.nonce = 0
    start_time = time.time()
    
    while True:
        block.hash = calculate_block_hash(block)
        if block.hash.startswith(target_prefix):
            block.mining_time = time.time() - start_time
            return block
            
        block.nonce += 1
        
        # Periodic progress emission every 5,000 iterations for UI WebSocket stream
        if progress_callback and block.nonce % 5000 == 0:
            progress_callback(block.index, block.nonce, block.hash)
```

#### 🔹 Pseudocode 3: Proof of Stake Weighted Validator Lottery (`consensus.py`)
```python
def select_validator(self, validators: Dict[str, Validator]) -> str:
    active_validators = {k: v for k, v in validators.items() if v.stake > 0 and not v.is_slashed}
    if not active_validators:
        raise ValueError("No active validators available for selection.")
        
    total_stake = sum(v.stake for v in active_validators.values())
    pick = random.uniform(0, total_stake)
    
    current = 0.0
    for name, validator in active_validators.items():
        current += validator.stake
        if pick <= current:
            return name
            
    return list(active_validators.keys())[-1]
```

#### 🔹 Pseudocode 4: Full Chain Integrity Verifier (`chain.py`)
```python
def is_chain_valid(self) -> ChainValidationResult:
    for i in range(1, len(self.blocks)):
        current = self.blocks[i]
        previous = self.blocks[i - 1]
        
        # 1. Verify internal hash validity
        recomputed_hash = calculate_block_hash(current)
        if current.hash != recomputed_hash:
            return ChainValidationResult(
                is_valid=False, 
                broken_at_index=i, 
                reason=f"Block {i} hash mismatch: computed {recomputed_hash[:8]}, stored {current.hash[:8]}"
            )
            
        # 2. Verify chain link pointer continuity
        if current.previous_hash != previous.hash:
            return ChainValidationResult(
                is_valid=False,
                broken_at_index=i,
                reason=f"Block {i} previous_hash link broken: points to {current.previous_hash[:8]}, previous block hash is {previous.hash[:8]}"
            )
            
        # 3. Verify consensus specific criteria (PoW target or PoS validator)
        if not self.consensus_strategy.validate_block(current, previous):
            return ChainValidationResult(
                is_valid=False,
                broken_at_index=i,
                reason=f"Block {i} failed consensus validation rules ({self.consensus_mode})"
            )
            
    return ChainValidationResult(is_valid=True, broken_at_index=None, reason="Chain is 100% valid")
```

---

### 🕒 Timestamp: `2026-09-07 19:38:00 IST`
- **Action:** Full transition to Pure Proof of Stake (PoS) Blockchain Engine & Visualizer.
- **Key Changes Implemented:**
  - **Deleted PoW Artifacts & Guides:** Removed `blockchain-pow-simulation-guide.md`, `backend/blockchain.py`, and empty `frontend/main.js`.
  - **Refactored Consensus Engine (`backend/blockchain/consensus.py`):** Eliminated `ProofOfWorkStrategy` and computationally wasteful nonce-mining loops. Implemented pure `ProofOfStakeStrategy` featuring weighted validator lottery based on active stake.
  - **Updated Data Models & Hashing (`models.py`, `hashing.py`):** Removed `nonce` from `Block` and deterministic block hash serialization; replaced `mining_time` with `validation_time`.
  - **Refactored Blockchain Engine (`chain.py`):** Configured default pure PoS mode, updated `add_block` and `reseal_block` without PoW difficulty, and added PoS validator validation in `is_chain_valid`.
  - **API & WebSocket Modernization (`backend/app.py`):** Removed `mining_progress` event and PoW difficulty endpoints; added `/api/forge` and `/api/reseal` endpoints.
  - **Enhanced Test Suite (`backend/test_engine.py`):** Implemented comprehensive PoS automated tests covering block forging, validator staking, slashing exclusion, tamper detection, and Merkle tree packaging. All tests passed with 100% success.
  - **Refactored 2D Visualizer (`frontend/`):** Removed PoW consensus mode toggle and difficulty slider from toolbar; updated canvas renderer, block inspector, and PoS validator selection feedback.
- **Git Status:** Prepared for commit and push to remote repository (`origin main`).
