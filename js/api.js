/* ==========================================================================
   API CLIENT & WEBSOCKET MANAGER (Proof of Stake)
   ========================================================================== */

class ApiClient {
    constructor() {
        this.socket = null;
        this.eventListeners = {};
    }

    initSocket() {
        if (typeof io !== 'undefined') {
            try {
                this.socket = io(CONFIG.SOCKET_URL, {
                    reconnectionAttempts: 3,
                    timeout: 5000,
                    transports: ['websocket', 'polling']
                });
                
                this.socket.on('connect', () => {
                    console.log('⚡ Socket.IO Connected to PoS Server');
                });

                this.socket.on('connect_error', (err) => {
                    // Gracefully handles serverless environments (e.g. Vercel) where WebSockets are unavailable
                    console.warn('Socket.IO connection notice (operating in HTTP REST mode):', err.message);
                });
            } catch (err) {
                console.warn('Socket.IO initialization skipped:', err.message);
            }

            this.socket.on('block_added', (data) => {
                this._emit('block_added', data);
            });

            this.socket.on('chain_tampered', (data) => {
                this._emit('chain_tampered', data);
            });

            this.socket.on('block_resealed', (data) => {
                this._emit('block_resealed', data);
            });

            this.socket.on('block_remined', (data) => {
                this._emit('block_remined', data);
            });

            this.socket.on('mempool_updated', (data) => {
                this._emit('mempool_updated', data);
            });

            this.socket.on('validators_updated', (data) => {
                this._emit('validators_updated', data);
            });
        }
    }

    on(event, callback) {
        if (!this.eventListeners[event]) {
            this.eventListeners[event] = [];
        }
        this.eventListeners[event].push(callback);
    }

    _emit(event, data) {
        if (this.eventListeners[event]) {
            this.eventListeners[event].forEach(cb => cb(data));
        }
    }

    async _request(endpoint, method = 'GET', body = null) {
        const headers = {
            'Content-Type': 'application/json'
        };

        if (typeof auth !== 'undefined' && auth && auth.getToken()) {
            headers['Authorization'] = `Bearer ${auth.getToken()}`;
        }

        const options = {
            method,
            headers
        };

        if (body) {
            options.body = JSON.stringify(body);
        }

        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}${endpoint}`, options);
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || `HTTP error status ${response.status}`);
            }
            return data;
        } catch (error) {
            console.error(`API Request Error [${method} ${endpoint}]:`, error);
            throw error;
        }
    }

    async getChain() {
        return await this._request('/chain');
    }

    async forgeBlock(data = '', validator = null) {
        return await this._request('/forge', 'POST', { data, validator });
    }

    async mineBlock(data = '', validator = null) {
        return await this.forgeBlock(data, validator);
    }

    async tamperBlock(index, data) {
        return await this._request(`/tamper/${index}`, 'POST', { data });
    }

    async resealBlock(index, validator = null) {
        return await this._request(`/reseal/${index}`, 'POST', { validator });
    }

    async remineBlock(index) {
        return await this.resealBlock(index);
    }

    async validateChain() {
        return await this._request('/validate');
    }

    async getMempool() {
        return await this._request('/mempool');
    }

    async createTransaction(sender, recipient, amount) {
        return await this._request('/mempool', 'POST', { sender, recipient, amount });
    }

    async getValidators() {
        return await this._request('/validators');
    }

    async updateValidator(action, name, stake = 0) {
        return await this._request('/validators', 'POST', { action, name, stake });
    }

    async register(username, password, role = 'viewer') {
        return await this._request('/auth/register', 'POST', { username, password, role });
    }

    async login(username, password) {
        return await this._request('/auth/login', 'POST', { username, password });
    }

    async getProfile() {
        return await this._request('/auth/me');
    }
}

const api = new ApiClient();
