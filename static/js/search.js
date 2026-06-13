/**
 * Real-time search with autocomplete suggestions for the results table.
 */
document.addEventListener('DOMContentLoaded', function () {
    const searchInput = document.getElementById('search-input');
    const searchFilter = document.getElementById('search-filter');
    const resultsBody = document.getElementById('results-body');
    const suggestionsBox = document.getElementById('search-suggestions');

    if (!searchInput || !resultsBody) return;

    let debounceTimer;

    // Search on input
    searchInput.addEventListener('input', function () {
        clearTimeout(debounceTimer);
        const q = this.value.trim();

        // Show suggestions
        if (q.length >= 1) {
            fetchSuggestions(q, searchFilter.value);
        } else {
            suggestionsBox.classList.add('hidden');
        }

        // Debounced search
        debounceTimer = setTimeout(() => {
            performSearch(q, searchFilter.value);
        }, 300);
    });

    // Search on filter change
    searchFilter.addEventListener('change', function () {
        const q = searchInput.value.trim();
        performSearch(q, this.value);
        if (q.length >= 1) {
            fetchSuggestions(q, this.value);
        }
    });

    // Search on Enter
    searchInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
            suggestionsBox.classList.add('hidden');
        }
    });

    // Click outside to close suggestions
    document.addEventListener('click', function (e) {
        if (!searchInput.contains(e.target) && !suggestionsBox.contains(e.target)) {
            suggestionsBox.classList.add('hidden');
        }
    });

    function fetchSuggestions(q, filter) {
        fetch(`/api/search/suggestions?q=${encodeURIComponent(q)}&filter=${filter}`)
            .then(r => r.json())
            .then(data => {
                suggestionsBox.innerHTML = '';
                if (data.length === 0) {
                    suggestionsBox.classList.add('hidden');
                    return;
                }
                data.forEach(item => {
                    const div = document.createElement('div');
                    div.className = 'px-4 py-2 hover:bg-gray-100 cursor-pointer text-sm';
                    div.textContent = item;
                    div.addEventListener('click', function () {
                        searchInput.value = this.textContent;
                        suggestionsBox.classList.add('hidden');
                        performSearch(this.textContent, searchFilter.value);
                    });
                    suggestionsBox.appendChild(div);
                });
                suggestionsBox.classList.remove('hidden');
            })
            .catch(() => {});
    }

    function performSearch(q, filter) {
        const params = new URLSearchParams({ q, filter });
        fetch(`/api/search?${params}`)
            .then(r => r.json())
            .then(data => {
                resultsBody.innerHTML = '';
                if (data.length === 0) {
                    resultsBody.innerHTML = `
                        <tr>
                            <td colspan="4" class="px-4 py-8 text-center text-gray-400">
                                No results found.
                            </td>
                        </tr>`;
                    return;
                }
                data.forEach(r => {
                    const tr = document.createElement('tr');
                    tr.className = 'hover:bg-gray-50';
                    tr.innerHTML = `
                        <td class="px-4 py-2.5 font-mono">${r.student_id}</td>
                        <td class="px-4 py-2.5 text-center font-medium">${r.rank || '—'}</td>
                        <td class="px-4 py-2.5 text-center">
                            <span class="font-mono font-bold text-buet-blue">${r.combo}</span>
                        </td>
                        <td class="px-4 py-2.5">${r.supervisor}</td>
                    `;
                    resultsBody.appendChild(tr);
                });
            })
            .catch(() => {});
    }
});
