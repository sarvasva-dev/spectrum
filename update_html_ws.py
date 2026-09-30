import re

def update_html():
    filepath = r"c:\Users\Admin\OneDrive\Desktop\spectrum\frontend\pages\api_playground.html"
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update Subtitle & Status
    # from: <span id="healthText">CHECKING API...</span>
    # to: <span id="healthText">WEBSOCKET CONNECTED</span>
    if 'id="wsStatusText"' not in content:
        content = content.replace(
            '<span id="healthText">CHECKING API...</span>',
            '<span id="wsStatusText">CONNECTING...</span>'
        )

    # 2. Add SVG graph
    # Replace the current `.flow-diagram-container`
    new_svg_graph = """
        <div class="metrics-bar" style="display:flex; gap:20px; font-family:var(--font-mono); font-size:0.85rem; color:var(--text-muted); margin-bottom:12px; background:#05070f; padding:10px 16px; border-radius:8px; border:1px solid #1e293b;">
            <div style="color:var(--primary); font-weight:bold;">LIVE REQUESTS: <span id="metric-total">0</span></div>
            <div style="color:#34d399;">2xx: <span id="metric-2xx">0</span></div>
            <div style="color:#fbbf24;">4xx: <span id="metric-4xx">0</span></div>
            <div style="color:#ef4444;">5xx: <span id="metric-5xx">0</span></div>
            <div style="color:#06b6d4;">ACTIVE: <span id="metric-active">0</span></div>
            <div style="color:#a855f7;">AVG RESP: <span id="metric-avg">0</span>ms</div>
            <div style="margin-left:auto;">Last event: <span id="metric-last">--:--:--</span></div>
        </div>

        <div style="position: relative; padding: 20px; background-color: #05070f; border: 1px solid #1e293b; border-radius: 10px; overflow: hidden; margin-bottom: 20px;">
            <svg id="liveGraph" width="100%" height="150" style="display: block;">
                <defs>
                    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                        <path d="M 0 0 L 10 5 L 0 10 z" fill="#334155" />
                    </marker>
                    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                        <feGaussianBlur stdDeviation="3" result="blur" />
                        <feComposite in="SourceGraphic" in2="blur" operator="over" />
                    </filter>
                </defs>
                <!-- Paths will be drawn by JS -->
            </svg>
            <div id="nodes-container" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; display: flex; align-items: center; justify-content: space-between; padding: 0 40px;">
                <!-- HTML Nodes overlay -->
                <div class="flow-step-node" id="node-client" style="position:relative; pointer-events:auto; z-index:2; transition: all 0.2s;">
                    <div class="node-icon">🌐</div>
                    <div class="node-title">CLIENT</div>
                    <div class="node-subtitle">Browser / fetch()</div>
                    <div class="node-status" style="font-size:0.65rem; color:#34d399; margin-top:5px; font-weight:bold; height:12px;"></div>
                </div>
                
                <div class="flow-step-node" id="node-django" style="position:relative; pointer-events:auto; z-index:2; transition: all 0.2s;">
                    <div class="node-icon">🐍</div>
                    <div class="node-title">DJANGO BACKEND</div>
                    <div class="node-subtitle">urls.py & views.py</div>
                    <div class="node-status" style="font-size:0.65rem; color:#34d399; margin-top:5px; font-weight:bold; height:12px;"></div>
                </div>
                
                <div class="flow-step-node" id="node-smart_logic" style="position:relative; pointer-events:auto; z-index:2; transition: all 0.2s;">
                    <div class="node-icon">⚙️</div>
                    <div class="node-title">SMART LOGIC</div>
                    <div class="node-subtitle">Priority Engine</div>
                    <div class="node-status" style="font-size:0.65rem; color:#34d399; margin-top:5px; font-weight:bold; height:12px;"></div>
                </div>
                
                <div class="flow-step-node" id="node-sqlite" style="position:relative; pointer-events:auto; z-index:2; transition: all 0.2s;">
                    <div class="node-icon">💾</div>
                    <div class="node-title">SQLITE3 DB</div>
                    <div class="node-subtitle">Django ORM</div>
                    <div class="node-status" style="font-size:0.65rem; color:#34d399; margin-top:5px; font-weight:bold; height:12px;"></div>
                </div>
                
                <div class="flow-step-node" id="node-response" style="position:relative; pointer-events:auto; z-index:2; transition: all 0.2s;">
                    <div class="node-icon">📦</div>
                    <div class="node-title">JSON RESPONSE</div>
                    <div class="node-subtitle">HTTP Output</div>
                    <div class="node-status" style="font-size:0.65rem; color:#34d399; margin-top:5px; font-weight:bold; height:12px;"></div>
                </div>
            </div>
        </div>
        
        <div style="font-family:var(--font-mono); font-size:0.75rem; color:var(--text-muted); text-align:center;">
            Every animation on this screen is driven by a real backend event via Django Channels.
        </div>
        
        <div style="margin-top:20px; padding:16px; background:#05070f; border:1px solid #1e293b; border-radius:10px;">
            <div style="font-family:var(--font-mono); font-size:0.85rem; color:var(--primary); margin-bottom:8px; display:flex; justify-content:space-between;">
                <span>LIVE EVENT LOG</span>
                <button class="btn-dev btn-dev-primary" onclick="runLiveDemo()" style="padding: 4px 12px; font-size: 0.8rem;">▶ RUN LIVE DEMO</button>
            </div>
            <div id="event-log" style="font-family:var(--font-mono); font-size:0.8rem; color:var(--text-code); height:150px; overflow-y:auto; display:flex; flex-direction:column-reverse; gap:4px; padding:8px; background:#0f172a; border-radius:6px; border:1px solid #1e293b;">
                <div style="color:var(--text-muted);">[System] Event stream ready...</div>
            </div>
        </div>
"""

    content = re.sub(r'<div class="flow-diagram-container">.*?</section>', new_svg_graph + "\n      </section>", content, flags=re.DOTALL)

    # 3. Add JS script for websocket and animations
    js_logic = """
<script>
    // System Visualizer WebSocket Logic
    const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
    const wsUrl = wsScheme + "://" + window.location.host + "/ws/visualizer/";
    let visualizerWs = null;
    let wsReconnectAttempts = 0;
    
    // Metrics State
    let metrics = { total: 0, _2xx: 0, _4xx: 0, _5xx: 0, active: 0, durations: [] };

    function connectWebSocket() {
        visualizerWs = new WebSocket(wsUrl);
        
        visualizerWs.onopen = function() {
            document.getElementById('wsStatusText').innerText = "WEBSOCKET CONNECTED";
            document.getElementById('healthBadge').style.backgroundColor = "#064e3b";
            document.getElementById('healthBadge').style.borderColor = "#059669";
            wsReconnectAttempts = 0;
            logEvent("SYSTEM", "WebSocket connected successfully.", "#34d399");
        };
        
        visualizerWs.onmessage = function(e) {
            const data = JSON.parse(e.data);
            handleBackendEvent(data);
        };
        
        visualizerWs.onclose = function() {
            document.getElementById('wsStatusText').innerText = "OFFLINE - RECONNECTING...";
            document.getElementById('healthBadge').style.backgroundColor = "#7f1d1d";
            document.getElementById('healthBadge').style.borderColor = "#dc2626";
            
            const backoff = Math.min(10000, 1000 * Math.pow(1.5, wsReconnectAttempts));
            wsReconnectAttempts++;
            setTimeout(connectWebSocket, backoff);
        };
    }
    
    function logEvent(source, msg, color="#e2e8f0") {
        const log = document.getElementById('event-log');
        const d = new Date();
        const ts = `[${d.getHours().toString().padStart(2,'0')}:${d.getMinutes().toString().padStart(2,'0')}:${d.getSeconds().toString().padStart(2,'0')}.${d.getMilliseconds().toString().padStart(3,'0')}]`;
        document.getElementById('metric-last').innerText = ts.replace('[','').replace(']','').split('.')[0];
        
        const entry = document.createElement('div');
        entry.innerHTML = `<span style="color:var(--text-muted);">${ts}</span> <span style="color:${color}; font-weight:bold;">${source}</span> ${msg}`;
        log.prepend(entry);
        
        if (log.children.length > 50) log.removeChild(log.lastChild);
    }
    
    function updateMetricsDisplay() {
        document.getElementById('metric-total').innerText = metrics.total;
        document.getElementById('metric-2xx').innerText = metrics._2xx;
        document.getElementById('metric-4xx').innerText = metrics._4xx;
        document.getElementById('metric-5xx').innerText = metrics._5xx;
        document.getElementById('metric-active').innerText = metrics.active;
        
        if (metrics.durations.length > 0) {
            const avg = metrics.durations.reduce((a,b)=>a+b, 0) / metrics.durations.length;
            document.getElementById('metric-avg').innerText = Math.round(avg);
        }
    }
    
    // Nodes mapping
    const nodeSequence = ['client', 'django', 'smart_logic', 'sqlite', 'response'];
    const activeRequests = {};
    
    function handleBackendEvent(evt) {
        if (!activeRequests[evt.request_id]) {
            activeRequests[evt.request_id] = { current: 'client' };
            metrics.total++;
            metrics.active++;
            updateMetricsDisplay();
        }
        
        const req = activeRequests[evt.request_id];
        let fromNode = req.current;
        let toNode = evt.node;
        
        // Handle node sequence jump
        if (evt.type === 'response') {
            toNode = 'response';
        }
        
        animatePacket(fromNode, toNode, evt.type === 'response' ? '#10b981' : '#3b82f6');
        glowNode(toNode, evt.request_id);
        req.current = toNode;
        
        // Log event
        if (evt.type === 'request_start') {
            logEvent("REQUEST", `${evt.method} ${evt.path} [${evt.request_id}]`, "#3b82f6");
        } else if (evt.type === 'response') {
            metrics.active = Math.max(0, metrics.active - 1);
            if (evt.status >= 200 && evt.status < 300) metrics._2xx++;
            else if (evt.status >= 400 && evt.status < 500) metrics._4xx++;
            else if (evt.status >= 500) metrics._5xx++;
            
            if (evt.duration_ms) {
                metrics.durations.push(evt.duration_ms);
                if (metrics.durations.length > 20) metrics.durations.shift();
            }
            updateMetricsDisplay();
            
            let color = evt.status >= 400 ? "#ef4444" : "#10b981";
            logEvent("RESPONSE", `${evt.status} OK • ${evt.duration_ms}ms [${evt.request_id}]`, color);
            delete activeRequests[evt.request_id];
        } else {
            logEvent(toNode.toUpperCase(), `EVENT RECEIVED [${evt.request_id}]`, "#a855f7");
        }
    }
    
    function glowNode(nodeId, reqId) {
        const el = document.getElementById(`node-${nodeId}`);
        if (!el) return;
        el.style.borderColor = "#3b82f6";
        el.style.boxShadow = "0 0 20px rgba(59, 130, 246, 0.6)";
        el.style.transform = "translateY(-4px)";
        
        const statusEl = el.querySelector('.node-status');
        if (statusEl) {
            statusEl.innerText = `REC: ${reqId}`;
            statusEl.style.color = "#34d399";
        }
        
        setTimeout(() => {
            el.style.borderColor = "#334155";
            el.style.boxShadow = "none";
            el.style.transform = "none";
            if (statusEl) statusEl.innerText = "";
        }, 800);
    }
    
    function animatePacket(fromId, toId, color) {
        if (fromId === toId) return;
        const fromEl = document.getElementById(`node-${fromId}`);
        const toEl = document.getElementById(`node-${toId}`);
        const container = document.getElementById('nodes-container');
        
        if (!fromEl || !toEl || !container) return;
        
        const fromRect = fromEl.getBoundingClientRect();
        const toRect = toEl.getBoundingClientRect();
        const contRect = container.getBoundingClientRect();
        
        const startX = fromRect.right - contRect.left;
        const startY = fromRect.top + fromRect.height/2 - contRect.top;
        const endX = toRect.left - contRect.left;
        const endY = toRect.top + toRect.height/2 - contRect.top;
        
        const svg = document.getElementById('liveGraph');
        
        // Draw line temporarily
        const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
        line.setAttribute("x1", startX);
        line.setAttribute("y1", startY);
        line.setAttribute("x2", endX);
        line.setAttribute("y2", endY);
        line.setAttribute("stroke", "#1e3a8a");
        line.setAttribute("stroke-width", "2");
        line.setAttribute("stroke-dasharray", "4,4");
        svg.appendChild(line);
        
        // Particle
        const particle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        particle.setAttribute("r", "5");
        particle.setAttribute("fill", color);
        particle.setAttribute("filter", "url(#glow)");
        svg.appendChild(particle);
        
        let start = null;
        const duration = 400; // ms
        
        function step(timestamp) {
            if (!start) start = timestamp;
            const progress = (timestamp - start) / duration;
            if (progress < 1) {
                const x = startX + (endX - startX) * progress;
                const y = startY + (endY - startY) * progress;
                particle.setAttribute("cx", x);
                particle.setAttribute("cy", y);
                window.requestAnimationFrame(step);
            } else {
                svg.removeChild(particle);
                svg.removeChild(line);
            }
        }
        window.requestAnimationFrame(step);
    }

    // Connect WebSocket on load
    window.addEventListener('DOMContentLoaded', connectWebSocket);
    
    // Live Demo Function
    async function runLiveDemo() {
        logEvent("DEMO", "Starting live request sequence...", "#fbbf24");
        
        // Execute a quick sequence of safe GET requests to drive the graph
        try {
            await fetch('/api/health/');
            await new Promise(r => setTimeout(r, 600));
            await fetch('/api/complaints/');
            await new Promise(r => setTimeout(r, 700));
            await fetch('/api/health/');
        } catch (e) {
            console.error("Demo error", e);
        }
    }
</script>
"""
    if "connectWebSocket" not in content:
        content = content.replace("</body>", js_logic + "\n</body>")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print("Injected HTML visualizer.")

if __name__ == "__main__":
    update_html()
