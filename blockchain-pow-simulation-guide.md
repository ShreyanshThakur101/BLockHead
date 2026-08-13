# Build Your Own Blockchain Simulation + 2D Visualizer
### A ground-up guide, tailored for: knows Python, knows a bit of web dev

---

## 0. What you're actually building

By the end of this you'll have:

- A **Python "engine"** that implements a real (simplified) blockchain: blocks, hashing, proof-of-work mining, chain validation, tamper detection.
- A **web API** that exposes that engine over HTTP.
- A **2D web frontend** (HTML/CSS/JS + Canvas or SVG) that visualizes blocks being created, linked, mined, and — if you tamper with one — visually breaking.

You will build this in **7 phases**, each one a working, testable milestone. Don't skip ahead — each phase is small enough to finish in one sitting, and each one teaches the next one's prerequisites.

Architecture, in one picture:

```
┌─────────────────────┐        HTTP (JSON)        ┌──────────────────────┐
│   Browser (frontend) │ ─────────────────────────▶│   Python backend      │
│  HTML/CSS/JS + Canvas│ ◀───────────────────────── │  Flask/FastAPI + your │
│  draws the chain     │        JSON responses      │  Blockchain class     │
└─────────────────────┘                            └──────────────────────┘
```

Why this split, and not "just do it all in Python" or "just do it all in JS"?
Because you already know Python — that's where the *interesting* logic (hashing, mining, validation) belongs, so you're learning blockchain concepts in a language you're fluent in. The browser side is *only* responsible for drawing what the backend tells it. This is also how real systems are structured: a backend that owns state/logic, a frontend that renders it.

---

## 1. Skills inventory — what you know vs. what to learn

Given you know Python and "a bit" of web dev, here's the honest breakdown.

**You probably already have:**
- Python basics: classes, functions, lists, dicts, loops
- Basic HTML/CSS
- Some JavaScript (variables, functions, maybe DOM manipulation)

**Learn this** — new things you'll need, in the order you'll hit them:

| # | Topic | Why you need it | Where |
|---|---|---|---|
| 1 | `hashlib` (Python stdlib) | Core of every block's identity | [Python docs: hashlib](https://docs.python.org/3/library/hashlib.html) |
| 2 | Proof-of-work concept | The "mining" mechanic | Read: "Bitcoin proof of work explained" (any good beginner article) — you'll implement it yourself, don't need Bitcoin's actual code |
| 3 | Dataclasses or plain classes with `to_dict()` | Clean block representation | [Python docs: dataclasses](https://docs.python.org/3/library/dataclasses.html) |
| 4 | A Python web framework: **Flask** (simpler, recommended for this) or FastAPI | Expose your engine as an API | [Flask Quickstart](https://flask.palletsprojects.com/en/latest/quickstart/) |
| 5 | REST API basics (GET/POST, JSON bodies, status codes) | Frontend ↔ backend contract | [MDN: HTTP methods](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods) |
| 6 | `fetch()` in JavaScript | Frontend calling your API | [MDN: Using Fetch](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch) |
| 7 | HTML5 **Canvas API** (2D drawing) | This is your visualization engine | [MDN: Canvas tutorial](https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API/Tutorial) |
| 8 | `requestAnimationFrame` | Smooth animation loop (mining spinner, block sliding in) | [MDN: requestAnimationFrame](https://developer.mozilla.org/en-US/docs/Web/API/window/requestAnimationFrame) |
| 9 | CORS (if frontend/backend run on different ports) | Browser will block your API calls otherwise | [MDN: CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS) + `flask-cors` package |
| 10 | (Optional, Phase 6+) WebSockets | Push live mining progress instead of polling | [MDN: WebSockets API](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API), Python: `flask-socketio` |
| 11 | (Optional, Phase 7) Public-key crypto basics (`cryptography` or `ecdsa` package) | Simulated wallets/signed transactions | [Python `cryptography` docs](https://cryptography.io/en/latest/) |

Don't pre-learn all of these now. Learn each one right when its phase tells you to — that's the point of ordering it this way.

---

## 2. Project setup

```
blockchain-sim/
├── backend/
│   ├── venv/                  (virtual environment, don't commit)
│   ├── blockchain.py          (the core engine — pure Python, no web code)
│   ├── app.py                 (Flask app exposing the engine)
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── main.js
└── README.md
```

Setup commands:

```bash
mkdir -p blockchain-sim/backend blockchain-sim/frontend
cd blockchain-sim/backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install flask flask-cors
pip freeze > requirements.txt
```

**Learn this:** if you haven't used a Python virtual environment before, spend 10 minutes on why it exists (dependency isolation per-project) before moving on.

Initialize git now, commit after every phase. You want a working checkpoint you can roll back to.

---

## 3. Phase 1 — The core blockchain engine (pure Python, no web yet)

**Goal:** a `blockchain.py` you can run and test entirely from the terminal, with zero web code. Get this rock solid before touching Flask.

### 3.1 Design the `Block`

A block needs, at minimum:

- `index` — position in the chain
- `timestamp`
- `data` — whatever payload you want (a string, or a list of "transactions")
- `previous_hash` — the hash of the block before it (this is *the* mechanism that chains blocks together)
- `nonce` — the number you'll increment while mining
- `hash` — computed from all the above

**Concept to internalize before coding:** a block's hash is a function of *everything in the block, including the previous block's hash*. That's what makes it a *chain* — change anything in block 3, and block 3's hash changes, which invalidates block 4's `previous_hash` reference, and so on down the line. This single fact is the entire "why is blockchain tamper-evident" story. Everything else is engineering around it.

Pseudocode for the hash function:

```
def compute_hash(block):
    block_string = string representation of (index, timestamp, data, previous_hash, nonce)
    return sha256(block_string).hexdigest()
```

**Learn this:** why you must serialize *all* fields deterministically (same field order every time) before hashing — if you use a Python dict's `str()` representation, dict ordering could bite you in older Python or when you add fields later. Prefer explicit string formatting or `json.dumps(..., sort_keys=True)`.

### 3.2 Proof-of-work mining

Define a `difficulty` (e.g. "hash must start with N zeros"). Mining = brute-force searching for a `nonce` value that makes the hash satisfy that condition.

Pseudocode:

```
def mine_block(block, difficulty):
    target = "0" * difficulty
    block.nonce = 0
    while True:
        block.hash = compute_hash(block)
        if block.hash.startswith(target):
            return block
        block.nonce += 1
```

Try this at the terminal first with `difficulty = 4` or `5` and watch how much slower it gets as difficulty increases by 1. This is the moment you'll *feel* why proof-of-work is expensive — that intuition matters more than reading about it.

**Learn this:** why difficulty scales *exponentially* (each added hex digit of required zeros multiplies the search space by 16). You'll want this fact later when you build the difficulty slider in the UI — it explains why difficulty 6 vs 5 isn't "a bit slower," it's 16x slower.

### 3.3 The `Blockchain` class

Responsibilities:
- Hold a list of blocks, starting with a hardcoded **genesis block** (index 0, arbitrary/no real previous hash).
- `add_block(data)` — build a new block referencing the current last block's hash, mine it, append it.
- `is_chain_valid()` — walk the chain and check two things per block: (a) its stored hash matches a fresh recomputation, (b) its `previous_hash` matches the actual previous block's `hash`. Return the index of the first broken block, or "valid."

### 3.4 Test it like a script, not a web app yet

```python
if __name__ == "__main__":
    chain = Blockchain(difficulty=4)
    chain.add_block("Alice pays Bob 5 coins")
    chain.add_block("Bob pays Carol 2 coins")
    print(chain.is_chain_valid())

    # now tamper
    chain.blocks[1].data = "Alice pays Bob 5000 coins"
    print(chain.is_chain_valid())  # should now report block 1 broken
```

**Milestone check:** you should be able to run this file directly, see mining take visibly longer as you raise difficulty, and see validation correctly flag tampering. Don't move to Phase 2 until this feels solid — everything downstream just visualizes this.

---

## 4. Phase 2 — Expose it as a web API

**Goal:** the exact same `Blockchain` object, reachable from a browser via HTTP.

### 4.1 Minimal Flask app shape

Endpoints to build:

| Method | Route | Does |
|---|---|---|
| GET | `/chain` | Returns the whole chain as JSON |
| POST | `/mine` | Accepts `{ "data": "..." }`, mines a new block, returns it |
| POST | `/tamper/<index>` | Accepts `{ "data": "..." }`, overwrites that block's data *without* re-mining (this is your "attack" endpoint) |
| GET | `/validate` | Returns `{ "valid": true/false, "broken_at": index_or_null }` |
| POST | `/remine/<index>` | Re-mines just that one block (to demo "you can patch one block but not the chain after it") |

**Concept:** your Flask app should hold **one shared `Blockchain` instance in memory** (module-level global, or `app.config`) that all requests read/write. This is a simulation, not a production system — a single in-memory instance per server process is fine and simpler than a database for now.

Each block needs a `to_dict()` method so Flask's `jsonify()` can serialize it — Python objects aren't JSON-serializable by default.

**Learn this:** the difference between `jsonify()` and `json.dumps()` in Flask, and why Flask wants the former for response bodies.

### 4.2 CORS

If you'll open `frontend/index.html` directly in a browser (via `file://`) or serve it from a different port than Flask, the browser will block your `fetch()` calls unless the backend sends CORS headers. Install `flask-cors` and wrap your app:

```python
from flask_cors import CORS
CORS(app)
```

### 4.3 Test with curl or a REST client before touching JS

```bash
curl http://localhost:5000/chain
curl -X POST http://localhost:5000/mine -H "Content-Type: application/json" -d '{"data":"test tx"}'
```

**Milestone check:** you can mine, view, tamper, and validate the chain purely via curl/Postman, no browser involved yet. This isolates backend bugs from frontend bugs — very worth doing before you add a UI layer on top.

---

## 5. Phase 3 — Frontend skeleton (no visualization yet, just data)

**Goal:** a webpage that calls your API and renders the chain as plain HTML — get the plumbing working before you touch Canvas.

- `index.html`: a container `<div id="chain-list"></div>`, a text input + "Mine" button, a "Validate" button.
- `main.js`: on load, `fetch('http://localhost:5000/chain')`, loop over blocks, render each as a `<div>` with its index/hash/data as text.
- Wire the Mine button to POST `/mine`, then re-fetch and re-render.

**Learn this:** `async/await` in JS if you haven't used it — every `fetch()` call here will be asynchronous, and mining especially (since it may take real time on the backend) benefits from a clear async flow rather than nested `.then()` chains.

**Milestone check:** clicking "Mine" adds a visible new entry to a plain list on the page, sourced live from your Python backend. No graphics yet — that's next.

---

## 6. Phase 4 — The 2D visualization (the fun part)

**Goal:** replace the plain list with an actual drawn chain: boxes connected by lines, colored by validity.

### 6.1 Canvas vs. SVG — pick one deliberately

- **Canvas**: you draw imperatively (`ctx.fillRect(...)`, `ctx.strokeText(...)`). Better for animation-heavy scenes (mining spinners, particles), but you manage redraw-on-every-frame yourself and there's no "block element" you can click on directly — you have to hit-test coordinates manually.
- **SVG**: each block is an actual DOM element (`<rect>`, `<text>`) you can style with CSS and attach click listeners to directly, like normal HTML. Easier for a chain of static-ish boxes with occasional animation; harder for continuous frame-by-frame animation.

**Recommendation for this project:** start with **Canvas** — a blockchain is fundamentally about repeated boxes-and-lines you'll want to animate (a block sliding in when mined, a red pulse when tampered), and Canvas keeps that simple once you have the basic draw loop. If clicking directly on a block to tamper with it turns out to matter more to you than animation, switch to SVG — both are valid, and switching later is a learning exercise in itself, not wasted work.

**Learn this:** the Canvas coordinate system (0,0 is top-left, y increases downward) and the basic draw loop pattern:

```
function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    // recompute positions, redraw every block + connecting lines
    requestAnimationFrame(draw);
}
```

### 6.2 Layout the blocks

Simplest layout: fixed-width boxes in a horizontal row (or vertical column if you expect many blocks), spaced evenly, with a line drawn between the right edge of block N and the left edge of block N+1.

Per block, draw:
- A rectangle (`ctx.fillRect` / `ctx.strokeRect`)
- Text inside it: index, short hash (first 8 chars + "…"), nonce
- Color: green/teal border if valid, red border if invalid (this comes straight from your `/validate` response)

### 6.3 Animate mining

Since real mining happens on the backend and could take a moment at higher difficulty, give the *frontend* something to show while waiting:

- A simple pulsing/spinning indicator on a "pending block" placeholder while the `/mine` request is in flight.
- Optionally, poach a fake nonce counter that increments rapidly on the frontend purely for visual effect while waiting — cosmetic, not connected to the real backend nonce, but it *looks* like mining is happening. (For a more honest version, see Phase 6's WebSocket note — that lets you show the *real* nonce counter live.)

### 6.4 Animate the "slide in" on new blocks and the "break" on tamper

- New block: animate its x/y position from off-screen to its slot over ~15-20 frames.
- Tamper: when `/validate` reports a broken index, animate the connecting line at that point flashing red, and optionally cascade a brief red pulse through every subsequent block.

**Milestone check:** you can mine a block and watch it visually appear and link in; you can tamper via a UI control and watch the chain visually break from that point forward.

---

## 7. Phase 5 — Interactivity

- Click a block to open a small panel showing its full data/hash/nonce, with an editable field to tamper with it in place, wired to your `/tamper/<index>` endpoint.
- A "re-mine block" button per broken block, wired to `/remine/<index>` — lets you show that fixing one block doesn't fix the chain, since the *next* block's `previous_hash` still won't match.
- A difficulty slider that's actually connected to the backend's difficulty setting for future mines.

**Concept worth building deliberately:** make re-mining a tampered block *not* automatically cascade-fix the rest of the chain. Forcing the user to manually re-mine every subsequent block (or write a "re-mine from here to tip" helper) is what makes the cost of an attack visceral — this is the core "aha" of the whole simulation.

---

## 8. Phase 6 — Make it feel like a network, not one ledger

Right now you have one chain. To make it feel like a *network* simulation:

- Simulate 2–3 "nodes" purely as labels in the UI, each independently calling `/validate` and displaying synced/rejected — since they're all really hitting the same backend chain, this is a simplification, but it visually teaches the idea that multiple independent parties check the same chain and can independently reject a tampered version.
- **Learn this (optional, bigger step):** to make it *actually* distributed rather than simulated-in-name, run 2-3 separate instances of your Flask app (different ports) each with their own in-memory chain, plus a simple "broadcast" endpoint each node calls on the others when it mines a block, so they converge. This introduces real concepts: network partitions, propagation delay, and (if you go further) a basic **longest-chain-wins conflict resolution rule** — the actual mechanism real blockchains use to agree on one canonical history. This is a meaningfully bigger project step; treat it as a stretch goal, not a requirement.
- **Learn this (optional):** WebSockets (`flask-socketio` + the browser `WebSocket` API) to push live updates (e.g. real nonce-search progress during mining) to the frontend instead of polling — makes the mining animation in 6.3 show the *real* number instead of a cosmetic one.

---

## 9. Phase 7 — Stretch goals, roughly in order of effort

1. **Persistence** — save the chain to a JSON file or SQLite so it survives a server restart. (`Learn this:` basic `sqlite3` stdlib module, or just `json.dump`/`json.load` for the simplest version.)
2. **Transactions instead of raw strings** — each block holds a list of `{from, to, amount}` transactions rather than one string.
3. **A transaction pool ("mempool")** — transactions submitted via an endpoint sit in a pending list; mining a block pulls several from the pool instead of taking one string per mine.
4. **Merkle trees** — instead of hashing all transaction data as one blob, build a Merkle tree of transactions and store only the root hash in the block header. (`Learn this:` what a Merkle tree is and why it lets you prove a single transaction is included without revealing all the others — this is the real reason Bitcoin blocks are efficient to verify.)
5. **Signed transactions** — generate a public/private keypair per simulated "wallet" (`Learn this:` the `cryptography` or `ecdsa` Python package) and require transactions to carry a valid signature before a block can include them. This is where "blockchain" starts to actually resemble a cryptocurrency rather than just a tamper-evident log.
6. **Difficulty retargeting** — automatically adjust difficulty based on how fast recent blocks were mined, to simulate the "aim for ~1 block per N seconds" mechanism real chains use.

None of these are required to call the project "done" — the 2D visualizer with mining/tamper/validate from Phases 1–5 is already a complete, demonstrable simulation.

---

## 10. Suggested order of attack, summarized

1. `blockchain.py` runs standalone in the terminal, mines, validates, detects tampering. ✅ before moving on.
2. Flask wraps it; you can drive the whole thing with `curl`. ✅ before moving on.
3. Plain HTML/JS list renders the live chain from the API. ✅ before moving on.
4. Canvas draws it as connected boxes instead of a list.
5. Mining and tampering animate visually.
6. Click-to-tamper and re-mine controls.
7. (Optional) multi-node simulation, WebSockets, persistence, transactions, Merkle trees, signatures.

Each numbered step above is a real commit-able milestone — resist the urge to jump to the Canvas visuals before step 1–3 are solid. The visualization is only as good as the data it's fed, and debugging drawing code *and* blockchain logic *and* API plumbing simultaneously is the fastest way to get stuck.

Good luck — this is a genuinely good project for learning both "how does a blockchain actually work" and "how do a Python backend and a JS frontend talk to each other," which is a useful pairing well beyond this specific project.
