"""
Parser for Move Stats import format (semicolon-delimited).
Parses the MoveStats.js bookmarklet output.
"""

from backend.parsers.exceptions import ValidationError, ParseError


def parse_move_stats(raw_text):
    """
    Parse Move Stats export into structured data.
    
    Format: TABLE_ID;GAME_NAME;MOVE_NO;DATETIME_LOCAL;DATETIME_EXCEL;PLAYER_NAME;REMAINING_TIME
    
    Args:
        raw_text (str): Semicolon-delimited text from MoveStats bookmarklet
        
    Returns:
        dict: Dictionary with structure:
            {
                'table_id': int,
                'game_name': str,
                'moves': [{
                    'move_no': str,
                    'datetime_local': str,
                    'datetime_excel': str,
                    'player_name': str,
                    'remaining_time': str
                }]
            }
            
    Raises:
        ValidationError: If input is empty or invalid
        ParseError: If row format is incorrect
    """
    if not raw_text or not raw_text.strip():
        raise ValidationError("Input text is empty")
    
    lines = raw_text.strip().split('\n')
    
    table_id = None
    game_name = None
    moves = []
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
        
        columns = line.split(';')
        
        if len(columns) != 7:
            raise ParseError(f"Line {line_num}: Expected 7 columns, got {len(columns)}")
        
        # Parse table ID
        try:
            current_table_id = int(columns[0].strip())
        except ValueError:
            raise ParseError(f"Line {line_num}: Table ID must be numeric, got '{columns[0]}'")
        
        # Verify all rows have the same table ID
        if table_id is None:
            table_id = current_table_id
        elif table_id != current_table_id:
            raise ParseError(f"Line {line_num}: Mixed table IDs found ({table_id} and {current_table_id})")
        
        # Parse game name
        current_game_name = columns[1].strip()
        if game_name is None:
            game_name = current_game_name
        elif game_name != current_game_name:
            raise ParseError(f"Line {line_num}: Mixed game names found ('{game_name}' and '{current_game_name}')")
        
        # Parse move number (can be "null")
        move_no = columns[2].strip()
        
        # Parse datetimes
        datetime_local = columns[3].strip()
        datetime_excel = columns[4].strip()
        
        # Parse player name
        player_name = columns[5].strip()
        if not player_name:
            raise ParseError(f"Line {line_num}: Player name is empty")
        
        # Parse remaining time (can be empty)
        remaining_time = columns[6].strip()
        
        moves.append({
            'move_no': move_no,
            'datetime_local': datetime_local,
            'datetime_excel': datetime_excel,
            'player_name': player_name,
            'remaining_time': remaining_time
        })
    
    if not moves:
        raise ValidationError("No valid move data found")
    
    if table_id is None or game_name is None:
        raise ValidationError("Could not determine table ID or game name")
    
    return {
        'table_id': table_id,
        'game_name': game_name,
        'moves': moves
    }
