"""
Parser for Tournament Stats import format (TSV).
Parses the TournamentStats.js bookmarklet output.
"""

from backend.parsers.exceptions import ValidationError, ParseError


def parse_tournament_stats(raw_text):
    """
    Parse Tournament Stats TSV export into structured data.
    
    Format consists of:
    - Summary row: TOURNAMENT_ID\tTOURNAMENT_NAME\t\tGAME_NAME\tSTART_TIME\tEND_TIME\tROUNDS\tROUND_LIMIT\tTOTAL_MATCHES\tTIMEOUT_MATCHES\tPLAYER_COUNT
    - Match rows: TOURNAMENT_ID\tTABLE_ID\tIS_TIMEOUT\tPROGRESS\tPLAYER1_NAME\tPLAYER1_TIME\tPLAYER1_POINTS\t...
    
    Args:
        raw_text (str): TSV text from TournamentStats bookmarklet
        
    Returns:
        list: List of tournament dictionaries with structure:
            [{
                'tournament_id': int,
                'name': str,
                'game_name': str,
                'start_time': str,
                'end_time': str,
                'rounds': int,
                'round_limit': int,
                'total_matches': int,
                'timeout_matches': int,
                'player_count': int,
                'matches': [{
                    'table_id': int,
                    'is_timeout': bool,
                    'progress': int,
                    'players': [{
                        'name': str,
                        'remaining_time_seconds': int,
                        'points': int
                    }]
                }]
            }]
            
    Raises:
        ValidationError: If input is empty or invalid
        ParseError: If row format is incorrect
    """
    if not raw_text or not raw_text.strip():
        raise ValidationError("Input text is empty")
    
    lines = raw_text.strip().split('\n')
    tournaments = {}  # Key: tournament_id
    current_tournament_id = None
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
        
        columns = line.split('\t')
        
        if len(columns) < 4:
            raise ParseError(f"Line {line_num}: Expected at least 4 columns, got {len(columns)}")
        
        # Parse tournament ID
        try:
            tournament_id = int(columns[0].strip())
        except ValueError:
            raise ParseError(f"Line {line_num}: Tournament ID must be numeric, got '{columns[0]}'")
        
        # Detect row type by column count
        if len(columns) == 11:
            # Summary row (has empty column at index 2)
            _parse_tournament_summary(tournaments, columns, line_num)
            current_tournament_id = tournament_id
        else:
            # Match row (variable length based on player count)
            if tournament_id not in tournaments:
                raise ParseError(f"Line {line_num}: Match row found before tournament summary")
            
            _parse_tournament_match(tournaments[tournament_id], columns, line_num)
    
    if not tournaments:
        raise ValidationError("No valid tournament data found")
    
    return list(tournaments.values())


def _parse_tournament_summary(tournaments, columns, line_num):
    """Parse tournament summary row."""
    try:
        tournament_id = int(columns[0])
        name = columns[1].strip()
        # columns[2] is empty (double tab in format)
        game_name = columns[3].strip()
        start_time = columns[4].strip()
        end_time = columns[5].strip()
        rounds = int(columns[6])
        round_limit = int(columns[7])
        total_matches = int(columns[8])
        timeout_matches = int(columns[9])
        player_count = int(columns[10])
        
        tournaments[tournament_id] = {
            'tournament_id': tournament_id,
            'name': name,
            'game_name': game_name,
            'start_time': start_time,
            'end_time': end_time,
            'rounds': rounds,
            'round_limit': round_limit,
            'total_matches': total_matches,
            'timeout_matches': timeout_matches,
            'player_count': player_count,
            'matches': []
        }
    except (ValueError, IndexError) as e:
        raise ParseError(f"Line {line_num}: Failed to parse tournament summary: {e}")


def _parse_tournament_match(tournament, columns, line_num):
    """Parse tournament match row."""
    try:
        # columns[0] is tournament_id (already validated)
        table_id = int(columns[1])
        is_timeout = columns[2].strip() == '1'
        progress = int(columns[3])
        
        # Remaining columns are player data (groups of 3: name, time, points)
        player_data = columns[4:]
        
        if len(player_data) % 3 != 0:
            raise ParseError(f"Line {line_num}: Player data columns must be multiple of 3")
        
        players = []
        for i in range(0, len(player_data), 3):
            player_name = player_data[i].strip()
            remaining_time = int(player_data[i + 1])
            points = int(player_data[i + 2])
            
            players.append({
                'name': player_name,
                'remaining_time_seconds': remaining_time,
                'points': points
            })
        
        tournament['matches'].append({
            'table_id': table_id,
            'is_timeout': is_timeout,
            'progress': progress,
            'players': players
        })
        
    except (ValueError, IndexError) as e:
        raise ParseError(f"Line {line_num}: Failed to parse match row: {e}")
