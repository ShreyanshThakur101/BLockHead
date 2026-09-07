/* ==========================================================================
   CONFIG CONSTANTS & CONSTANTS DEFAULTS
   ========================================================================== */

const CONFIG = {
    API_BASE_URL: 'http://127.0.0.1:5000/api',
    SOCKET_URL: 'http://127.0.0.1:5000',
    
    // Canvas Card Dimensions & Rendering Options
    CANVAS: {
        BLOCK_WIDTH: 220,
        BLOCK_HEIGHT: 150,
        BLOCK_SPACING: 80,
        BORDER_RADIUS: 12,
        START_X: 100,
        START_Y: 200,
        FONT_FAMILY: "'Inter', sans-serif",
        FONT_CODE: "'JetBrains Mono', monospace",
        
        // Colors
        COLOR_BG_CARD: '#1E293B',
        COLOR_BORDER_VALID: '#10B981',
        COLOR_BORDER_INVALID: '#EF4444',
        COLOR_BORDER_NORMAL: '#334155',
        COLOR_TEXT_TITLE: '#F8FAFC',
        COLOR_TEXT_SUB: '#94A3B8',
        COLOR_LINK_VALID: '#00F2FE',
        COLOR_LINK_INVALID: '#EF4444',
        COLOR_GLOW_VALID: 'rgba(0, 242, 254, 0.4)',
        COLOR_GLOW_INVALID: 'rgba(239, 68, 68, 0.5)'
    }
};
