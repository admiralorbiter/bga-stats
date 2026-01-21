$(document).ready(function() {
    const $loading = $('#loading');
    const $error = $('#error');
    const $errorMessage = $('#error-message');
    const $emptyState = $('#empty-state');
    const $matchesTable = $('#matches-table');
    const $matchesTbody = $('#matches-tbody');
    const $gameFilter = $('#game-filter');
    const $playerFilter = $('#player-filter');
    const $dateFromFilter = $('#date-from-filter');
    const $dateToFilter = $('#date-to-filter');
    const $minMovesFilter = $('#min-moves-filter');
    const $maxMovesFilter = $('#max-moves-filter');
    const $clearFilters = $('#clear-filters');
    const $resultsCount = $('#results-count');
    const $countValue = $('#count-value');

    // Load matches on page load
    loadMatches();

    // Filter inputs with debouncing
    let filterTimeout;
    function debounceFilter() {
        clearTimeout(filterTimeout);
        filterTimeout = setTimeout(loadMatches, 300);
    }

    $gameFilter.on('input', debounceFilter);
    $playerFilter.on('input', debounceFilter);
    $dateFromFilter.on('change', loadMatches);
    $dateToFilter.on('change', loadMatches);
    $minMovesFilter.on('input', debounceFilter);
    $maxMovesFilter.on('input', debounceFilter);

    // Clear filters button
    $clearFilters.on('click', function() {
        $gameFilter.val('');
        $playerFilter.val('');
        $dateFromFilter.val('');
        $dateToFilter.val('');
        $minMovesFilter.val('');
        $maxMovesFilter.val('');
        loadMatches();
    });

    function loadMatches() {
        $loading.show();
        $error.hide();
        $emptyState.hide();
        $matchesTable.hide();
        $resultsCount.hide();

        // Build query parameters
        const params = {};
        
        const gameName = $gameFilter.val().trim();
        if (gameName) {
            params.game_name = gameName;
        }
        
        const playerName = $playerFilter.val().trim();
        if (playerName) {
            params.player_name = playerName;
        }
        
        const dateFrom = $dateFromFilter.val();
        if (dateFrom) {
            params.date_from = dateFrom + 'T00:00:00';
        }
        
        const dateTo = $dateToFilter.val();
        if (dateTo) {
            params.date_to = dateTo + 'T23:59:59';
        }
        
        const minMoves = $minMovesFilter.val();
        if (minMoves) {
            params.min_moves = minMoves;
        }
        
        const maxMoves = $maxMovesFilter.val();
        if (maxMoves) {
            params.max_moves = maxMoves;
        }

        $.ajax({
            url: '/api/matches',
            method: 'GET',
            data: params,
            success: function(response) {
                $loading.hide();
                
                if (response.success && response.matches && response.matches.length > 0) {
                    renderMatches(response.matches);
                    $matchesTable.show();
                    $resultsCount.show();
                    $countValue.text(response.count);
                } else {
                    $emptyState.show();
                }
            },
            error: function(xhr, status, error) {
                $loading.hide();
                $error.show();
                $errorMessage.text(xhr.responseJSON?.error || 'Failed to load matches. Please try again.');
            }
        });
    }

    function renderMatches(matches) {
        $matchesTbody.empty();
        
        matches.forEach(function(match) {
            const row = $('<tr>')
                .addClass('hover:bg-gray-50 cursor-pointer')
                .on('click', function() {
                    window.location.href = `/matches/${match.bga_table_id}`;
                });
            
            // Table ID
            const tableIdCell = $('<td>')
                .addClass('px-6 py-4 whitespace-nowrap text-sm font-medium text-blue-600')
                .text('#' + match.bga_table_id);
            
            // Game Name
            const gameCell = $('<td>')
                .addClass('px-6 py-4 whitespace-nowrap text-sm text-gray-900')
                .text(match.game_name);
            
            // Move Count with badge
            const movesCell = $('<td>')
                .addClass('px-6 py-4 whitespace-nowrap text-sm text-gray-900');
            const movesBadge = $('<span>')
                .addClass('inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium')
                .text(match.move_count);
            
            // Color badge based on move count
            if (match.move_count <= 50) {
                movesBadge.addClass('bg-green-100 text-green-800');
            } else if (match.move_count <= 100) {
                movesBadge.addClass('bg-yellow-100 text-yellow-800');
            } else {
                movesBadge.addClass('bg-red-100 text-red-800');
            }
            movesCell.append(movesBadge);
            
            // Duration
            const durationCell = $('<td>')
                .addClass('px-6 py-4 whitespace-nowrap text-sm text-gray-500')
                .text(formatDuration(match.duration_minutes));
            
            // Players
            const playersCell = $('<td>')
                .addClass('px-6 py-4 text-sm text-gray-500')
                .text(truncatePlayers(match.player_names, 3));
            
            // Imported Date
            const importedCell = $('<td>')
                .addClass('px-6 py-4 whitespace-nowrap text-sm text-gray-500')
                .text(formatDate(match.imported_at));
            
            row.append(tableIdCell, gameCell, movesCell, durationCell, playersCell, importedCell);
            $matchesTbody.append(row);
        });
    }

    function formatDuration(minutes) {
        if (!minutes && minutes !== 0) {
            return 'N/A';
        }
        
        if (minutes < 60) {
            return minutes + ' min' + (minutes !== 1 ? 's' : '');
        }
        
        const hours = Math.floor(minutes / 60);
        const remainingMins = minutes % 60;
        
        if (remainingMins === 0) {
            return hours + ' hr' + (hours !== 1 ? 's' : '');
        }
        
        return hours + ' hr' + (hours !== 1 ? 's' : '') + ' ' + remainingMins + ' min' + (remainingMins !== 1 ? 's' : '');
    }

    function truncatePlayers(players, maxDisplay) {
        if (!players || players.length === 0) {
            return 'N/A';
        }
        
        if (players.length <= maxDisplay) {
            return players.join(', ');
        }
        
        const displayed = players.slice(0, maxDisplay);
        const remaining = players.length - maxDisplay;
        return displayed.join(', ') + ' and ' + remaining + ' more';
    }

    function formatDate(isoDate) {
        if (!isoDate) {
            return 'N/A';
        }
        
        const date = new Date(isoDate);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
});
