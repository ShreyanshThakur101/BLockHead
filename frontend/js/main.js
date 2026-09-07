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
            const response = await api.getChain();
            if (response.success) {
                currentChainState = response.data;
                renderer.setChainData(currentChainState.blocks, currentChainState.validation);
                ui.updateHealthBadge(currentChainState.validation);
                
                // Update Mempool & Validators UI
                const mempoolRes = await api.getMempool();
                if (mempoolRes.success) {
                    ui.renderMempoolList(mempoolRes.pending_transactions);
                }

                const valRes = await api.getValidators();
                if (valRes.success) {
                    ui.renderValidatorsList(valRes.validators);
                }
            }
        } catch (err) {
            console.error('Failed to sync chain state:', err);
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
        if (ui.selectedBlockIndex !== null) {
            const updatedBlock = data.chain_state.blocks[ui.selectedBlockIndex];
            ui.openInspector(updatedBlock, ui.selectedBlockIndex, data.validation);
        }
    });

    api.on('block_resealed', (data) => {
        ui.hideMiningLoader();
        syncChainState();
        if (ui.selectedBlockIndex !== null) {
            const updatedBlock = data.chain_state.blocks[ui.selectedBlockIndex];
            ui.openInspector(updatedBlock, ui.selectedBlockIndex, data.validation);
        }
    });

    api.on('block_remined', (data) => {
        ui.hideMiningLoader();
        syncChainState();
        if (ui.selectedBlockIndex !== null) {
            const updatedBlock = data.chain_state.blocks[ui.selectedBlockIndex];
            ui.openInspector(updatedBlock, ui.selectedBlockIndex, data.validation);
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

    // 5. Action Handlers

    // Forge / Propose Block Button
    document.getElementById('btn-mine-block').addEventListener('click', async () => {
        ui.showMiningLoader('Selecting Validator via PoS Lottery...');
        try {
            await api.forgeBlock();
        } catch (err) {
            ui.hideMiningLoader();
            alert(`PoS Block Proposal Error: ${err.message}`);
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
        if (ui.selectedBlockIndex === null) return;
        const newPayload = document.getElementById('insp-data-input').value;
        try {
            await api.tamperBlock(ui.selectedBlockIndex, newPayload);
        } catch (err) {
            alert(`Tamper Error: ${err.message}`);
        }
    });

    // Re-seal / Repair Block Button in Drawer
    document.getElementById('btn-remine-block').addEventListener('click', async () => {
        if (ui.selectedBlockIndex === null) return;
        ui.showMiningLoader(`Re-sealing Block #${ui.selectedBlockIndex}...`);
        try {
            await api.resealBlock(ui.selectedBlockIndex);
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
        } catch (err) {
            alert(`Transaction Error: ${err.message}`);
        }
    });

    // Register Validator Form Submission
    document.getElementById('form-add-validator').addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('val-name').value;
        const stake = parseFloat(document.getElementById('val-stake').value);

        try {
            await api.updateValidator('add', name, stake);
            document.getElementById('val-name').value = '';
            document.getElementById('val-stake').value = '';
        } catch (err) {
            alert(`Validator Error: ${err.message}`);
        }
    });

    // Slash Validator Callback
    ui.onSlashValidator = async (name) => {
        try {
            await api.updateValidator('slash', name, 0);
        } catch (err) {
            alert(`Slash Error: ${err.message}`);
        }
    };

    // Initial State Fetch
    await syncChainState();
});
