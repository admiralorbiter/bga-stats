"""
Parser for Player Stats import format (TSV).
Handles XP rows, Recent games rows, and per-game statistics.
"""

from backend.parsers.exceptions import ValidationError, ParseError


def parse_player_stats(raw_text):
    """
    Parse Player Stats TSV export into structured data.
    
    Args:
        raw_text (str): TSV text from PlayerStats bookmarklet
        
    Returns:
        list: List of player dictionaries with structure:
            [{
                'name': str,
                'bga_player_id': int,
                'xp': int,
                'karma': int,
                'matches_total': int,
                'wins_total': int,
                'abandoned': int,
                'timeout': int,
                'recent_matches': int,
                'last_seen_days': int,
                'game_stats': [{
                    'game_name': str,
                    'elo': str,
                    'rank': str,
                    'played': int,
                    'won': int
                }]
            }]
            
    Raises:
        ValidationError: If input is empty or invalid
        ParseError: If row format is incorrect
    """
    if not raw_text or not raw_text.strip():
        raise ValidationError("Input text is empty")
    
    lines = raw_text.strip().split('\n')
    players = {}  # Key: player_name, Value: player dict
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
            
        columns = line.split('\t')
        
        if len(columns) < 7:
            raise ParseError(f"Line {line_num}: Expected at least 7 columns, got {len(columns)}")
        
        player_name = columns[0].strip()
        if not player_name:
            raise ParseError(f"Line {line_num}: Player name is empty")
        
        # Extract and validate player ID
        try:
            bga_player_id = int(columns[1].strip())
        except ValueError:
            raise ParseError(f"Line {line_num}: Player ID must be numeric, got '{columns[1]}'")
        
        # Initialize player if not exists (keyed by bga_player_id for uniqueness)
        if bga_player_id not in players:
            players[bga_player_id] = {
                'name': player_name,
                'bga_player_id': bga_player_id,
                'xp': None,
                'karma': None,
                'matches_total': None,
                'wins_total': None,
                'abandoned': None,
                'timeout': None,
                'recent_matches': None,
                'last_seen_days': None,
                'game_stats': []
            }
        
        row_type = columns[2].strip()
        
        try:
            if row_type == "XP":
                _parse_xp_row(players[bga_player_id], columns, line_num)
            elif row_type == "Recent games":
                _parse_recent_games_row(players[bga_player_id], columns, line_num)
            else:
                # It's a per-game row (game name in column 3)
                _parse_game_row(players[bga_player_id], columns, line_num)
        except (ValueError, IndexError) as e:
            raise ParseError(f"Line {line_num}: {str(e)}")
    
    # Validate all players have required data
    for bga_player_id, player_data in players.items():
        if player_data['xp'] is None:
            raise ValidationError(f"Player '{player_data['name']}' (ID: {bga_player_id}) missing XP row")
        if player_data['abandoned'] is None:
            raise ValidationError(f"Player '{player_data['name']}' (ID: {bga_player_id}) missing Recent games row")
    
    return list(players.values())


def _parse_xp_row(player_dict, columns, line_num):
    """
    Parse XP row and update player dict.
    Format: PlayerName \t PlayerID \t XP \t xp_value \t karma \t total_matches \t total_wins
    """
    if len(columns) != 7:
        raise ValueError(f"XP row must have exactly 7 columns")
    
    try:
        player_dict['xp'] = int(columns[3])
        player_dict['karma'] = int(columns[4])
        player_dict['matches_total'] = int(columns[5])
        player_dict['wins_total'] = int(columns[6])
    except ValueError as e:
        raise ValueError(f"XP row has invalid numeric value: {e}")


def _parse_recent_games_row(player_dict, columns, line_num):
    """
    Parse Recent games row and update player dict.
    Format: PlayerName \t PlayerID \t Recent games \t abandoned \t timeout \t recent_matches \t last_seen_days
    """
    if len(columns) != 7:
        raise ValueError(f"Recent games row must have exactly 7 columns")
    
    try:
        player_dict['abandoned'] = int(columns[3])
        player_dict['timeout'] = int(columns[4])
        player_dict['recent_matches'] = int(columns[5])
        player_dict['last_seen_days'] = int(columns[6])
    except ValueError as e:
        raise ValueError(f"Recent games row has invalid numeric value: {e}")


def _parse_game_row(player_dict, columns, line_num):
    """
    Parse per-game statistics row.
    Format: PlayerName \t PlayerID \t GameName \t elo \t rank \t played \t won
    """
    if len(columns) != 7:
        raise ValueError(f"Game row must have exactly 7 columns")
    
    game_name = columns[2].strip()
    if not game_name:
        raise ValueError("Game name is empty")
    
    elo = columns[3].strip()
    rank = columns[4].strip()
    
    # ELO can be "N/A" or numeric, store as string
    # Rank can be empty or numeric, store as string
    
    try:
        played = int(columns[5])
        won = int(columns[6])
    except ValueError as e:
        raise ValueError(f"Game row has invalid played/won value: {e}")
    
    player_dict['game_stats'].append({
        'game_name': game_name,
        'elo': elo if elo else None,
        'rank': rank if rank else None,
        'played': played,
        'won': won
    })
