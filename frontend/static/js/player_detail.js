$(document).ready(function() {
    const $loading = $('#loading');
    const $error = $('#error');
    const $errorMessage = $('#error-message');
    const $playerContent = $('#player-content');
    
    const $playerName = $('#player-name');
    const $playerBgaId = $('#player-bga-id');
    
    const $statXp = $('#stat-xp');
    const $statKarma = $('#stat-karma');
    const $statMatches = $('#stat-matches');
    const $statWins = $('#stat-wins');
    
    const $statAbandoned = $('#stat-abandoned');
    const $statTimeout = $('#stat-timeout');
    const $statRecent = $('#stat-recent');
    const $statLastSeen = $('#stat-last-seen');
    
    const $gameStatsEmpty = $('#game-stats-empty');
    const $gameStatsTable = $('#game-stats-table');
    const $gameStatsTbody = $('#game-stats-tbody');

    // Get player ID from window object (set by Flask template)
    const playerId = window.PLAYER_ID;

    // Load player details on page load
    loadPlayerDetails();

    function loadPlayerDetails() {
        $loading.show();
        $error.hide();
        $playerContent.hide();

        $.ajax({
            url: `/api/players/${playerId}`,
            method: 'GET',
            success: function(response) {
                $loading.hide();
                
                if (response.success && response.player) {
                    renderPlayer(response.player);
                    $playerContent.show();
                } else {
                    showError('Failed to load player details');
                }
            },
            error: function(xhr) {
                $loading.hide();
                
                let errorMsg = 'Failed to load player details';
                if (xhr.status === 404) {
                    errorMsg = 'Player not found';
                } else if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMsg = xhr.responseJSON.error;
                }
                showError(errorMsg);
            }
        });
    }

    function renderPlayer(player) {
        // Set header
        $playerName.text(player.name);
        $playerBgaId.text(`BGA ID: ${player.bga_player_id || 'N/A'}`);

        // Set overall stats
        $statXp.text(formatNumber(player.xp));
        $statKarma.text(formatNumber(player.karma));
        $statMatches.text(formatNumber(player.matches_total));
        $statWins.text(formatNumber(player.wins_total));

        // Set recent activity stats
        $statAbandoned.text(formatNumber(player.abandoned));
        $statTimeout.text(formatNumber(player.timeout));
        $statRecent.text(formatNumber(player.recent_matches));
        
        if (player.last_seen_days !== null && player.last_seen_days !== undefined) {
            $statLastSeen.text(`${player.last_seen_days} days ago`);
        } else {
            $statLastSeen.text('N/A');
        }

        // Render game stats
        if (player.game_stats && player.game_stats.length > 0) {
            renderGameStats(player.game_stats);
            $gameStatsTable.show();
        } else {
            $gameStatsEmpty.show();
        }
    }

    function renderGameStats(gameStats) {
        $gameStatsTbody.empty();

        // Sort by played count (descending)
        gameStats.sort((a, b) => (b.played || 0) - (a.played || 0));

        gameStats.forEach(function(stat) {
            const winRate = stat.played > 0 
                ? ((stat.won / stat.played) * 100).toFixed(1) + '%'
                : 'N/A';

            const row = `
                <tr class="hover:bg-gray-50 transition-colors">
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="text-sm font-medium text-gray-900">
                            ${escapeHtml(stat.game_name)}
                        </div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="text-sm text-gray-900">${stat.elo || 'N/A'}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="text-sm text-gray-900">${stat.rank || 'N/A'}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="text-sm text-gray-900">${formatNumber(stat.played)}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="text-sm text-gray-900">${formatNumber(stat.won)}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getWinRateColor(stat.won, stat.played)}">
                            ${winRate}
                        </span>
                    </td>
                </tr>
            `;

            $gameStatsTbody.append(row);
        });
    }

    function getWinRateColor(wins, total) {
        if (total === 0) return 'bg-gray-100 text-gray-800';
        
        const rate = (wins / total) * 100;
        
        if (rate >= 60) return 'bg-green-100 text-green-800';
        if (rate >= 50) return 'bg-blue-100 text-blue-800';
        if (rate >= 40) return 'bg-yellow-100 text-yellow-800';
        return 'bg-red-100 text-red-800';
    }

    function formatNumber(num) {
        if (num === null || num === undefined) return 'N/A';
        return num.toLocaleString();
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function showError(message) {
        $error.show();
        $errorMessage.text(message);
    }
});
