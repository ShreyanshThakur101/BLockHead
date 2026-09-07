/* ==========================================================================
   2D HTML5 CANVAS RENDERER ENGINE
   ========================================================================== */

class CanvasRenderer {
    constructor(canvasElement) {
        this.canvas = canvasElement;
        this.ctx = canvasElement.getContext('2d');
        
        // Camera Transform State
        this.cameraX = 0;
        this.cameraY = 0;
        this.zoom = 1;

        // Interaction State
        this.isDragging = false;
        this.dragStartX = 0;
        this.dragStartY = 0;
        this.selectedBlockIndex = null;
        this.onBlockSelectCallback = null;

        // Chain Render Cache
        this.blocks = [];
        this.validation = { is_valid: true, broken_at_index: null };
        
        // Animation Phase Timers
        this.pulsePhase = 0;
        
        this.init();
    }

    init() {
        this.resize();
        window.addEventListener('resize', () => this.resize());
        this.bindEvents();
        this.startLoop();
    }

    resize() {
        const dpr = window.devicePixelRatio || 1;
        const rect = this.canvas.parentElement.getBoundingClientRect();
        this.canvas.width = rect.width * dpr;
        this.canvas.height = rect.height * dpr;
        this.ctx.scale(dpr, dpr);
        this.viewportWidth = rect.width;
        this.viewportHeight = rect.height;
        this.requestRender();
    }

    bindEvents() {
        this.canvas.addEventListener('mousedown', (e) => {
            this.isDragging = true;
            this.dragStartX = e.clientX - this.cameraX;
            this.dragStartY = e.clientY - this.cameraY;
            this.requestRender();
        });

        window.addEventListener('mousemove', (e) => {
            if (this.isDragging) {
                this.cameraX = e.clientX - this.dragStartX;
                this.cameraY = e.clientY - this.dragStartY;
                this.requestRender();
            }
        });

        window.addEventListener('mouseup', (e) => {
            if (this.isDragging) {
                // If drag distance was negligible, treat as click selection
                const distMoved = Math.hypot(
                    e.clientX - (this.dragStartX + this.cameraX),
                    e.clientY - (this.dragStartY + this.cameraY)
                );
                this.isDragging = false;
                
                if (distMoved < 5) {
                    this.handleCanvasClick(e);
                }
                this.requestRender();
            }
        });

        this.canvas.addEventListener('wheel', (e) => {
            e.preventDefault();
            const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
            this.zoom = Math.min(Math.max(this.zoom * zoomFactor, 0.4), 2.5);
            this.requestRender();
        }, { passive: false });
    }

    setChainData(blocks, validation) {
        this.blocks = blocks || [];
        this.validation = validation || { is_valid: true, broken_at_index: null };
        this.requestRender();
    }

    resetView() {
        this.cameraX = 0;
        this.cameraY = 0;
        this.zoom = 1;
        this.requestRender();
    }

    screenToWorld(screenX, screenY) {
        const rect = this.canvas.getBoundingClientRect();
        const mouseX = screenX - rect.left;
        const mouseY = screenY - rect.top;
        
        const worldX = (mouseX - this.viewportWidth / 2 - this.cameraX) / this.zoom + this.viewportWidth / 2;
        const worldY = (mouseY - this.viewportHeight / 2 - this.cameraY) / this.zoom + this.viewportHeight / 2;
        
        return { x: worldX, y: worldY };
    }

    getBlockLayoutPosition(index) {
        const cfg = CONFIG.CANVAS;
        const totalSpacing = cfg.BLOCK_WIDTH + cfg.BLOCK_SPACING;
        const x = cfg.START_X + index * totalSpacing;
        const y = cfg.START_Y;
        return { x, y, w: cfg.BLOCK_WIDTH, h: cfg.BLOCK_HEIGHT };
    }

    handleCanvasClick(e) {
        const pos = this.screenToWorld(e.clientX, e.clientY);
        
        for (let i = 0; i < this.blocks.length; i++) {
            const bPos = this.getBlockLayoutPosition(i);
            if (
                pos.x >= bPos.x &&
                pos.x <= bPos.x + bPos.w &&
                pos.y >= bPos.y &&
                pos.y <= bPos.y + bPos.h
            ) {
                this.selectedBlockIndex = i;
                this.requestRender();
                if (this.onBlockSelectCallback) {
                    this.onBlockSelectCallback(this.blocks[i], i);
                }
                return;
            }
        }
    }

    startLoop() {
        this.renderRequested = false;
        this.requestRender();
    }

    requestRender() {
        if (!this.renderRequested) {
            this.renderRequested = true;
            requestAnimationFrame(() => this.renderFrame());
        }
    }

    renderFrame() {
        this.renderRequested = false;
        if (!this.validation.is_valid) {
            this.pulsePhase = (this.pulsePhase + 0.05) % (Math.PI * 2);
        }
        this.draw();

        // Continue animation loop only if pulsing invalid chain or currently dragging
        if (!this.validation.is_valid || this.isDragging) {
            this.requestRender();
        }
    }

    draw() {
        const ctx = this.ctx;
        ctx.clearRect(0, 0, this.viewportWidth, this.viewportHeight);

        ctx.save();
        // Camera Transformations
        ctx.translate(this.viewportWidth / 2 + this.cameraX, this.viewportHeight / 2 + this.cameraY);
        ctx.scale(this.zoom, this.zoom);
        ctx.translate(-this.viewportWidth / 2, -this.viewportHeight / 2);

        // 1. Draw Chain Links / Connecting Lines
        for (let i = 0; i < this.blocks.length - 1; i++) {
            this.drawChainLink(i, i + 1);
        }

        // 2. Draw Block Nodes
        for (let i = 0; i < this.blocks.length; i++) {
            this.drawBlockNode(this.blocks[i], i);
        }

        ctx.restore();
    }

    drawChainLink(fromIdx, toIdx) {
        const ctx = this.ctx;
        const fromPos = this.getBlockLayoutPosition(fromIdx);
        const toPos = this.getBlockLayoutPosition(toIdx);

        const startX = fromPos.x + fromPos.w;
        const startY = fromPos.y + fromPos.h / 2;
        const endX = toPos.x;
        const endY = toPos.y + toPos.h / 2;

        // Check if link is broken (if chain is invalid at or before toIdx)
        const isBroken = !this.validation.is_valid && 
            this.validation.broken_at_index !== null && 
            toIdx >= this.validation.broken_at_index;

        ctx.save();
        ctx.beginPath();
        ctx.moveTo(startX, startY);
        ctx.lineTo(endX, endY);

        if (isBroken) {
            ctx.strokeStyle = CONFIG.CANVAS.COLOR_LINK_INVALID;
            ctx.lineWidth = 3;
            ctx.shadowColor = CONFIG.CANVAS.COLOR_GLOW_INVALID;
            ctx.shadowBlur = 12 + Math.sin(this.pulsePhase) * 6;
            ctx.setLineDash([8, 6]);
        } else {
            ctx.strokeStyle = CONFIG.CANVAS.COLOR_LINK_VALID;
            ctx.lineWidth = 2.5;
            ctx.shadowColor = CONFIG.CANVAS.COLOR_GLOW_VALID;
            ctx.shadowBlur = 8;
            ctx.setLineDash([]);
        }

        ctx.stroke();

        // Draw directional link arrow
        const arrowSize = 8;
        ctx.fillStyle = isBroken ? CONFIG.CANVAS.COLOR_LINK_INVALID : CONFIG.CANVAS.COLOR_LINK_VALID;
        ctx.beginPath();
        ctx.moveTo(endX - arrowSize, endY - arrowSize);
        ctx.lineTo(endX, endY);
        ctx.lineTo(endX - arrowSize, endY + arrowSize);
        ctx.fill();

        ctx.restore();
    }

    drawBlockNode(block, index) {
        const ctx = this.ctx;
        const pos = this.getBlockLayoutPosition(index);
        const cfg = CONFIG.CANVAS;

        // Determine validity status for block
        const isTamperedHere = !this.validation.is_valid && this.validation.broken_at_index === index;
        const isBrokenDownstream = !this.validation.is_valid && this.validation.broken_at_index !== null && index >= this.validation.broken_at_index;
        const isSelected = this.selectedBlockIndex === index;

        ctx.save();

        // Card Shadow & Glow
        if (isTamperedHere || isBrokenDownstream) {
            ctx.shadowColor = cfg.COLOR_GLOW_INVALID;
            ctx.shadowBlur = 16 + Math.sin(this.pulsePhase) * 4;
        } else if (isSelected) {
            ctx.shadowColor = cfg.COLOR_GLOW_VALID;
            ctx.shadowBlur = 20;
        } else {
            ctx.shadowColor = 'rgba(0,0,0,0.4)';
            ctx.shadowBlur = 10;
        }

        // Draw Rounded Card Background
        ctx.fillStyle = cfg.COLOR_BG_CARD;
        ctx.beginPath();
        ctx.roundRect(pos.x, pos.y, pos.w, pos.h, cfg.BORDER_RADIUS);
        ctx.fill();

        // Draw Card Border
        if (isTamperedHere || isBrokenDownstream) {
            ctx.strokeStyle = cfg.COLOR_BORDER_INVALID;
            ctx.lineWidth = 2.5;
        } else if (isSelected) {
            ctx.strokeStyle = cfg.COLOR_BORDER_VALID;
            ctx.lineWidth = 2.5;
        } else {
            ctx.strokeStyle = cfg.COLOR_BORDER_NORMAL;
            ctx.lineWidth = 1.5;
        }
        ctx.stroke();

        // Header Bar & Block Index Title
        ctx.font = `700 13px ${cfg.FONT_FAMILY}`;
        ctx.fillStyle = cfg.COLOR_TEXT_TITLE;
        ctx.fillText(`BLOCK #${block.index}`, pos.x + 16, pos.y + 28);

        // Status Badge Tag
        const badgeText = index === 0 ? 'GENESIS' : (isBrokenDownstream ? 'INVALID' : 'VALID');
        const badgeColor = index === 0 ? cfg.COLOR_LINK_VALID : (isBrokenDownstream ? cfg.COLOR_BORDER_INVALID : cfg.COLOR_BORDER_VALID);
        
        ctx.font = `600 10px ${cfg.FONT_FAMILY}`;
        ctx.fillStyle = badgeColor;
        ctx.fillText(badgeText, pos.x + pos.w - 60, pos.y + 28);

        // Divider Line inside Card
        ctx.strokeStyle = 'rgba(255,255,255,0.08)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(pos.x + 12, pos.y + 38);
        ctx.lineTo(pos.x + pos.w - 12, pos.y + 38);
        ctx.stroke();

        // Hash Info
        ctx.font = `400 11px ${cfg.FONT_CODE}`;
        ctx.fillStyle = cfg.COLOR_TEXT_SUB;
        ctx.fillText('Hash:', pos.x + 16, pos.y + 58);
        
        ctx.fillStyle = isBrokenDownstream ? cfg.COLOR_BORDER_INVALID : cfg.COLOR_LINK_VALID;
        const shortHash = block.hash ? `${block.hash.substring(0, 10)}...` : 'N/A';
        ctx.fillText(shortHash, pos.x + 55, pos.y + 58);

        // Prev Hash Info
        ctx.fillStyle = cfg.COLOR_TEXT_SUB;
        ctx.fillText('Prev:', pos.x + 16, pos.y + 78);
        const shortPrev = block.previous_hash ? `${block.previous_hash.substring(0, 10)}...` : 'None';
        ctx.fillText(shortPrev, pos.x + 55, pos.y + 78);

        // Validator Info
        ctx.fillStyle = cfg.COLOR_TEXT_SUB;
        ctx.fillText(`Validator: ${block.validator || 'System'}`, pos.x + 16, pos.y + 98);

        // Data / Payload snippet
        ctx.fillStyle = cfg.COLOR_TEXT_TITLE;
        const dataSnippet = block.data ? (block.data.length > 20 ? `${block.data.substring(0, 20)}...` : block.data) : 'Empty Payload';
        ctx.fillText(`Data: ${dataSnippet}`, pos.x + 16, pos.y + 124);

        ctx.restore();
    }
}
