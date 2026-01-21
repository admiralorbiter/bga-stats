// Load tournament details on page load
$(document).ready(function() {
    loadTournamentDetail();
});

function loadTournamentDetail() {
    $('#loading').show();
    $('#error').hide();
    $('#tournament-content').hide();
    
    $.ajax({
        url: `/api/tournaments/${TOURNAMENT_ID}`,
        method: 'GET',
        success: function(response) {
            $('#loading').hide();
            
            if (response.success) {
                renderTournamentDetail(response.tournament);
                $('#tournament-content').show();
            } else {
                showError('Tournament not found');
            }
        },
        error: function(xhr) {
            $('#loading').hide();
            const errorMsg = xhr.responseJSON && xhr.responseJSON.error 
                ? xhr.responseJSON.error 
                : 'Failed to load tournament details';
            showError(errorMsg);
        }
    });
}

function renderTournamentDetail(tournament) {
    // Header
    $('#tournament-name').text(tournament.name);
    $('#tournament-game').text(tournament.game_name);
    
    const dates = tournament.start_time && tournament.end_time
        ? `${tournament.start_time} to ${tournament.end_time}`
        : tournament.start_time || 'Dates not available';
    $('#tournament-dates').text(dates);
    
    // Stats
    $('#stat-rounds').text(tournament.rounds || 0);
    $('#stat-round-limit').text(tournament.round_limit || 0);
    $('#stat-matches').text(tournament.total_matches || 0);
    $('#stat-timeouts').text(tournament.timeout_matches || 0);
    $('#stat-players').text(tournament.player_count || 0);
    
    // Matches table
    renderMatches(tournament.matches);
}

function renderMatches(matches) {
    const tbody = $('#matches-tbody');
    tbody.empty();
    
    if (!matches || matches.length === 0) {
        tbody.append(`
            <tr>
                <td colspan="4" class="px-6 py-4 text-center text-sm text-gray-500">
                    No matches found
                </td>
            </tr>
        `);
        return;
    }
    
    matches.forEach(function(match) {
        const statusBadge = match.is_timeout
            ? '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">Timeout</span>'
            : '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">Completed</span>';
        
        const playersList = match.players.map(function(player) {
            const timeClass = player.timed_out ? 'text-red-600 font-semibold' : 'text-gray-600';
            const timeDisplay = player.remaining_time_hours !== null 
                ? `${player.remaining_time_hours}h`
                : 'N/A';
            
            return `
                <div class="mb-1">
                    <span class="font-medium">${escapeHtml(player.name)}</span>:
                    <span class="${timeClass}">${timeDisplay}</span>
                    ${player.points ? `(${player.points} pts)` : ''}
                </div>
            `;
        }).join('');
        
        const row = `
            <tr>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    ${match.bga_table_id}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm">
                    ${statusBadge}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${match.progress}%
                </td>
                <td class="px-6 py-4 text-sm text-gray-500">
                    ${playersList}
                </td>
            </tr>
        `;
        
        tbody.append(row);
    });
}

function showError(message) {
    $('#error').show();
    $('#error-message').text(message);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
