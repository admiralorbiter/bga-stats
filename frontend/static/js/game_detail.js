$(document).ready(function() {
    const $loading = $('#loading');
    const $error = $('#error');
    const $errorMessage = $('#error-message');
    const $gameContent = $('#game-content');
    
    const $gameDisplayName = $('#game-display-name');
    const $gameName = $('#game-name');
    const $gameStatus = $('#game-status');
    const $gamePremium = $('#game-premium');
    const $gameBgaId = $('#game-bga-id');
    const $playerCount = $('#player-count');
    
    const $playerStatsEmpty = $('#player-stats-empty');
    const $playerStatsTable = $('#player-stats-table');
    const $playerStatsTbody = $('#player-stats-tbody');

    // Get game ID from window object (set by Flask template)
    const gameId = window.GAME_ID;

    // Load game details on page load
    loadGameDetails();

    function loadGameDetails() {
        $loading.show();
        $error.hide();
        $gameContent.hide();

        $.ajax({
            url: `/api/games/${gameId}`,
            method: 'GET',
            success: function(response) {
                $loading.hide();
                
                if (response.success && response.game) {
                    renderGame(response.game);
                    $gameContent.show();
                } else {
                    showError('Failed to load game details');
                }
            },
            error: function(xhr) {
                $loading.hide();
                
                let errorMsg = 'Failed to load game details';
                if (xhr.status === 404) {
                    errorMsg = 'Game not found';
                } else if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMsg = xhr.responseJSON.error;
                }
                showError(errorMsg);
            }
        });
    }

    function renderGame(game) {
        // Set header
        $gameDisplayName.text(game.display_name);
        $gameName.text(`Internal name: ${game.name}`);

        // Set game info
        $gameStatus.html(getStatusBadge(game.status));
        $gamePremium.html(getPremiumBadge(game.premium));
        $gameBgaId.text(game.bga_game_id);
        $playerCount.text(game.player_count);

        // Render player stats
        if (game.players && game.players.length > 0) {
            renderPlayerStats(game.players);
            $playerStatsTable.show();
        } else {
            $playerStatsEmpty.show();
        }
    }

    function renderPlayerStats(players) {
        $playerStatsTbody.empty();

        // Sort by ELO (descending), handling "N/A" values
        players.sort((a, b) => {
            const aElo = isNaN(a.elo) ? 0 : parseInt(a.elo);
            const bElo = isNaN(b.elo) ? 0 : parseInt(b.elo);
            return bElo - aElo;
        });

        players.forEach(function(player) {
            const winRateBadge = getWinRateBadge(player.win_rate);

            const row = `
                <tr class="hover:bg-gray-50 transition-colors">
                    <td class="px-6 py-4">
                        <div class="text-sm font-medium text-gray-900">
                            ${escapeHtml(player.player_name)}
                        </div>
                        <div class="text-xs text-gray-500">
                            ID: ${player.bga_player_id || 'N/A'}
                        </div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="text-sm text-gray-900">${player.elo || 'N/A'}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="text-sm text-gray-900">${player.rank || 'N/A'}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="text-sm text-gray-900">${formatNumber(player.played)}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="text-sm text-gray-900">${formatNumber(player.won)}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        ${winRateBadge}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <a href="/players/${player.player_id}" class="text-blue-600 hover:text-blue-900 font-medium">
                            View Player →
                        </a>
                    </td>
                </tr>
            `;

            $playerStatsTbody.append(row);
        });
    }

    function getStatusBadge(status) {
        const badges = {
            'published': '<span class="text-lg px-3 py-1 inline-flex leading-5 font-semibold rounded-full bg-green-100 text-green-800">Published</span>',
            'beta': '<span class="text-lg px-3 py-1 inline-flex leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">Beta</span>',
            'alpha': '<span class="text-lg px-3 py-1 inline-flex leading-5 font-semibold rounded-full bg-orange-100 text-orange-800">Alpha</span>'
        };
        return badges[status] || status;
    }

    function getPremiumBadge(isPremium) {
        if (isPremium) {
            return '<span class="text-lg px-3 py-1 inline-flex leading-5 font-semibold rounded-full bg-yellow-100 text-yellow-800">Premium</span>';
        } else {
            return '<span class="text-lg px-3 py-1 inline-flex leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">Free</span>';
        }
    }

    function getWinRateBadge(winRate) {
        let colorClass;
        if (winRate >= 60) colorClass = 'bg-green-100 text-green-800';
        else if (winRate >= 50) colorClass = 'bg-blue-100 text-blue-800';
        else if (winRate >= 40) colorClass = 'bg-yellow-100 text-yellow-800';
        else colorClass = 'bg-red-100 text-red-800';

        return `<span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${colorClass}">${winRate}%</span>`;
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
