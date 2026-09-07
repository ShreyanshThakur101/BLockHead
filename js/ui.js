/* ==========================================================================
   DOM UI MANAGER & EVENT CONTROLLERS (Proof of Stake)
   ========================================================================== */

function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

class UiManager {
    constructor() {
        this.selectedBlock = null;
        this.selectedBlockIndex = null;
        this.onSlashValidator = null;
        this.authMode = 'login'; // 'login' | 'register'
        this.onAuthSubmit = null;
        this.onDemoLogin = null;
        this.onLogout = null;
        
        // Element References
        this.elements = {
            // PoS toolbar controls
            posControls: document.getElementById('pos-controls'),
            
            // Health badge
            healthBadge: document.getElementById('health-badge'),
            healthBadgeText: document.getElementById('health-badge-text'),

            // Role & Auth Elements
            userRoleBadge: document.getElementById('user-role-badge'),
            userRoleText: document.getElementById('user-role-text'),
            btnOpenAuth: document.getElementById('btn-open-auth'),
            btnLogout: document.getElementById('btn-logout'),
            roleModeBanner: document.getElementById('role-mode-banner'),
            modeBannerIcon: document.getElementById('mode-banner-icon'),
            modeBannerText: document.getElementById('mode-banner-text'),
            btnBannerSwitchAdmin: document.getElementById('btn-banner-switch-admin'),
            drawerViewerNotice: document.getElementById('drawer-viewer-notice'),

            // Auth Modal
            authModal: document.getElementById('auth-modal'),
            btnCloseAuth: document.getElementById('btn-close-auth'),
            authModalTitle: document.getElementById('auth-modal-title'),
            tabAuthLogin: document.getElementById('tab-auth-login'),
            tabAuthRegister: document.getElementById('tab-auth-register'),
            formAuth: document.getElementById('form-auth'),
            authUsername: document.getElementById('auth-username'),
            authPassword: document.getElementById('auth-password'),
            authRoleGroup: document.getElementById('auth-role-group'),
            authRole: document.getElementById('auth-role'),
            authErrorBox: document.getElementById('auth-error-box'),
            authErrorText: document.getElementById('auth-error-text'),
            btnSubmitAuth: document.getElementById('btn-submit-auth'),
            btnDemoAdmin: document.getElementById('btn-demo-admin'),
            btnDemoViewer: document.getElementById('btn-demo-viewer'),
            
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
        if (this.elements.btnCloseInspector) {
            this.elements.btnCloseInspector.addEventListener('click', () => this.closeInspector());
        }
        
        // Modals Open/Close
        if (this.elements.btnOpenMempool) {
            this.elements.btnOpenMempool.addEventListener('click', () => this.openMempoolModal());
        }
        if (this.elements.btnCloseMempool) {
            this.elements.btnCloseMempool.addEventListener('click', () => this.closeMempoolModal());
        }
        if (this.elements.btnManageValidators) {
            this.elements.btnManageValidators.addEventListener('click', () => this.openValidatorsModal());
        }
        if (this.elements.btnCloseValidators) {
            this.elements.btnCloseValidators.addEventListener('click', () => this.closeValidatorsModal());
        }

        // Auth Modal & Role Events
        if (this.elements.btnOpenAuth) {
            this.elements.btnOpenAuth.addEventListener('click', () => this.openAuthModal('login'));
        }
        if (this.elements.btnBannerSwitchAdmin) {
            this.elements.btnBannerSwitchAdmin.addEventListener('click', () => this.openAuthModal('login'));
        }
        if (this.elements.btnCloseAuth) {
            this.elements.btnCloseAuth.addEventListener('click', () => this.closeAuthModal());
        }
        if (this.elements.tabAuthLogin) {
            this.elements.tabAuthLogin.addEventListener('click', (e) => {
                e.preventDefault();
                this.setAuthMode('login');
            });
        }
        if (this.elements.tabAuthRegister) {
            this.elements.tabAuthRegister.addEventListener('click', (e) => {
                e.preventDefault();
                this.setAuthMode('register');
            });
        }
        if (this.elements.btnLogout) {
            this.elements.btnLogout.addEventListener('click', () => {
                if (this.onLogout) this.onLogout();
            });
        }
        if (this.elements.btnDemoAdmin) {
            this.elements.btnDemoAdmin.addEventListener('click', () => {
                if (this.onDemoLogin) this.onDemoLogin('admin', 'admin123');
            });
        }
        if (this.elements.btnDemoViewer) {
            this.elements.btnDemoViewer.addEventListener('click', () => {
                if (this.onDemoLogin) this.onDemoLogin('viewer', 'viewer123');
            });
        }
        if (this.elements.formAuth) {
            this.elements.formAuth.addEventListener('submit', (e) => {
                e.preventDefault();
                const username = this.elements.authUsername ? this.elements.authUsername.value.trim() : '';
                const password = this.elements.authPassword ? this.elements.authPassword.value : '';
                const role = this.elements.authRole ? this.elements.authRole.value : 'viewer';
                if (this.onAuthSubmit) {
                    this.onAuthSubmit(username, password, role, this.authMode === 'register');
                }
            });
        }

        // Event delegation for validator slash buttons
        if (this.elements.validatorsList) {
            this.elements.validatorsList.addEventListener('click', (e) => {
                const btn = e.target.closest('.btn-slash');
                if (btn && this.onSlashValidator) {
                    const name = btn.getAttribute('data-name');
                    if (name) {
                        this.onSlashValidator(name);
                    }
                }
            });
        }
    }

    setAuthMode(mode) {
        this.authMode = mode;
        this.hideAuthError();
        if (mode === 'login') {
            if (this.elements.tabAuthLogin) {
                this.elements.tabAuthLogin.className = 'btn btn-primary';
                this.elements.tabAuthLogin.style.flex = '1';
            }
            if (this.elements.tabAuthRegister) {
                this.elements.tabAuthRegister.className = 'btn btn-secondary';
                this.elements.tabAuthRegister.style.flex = '1';
            }
            if (this.elements.authModalTitle) {
                this.elements.authModalTitle.textContent = 'Sign In';
            }
            if (this.elements.btnSubmitAuth) {
                this.elements.btnSubmitAuth.textContent = 'Sign In';
            }
            if (this.elements.authRoleGroup) {
                this.elements.authRoleGroup.classList.add('hidden');
            }
        } else {
            if (this.elements.tabAuthLogin) {
                this.elements.tabAuthLogin.className = 'btn btn-secondary';
                this.elements.tabAuthLogin.style.flex = '1';
            }
            if (this.elements.tabAuthRegister) {
                this.elements.tabAuthRegister.className = 'btn btn-primary';
                this.elements.tabAuthRegister.style.flex = '1';
            }
            if (this.elements.authModalTitle) {
                this.elements.authModalTitle.textContent = 'Create Account';
            }
            if (this.elements.btnSubmitAuth) {
                this.elements.btnSubmitAuth.textContent = 'Register & Sign In';
            }
            if (this.elements.authRoleGroup) {
                this.elements.authRoleGroup.classList.remove('hidden');
            }
        }
    }

    openAuthModal(mode = 'login') {
        this.setAuthMode(mode);
        if (this.elements.authUsername) this.elements.authUsername.value = '';
        if (this.elements.authPassword) this.elements.authPassword.value = '';
        if (this.elements.authModal) this.elements.authModal.classList.remove('hidden');
        if (this.elements.authUsername) this.elements.authUsername.focus();
    }

    closeAuthModal() {
        if (this.elements.authModal) this.elements.authModal.classList.add('hidden');
    }

    showAuthError(msg) {
        if (this.elements.authErrorBox && this.elements.authErrorText) {
            this.elements.authErrorText.textContent = msg;
            this.elements.authErrorBox.classList.remove('hidden');
        }
    }

    hideAuthError() {
        if (this.elements.authErrorBox) {
            this.elements.authErrorBox.classList.add('hidden');
        }
    }

    updateRoleUI(user) {
        const isAdmin = !!(user && user.role === 'admin');

        // Header Badge & Buttons
        if (user) {
            if (this.elements.btnOpenAuth) this.elements.btnOpenAuth.classList.add('hidden');
            if (this.elements.btnLogout) this.elements.btnLogout.classList.remove('hidden');
            if (isAdmin) {
                if (this.elements.userRoleBadge) this.elements.userRoleBadge.className = 'badge badge-admin';
                if (this.elements.userRoleText) this.elements.userRoleText.textContent = `🛡️ Admin: ${user.username}`;
            } else {
                if (this.elements.userRoleBadge) this.elements.userRoleBadge.className = 'badge badge-viewer';
                if (this.elements.userRoleText) this.elements.userRoleText.textContent = `👁️ Viewer: ${user.username}`;
            }
        } else {
            if (this.elements.btnOpenAuth) this.elements.btnOpenAuth.classList.remove('hidden');
            if (this.elements.btnLogout) this.elements.btnLogout.classList.add('hidden');
            if (this.elements.userRoleBadge) this.elements.userRoleBadge.className = 'badge badge-viewer';
            if (this.elements.userRoleText) this.elements.userRoleText.textContent = '👁️ Viewer';
        }

        // Mode Banner
        if (this.elements.roleModeBanner) {
            if (isAdmin) {
                this.elements.roleModeBanner.className = 'mode-banner admin-banner';
                if (this.elements.modeBannerIcon) this.elements.modeBannerIcon.textContent = '🛡️';
                if (this.elements.modeBannerText) {
                    this.elements.modeBannerText.innerHTML = '<strong>Admin Mode:</strong> Full blockchain authority enabled. You can forge blocks, simulate attacks, add/slash validators, and modify network state.';
                }
                if (this.elements.btnBannerSwitchAdmin) this.elements.btnBannerSwitchAdmin.classList.add('hidden');
            } else {
                this.elements.roleModeBanner.className = 'mode-banner viewer-banner';
                if (this.elements.modeBannerIcon) this.elements.modeBannerIcon.textContent = '👁️';
                if (this.elements.modeBannerText) {
                    this.elements.modeBannerText.innerHTML = '<strong>Viewer Mode:</strong> Exploring the blockchain in read-only mode. Sign in as <strong>Admin</strong> to forge blocks, simulate attacks, or edit network state.';
                }
                if (this.elements.btnBannerSwitchAdmin) this.elements.btnBannerSwitchAdmin.classList.remove('hidden');
            }
        }

        // Toolbar Propose/Forge Block Button
        if (this.elements.btnMineBlock) {
            if (isAdmin) {
                this.elements.btnMineBlock.removeAttribute('disabled');
                this.elements.btnMineBlock.title = 'Forge a new block via PoS lottery';
            } else {
                this.elements.btnMineBlock.setAttribute('disabled', 'true');
                this.elements.btnMineBlock.title = 'Admin privileges required to forge blocks';
            }
        }

        // Validator form gating
        if (this.elements.formAddValidator) {
            const submitBtn = this.elements.formAddValidator.querySelector('button[type="submit"]');
            if (submitBtn) {
                if (isAdmin) {
                    submitBtn.removeAttribute('disabled');
                    submitBtn.textContent = 'Register Validator';
                } else {
                    submitBtn.setAttribute('disabled', 'true');
                    submitBtn.textContent = 'Admin Required to Add Validator';
                }
            }
        }

        // Update drawer permissions if open
        this._updateDrawerPermissions(isAdmin);
    }

    _updateDrawerPermissions(isAdmin) {
        if (this.elements.drawerViewerNotice) {
            if (isAdmin) {
                this.elements.drawerViewerNotice.classList.add('hidden');
            } else {
                this.elements.drawerViewerNotice.classList.remove('hidden');
            }
        }
        if (this.elements.btnTamperBlock) {
            if (isAdmin) {
                this.elements.btnTamperBlock.removeAttribute('disabled');
            } else {
                this.elements.btnTamperBlock.setAttribute('disabled', 'true');
            }
        }
        if (this.elements.btnRemineBlock) {
            if (isAdmin) {
                this.elements.btnRemineBlock.removeAttribute('disabled');
            } else {
                this.elements.btnRemineBlock.setAttribute('disabled', 'true');
            }
        }
        if (this.elements.inspDataInput) {
            this.elements.inspDataInput.readOnly = !isAdmin;
        }
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

        // Role-based drawer control
        const isAdmin = typeof auth !== 'undefined' && auth && auth.isAdmin();
        this._updateDrawerPermissions(isAdmin);

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
        const txList = Array.isArray(transactions) ? transactions : [];
        this.elements.mempoolCount.textContent = txList.length;
        this.elements.mempoolQueueCount.textContent = txList.length;

        const list = this.elements.mempoolList;
        list.innerHTML = '';

        if (txList.length === 0) {
            list.innerHTML = '<div class="empty-msg">No pending transactions in mempool.</div>';
            return;
        }

        txList.forEach(tx => {
            const div = document.createElement('div');
            div.className = 'tx-item';
            const safeSender = escapeHtml(tx.sender);
            const safeRecipient = escapeHtml(tx.recipient);
            const safeAmount = Number(tx.amount) || 0;
            div.innerHTML = `
                <div><strong>${safeSender}</strong> ➔ <strong>${safeRecipient}</strong></div>
                <div style="color: var(--accent-cyan); font-weight: 600;">${safeAmount} Coins</div>
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
        const valList = Array.isArray(validators) ? validators : [];
        this.elements.validatorCount.textContent = valList.length;
        const list = this.elements.validatorsList;
        list.innerHTML = '';

        if (valList.length === 0) {
            list.innerHTML = '<div class="empty-msg">No validators registered.</div>';
            return;
        }

        const totalStake = valList.reduce((acc, v) => acc + (v.is_slashed ? 0 : (Number(v.stake) || 0)), 0);
        const isAdmin = typeof auth !== 'undefined' && auth && auth.isAdmin();

        valList.forEach(v => {
            const stakeNum = Number(v.stake) || 0;
            const prob = totalStake > 0 && !v.is_slashed ? ((stakeNum / totalStake) * 100).toFixed(1) : '0.0';
            const safeName = escapeHtml(v.name);
            const div = document.createElement('div');
            div.className = 'val-item';
            div.innerHTML = `
                <div>
                    <strong>${safeName}</strong> 
                    ${v.is_slashed ? '<span style="color:var(--accent-rose);">(SLASHED)</span>' : ''}
                </div>
                <div>Stake: <strong>${stakeNum}</strong> (${prob}%)</div>
                ${isAdmin && !v.is_slashed ? `<button class="btn btn-danger btn-slash" data-name="${safeName}" style="padding:4px 8px; font-size:11px;">Slash</button>` : ''}
            `;
            list.appendChild(div);
        });
    }
}

const ui = new UiManager();
