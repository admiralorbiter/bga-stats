"""
Parser for Game List import format (TSV).
Parses the GameList.js bookmarklet output.
"""

from backend.parsers.exceptions import ValidationError, ParseError


def parse_game_list(raw_text):
    """
    Parse Game List TSV export into structured data.
    
    Format: BGA_GAME_ID\tINTERNAL_NAME\tDISPLAY_NAME\tSTATUS\tPREMIUM_FLAG
    
    Args:
        raw_text (str): TSV text from GameList bookmarklet
        
    Returns:
        list: List of game dictionaries with structure:
            [{
                'bga_game_id': int,
                'name': str,
                'display_name': str,
                'status': str,
                'premium': bool
            }]
            
    Raises:
        ValidationError: If input is empty or invalid
        ParseError: If row format is incorrect
    """
    if not raw_text or not raw_text.strip():
        raise ValidationError("Input text is empty")
    
    lines = raw_text.strip().split('\n')
    games = []
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
        
        columns = line.split('\t')
        
        if len(columns) != 5:
            raise ParseError(f"Line {line_num}: Expected 5 columns, got {len(columns)}")
        
        # Parse columns
        try:
            bga_game_id = int(columns[0].strip())
        except ValueError:
            raise ParseError(f"Line {line_num}: BGA game ID must be numeric, got '{columns[0]}'")
        
        name = columns[1].strip()
        display_name = columns[2].strip()
        status = columns[3].strip()
        
        # Validate status
        if status not in ['alpha', 'beta', 'published']:
            raise ParseError(f"Line {line_num}: Status must be alpha, beta, or published, got '{status}'")
        
        # Parse premium flag
        premium_str = columns[4].strip()
        if premium_str not in ['0', '1']:
            raise ParseError(f"Line {line_num}: Premium flag must be 0 or 1, got '{premium_str}'")
        
        premium = premium_str == '1'
        
        games.append({
            'bga_game_id': bga_game_id,
            'name': name,
            'display_name': display_name,
            'status': status,
            'premium': premium
        })
    
    if not games:
        raise ValidationError("No valid game data found")
    
    return games
