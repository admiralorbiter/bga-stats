// Sample data for testing
const SAMPLE_DATA = `TestPlayer\t99999\tXP\t35000\t97\t1000\t600
TestPlayer\t99999\tRecent games\t2\t1\t40\t4
TestPlayer\t99999\tChess\t1750\t20\t400\t250
TestPlayer\t99999\tCarcassonne\t1650\t30\t300\t180`;

$(document).ready(function() {
    const $form = $('#import-form');
    const $importBtn = $('#import-btn');
    const $btnText = $('#btn-text');
    const $btnSpinner = $('#btn-spinner');
    const $clearBtn = $('#clear-btn');
    const $loadSampleBtn = $('#load-sample');
    const $importData = $('#import-data');
    const $importType = $('#import-type');
    const $messageArea = $('#message-area');
    const $successMessage = $('#success-message');
    const $errorMessage = $('#error-message');
    const $successDetails = $('#success-details');
    const $errorDetails = $('#error-details');
    const $toggleInstructions = $('#toggle-instructions');
    const $instructionsContent = $('#instructions-content');
    const $instructionsIcon = $('#instructions-icon');

    // Load sample data
    $loadSampleBtn.on('click', function() {
        $importData.val(SAMPLE_DATA);
    });

    // Clear form
    $clearBtn.on('click', function() {
        $importData.val('');
        hideMessages();
    });

    // Toggle instructions
    $toggleInstructions.on('click', function() {
        $instructionsContent.toggleClass('hidden');
        $instructionsIcon.toggleClass('rotate-180');
    });

    // Form submission
    $form.on('submit', function(e) {
        e.preventDefault();
        
        const data = $importData.val().trim();
        
        if (!data) {
            showError('Please paste some data to import.');
            return;
        }

        // Prepare request payload
        const payload = {
            data: data
        };
        
        const importType = $importType.val();
        if (importType) {
            payload.type = importType;
        }

        // Show loading state
        setLoading(true);
        hideMessages();

        // Send AJAX request
        $.ajax({
            url: '/api/import',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(payload),
            success: function(response) {
                setLoading(false);
                if (response.success) {
                    showSuccess(response);
                    // Clear textarea on success
                    $importData.val('');
                } else {
                    showError(response.error || 'Import failed');
                }
            },
            error: function(xhr) {
                setLoading(false);
                let errorMsg = 'An error occurred during import.';
                
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMsg = xhr.responseJSON.error;
                } else if (xhr.statusText) {
                    errorMsg = `Error: ${xhr.statusText}`;
                }
                
                showError(errorMsg);
            }
        });
    });

    // Helper functions
    function setLoading(isLoading) {
        if (isLoading) {
            $importBtn.prop('disabled', true);
            $btnText.text('Importing...');
            $btnSpinner.removeClass('hidden');
        } else {
            $importBtn.prop('disabled', false);
            $btnText.text('Import Data');
            $btnSpinner.addClass('hidden');
        }
    }

    function hideMessages() {
        $messageArea.addClass('hidden');
        $successMessage.addClass('hidden');
        $errorMessage.addClass('hidden');
    }

    function showSuccess(response) {
        const results = response.results || {};
        const details = [];
        
        if (results.players_created > 0) {
            details.push(`Created ${results.players_created} new player(s)`);
        }
        if (results.players_updated > 0) {
            details.push(`Updated ${results.players_updated} existing player(s)`);
        }
        if (results.games_created > 0) {
            details.push(`Added ${results.games_created} new game(s)`);
        }
        if (results.game_stats_created > 0) {
            details.push(`Created ${results.game_stats_created} new game stat(s)`);
        }
        if (results.game_stats_updated > 0) {
            details.push(`Updated ${results.game_stats_updated} game stat(s)`);
        }
        
        $successDetails.empty();
        details.forEach(function(detail) {
            $successDetails.append($('<li>').text(detail));
        });
        
        $messageArea.removeClass('hidden');
        $successMessage.removeClass('hidden');
        $errorMessage.addClass('hidden');
        
        // Scroll to message
        $messageArea[0].scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    function showError(errorMsg) {
        $errorDetails.text(errorMsg);
        $messageArea.removeClass('hidden');
        $errorMessage.removeClass('hidden');
        $successMessage.addClass('hidden');
        
        // Scroll to message
        $messageArea[0].scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
});
