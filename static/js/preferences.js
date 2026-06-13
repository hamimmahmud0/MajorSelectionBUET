/* ================================================================
   Drag-and-Drop (shared for combos and supervisors)
   ================================================================ */

let draggedRow = null;

/**
 * Enable drag-and-drop on all rows inside a container.
 * @param {string|Element} container — container element or its id
 * @param {string} rowSelector — CSS selector for draggable rows
 * @param {string} badgeSelector — CSS selector for the priority badge inside each row
 * @param {string} highlightColor — ring/border color class for visual feedback
 */
function enableDragDrop(container, rowSelector, badgeSelector, highlightColor) {
    const list = typeof container === 'string'
        ? document.getElementById(container)
        : container;
    if (!list) return;

    const refreshRows = () => {
        list.querySelectorAll(rowSelector).forEach(row => attachDragEvents(row, list, rowSelector, badgeSelector, highlightColor));
    };
    refreshRows();
}


function attachDragEvents(row, list, rowSelector, badgeSelector, highlightColor) {
    // Remove old listeners by cloning (simplest approach for re-init safety)
    // Instead, we use a flag to avoid double-binding
    if (row._dragInitialized) return;
    row._dragInitialized = true;

    row.addEventListener('dragstart', function (e) {
        draggedRow = this;
        this.classList.add('opacity-40', 'ring-2', highlightColor);
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', 'dragged');
    });

    row.addEventListener('dragend', function () {
        this.classList.remove('opacity-40', 'ring-2', highlightColor);
        list.querySelectorAll(rowSelector).forEach(r => {
            r.classList.remove('ring-2', highlightColor);
        });
        draggedRow = null;
    });

    row.addEventListener('dragover', function (e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
    });

    row.addEventListener('dragleave', function () {
        // no-op
    });

    row.addEventListener('drop', function (e) {
        e.preventDefault();
        if (this === draggedRow) return;

        const allRows = Array.from(list.querySelectorAll(rowSelector));
        const fromIdx = allRows.indexOf(draggedRow);
        const toIdx = allRows.indexOf(this);

        if (fromIdx < toIdx) {
            this.insertAdjacentElement('afterend', draggedRow);
        } else {
            this.insertAdjacentElement('beforebegin', draggedRow);
        }

        // Renumber badges in this container
        renumberBadges(list, rowSelector, badgeSelector);
    });
}

function renumberBadges(list, rowSelector, badgeSelector) {
    const rows = list.querySelectorAll(rowSelector);
    rows.forEach((row, idx) => {
        const badge = row.querySelector(badgeSelector);
        if (badge) badge.textContent = idx + 1;
    });
}

/* ================================================================
   Combo Preferences
   ================================================================ */

function initComboDragDrop() {
    enableDragDrop('combo-preference-list', '.combo-row', '.priority-badge', 'ring-buet-blue');
}

function saveComboPreferences() {
    const list = document.getElementById('combo-preference-list');
    if (!list) return;

    const rows = list.querySelectorAll('.combo-row');
    const preferences = [];

    rows.forEach((row, idx) => {
        preferences.push({
            major: row.dataset.major,
            minor: row.dataset.minor,
            priority: idx + 1
        });
    });

    fetch('/api/preferences/combo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ preferences })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            const status = document.getElementById('combo-save-status');
            status.classList.remove('hidden');
            status.textContent = '✓ Saved! Allocation updated.';
            setTimeout(() => status.classList.add('hidden'), 3000);
        } else {
            alert('Error: ' + (data.error || 'Failed to save'));
        }
    })
    .catch(err => {
        alert('Network error: ' + err);
    });
}

/* ================================================================
   Supervisor Tab Switching
   ================================================================ */

function switchSupervisorTab(majorCode) {
    // Hide all panels
    document.querySelectorAll('.sup-panel').forEach(p => p.style.display = 'none');

    // Show selected panel
    const panel = document.getElementById('sup-panel-' + majorCode);
    if (panel) panel.style.display = 'block';

    // Update tab styles
    document.querySelectorAll('.sup-tab').forEach(tab => {
        const m = tab.dataset.major;
        const clr = getMajorColor(m);
        if (m === majorCode) {
            tab.className = `sup-tab px-5 py-2 rounded-t-lg text-sm font-medium transition cursor-pointer bg-${clr}-500 text-white`;
        } else {
            tab.className = `sup-tab px-5 py-2 rounded-t-lg text-sm font-medium transition cursor-pointer bg-gray-100 text-gray-600 hover:bg-${clr}-100`;
        }
    });
}

function getMajorColor(major) {
    return { S: 'blue', T: 'emerald', E: 'violet', G: 'amber' }[major] || 'gray';
}

/* ================================================================
   Supervisor Preferences (drag-drop based)
   ================================================================ */

function initSupervisorDragDrop() {
    document.querySelectorAll('.supervisor-list').forEach(list => {
        enableDragDrop(list, '.supervisor-row', '.sup-priority-badge', 'ring-gray-400');
    });
}

function saveSupervisorPreferences(majorCode) {
    const list = document.getElementById('supervisor-list-' + majorCode);
    if (!list) return;

    const rows = list.querySelectorAll('.supervisor-row');
    const preferences = [];

    rows.forEach((row, idx) => {
        preferences.push({
            supervisor_id: parseInt(row.dataset.supervisorId),
            priority: idx + 1
        });
    });

    fetch('/api/preferences/supervisor', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ major_code: majorCode, preferences })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            const status = document.getElementById('sup-save-status-' + majorCode);
            status.classList.remove('hidden');
            status.textContent = '✓ Saved! Allocation updated.';
            setTimeout(() => status.classList.add('hidden'), 3000);
        } else {
            alert('Error: ' + (data.error || 'Failed to save'));
        }
    })
    .catch(err => {
        alert('Network error: ' + err);
    });
}

/* ================================================================
   Init on page load
   ================================================================ */
document.addEventListener('DOMContentLoaded', function () {
    initComboDragDrop();
    initSupervisorDragDrop();
});
