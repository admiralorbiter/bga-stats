"""
Test script for Player Stats parser.
Run: python backend/test_parser.py
"""

import sys
from backend.parsers.player_stats_parser import parse_player_stats
from backend.parsers.exceptions import ValidationError, ParseError


def test_single_player():
    """Test parsing single player with multiple games."""
    print("Test 1: Single player with multiple games...")
    
    sample = """JohnDoe\t12345\tXP\t45000\t95\t1250\t650
JohnDoe\t12345\tRecent games\t2\t1\t45\t3
JohnDoe\t12345\tTicket to Ride\t1500\t42\t150\t75
JohnDoe\t12345\tCarcassonne\t1650\t25\t200\t110"""
    
    result = parse_player_stats(sample)
    
    assert len(result) == 1, f"Expected 1 player, got {len(result)}"
    
    player = result[0]
    assert player['name'] == 'JohnDoe'
    assert player['bga_player_id'] == 12345
    assert player['xp'] == 45000
    assert player['karma'] == 95
    assert player['matches_total'] == 1250
    assert player['wins_total'] == 650
    assert player['abandoned'] == 2
    assert player['timeout'] == 1
    assert player['recent_matches'] == 45
    assert player['last_seen_days'] == 3
    assert len(player['game_stats']) == 2
    
    game1 = player['game_stats'][0]
    assert game1['game_name'] == 'Ticket to Ride'
    assert game1['elo'] == '1500'
    assert game1['rank'] == '42'
    assert game1['played'] == 150
    assert game1['won'] == 75
    
    print("  [OK] All assertions passed\n")


def test_multiple_players():
    """Test parsing multiple players."""
    print("Test 2: Multiple players...")
    
    sample = """Alice\t98765\tXP\t30000\t98\t800\t450
Alice\t98765\tRecent games\t0\t0\t25\t1
Alice\t98765\tChess\t1800\t5\t300\t180
Bob\t54321\tXP\t20000\t85\t500\t200
Bob\t54321\tRecent games\t1\t2\t15\t7
Bob\t54321\tPoker\tN/A\t\t100\t30"""
    
    result = parse_player_stats(sample)
    
    assert len(result) == 2, f"Expected 2 players, got {len(result)}"
    
    # Find Alice
    alice = next(p for p in result if p['name'] == 'Alice')
    assert alice['bga_player_id'] == 98765
    assert alice['xp'] == 30000
    assert len(alice['game_stats']) == 1
    
    # Find Bob
    bob = next(p for p in result if p['name'] == 'Bob')
    assert bob['bga_player_id'] == 54321
    assert bob['xp'] == 20000
    assert len(bob['game_stats']) == 1
    
    # Bob has "N/A" ELO and empty rank
    bob_game = bob['game_stats'][0]
    assert bob_game['elo'] == 'N/A'
    assert bob_game['rank'] is None
    
    print("  [OK] All assertions passed\n")


def test_empty_rank_and_na_elo():
    """Test handling of empty rank and N/A ELO."""
    print("Test 3: Empty rank and N/A ELO...")
    
    sample = """TestPlayer\t11111\tXP\t10000\t90\t100\t50
TestPlayer\t11111\tRecent games\t0\t0\t10\t0
TestPlayer\t11111\tNewGame\tN/A\t\t50\t20"""
    
    result = parse_player_stats(sample)
    player = result[0]
    game = player['game_stats'][0]
    
    assert game['elo'] == 'N/A'
    assert game['rank'] is None
    assert game['played'] == 50
    assert game['won'] == 20
    
    print("  [OK] All assertions passed\n")


def test_empty_input():
    """Test error handling for empty input."""
    print("Test 4: Empty input validation...")
    
    try:
        parse_player_stats("")
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "empty" in str(e).lower()
        print(f"  [OK] Raised ValidationError: {e}\n")


def test_missing_xp_row():
    """Test error for missing XP row."""
    print("Test 5: Missing XP row validation...")
    
    sample = """Player1\t99999\tRecent games\t0\t0\t10\t0
Player1\t99999\tChess\t1500\t10\t100\t50"""
    
    try:
        parse_player_stats(sample)
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "XP row" in str(e)
        print(f"  [OK] Raised ValidationError: {e}\n")


def test_invalid_column_count():
    """Test error for invalid column count."""
    print("Test 6: Invalid column count...")
    
    sample = """Player1\tXP\t10000"""
    
    try:
        parse_player_stats(sample)
        assert False, "Should have raised ParseError"
    except ParseError as e:
        assert "7 columns" in str(e)
        print(f"  [OK] Raised ParseError: {e}\n")


def test_invalid_numeric_value():
    """Test error for invalid numeric values."""
    print("Test 7: Invalid numeric values...")
    
    sample = """Player1\t88888\tXP\tNotANumber\t95\t100\t50
Player1\t88888\tRecent games\t0\t0\t10\t0"""
    
    try:
        parse_player_stats(sample)
        assert False, "Should have raised ParseError"
    except ParseError as e:
        assert "invalid" in str(e).lower()
        print(f"  [OK] Raised ParseError: {e}\n")


def test_invalid_player_id():
    """Test error for non-numeric player ID."""
    print("Test 8: Invalid player ID (non-numeric)...")
    
    sample = """Player1\tNotANumber\tXP\t10000\t95\t100\t50
Player1\tNotANumber\tRecent games\t0\t0\t10\t0"""
    
    try:
        parse_player_stats(sample)
        assert False, "Should have raised ParseError"
    except ParseError as e:
        assert "Player ID must be numeric" in str(e)
        print(f"  [OK] Raised ParseError: {e}\n")


def run_all_tests():
    """Run all parser tests."""
    print("=" * 60)
    print("Testing Player Stats Parser (7-column format)")
    print("=" * 60)
    print()
    
    try:
        test_single_player()
        test_multiple_players()
        test_empty_rank_and_na_elo()
        test_empty_input()
        test_missing_xp_row()
        test_invalid_column_count()
        test_invalid_numeric_value()
        test_invalid_player_id()
        
        print("=" * 60)
        print("All tests passed! (8/8)")
        print("=" * 60)
        return 0
    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
