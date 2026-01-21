// Load tournaments on page load
$(document).ready(function() {
    loadTournaments();
});

function loadTournaments() {
    $('#loading').show();
    $('#error').hide();
    $('#empty-state').hide();
    $('#tournaments-grid').hide();
    
    $.ajax({
        url: '/api/tournaments',
        method: 'GET',
        success: function(response) {
            $('#loading').hide();
            
            if (response.success && response.tournaments.length > 0) {
                renderTournaments(response.tournaments);
                $('#tournaments-grid').show();
            } else {
                $('#empty-state').show();
            }
        },
        error: function(xhr) {
            $('#loading').hide();
            $('#error').show();
            
            const errorMsg = xhr.responseJSON && xhr.responseJSON.error 
                ? xhr.responseJSON.error 
                : 'Failed to load tournaments';
            $('#error-message').text(errorMsg);
        }
    });
}

function renderTournaments(tournaments) {
    const container = $('#tournaments-container');
    container.empty();
    
    tournaments.forEach(function(tournament) {
        const timeoutBadge = tournament.timeout_matches > 0 
            ? `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                ${tournament.timeout_matches} timeouts
               </span>`
            : '';
        
        const card = `
            <div class="bg-white overflow-hidden shadow rounded-lg border border-gray-200 hover:shadow-lg transition-shadow duration-200">
                <div class="px-4 py-5 sm:p-6">
                    <h3 class="text-lg font-medium text-gray-900 mb-2">
                        ${escapeHtml(tournament.name)}
                    </h3>
                    <p class="text-sm text-gray-600 mb-3">
                        ${escapeHtml(tournament.game_name)}
                    </p>
                    
                    <div class="space-y-2 text-sm">
                        <div class="flex justify-between">
                            <span class="text-gray-500">Dates:</span>
                            <span class="text-gray-900">${escapeHtml(tournament.start_time || 'N/A')}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-500">Rounds:</span>
                            <span class="text-gray-900">${tournament.rounds}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-500">Matches:</span>
                            <span class="text-gray-900">${tournament.total_matches}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-500">Players:</span>
                            <span class="text-gray-900">${tournament.player_count}</span>
                        </div>
                        ${timeoutBadge ? `<div class="mt-2">${timeoutBadge}</div>` : ''}
                    </div>
                    
                    <div class="mt-4">
                        <a href="/tournaments/${tournament.id}" 
                           class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                            View Details
                        </a>
                    </div>
                </div>
            </div>
        `;
        
        container.append(card);
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
