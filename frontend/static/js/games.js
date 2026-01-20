$(document).ready(function() {
    const $loading = $('#loading');
    const $error = $('#error');
    const $errorMessage = $('#error-message');
    const $emptyState = $('#empty-state');
    const $gamesTable = $('#games-table');
    const $gamesTbody = $('#games-tbody');
    const $searchInput = $('#search-input');
    const $statusFilter = $('#status-filter');
    const $premiumFilter = $('#premium-filter');
    const $clearFilters = $('#clear-filters');
    const $resultsCount = $('#results-count');

    let allGames = []; // Store all games for client-side filtering

    // Load games on page load
    loadGames();

    // Search input with debounce
    let searchTimeout;
    $searchInput.on('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(filterGames, 300);
    });

    // Filter change handlers
    $statusFilter.on('change', filterGames);
    $premiumFilter.on('change', filterGames);

    // Clear filters button
    $clearFilters.on('click', function() {
        $searchInput.val('');
        $statusFilter.val('');
        $premiumFilter.val('');
        filterGames();
    });

    function loadGames() {
        $loading.show();
        $error.hide();
        $emptyState.hide();
        $gamesTable.hide();

        $.ajax({
            url: '/api/games',
            method: 'GET',
            success: function(response) {
                $loading.hide();
                
                if (response.success && response.games) {
                    allGames = response.games;
                    filterGames(); // Apply any active filters
                } else {
                    $emptyState.show();
                }
            },
            error: function(xhr) {
                $loading.hide();
                $error.show();
                
                let errorMsg = 'Failed to load games';
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMsg = xhr.responseJSON.error;
                }
                $errorMessage.text(errorMsg);
            }
        });
    }

    function filterGames() {
        const searchTerm = $searchInput.val().toLowerCase();
        const statusFilter = $statusFilter.val();
        const premiumFilter = $premiumFilter.val();

        const filtered = allGames.filter(function(game) {
            // Search filter
            if (searchTerm) {
                const nameMatch = game.name.toLowerCase().includes(searchTerm);
                const displayMatch = game.display_name.toLowerCase().includes(searchTerm);
                if (!nameMatch && !displayMatch) return false;
            }

            // Status filter
            if (statusFilter && game.status !== statusFilter) {
                return false;
            }

            // Premium filter
            if (premiumFilter !== '') {
                const isPremium = game.premium;
                if ((premiumFilter === '1' && !isPremium) || 
                    (premiumFilter === '0' && isPremium)) {
                    return false;
                }
            }

            return true;
        });

        if (filtered.length > 0) {
            renderGames(filtered);
            $gamesTable.show();
            $emptyState.hide();
        } else {
            $gamesTable.hide();
            $emptyState.show();
        }

        // Update results count
        $resultsCount.text(`Showing ${filtered.length} of ${allGames.length} games`);
    }

    function renderGames(games) {
        $gamesTbody.empty();

        games.forEach(function(game) {
            const statusBadge = getStatusBadge(game.status);
            const premiumBadge = game.premium ? 
                '<span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-yellow-100 text-yellow-800">Premium</span>' :
                '<span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">Free</span>';

            const row = `
                <tr class="hover:bg-gray-50 transition-colors">
                    <td class="px-6 py-4">
                        <div class="text-sm font-medium text-gray-900">
                            ${escapeHtml(game.display_name)}
                        </div>
                        <div class="text-xs text-gray-500">
                            ${escapeHtml(game.name)}
                        </div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        ${statusBadge}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        ${premiumBadge}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="text-sm text-gray-900">${game.bga_game_id}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <a href="/games/${game.id}" class="text-blue-600 hover:text-blue-900 font-medium">
                            View Details →
                        </a>
                    </td>
                </tr>
            `;

            $gamesTbody.append(row);
        });
    }

    function getStatusBadge(status) {
        const badges = {
            'published': '<span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">Published</span>',
            'beta': '<span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">Beta</span>',
            'alpha': '<span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-orange-100 text-orange-800">Alpha</span>'
        };
        return badges[status] || status;
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
});
