import re

filepath = r"c:\Users\Admin\OneDrive\Desktop\spectrum\frontend\pages\api_playground.html"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Add drawStaticConnections function and listeners
static_lines_js = """
    function drawStaticConnections() {
        const svg = document.getElementById('liveGraph');
        if (!svg) return;
        
        const existingLines = svg.querySelectorAll('.static-line');
        existingLines.forEach(l => l.remove());
        
        const container = document.getElementById('nodes-container');
        if (!container) return;
        const contRect = container.getBoundingClientRect();
        
        for (let i = 0; i < nodeSequence.length - 1; i++) {
            const fromEl = document.getElementById(`node-${nodeSequence[i]}`);
            const toEl = document.getElementById(`node-${nodeSequence[i+1]}`);
            if (!fromEl || !toEl) continue;
            
            const fromRect = fromEl.getBoundingClientRect();
            const toRect = toEl.getBoundingClientRect();
            
            // Draw from right edge of fromNode to left edge of toNode
            const startX = fromRect.right - contRect.left + 5;
            const startY = fromRect.top + fromRect.height/2 - contRect.top;
            const endX = toRect.left - contRect.left - 5;
            const endY = toRect.top + toRect.height/2 - contRect.top;
            
            const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
            line.setAttribute("x1", startX);
            line.setAttribute("y1", startY);
            line.setAttribute("x2", endX);
            line.setAttribute("y2", endY);
            line.setAttribute("stroke", "#334155"); // Static faint color
            line.setAttribute("stroke-width", "2");
            line.setAttribute("stroke-dasharray", "5,5");
            line.setAttribute("marker-end", "url(#arrow)");
            line.setAttribute("class", "static-line");
            
            // Insert at the beginning so particles draw over it
            svg.insertBefore(line, svg.firstChild);
        }
    }
    
    window.addEventListener('resize', drawStaticConnections);
    // Draw immediately, then again slightly later to ensure layout is complete
    window.addEventListener('DOMContentLoaded', () => setTimeout(drawStaticConnections, 100));
    window.addEventListener('load', () => setTimeout(drawStaticConnections, 500));
"""

if "drawStaticConnections" not in content:
    content = content.replace("    // Connect WebSocket on load", static_lines_js + "\n    // Connect WebSocket on load")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print("Injected static lines script.")
else:
    print("Already injected.")
