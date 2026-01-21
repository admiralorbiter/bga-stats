$(document).ready(function() {
    const $loading = $('#loading');
    const $error = $('#error');
    const $errorMessage = $('#error-message');
    const $matchContent = $('#match-content');
    
    let timelineChart = null;

    // Load match details on page load
    loadMatchDetail(BGA_TABLE_ID);

    function loadMatchDetail(bgaTableId) {
        $loading.show();
        $error.hide();
        $matchContent.hide();

        $.ajax({
            url: `/api/matches/${bgaTableId}`,
            method: 'GET',
            success: function(response) {
                $loading.hide();
                
                if (response.success) {
                    renderMatchDetails(response.match, response.moves, response.statistics);
                    $matchContent.show();
                } else {
                    showError(response.error || 'Failed to load match details');
                }
            },
            error: function(xhr, status, error) {
                $loading.hide();
                showError(xhr.responseJSON?.error || 'Failed to load match details. Please try again.');
            }
        });
    }

    function showError(message) {
        $error.show();
        $errorMessage.text(message);
    }

    function renderMatchDetails(match, moves, statistics) {
        // Render header
        $('#match-title').text(`Match #${match.bga_table_id} - ${match.game_name}`);
        $('#match-game').text(match.game_name);
        
        if (match.imported_at) {
            const importDate = new Date(match.imported_at);
            $('#match-date').text('Imported ' + importDate.toLocaleDateString() + ' at ' + importDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
        }

        // Render statistics cards
        $('#stat-moves').text(statistics.total_moves || 0);
        $('#stat-duration').text(formatDuration(statistics.duration_minutes));
        $('#stat-players').text(statistics.player_count || 0);
        $('#stat-avg-time').text(formatAvgTime(statistics.avg_time_per_move_seconds));

        // Render moves table
        renderMovesTable(moves, statistics.player_names);

        // Render timeline chart
        renderTimelineChart(moves, statistics.player_names);
    }

    function renderMovesTable(moves, playerNames) {
        const $tbody = $('#moves-tbody');
        $tbody.empty();

        moves.forEach(function(move, index) {
            const row = $('<tr>');
            
            // Alternate row colors
            if (index % 2 === 0) {
                row.addClass('bg-white');
            } else {
                row.addClass('bg-gray-50');
            }

            // Highlight rows with low remaining time
            const remainingTime = parseRemainingTime(move.remaining_time);
            if (remainingTime !== null && remainingTime < 300) { // Less than 5 minutes
                row.addClass('bg-yellow-50');
            }

            // Move number
            const moveNoCell = $('<td>')
                .addClass('px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900')
                .text(move.move_no || 'null');

            // Player name
            const playerCell = $('<td>')
                .addClass('px-6 py-4 whitespace-nowrap text-sm text-gray-900')
                .text(move.player_name);

            // DateTime
            const dateTimeCell = $('<td>')
                .addClass('px-6 py-4 whitespace-nowrap text-sm text-gray-500')
                .text(move.datetime_local || 'N/A');

            // Remaining time
            const remainingTimeCell = $('<td>')
                .addClass('px-6 py-4 whitespace-nowrap text-sm text-gray-500')
                .text(move.remaining_time || 'N/A');

            row.append(moveNoCell, playerCell, dateTimeCell, remainingTimeCell);
            $tbody.append(row);
        });
    }

    function renderTimelineChart(moves, playerNames) {
        const canvas = document.getElementById('timeline-chart');
        const ctx = canvas.getContext('2d');

        // Prepare data for chart
        const datasets = [];
        const playerColors = generatePlayerColors(playerNames.length);

        playerNames.forEach(function(playerName, playerIndex) {
            const playerMoves = moves
                .map((move, index) => ({
                    x: index + 1, // Move number as x-axis
                    y: playerIndex + 1, // Player index as y-axis
                    move: move
                }))
                .filter(point => point.move.player_name === playerName);

            datasets.push({
                label: playerName,
                data: playerMoves,
                backgroundColor: playerColors[playerIndex],
                borderColor: playerColors[playerIndex],
                pointRadius: 4,
                pointHoverRadius: 6
            });
        });

        // Destroy existing chart if it exists
        if (timelineChart) {
            timelineChart.destroy();
        }

        // Create new chart
        timelineChart = new Chart(ctx, {
            type: 'scatter',
            data: {
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 2.5,
                plugins: {
                    title: {
                        display: true,
                        text: 'Player Activity Timeline',
                        font: {
                            size: 16
                        }
                    },
                    legend: {
                        display: true,
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const move = context.raw.move;
                                return [
                                    `Player: ${move.player_name}`,
                                    `Move: ${move.move_no || 'null'}`,
                                    `Time: ${move.datetime_local}`,
                                    `Remaining: ${move.remaining_time || 'N/A'}`
                                ];
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'linear',
                        position: 'bottom',
                        title: {
                            display: true,
                            text: 'Move Number'
                        },
                        ticks: {
                            stepSize: 1
                        }
                    },
                    y: {
                        type: 'linear',
                        title: {
                            display: true,
                            text: 'Player'
                        },
                        ticks: {
                            stepSize: 1,
                            callback: function(value, index, values) {
                                // Show player names on y-axis
                                if (value >= 1 && value <= playerNames.length) {
                                    return playerNames[value - 1];
                                }
                                return '';
                            }
                        },
                        min: 0.5,
                        max: playerNames.length + 0.5
                    }
                }
            }
        });
    }

    function generatePlayerColors(count) {
        const colors = [
            'rgba(59, 130, 246, 0.8)',   // Blue
            'rgba(239, 68, 68, 0.8)',    // Red
            'rgba(34, 197, 94, 0.8)',    // Green
            'rgba(251, 146, 60, 0.8)',   // Orange
            'rgba(168, 85, 247, 0.8)',   // Purple
            'rgba(236, 72, 153, 0.8)',   // Pink
            'rgba(14, 165, 233, 0.8)',   // Sky
            'rgba(132, 204, 22, 0.8)',   // Lime
        ];

        // Return enough colors for all players, cycling if needed
        const result = [];
        for (let i = 0; i < count; i++) {
            result.push(colors[i % colors.length]);
        }
        return result;
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

        return hours + ' hr' + (hours !== 1 ? 's' : '') + ' ' + remainingMins + ' min';
    }

    function formatAvgTime(seconds) {
        if (!seconds && seconds !== 0) {
            return 'N/A';
        }

        if (seconds < 60) {
            return Math.round(seconds) + 's';
        }

        const minutes = Math.floor(seconds / 60);
        const remainingSecs = Math.round(seconds % 60);

        if (remainingSecs === 0) {
            return minutes + 'm';
        }

        return minutes + 'm ' + remainingSecs + 's';
    }

    function parseRemainingTime(timeStr) {
        if (!timeStr) {
            return null;
        }

        // Try to parse time string (e.g., "1h 23m 45s" or "23m 45s" or "45s")
        const hours = timeStr.match(/(\d+)h/);
        const minutes = timeStr.match(/(\d+)m/);
        const seconds = timeStr.match(/(\d+)s/);

        let totalSeconds = 0;
        if (hours) totalSeconds += parseInt(hours[1]) * 3600;
        if (minutes) totalSeconds += parseInt(minutes[1]) * 60;
        if (seconds) totalSeconds += parseInt(seconds[1]);

        return totalSeconds || null;
    }
});
