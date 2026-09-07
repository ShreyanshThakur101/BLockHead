/* ==========================================================================
   AUTHENTICATION & ROLE-BASED ACCESS CONTROL (RBAC) MANAGER
   ========================================================================== */

class AuthManager {
    constructor() {
        this.tokenKey = 'blockhead_auth_token';
        this.userKey = 'blockhead_auth_user';
        this.token = localStorage.getItem(this.tokenKey) || null;
        this.user = null;
        try {
            const rawUser = localStorage.getItem(this.userKey);
            this.user = rawUser ? JSON.parse(rawUser) : null;
        } catch (e) {
            this.user = null;
        }
        this.listeners = [];
    }

    isLoggedIn() {
        return !!(this.token && this.user);
    }

    isAdmin() {
        return this.isLoggedIn() && this.user.role === 'admin';
    }

    isViewer() {
        return !this.isLoggedIn() || this.user.role === 'viewer';
    }

    getUser() {
        return this.user;
    }

    getToken() {
        return this.token;
    }

    setSession(token, user) {
        this.token = token;
        this.user = user;
        localStorage.setItem(this.tokenKey, token);
        localStorage.setItem(this.userKey, JSON.stringify(user));
        this._notifyListeners();
    }

    clearSession() {
        this.token = null;
        this.user = null;
        localStorage.removeItem(this.tokenKey);
        localStorage.removeItem(this.userKey);
        this._notifyListeners();
    }

    onAuthStateChanged(callback) {
        this.listeners.push(callback);
    }

    _notifyListeners() {
        this.listeners.forEach(cb => {
            try { cb(this.user); } catch (e) { console.error('Auth listener error:', e); }
        });
    }
}

const auth = new AuthManager();