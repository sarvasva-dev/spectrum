/**
 * SMART WASTE MANAGEMENT SYSTEM - VANILLA JAVASCRIPT
 * Lightweight, zero-framework, clean interactions
 */

document.addEventListener('DOMContentLoaded', function () {
  // 1. Mobile Navigation Menu Toggle
  const mobileToggle = document.getElementById('mobileToggle');
  const navMenu = document.getElementById('navMenu');

  if (mobileToggle && navMenu) {
    mobileToggle.addEventListener('click', function () {
      navMenu.classList.toggle('show');
    });
  }

  // 2. Auto-dismiss Alert Messages after 6 seconds
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(function (alert) {
    setTimeout(function () {
      alert.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-10px)';
      setTimeout(function () {
        alert.remove();
      }, 400);
    }, 6000);
  });

  // 3. Dynamic Waste Category Guidance on Pickup Page
  const categorySelect = document.getElementById('pickup_category_select');
  const categoryGuidanceBox = document.getElementById('categoryGuidanceBox');
  const categoryGuidanceText = document.getElementById('categoryGuidanceText');

  const guidanceMap = {
    'ORGANIC': '🌿 Wet/Organic: Keep separate from plastics. Use compostable bags or green bins. Includes food scraps, peels, leaves.',
    'PLASTIC': '♻️ Plastic: Rinse food containers and squeeze bottles to reduce bulk. Remove caps. Recyclable.',
    'PAPER': '📦 Paper & Cardboard: Flatten cardboard boxes. Keep dry. Clean paper only; no oil-soaked wrappers.',
    'E_WASTE': '⚡ E-Waste: Handle with care! Keep batteries separate from regular solid trash. Prevent water exposure.',
    'GLASS': '🍾 Glass: Wrap broken glass carefully to protect sanitation crew. Rinse glass jars.',
    'METAL': '🔩 Metal: Scrap iron, aluminum cans, copper wires. Separate sharp edges safely.',
    'GENERAL': '🗑️ General: Mixed non-recyclable solid domestic waste.',
    'OTHER': 'ℹ️ Miscellaneous: Please describe specific waste characteristics in the notes field.'
  };

  if (categorySelect && categoryGuidanceBox && categoryGuidanceText) {
    function updateGuidance() {
      const selected = categorySelect.value;
      if (guidanceMap[selected]) {
        categoryGuidanceText.textContent = guidanceMap[selected];
        categoryGuidanceBox.style.display = 'block';
      } else {
        categoryGuidanceBox.style.display = 'none';
      }
    }
    categorySelect.addEventListener('change', updateGuidance);
    updateGuidance();
  }

  // 4. Smart Priority Preview on Report Waste Page
  const issueSelect = document.getElementById('issue_type_select');
  const priorityTipBox = document.getElementById('priorityTipBox');
  const priorityTipText = document.getElementById('priorityTipText');

  const priorityHints = {
    'OVERFLOWING_BIN': 'Urgent: Overflowing bins attract pests and will be prioritized as HIGH or CRITICAL.',
    'GARBAGE_ON_ROAD': 'Public Hazard: Road waste obstructs traffic and will be assigned HIGH priority.',
    'ILLEGAL_DUMPING': 'Violation: Illegal dumping poses environmental risks and triggers HIGH priority.',
    'MISSED_COLLECTION': 'Standard: Missed collection triggers a re-route notification (MEDIUM priority).',
    'IMPROPER_SEGREGATION': 'Quality: Segregation violation flagged for inspection (MEDIUM priority).',
    'OTHER': 'General: Assessed by municipal dispatch coordinator.'
  };

  if (issueSelect && priorityTipBox && priorityTipText) {
    function updatePriorityHint() {
      const issue = issueSelect.value;
      if (priorityHints[issue]) {
        priorityTipText.textContent = priorityHints[issue];
        priorityTipBox.style.display = 'block';
      } else {
        priorityTipBox.style.display = 'none';
      }
    }
    issueSelect.addEventListener('change', updatePriorityHint);
    updatePriorityHint();
  }

  // 5. Interactive Awareness Waste Search
  const searchInput = document.getElementById('wasteSearchInput');
  const searchResultBox = document.getElementById('wasteSearchResult');

  const wasteLookupDB = [
    { item: 'Banana Peel / Fruit Scraps', bin: 'Green Bin (Wet / Organic)', tip: 'Compostable naturally.' },
    { item: 'Plastic Water Bottle', bin: 'Blue Bin (Dry / Recyclable)', tip: 'Rinse and crush.' },
    { item: 'Milk Packet / Pouch', bin: 'Blue Bin (Dry / Recyclable)', tip: 'Rinse with water before binning.' },
    { item: 'Newspaper / Cardboard', bin: 'Blue Bin (Dry / Recyclable)', tip: 'Keep dry and flat.' },
    { item: 'Mobile Phone Battery', bin: 'Red/Black Bin (Hazardous / E-Waste)', tip: 'Never discard in municipal bins.' },
    { item: 'Medicine Blister Pack', bin: 'Red/Black Bin (Hazardous)', tip: 'Expired medicines require medical drop-off.' },
    { item: 'Glass Jam Jar', bin: 'Blue Bin (Dry / Recyclable)', tip: 'Wash and keep separate.' },
    { item: 'Soda Can / Tin Can', bin: 'Blue Bin (Dry / Recyclable)', tip: 'Recyclable metal.' },
    { item: 'Food Leftovers / Rice / Bread', bin: 'Green Bin (Wet / Organic)', tip: 'Decomposes into compost.' },
    { item: 'Fluorescent Bulb / CFL', bin: 'Red/Black Bin (Hazardous)', tip: 'Contains mercury vapors; do not break.' }
  ];

  if (searchInput && searchResultBox) {
    searchInput.addEventListener('input', function () {
      const query = searchInput.value.trim().toLowerCase();
      if (!query) {
        searchResultBox.innerHTML = '';
        searchResultBox.style.display = 'none';
        return;
      }

      const matches = wasteLookupDB.filter(entry => 
        entry.item.toLowerCase().includes(query) || entry.bin.toLowerCase().includes(query)
      );

      if (matches.length > 0) {
        let html = '<div class="card" style="padding: 14px; margin-top: 10px;">';
        matches.forEach(m => {
          html += `
            <div style="padding: 8px 0; border-bottom: 1px solid var(--border-color);">
              <strong>${m.item}</strong> ➔ <span class="badge ${m.bin.includes('Green') ? 'badge-resolved' : m.bin.includes('Blue') ? 'badge-assigned' : 'badge-danger'}">${m.bin}</span>
              <p style="font-size: 0.82rem; color: var(--text-muted); margin-top: 2px;">${m.tip}</p>
            </div>
          `;
        });
        html += '</div>';
        searchResultBox.innerHTML = html;
        searchResultBox.style.display = 'block';
      } else {
        searchResultBox.innerHTML = `
          <div class="card" style="padding: 12px; margin-top: 10px; color: var(--text-muted); font-size: 0.9rem;">
            No direct match found for "<strong>${searchInput.value}</strong>". If dry and clean, use <strong>Blue Bin</strong>; if wet/food, use <strong>Green Bin</strong>.
          </div>
        `;
        searchResultBox.style.display = 'block';
      }
    });
  }
});
