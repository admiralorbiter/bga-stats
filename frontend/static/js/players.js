$(document).ready(function() {
    const $loading = $('#loading');
    const $error = $('#error');
    const $errorMessage = $('#error-message');
    const $emptyState = $('#empty-state');
    const $playersTable = $('#players-table');
    const $playersTbody = $('#players-tbody');

    // Load players on page load
    loadPlayers();

    function loadPlayers() {
        $loading.show();
        $error.hide();
        $emptyState.hide();
        $playersTable.hide();

        $.ajax({
            url: '/api/players',
            method: 'GET',
            success: function(response) {
                $loading.hide();
                
                if (response.success && response.players && response.players.length > 0) {
                    renderPlayers(response.players);
                    $playersTable.show();
                } else {
                    $emptyState.show();
                }
            },
            error: function(xhr) {
                $loading.hide();
                $error.show();
                
                let errorMsg = 'Failed to load players';
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMsg = xhr.responseJSON.error;
                }
                $errorMessage.text(errorMsg);
            }
        });
    }

    function renderPlayers(players) {
        $playersTbody.empty();

        players.forEach(function(player) {
            const winRate = player.matches_total > 0 
                ? ((player.wins_total / player.matches_total) * 100).toFixed(1) + '%'
                : 'N/A';

            const row = `
                <tr class="hover:bg-gray-50 transition-colors">
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="flex items-center">
                            <div>
                                <div class="text-sm font-medium text-gray-900">
                                    ${escapeHtml(player.name)}
                                </div>
                                <div class="text-xs text-gray-500">
                                    ID: ${player.bga_player_id || 'N/A'}
                                </div>
                            </div>
                        </div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="text-sm text-gray-900">${formatNumber(player.xp)}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="text-sm text-gray-900">${formatNumber(player.karma)}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="text-sm text-gray-900">${formatNumber(player.matches_total)}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="text-sm text-gray-900">${formatNumber(player.wins_total)}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getWinRateColor(player.wins_total, player.matches_total)}">
                            ${winRate}
                        </span>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <a href="/players/${player.id}" class="text-blue-600 hover:text-blue-900 font-medium">
                            View Details →
                        </a>
                    </td>
                </tr>
            `;

            $playersTbody.append(row);
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
});
