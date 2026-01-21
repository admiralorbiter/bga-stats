$(document).ready(function() {
    const $statusIndicator = $('#status-indicator');
    const $statusText = $('#status-text');
    const $loginBtn = $('#login-btn');
    const $loginBtnText = $('#login-btn-text');
    const $loginSpinner = $('#login-spinner');
    const $validateBtn = $('#validate-btn');
    const $logoutBtn = $('#logout-btn');
    const $pullSection = $('#pull-section');
    const $resultsArea = $('#results-area');
    const $successMessage = $('#success-message');
    const $errorMessage = $('#error-message');
    const $successDetails = $('#success-details');
    const $errorDetails = $('#error-details');
    
    const $pullPlayerBtn = $('#pull-player-stats-btn');
    const $pullPlayerText = $('#pull-player-text');
    const $pullPlayerSpinner = $('#pull-player-spinner');
    const $playerIds = $('#player-ids');
    
    const $progressSection = $('#progress-section');
    const $progressBar = $('#progress-bar');
    const $progressText = $('#progress-text');
    const $progressPercent = $('#progress-percent');
    const $progressDetail = $('#progress-detail');
    
    const $playerIdDisplay = $('#player-id-display');
    const $playerIdValue = $('#player-id-value');
    const $copyPlayerIdBtn = $('#copy-player-id-btn');
    const $useMyIdBtn = $('#use-my-id-btn');
    
    const $pullGameListBtn = $('#pull-game-list-btn');
    const $pullGameListText = $('#pull-game-list-text');
    const $pullGameListSpinner = $('#pull-game-list-spinner');
    const $gameListProgress = $('#game-list-progress');
    
    const $pullTournamentStatsBtn = $('#pull-tournament-stats-btn');
    const $pullTournamentStatsText = $('#pull-tournament-stats-text');
    const $pullTournamentStatsSpinner = $('#pull-tournament-stats-spinner');
    const $tournamentStatsProgress = $('#tournament-stats-progress');
    
    let currentPlayerId = null;

    // Check session status on load
    checkSessionStatus();

    // Login button
    $loginBtn.on('click', function() {
        initiateLogin();
    });

    // Validate button
    $validateBtn.on('click', function() {
        validateSession();
    });

    // Logout button
    $logoutBtn.on('click', function() {
        clearSession();
    });

    // Pull player stats button
    $pullPlayerBtn.on('click', function() {
        pullPlayerStats();
    });

    // Copy player ID button
    $copyPlayerIdBtn.on('click', function() {
        if (currentPlayerId) {
            navigator.clipboard.writeText(currentPlayerId).then(function() {
                $copyPlayerIdBtn.text('✓ Copied!');
                setTimeout(function() {
                    $copyPlayerIdBtn.text('📋 Copy');
                }, 2000);
            });
        }
    });

    // Use My ID button
    $useMyIdBtn.on('click', function() {
        if (currentPlayerId) {
            $playerIds.val(currentPlayerId);
            $playerIds.focus();
        }
    });

    // Pull game list button
    $pullGameListBtn.on('click', function() {
        pullGameList();
    });

    // Pull tournament stats button
    $pullTournamentStatsBtn.on('click', function() {
        handlePullTournamentStats();
    });

    function checkSessionStatus() {
        $.ajax({
            url: '/api/sync/session-info',
            method: 'GET',
            success: function(response) {
                if (response.success && response.has_session) {
                    // Store player ID if available
                    if (response.info && response.info.player_id) {
                        currentPlayerId = response.info.player_id;
                        displayPlayerId(currentPlayerId);
                    }
                    updateUIForLoggedIn();
                } else {
                    updateUIForLoggedOut();
                }
            },
            error: function(xhr) {
                showError('Failed to check session status');
                updateUIForLoggedOut();
            }
        });
    }

    function initiateLogin() {
        setLoginLoading(true);
        hideMessages();

        $.ajax({
            url: '/api/sync/login',
            method: 'POST',
            contentType: 'application/json',
            success: function(response) {
                setLoginLoading(false);
                if (response.success) {
                    // Store and display player ID if available
                    if (response.player_id) {
                        currentPlayerId = response.player_id;
                        displayPlayerId(currentPlayerId);
                    }
                    showSuccess('Login successful! Session saved.');
                    updateUIForLoggedIn();
                } else {
                    showError(response.message || 'Login failed');
                    updateUIForLoggedOut();
                }
            },
            error: function(xhr) {
                setLoginLoading(false);
                const errorMsg = xhr.responseJSON?.error || 'Login request failed';
                showError(errorMsg);
                updateUIForLoggedOut();
            }
        });
    }

    function validateSession() {
        hideMessages();
        $validateBtn.prop('disabled', true);

        $.ajax({
            url: '/api/sync/validate',
            method: 'POST',
            success: function(response) {
                $validateBtn.prop('disabled', false);
                if (response.valid) {
                    showSuccess('Session is valid and active');
                    updateUIForLoggedIn();
                } else {
                    showError('Session is invalid or expired. Please log in again.');
                    updateUIForLoggedOut();
                }
            },
            error: function(xhr) {
                $validateBtn.prop('disabled', false);
                showError('Failed to validate session');
            }
        });
    }

    function clearSession() {
        hideMessages();
        $logoutBtn.prop('disabled', true);

        $.ajax({
            url: '/api/sync/logout',
            method: 'POST',
            success: function(response) {
                $logoutBtn.prop('disabled', false);
                showSuccess('Session cleared successfully');
                updateUIForLoggedOut();
            },
            error: function(xhr) {
                $logoutBtn.prop('disabled', false);
                showError('Failed to clear session');
            }
        });
    }

    function pullPlayerStats() {
        const ids = $playerIds.val().trim();
        
        if (!ids) {
            showError('Please enter player IDs or group ID');
            return;
        }

        setPullPlayerLoading(true);
        hideMessages();
        showProgress();
        
        // Animate progress bar
        animateProgress();

        $.ajax({
            url: '/api/sync/pull/player-stats',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ ids: ids }),
            success: function(response) {
                setPullPlayerLoading(false);
                completeProgress();
                
                setTimeout(function() {
                    hideProgress();
                    
                    if (response.success) {
                        const results = response.results || {};
                        let msg = `Successfully pulled and imported data!\n`;
                        msg += `Players: ${results.players_created || 0} created, ${results.players_updated || 0} updated\n`;
                        msg += `Games: ${results.games_created || 0} created\n`;
                        msg += `Stats: ${results.game_stats_created || 0} created, ${results.game_stats_updated || 0} updated`;
                        showSuccess(msg);
                        $playerIds.val(''); // Clear input
                    } else {
                        showError(response.error || 'Pull failed');
                    }
                }, 500);
            },
            error: function(xhr) {
                setPullPlayerLoading(false);
                hideProgress();
                const errorMsg = xhr.responseJSON?.error || 'Pull request failed';
                showError(errorMsg);
            }
        });
    }

    function updateUIForLoggedIn() {
        $statusIndicator.removeClass('bg-gray-400 bg-red-500').addClass('bg-green-500');
        $statusText.text('Logged in to BGA');
        $loginBtn.hide();
        $validateBtn.removeClass('hidden').show();
        $logoutBtn.removeClass('hidden').show();
        $pullSection.removeClass('hidden').show();
    }

    function updateUIForLoggedOut() {
        $statusIndicator.removeClass('bg-green-500 bg-red-500').addClass('bg-gray-400');
        $statusText.text('Not logged in');
        $loginBtn.show();
        $validateBtn.hide();
        $logoutBtn.hide();
        $pullSection.hide();
        $playerIdDisplay.hide();
        $useMyIdBtn.hide();
        currentPlayerId = null;
    }
    
    function displayPlayerId(playerId) {
        if (playerId) {
            $playerIdValue.text(playerId);
            $playerIdDisplay.removeClass('hidden').show();
            $useMyIdBtn.removeClass('hidden').show();
        } else {
            $playerIdDisplay.hide();
            $useMyIdBtn.hide();
        }
    }

    function setLoginLoading(isLoading) {
        if (isLoading) {
            $loginBtn.prop('disabled', true);
            $loginBtnText.text('Opening browser...');
            $loginSpinner.removeClass('hidden');
        } else {
            $loginBtn.prop('disabled', false);
            $loginBtnText.text('Login to BGA');
            $loginSpinner.addClass('hidden');
        }
    }

    function setPullPlayerLoading(isLoading) {
        if (isLoading) {
            $pullPlayerBtn.prop('disabled', true);
            $pullPlayerText.text('Pulling data...');
            $pullPlayerSpinner.removeClass('hidden');
        } else {
            $pullPlayerBtn.prop('disabled', false);
            $pullPlayerText.text('Pull Player Stats');
            $pullPlayerSpinner.addClass('hidden');
        }
    }

    function hideMessages() {
        $resultsArea.addClass('hidden');
        $successMessage.addClass('hidden');
        $errorMessage.addClass('hidden');
    }

    function showSuccess(message) {
        $successDetails.text(message);
        $resultsArea.removeClass('hidden');
        $successMessage.removeClass('hidden');
        $errorMessage.addClass('hidden');
        $resultsArea[0].scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    function showError(message) {
        $errorDetails.text(message);
        $resultsArea.removeClass('hidden');
        $errorMessage.removeClass('hidden');
        $successMessage.addClass('hidden');
        $resultsArea[0].scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    
    function showProgress() {
        $progressSection.removeClass('hidden');
        $progressBar.css('width', '0%');
        $progressPercent.text('0%');
        $progressText.text('Pulling player data...');
        $progressDetail.text('Connecting to BGA...');
    }
    
    function hideProgress() {
        $progressSection.addClass('hidden');
    }
    
    function animateProgress() {
        let progress = 0;
        const messages = [
            'Connecting to BGA...',
            'Fetching player profiles...',
            'Extracting statistics...',
            'Processing game data...',
            'Importing to database...'
        ];
        let messageIndex = 0;
        
        const interval = setInterval(function() {
            progress += Math.random() * 15 + 5; // Random increment between 5-20%
            
            if (progress >= 90) {
                progress = 90; // Cap at 90% until actual completion
                clearInterval(interval);
            }
            
            $progressBar.css('width', progress + '%');
            $progressPercent.text(Math.round(progress) + '%');
            
            // Update message
            if (messageIndex < messages.length - 1 && progress > (messageIndex + 1) * 20) {
                messageIndex++;
                $progressDetail.text(messages[messageIndex]);
            }
        }, 400);
        
        // Store interval ID so we can clear it if needed
        $progressSection.data('interval', interval);
    }
    
    function completeProgress() {
        // Clear any running animation
        const interval = $progressSection.data('interval');
        if (interval) {
            clearInterval(interval);
        }
        
        // Complete the progress bar
        $progressBar.css('width', '100%');
        $progressPercent.text('100%');
        $progressText.text('Complete!');
        $progressDetail.text('Data imported successfully');
    }

    function pullGameList() {
        setPullGameListLoading(true);
        hideMessages();
        $gameListProgress.show();

        $.ajax({
            url: '/api/sync/pull/game-list',
            method: 'POST',
            success: function(response) {
                setPullGameListLoading(false);
                $gameListProgress.hide();
                
                if (response.success) {
                    const count = response.games_imported || 0;
                    const updated = response.games_updated || 0;
                    showSuccess(`Successfully imported ${count} games (${updated} updated)`);
                    
                    // Optionally redirect to /games after short delay
                    setTimeout(function() {
                        window.location.href = '/games';
                    }, 2000);
                } else {
                    showError(response.error || 'Failed to import games');
                }
            },
            error: function(xhr) {
                setPullGameListLoading(false);
                $gameListProgress.hide();
                
                const errorMsg = xhr.responseJSON?.error || 'Failed to pull game list';
                showError(errorMsg);
            }
        });
    }

    function setPullGameListLoading(isLoading) {
        $pullGameListBtn.prop('disabled', isLoading);
        
        if (isLoading) {
            $pullGameListText.text('Pulling...');
            $pullGameListSpinner.removeClass('hidden');
        } else {
            $pullGameListText.text('🎲 Pull Game List');
            $pullGameListSpinner.addClass('hidden');
        }
    }

    function handlePullTournamentStats() {
        setPullTournamentStatsLoading(true);
        showProgress('Pulling tournament statistics...');
        
        $.ajax({
            url: '/api/sync/pull/tournament-stats',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({}),
            success: function(response) {
                setPullTournamentStatsLoading(false);
                completeProgress();
                
                setTimeout(function() {
                    hideProgress();
                    
                    if (response.success) {
                        const results = response.results || {};
                        
                        if (results.tournaments_processed === 0) {
                            showSuccess('No tournaments found. Try participating in a tournament first!');
                        } else {
                            let msg = `Successfully pulled and imported tournament data!\n`;
                            msg += `Tournaments: ${results.tournaments_created || 0} created, ${results.tournaments_updated || 0} updated\n`;
                            msg += `Matches: ${results.matches_created || 0} created\n`;
                            msg += `Players: ${results.match_players_created || 0} player records`;
                            showSuccess(msg);
                        }
                    } else {
                        showError(response.error || 'Pull failed');
                    }
                }, 500);
            },
            error: function(xhr) {
                setPullTournamentStatsLoading(false);
                hideProgress();
                const errorMsg = xhr.responseJSON?.error || 'Pull request failed';
                showError(errorMsg);
            }
        });
    }

    function setPullTournamentStatsLoading(isLoading) {
        if (isLoading) {
            $pullTournamentStatsBtn.prop('disabled', true);
            $pullTournamentStatsText.text('Pulling...');
            $pullTournamentStatsSpinner.removeClass('hidden');
            $tournamentStatsProgress.removeClass('hidden').show();
        } else {
            $pullTournamentStatsBtn.prop('disabled', false);
            $pullTournamentStatsText.html('🏆 Pull Tournament Stats');
            $pullTournamentStatsSpinner.addClass('hidden');
            $tournamentStatsProgress.hide();
        }
    }
});
