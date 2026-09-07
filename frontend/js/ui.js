/* ==========================================================================
   DOM UI MANAGER & EVENT CONTROLLERS (Proof of Stake)
   ========================================================================== */

class UiManager {
    constructor() {
        this.selectedBlock = null;
        this.selectedBlockIndex = null;
        
        // Element References
        this.elements = {
            // PoS toolbar controls
            posControls: document.getElementById('pos-controls'),
            
            // Health badge
            healthBadge: document.getElementById('health-badge'),
            healthBadgeText: document.getElementById('health-badge-text'),
            
            // Actions
            btnMineBlock: document.getElementById('btn-mine-block'),
            btnValidateChain: document.getElementById('btn-validate-chain'),
            btnResetView: document.getElementById('btn-reset-view'),
            btnOpenMempool: document.getElementById('btn-open-mempool'),
            btnManageValidators: document.getElementById('btn-manage-validators'),
            
            // Drawer
            inspectorDrawer: document.getElementById('inspector-drawer'),
            btnCloseInspector: document.getElementById('btn-close-inspector'),
            inspTitle: document.getElementById('inspector-title'),
            inspHash: document.getElementById('insp-hash'),
            inspPrevHash: document.getElementById('insp-prev-hash'),
            inspValidator: document.getElementById('insp-validator'),
            inspTime: document.getElementById('insp-time'),
            inspDataInput: document.getElementById('insp-data-input'),
            btnTamperBlock: document.getElementById('btn-tamper-block'),
            btnRemineBlock: document.getElementById('btn-remine-block'),
            tamperAlertBox: document.getElementById('tamper-alert-box'),
            tamperAlertText: document.getElementById('tamper-alert-text'),
            
            // Overlay Loader
            miningOverlay: document.getElementById('mining-overlay'),
            miningStatusTitle: document.getElementById('mining-status-title'),
            posStatusVal: document.getElementById('pos-status-val'),
            
            // Mempool Modal
            mempoolModal: document.getElementById('mempool-modal'),
            btnCloseMempool: document.getElementById('btn-close-mempool'),
            formCreateTx: document.getElementById('form-create-tx'),
            mempoolCount: document.getElementById('mempool-count'),
            mempoolQueueCount: document.getElementById('mempool-queue-count'),
            mempoolList: document.getElementById('mempool-list'),
            
            // Validators Modal
            validatorsModal: document.getElementById('validators-modal'),
            btnCloseValidators: document.getElementById('btn-close-validators'),
            formAddValidator: document.getElementById('form-add-validator'),
            validatorCount: document.getElementById('validator-count'),
            validatorsList: document.getElementById('validators-list')
        };

        this.bindEvents();
    }

    bindEvents() {
        // Drawer Close
        this.elements.btnCloseInspector.addEventListener('click', () => this.closeInspector());
        
        // Modals Open/Close
        this.elements.btnOpenMempool.addEventListener('click', () => this.openMempoolModal());
        this.elements.btnCloseMempool.addEventListener('click', () => this.closeMempoolModal());
        this.elements.btnManageValidators.addEventListener('click', () => this.openValidatorsModal());
        this.elements.btnCloseValidators.addEventListener('click', () => this.closeValidatorsModal());
    }

    updateHealthBadge(validationResult) {
        const el = this.elements.healthBadge;
        const txt = this.elements.healthBadgeText;

        if (validationResult.is_valid) {
            el.className = 'badge badge-valid';
            txt.textContent = '100% VALID';
        } else {
            el.className = 'badge badge-tampered';
            txt.textContent = `TAMPERED @ BLOCK #${validationResult.broken_at_index}`;
        }
    }

    setServerOfflineUI() {
        const el = this.elements.healthBadge;
        const txt = this.elements.healthBadgeText;
        el.className = 'badge badge-tampered';
        txt.textContent = 'SERVER OFFLINE';
    }

    openInspector(block, index, validationResult) {
        this.selectedBlock = block;
        this.selectedBlockIndex = index;

        this.elements.inspTitle.textContent = `Block #${block.index} Inspector`;
        this.elements.inspHash.textContent = block.hash || 'Unsealed';
        this.elements.inspPrevHash.textContent = block.previous_hash || 'None';
        this.elements.inspValidator.textContent = block.validator || 'None';
        
        const timeVal = block.validation_time !== undefined ? block.validation_time : (block.mining_time || 0.0);
        this.elements.inspTime.textContent = `${Number(timeVal).toFixed(4)}s`;
        this.elements.inspDataInput.value = block.data || '';

        // Hide or show tamper alert
        const isBrokenHere = !validationResult.is_valid && validationResult.broken_at_index === index;
        if (isBrokenHere) {
            this.elements.tamperAlertBox.classList.remove('hidden');
            this.elements.tamperAlertText.textContent = validationResult.reason;
        } else {
            this.elements.tamperAlertBox.classList.add('hidden');
        }

        this.elements.inspectorDrawer.classList.remove('hidden');
    }

    closeInspector() {
        this.elements.inspectorDrawer.classList.add('hidden');
    }

    showMiningLoader(title = 'Selecting Validator via PoS Lottery...') {
        this.elements.miningStatusTitle.textContent = title;
        if (this.elements.posStatusVal) {
            this.elements.posStatusVal.textContent = 'Sampling weighted stake...';
        }
        this.elements.miningOverlay.classList.remove('hidden');
    }

    hideMiningLoader() {
        this.elements.miningOverlay.classList.add('hidden');
    }

    openMempoolModal() {
        this.elements.mempoolModal.classList.remove('hidden');
    }

    closeMempoolModal() {
        this.elements.mempoolModal.classList.add('hidden');
    }

    renderMempoolList(transactions) {
        this.elements.mempoolCount.textContent = transactions.length;
        this.elements.mempoolQueueCount.textContent = transactions.length;

        const list = this.elements.mempoolList;
        list.innerHTML = '';

        if (!transactions || transactions.length === 0) {
            list.innerHTML = '<div class="empty-msg">No pending transactions in mempool.</div>';
            return;
        }

        transactions.forEach(tx => {
            const div = document.createElement('div');
            div.className = 'tx-item';
            div.innerHTML = `
                <div><strong>${tx.sender}</strong> ➔ <strong>${tx.recipient}</strong></div>
                <div style="color: var(--accent-cyan); font-weight: 600;">${tx.amount} Coins</div>
            `;
            list.appendChild(div);
        });
    }

    openValidatorsModal() {
        this.elements.validatorsModal.classList.remove('hidden');
    }

    closeValidatorsModal() {
        this.elements.validatorsModal.classList.add('hidden');
    }

    renderValidatorsList(validators) {
        this.elements.validatorCount.textContent = validators.length;
        const list = this.elements.validatorsList;
        list.innerHTML = '';

        if (!validators || validators.length === 0) {
            list.innerHTML = '<div class="empty-msg">No validators registered.</div>';
            return;
        }

        const totalStake = validators.reduce((acc, v) => acc + (v.is_slashed ? 0 : v.stake), 0);

        validators.forEach(v => {
            const prob = totalStake > 0 && !v.is_slashed ? ((v.stake / totalStake) * 100).toFixed(1) : 0;
            const div = document.createElement('div');
            div.className = 'val-item';
            div.innerHTML = `
                <div>
                    <strong>${v.name}</strong> 
                    ${v.is_slashed ? '<span style="color:var(--accent-rose);">(SLASHED)</span>' : ''}
                </div>
                <div>Stake: <strong>${v.stake}</strong> (${prob}%)</div>
                ${!v.is_slashed ? `<button class="btn btn-danger btn-slash" data-name="${v.name}" style="padding:4px 8px; font-size:11px;">Slash</button>` : ''}
            `;
            list.appendChild(div);
        });

        // Bind slash buttons
        list.querySelectorAll('.btn-slash').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const name = e.target.getAttribute('data-name');
                if (this.onSlashValidator) {
                    this.onSlashValidator(name);
                }
            });
        });
    }
}

const ui = new UiManager();
