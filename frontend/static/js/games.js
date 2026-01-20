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
    const $myGamesFilter = $('#my-games-filter');
    const $clearFilters = $('#clear-filters');
    const $resultsCount = $('#results-count');

    // Load games on page load
    loadGames();

    // Search input with debounce
    let searchTimeout;
    $searchInput.on('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(loadGames, 300);
    });

    // Filter change handlers - reload from server when filters change
    $statusFilter.on('change', loadGames);
    $premiumFilter.on('change', loadGames);
    $myGamesFilter.on('change', loadGames);

    // Clear filters button
    $clearFilters.on('click', function() {
        $searchInput.val('');
        $statusFilter.val('');
        $premiumFilter.val('');
        $myGamesFilter.prop('checked', false);
        loadGames();
    });

    function loadGames() {
        $loading.show();
        $error.hide();
        $emptyState.hide();
        $gamesTable.hide();

        // Build query parameters
        const params = {};
        
        const searchTerm = $searchInput.val().trim();
        if (searchTerm) {
            params.search = searchTerm;
        }
        
        const statusFilter = $statusFilter.val();
        if (statusFilter) {
            params.status = statusFilter;
        }
        
        const premiumFilter = $premiumFilter.val();
        if (premiumFilter) {
            params.premium = premiumFilter;
        }
        
        // Add has_stats filter if "My Games" is checked
        if ($myGamesFilter.is(':checked')) {
            params.has_stats = 'true';
            console.log('Filtering to games with stats');
        }

        console.log('API params:', params);

        $.ajax({
            url: '/api/games',
            method: 'GET',
            data: params,
            success: function(response) {
                $loading.hide();
                
                if (response.success && response.games && response.games.length > 0) {
                    renderGames(response.games);
                    $gamesTable.show();
                    $resultsCount.text(`Showing ${response.games.length} games`);
                } else {
                    $emptyState.show();
                    $resultsCount.text('Showing 0 games');
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
