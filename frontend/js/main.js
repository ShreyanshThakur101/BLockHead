/* ==========================================================================
   MAIN APPLICATION BOOTSTRAPPER (Proof of Stake)
   ========================================================================== */

document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 Initializing Proof of Stake Blockchain Simulation...');

    // 1. Initialize Canvas Renderer Engine
    const canvasElement = document.getElementById('blockchain-canvas');
    const renderer = new CanvasRenderer(canvasElement);

    // 2. State Cache
    let currentChainState = null;

    // Helper to refresh chain data from API
    async function syncChainState() {
        try {
            const [chainRes, mempoolRes] = await Promise.all([
                api.getChain(),
                api.getMempool()
            ]);

            if (chainRes && chainRes.success) {
                currentChainState = chainRes.data;
                renderer.setChainData(currentChainState.blocks, currentChainState.validation);
                ui.updateHealthBadge(currentChainState.validation);
                
                // Active validators are directly provided in chain data
                if (currentChainState.validators) {
                    ui.renderValidatorsList(currentChainState.validators);
                }
            }

            if (mempoolRes && mempoolRes.success) {
                ui.renderMempoolList(mempoolRes.pending_transactions);
            }
        } catch (err) {
            console.error('Failed to sync chain state (server offline?):', err);
            ui.setServerOfflineUI();
        }
    }

    // 3. Connect Socket.IO Realtime Listeners
    api.initSocket();

    api.on('block_added', (data) => {
        ui.hideMiningLoader();
        syncChainState();
    });

    api.on('chain_tampered', (data) => {
        syncChainState();
        if (ui.selectedBlockIndex !== null && data.chain_state && data.chain_state.blocks) {
            const updatedBlock = data.chain_state.blocks[ui.selectedBlockIndex];
            if (updatedBlock) {
                ui.openInspector(updatedBlock, ui.selectedBlockIndex, data.validation);
            }
        }
    });

    api.on('block_resealed', (data) => {
        ui.hideMiningLoader();
        syncChainState();
        if (ui.selectedBlockIndex !== null && data.chain_state && data.chain_state.blocks) {
            const updatedBlock = data.chain_state.blocks[ui.selectedBlockIndex];
            if (updatedBlock) {
                ui.openInspector(updatedBlock, ui.selectedBlockIndex, data.validation);
            }
        }
    });

    api.on('mempool_updated', (data) => {
        syncChainState();
    });

    api.on('validators_updated', (data) => {
        syncChainState();
    });

    // 4. Bind Canvas Block Click to Inspector Drawer
    renderer.onBlockSelectCallback = (block, index) => {
        if (currentChainState) {
            ui.openInspector(block, index, currentChainState.validation);
        }
    };

    // 5. Auth & RBAC Handlers
    ui.onAuthSubmit = async (username, password, role, isRegister) => {
        try {
            if (!username || !password) {
                ui.showAuthError('Username and password are required.');
                return;
            }

            if (isRegister) {
                await api.register(username, password, role);
            }

            const loginRes = await api.login(username, password);
            if (loginRes && loginRes.token && loginRes.user) {
                auth.setSession(loginRes.token, loginRes.user);
                ui.closeAuthModal();
                ui.updateRoleUI(loginRes.user);
                await syncChainState();
            } else {
                ui.showAuthError('Invalid response from server.');
            }
        } catch (err) {
            ui.showAuthError(err.message || 'Authentication failed.');
        }
    };

    ui.onDemoLogin = async (username, password) => {
        try {
            const loginRes = await api.login(username, password);
            if (loginRes && loginRes.token && loginRes.user) {
                auth.setSession(loginRes.token, loginRes.user);
                ui.closeAuthModal();
                ui.updateRoleUI(loginRes.user);
                await syncChainState();
            }
        } catch (err) {
            ui.showAuthError(err.message || 'Demo login failed.');
        }
    };

    ui.onLogout = () => {
        auth.clearSession();
        ui.updateRoleUI(null);
        syncChainState();
    };

    auth.onAuthStateChanged((user) => {
        ui.updateRoleUI(user);
    });

    // Check token and initialize role UI
    if (auth.isLoggedIn()) {
        try {
            const profile = await api.getProfile();
            if (profile && profile.user) {
                auth.setSession(auth.getToken(), profile.user);
                ui.updateRoleUI(profile.user);
            } else {
                auth.clearSession();
                ui.updateRoleUI(null);
            }
        } catch (err) {
            console.warn('Session verification notice:', err.message);
            if (err.message && err.message.includes('401')) {
                auth.clearSession();
                ui.updateRoleUI(null);
            } else {
                ui.updateRoleUI(auth.getUser());
            }
        }
    } else {
        ui.updateRoleUI(null);
    }

    // 6. Action Handlers

    // Forge / Propose Block Button
    document.getElementById('btn-mine-block').addEventListener('click', async () => {
        if (!auth.isAdmin()) {
            ui.openAuthModal('login');
            return;
        }

        ui.showMiningLoader('Selecting Validator via PoS Lottery...');
        try {
            await api.forgeBlock();
            ui.hideMiningLoader();
            await syncChainState();
        } catch (err) {
            ui.hideMiningLoader();
            if (err.message && err.message.includes('Failed to fetch')) {
                alert(`Backend Server Offline: Cannot connect to ${CONFIG.API_BASE_URL}.\n\nPlease ensure the Python backend server is running in your terminal:\n  python backend/app.py`);
            } else {
                alert(`PoS Block Proposal Error: ${err.message}`);
            }
        }
    });

    // Validate Chain Button
    document.getElementById('btn-validate-chain').addEventListener('click', async () => {
        try {
            const res = await api.validateChain();
            if (res.success) {
                ui.updateHealthBadge(res.validation);
                alert(res.validation.reason);
            }
        } catch (err) {
            alert(`Validation Error: ${err.message}`);
        }
    });

    // Reset Camera View Button
    document.getElementById('btn-reset-view').addEventListener('click', () => {
        renderer.resetView();
    });

    // Tamper Attack Button in Drawer
    document.getElementById('btn-tamper-block').addEventListener('click', async () => {
        if (!auth.isAdmin()) {
            ui.openAuthModal('login');
            return;
        }
        if (ui.selectedBlockIndex === null) return;
        const newPayload = document.getElementById('insp-data-input').value;
        try {
            const res = await api.tamperBlock(ui.selectedBlockIndex, newPayload);
            await syncChainState();
            if (res && res.chain_state && res.chain_state.blocks) {
                const updatedBlock = res.chain_state.blocks[ui.selectedBlockIndex];
                if (updatedBlock) {
                    ui.openInspector(updatedBlock, ui.selectedBlockIndex, res.validation);
                }
            }
        } catch (err) {
            alert(`Tamper Error: ${err.message}`);
        }
    });

    // Re-seal / Repair Block Button in Drawer
    document.getElementById('btn-remine-block').addEventListener('click', async () => {
        if (!auth.isAdmin()) {
            ui.openAuthModal('login');
            return;
        }
        if (ui.selectedBlockIndex === null) return;
        ui.showMiningLoader(`Re-sealing Block #${ui.selectedBlockIndex}...`);
        try {
            const res = await api.resealBlock(ui.selectedBlockIndex);
            ui.hideMiningLoader();
            await syncChainState();
            if (res && res.chain_state && res.chain_state.blocks) {
                const updatedBlock = res.chain_state.blocks[ui.selectedBlockIndex];
                if (updatedBlock) {
                    ui.openInspector(updatedBlock, ui.selectedBlockIndex, res.validation);
                }
            }
        } catch (err) {
            ui.hideMiningLoader();
            alert(`Re-seal Error: ${err.message}`);
        }
    });

    // Create Transaction Form Submission
    document.getElementById('form-create-tx').addEventListener('submit', async (e) => {
        e.preventDefault();
        const sender = document.getElementById('tx-sender').value;
        const recipient = document.getElementById('tx-recipient').value;
        const amount = parseFloat(document.getElementById('tx-amount').value);

        try {
            await api.createTransaction(sender, recipient, amount);
            document.getElementById('tx-sender').value = '';
            document.getElementById('tx-recipient').value = '';
            document.getElementById('tx-amount').value = '';
            await syncChainState();
        } catch (err) {
            alert(`Transaction Error: ${err.message}`);
        }
    });

    // Register Validator Form Submission
    document.getElementById('form-add-validator').addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!auth.isAdmin()) {
            ui.openAuthModal('login');
            return;
        }
        const name = document.getElementById('val-name').value;
        const stake = parseFloat(document.getElementById('val-stake').value);

        try {
            await api.updateValidator('add', name, stake);
            document.getElementById('val-name').value = '';
            document.getElementById('val-stake').value = '';
            await syncChainState();
        } catch (err) {
            alert(`Validator Error: ${err.message}`);
        }
    });

    // Slash Validator Callback
    ui.onSlashValidator = async (name) => {
        if (!auth.isAdmin()) {
            ui.openAuthModal('login');
            return;
        }
        try {
            await api.updateValidator('slash', name, 0);
            await syncChainState();
        } catch (err) {
            alert(`Slash Error: ${err.message}`);
        }
    };

    // Initial State Fetch
    await syncChainState();
});
