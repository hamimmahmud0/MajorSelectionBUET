/* ================================================================
   Combined (Combo + Supervisor) Preference System
   ================================================================ */

let draggedRow = null;

/* ─── Helper: major color ─── */
function majorColor(m) {
    return { S: 'blue', T: 'emerald', E: 'violet', G: 'amber' }[m] || 'gray';
}

function majorName(m) {
    return { S: 'Structure', T: 'Transport', E: 'Environment', G: 'Geotech' }[m] || m;
}

/* ─── Supervisor dropdown filtering ─── */
document.addEventListener('DOMContentLoaded', function () {
    const comboSelect = document.getElementById('new-combo-select');
    const supSelect = document.getElementById('new-supervisor-select');
    if (!comboSelect || !supSelect) return;

    // Load supervisor data from hidden JSON
    const scriptTag = document.getElementById('supervisor-data');
    if (scriptTag) {
        try {
            window._allSupervisors = JSON.parse(scriptTag.textContent);
        } catch (e) {
            window._allSupervisors = [];
        }
    }

    comboSelect.addEventListener('change', function () {
        updateSupDropdown();
    });

    // Init drag-drop and badge numbering on existing rows
    initPrefListDragDrop();
    renumberPrefBadges();
});

function updateSupDropdown() {
    const comboSelect = document.getElementById('new-combo-select');
    const supSelect = document.getElementById('new-supervisor-select');
    if (!comboSelect || !supSelect) return;

    const val = comboSelect.value;
    supSelect.innerHTML = '<option value="">— Select supervisor —</option>';

    if (!val || val.length < 2) return;

    const major = val[0];
    const supData = window._allSupervisors || [];
    const filtered = supData.filter(s => s.major_code === major);

    filtered.forEach(s => {
        const opt = document.createElement('option');
        opt.value = s.id;
        opt.textContent = s.name + ' (' + s.seats + ' seats)';
        supSelect.appendChild(opt);
    });
}

/* ─── Add preference row ─── */
function addPreferenceRow() {
    const comboSelect = document.getElementById('new-combo-select');
    const supSelect = document.getElementById('new-supervisor-select');
    const list = document.getElementById('preference-list');
    if (!comboSelect || !supSelect || !list) return;

    const comboVal = comboSelect.value;
    const supVal = supSelect.value;
    if (!comboVal || !supVal) {
        alert('Please select both a combo and a supervisor.');
        return;
    }

    const major = comboVal[0];
    const minor = comboVal[1];
    const supId = parseInt(supVal);
    const supName = supSelect.options[supSelect.selectedIndex].textContent;
    const mclr = majorColor(major);

    // Remove empty message
    const emptyMsg = document.getElementById('empty-message');
    if (emptyMsg) emptyMsg.remove();

    // Check for duplicates
    const existing = Array.from(list.querySelectorAll('.pref-row'));
    const isDuplicate = existing.some(row =>
        row.dataset.major === major &&
        row.dataset.minor === minor &&
        parseInt(row.dataset.supervisorId) === supId
    );
    if (isDuplicate) {
        alert('This exact combo + supervisor pair is already in your list.');
        return;
    }

    const div = document.createElement('div');
    div.className = `pref-row flex items-center gap-3 rounded-lg px-4 py-3 border-l-4 shadow-sm cursor-grab active:cursor-grabbing select-none transition-shadow hover:shadow-md bg-white border-${mclr}-400`;
    div.draggable = true;
    div.dataset.major = major;
    div.dataset.minor = minor;
    div.dataset.supervisorId = supId;
    div.innerHTML = `
        <span class="text-gray-400 text-lg font-bold drag-handle">⠿</span>
        <span class="pref-badge w-7 h-7 rounded-full text-white text-xs font-bold flex items-center justify-center shrink-0 bg-${mclr}-600">${existing.length + 1}</span>
        <span class="font-mono font-bold w-14 text-${mclr}-700">${comboVal}</span>
        <span class="text-xs text-gray-500 flex-1">${majorName(major)} → ${majorName(minor)}</span>
        <span class="text-sm font-medium text-${mclr}-700">${supName}</span>
        <button onclick="this.closest('.pref-row').remove(); renumberPrefBadges();"
                class="text-red-400 hover:text-red-600 text-lg transition ml-2">✕</button>
    `;

    list.appendChild(div);

    // Attach drag events
    attachDragEvents(div, list, '.pref-row', '.pref-badge', 'ring-gray-400');
    renumberPrefBadges();

    // Reset selects
    comboSelect.value = '';
    supSelect.innerHTML = '<option value="">— Select combo first —</option>';
}

/* ─── Drag-and-Drop ─── */
function initPrefListDragDrop() {
    const list = document.getElementById('preference-list');
    if (!list) return;
    list.querySelectorAll('.pref-row').forEach(row => {
        attachDragEvents(row, list, '.pref-row', '.pref-badge', 'ring-gray-400');
    });
}

function attachDragEvents(row, list, rowSelector, badgeSelector, highlightColor) {
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
        list.querySelectorAll(rowSelector).forEach(r => r.classList.remove('ring-2', highlightColor));
        draggedRow = null;
    });

    row.addEventListener('dragover', function (e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
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
        renumberPrefBadges();
    });
}

function renumberPrefBadges() {
    const list = document.getElementById('preference-list');
    if (!list) return;
    const rows = list.querySelectorAll('.pref-row');
    rows.forEach((row, idx) => {
        const badge = row.querySelector('.pref-badge');
        if (badge) badge.textContent = idx + 1;
    });
    // Show/hide empty message
    let emptyMsg = document.getElementById('empty-message');
    if (rows.length === 0) {
        if (!emptyMsg) {
            emptyMsg = document.createElement('div');
            emptyMsg.id = 'empty-message';
            emptyMsg.className = 'text-center py-8 text-gray-400';
            emptyMsg.textContent = 'No preferences added yet. Use the form above to add combo + supervisor pairs.';
            list.appendChild(emptyMsg);
        }
    } else {
        if (emptyMsg) emptyMsg.remove();
    }
}

/* ─── Add available option to preferences ─── */
function addOptionToPrefs(major, minor, supervisorId, supervisorName) {
    const list = document.getElementById('preference-list');
    if (!list) return;

    const comboVal = major + minor;
    const mclr = majorColor(major);

    // Check for duplicates
    const existing = Array.from(list.querySelectorAll('.pref-row'));
    const isDuplicate = existing.some(row =>
        row.dataset.major === major &&
        row.dataset.minor === minor &&
        parseInt(row.dataset.supervisorId) === supervisorId
    );
    if (isDuplicate) {
        alert('This pair is already in your preference list.');
        return;
    }

    // Remove empty message
    const emptyMsg = document.getElementById('empty-message');
    if (emptyMsg) emptyMsg.remove();

    const div = document.createElement('div');
    div.className = `pref-row flex items-center gap-3 rounded-lg px-4 py-3 border-l-4 shadow-sm cursor-grab active:cursor-grabbing select-none transition-shadow hover:shadow-md bg-white border-${mclr}-400`;
    div.draggable = true;
    div.dataset.major = major;
    div.dataset.minor = minor;
    div.dataset.supervisorId = supervisorId;
    div.innerHTML = `
        <span class="text-gray-400 text-lg font-bold drag-handle">⠿</span>
        <span class="pref-badge w-7 h-7 rounded-full text-white text-xs font-bold flex items-center justify-center shrink-0 bg-${mclr}-600">${existing.length + 1}</span>
        <span class="font-mono font-bold w-14 text-${mclr}-700">${comboVal}</span>
        <span class="text-xs text-gray-500 flex-1">${majorName(major)} → ${majorName(minor)}</span>
        <span class="text-sm font-medium text-${mclr}-700">${supervisorName}</span>
        <button onclick="this.closest('.pref-row').remove(); renumberPrefBadges();"
                class="text-red-400 hover:text-red-600 text-lg transition ml-2">✕</button>
    `;

    list.appendChild(div);
    attachDragEvents(div, list, '.pref-row', '.pref-badge', 'ring-gray-400');
    renumberPrefBadges();
}

/* ─── Save ─── */
function savePreferences() {
    const list = document.getElementById('preference-list');
    if (!list) return;

    const rows = list.querySelectorAll('.pref-row');
    const preferences = [];

    rows.forEach((row, idx) => {
        preferences.push({
            major: row.dataset.major,
            minor: row.dataset.minor,
            supervisor_id: parseInt(row.dataset.supervisorId),
            priority: idx + 1
        });
    });

    fetch('/api/preferences/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ preferences })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            const status = document.getElementById('save-status');
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
