"""
Integration tests for import service.
Tests the full import pipeline: parse -> import -> database storage.
Run: python backend/test_import.py
"""

import sys
import os
from backend.services.import_service import import_data, detect_import_type
from backend.db import get_session
from backend.models import Player, Game, PlayerGameStat


def clear_test_data():
    """Clear all data from test database."""
    session = get_session()
    try:
        session.query(PlayerGameStat).delete()
        session.query(Player).delete()
        session.query(Game).delete()
        session.commit()
        print("  Test database cleared")
    except Exception as e:
        session.rollback()
        print(f"  [ERROR] Failed to clear test data: {e}")
        raise
    finally:
        session.close()


def test_detect_import_type():
    """Test import type auto-detection."""
    print("Test 1: Detect import type...")
    
    # Test Player Stats format
    sample = "Player\t12345\tXP\t10000\t95\t100\t50\nPlayer\t12345\tRecent games\t0\t0\t10\t0"
    detected = detect_import_type(sample)
    assert detected == 'player_stats', f"Expected 'player_stats', got '{detected}'"
    
    # Test empty input
    detected = detect_import_type("")
    assert detected == 'unknown', f"Expected 'unknown', got '{detected}'"
    
    # Test unrecognized format
    detected = detect_import_type("random text that doesn't match")
    assert detected == 'unknown', f"Expected 'unknown', got '{detected}'"
    
    print("  [OK] All detection tests passed\n")


def test_import_single_player():
    """Test importing a single player with multiple games."""
    print("Test 2: Import single player...")
    
    clear_test_data()
    
    sample = """TestPlayer\t99999\tXP\t50000\t100\t2000\t1000
TestPlayer\t99999\tRecent games\t3\t2\t50\t5
TestPlayer\t99999\tChess\t1900\t10\t500\t300
TestPlayer\t99999\tPoker\t1400\t50\t300\t150"""
    
    result = import_data(sample, 'player_stats')
    
    assert result['success'], f"Import failed: {result.get('error')}"
    assert result['import_type'] == 'player_stats'
    assert result['results']['players_created'] == 1
    assert result['results']['games_created'] == 2
    assert result['results']['game_stats_created'] == 2
    
    # Verify database state
    session = get_session()
    try:
        player = session.query(Player).filter_by(bga_player_id=99999).first()
        assert player is not None, "Player not found in database"
        assert player.name == 'TestPlayer'
        assert player.xp == 50000
        assert player.karma == 100
        assert player.matches_total == 2000
        assert player.wins_total == 1000
        assert player.abandoned == 3
        assert player.timeout == 2
        assert player.recent_matches == 50
        assert player.last_seen_days == 5
        
        # Check games
        games = session.query(Game).all()
        assert len(games) == 2
        game_names = [g.name for g in games]
        assert 'Chess' in game_names
        assert 'Poker' in game_names
        
        # Check stats
        stats = session.query(PlayerGameStat).filter_by(player_id=player.id).all()
        assert len(stats) == 2
        
        chess_stat = next((s for s in stats if s.game.name == 'Chess'), None)
        assert chess_stat is not None
        assert chess_stat.elo == '1900'
        assert chess_stat.rank == '10'
        assert chess_stat.played == 500
        assert chess_stat.won == 300
        
        print("  [OK] Import successful and data verified in database\n")
    finally:
        session.close()


def test_import_multiple_players():
    """Test importing multiple players."""
    print("Test 3: Import multiple players...")
    
    clear_test_data()
    
    sample = """Alice\t11111\tXP\t30000\t98\t800\t450
Alice\t11111\tRecent games\t0\t0\t25\t1
Alice\t11111\tChess\t1800\t5\t300\t180
Bob\t22222\tXP\t20000\t85\t500\t200
Bob\t22222\tRecent games\t1\t2\t15\t7
Bob\t22222\tPoker\tN/A\t\t100\t30"""
    
    result = import_data(sample, 'player_stats')
    
    assert result['success'], f"Import failed: {result.get('error')}"
    assert result['results']['players_created'] == 2
    assert result['results']['games_created'] == 2  # Chess and Poker
    assert result['results']['game_stats_created'] == 2
    
    # Verify database state
    session = get_session()
    try:
        alice = session.query(Player).filter_by(bga_player_id=11111).first()
        bob = session.query(Player).filter_by(bga_player_id=22222).first()
        
        assert alice is not None and bob is not None
        assert alice.name == 'Alice'
        assert bob.name == 'Bob'
        assert alice.xp == 30000
        assert bob.xp == 20000
        
        print("  [OK] Multiple players imported successfully\n")
    finally:
        session.close()


def test_upsert_behavior():
    """Test that re-importing updates existing records (no duplicates)."""
    print("Test 4: Test upsert behavior (re-import)...")
    
    clear_test_data()
    
    # First import
    sample1 = """Player1\t55555\tXP\t10000\t90\t100\t50
Player1\t55555\tRecent games\t0\t0\t10\t0
Player1\t55555\tChess\t1500\t100\t100\t50"""
    
    result1 = import_data(sample1, 'player_stats')
    assert result1['success']
    assert result1['results']['players_created'] == 1
    assert result1['results']['games_created'] == 1
    assert result1['results']['game_stats_created'] == 1
    
    # Second import with updated data
    sample2 = """Player1\t55555\tXP\t15000\t95\t150\t80
Player1\t55555\tRecent games\t1\t0\t20\t2
Player1\t55555\tChess\t1600\t90\t150\t80
Player1\t55555\tPoker\t1400\t\t50\t20"""
    
    result2 = import_data(sample2, 'player_stats')
    assert result2['success']
    assert result2['results']['players_created'] == 0  # Should update, not create
    assert result2['results']['players_updated'] == 1
    assert result2['results']['games_created'] == 1  # New game: Poker
    assert result2['results']['game_stats_created'] == 1  # Poker stat
    assert result2['results']['game_stats_updated'] == 1  # Chess stat updated
    
    # Verify no duplicates
    session = get_session()
    try:
        players = session.query(Player).filter_by(bga_player_id=55555).all()
        assert len(players) == 1, f"Expected 1 player, found {len(players)}"
        
        player = players[0]
        assert player.xp == 15000  # Updated value
        assert player.matches_total == 150  # Updated value
        
        stats = session.query(PlayerGameStat).filter_by(player_id=player.id).all()
        assert len(stats) == 2  # Chess (updated) + Poker (new)
        
        print("  [OK] Upsert behavior verified - no duplicates\n")
    finally:
        session.close()


def test_error_handling():
    """Test error handling for invalid data."""
    print("Test 5: Test error handling...")
    
    # Test empty input
    result = import_data("", 'player_stats')
    assert not result['success']
    assert result['error_type'] == 'ValidationError'
    print(f"  [OK] Empty input error: {result['error']}")
    
    # Test invalid column count
    result = import_data("Player\t12345\tXP", 'player_stats')
    assert not result['success']
    assert result['error_type'] == 'ParseError'
    print(f"  [OK] Invalid column count error: {result['error']}")
    
    # Test missing XP row
    result = import_data("Player1\t88888\tRecent games\t0\t0\t10\t0", 'player_stats')
    assert not result['success']
    assert result['error_type'] == 'ValidationError'
    print(f"  [OK] Missing XP row error: {result['error']}")
    
    # Test unsupported import type
    result = import_data("some data", 'unsupported_type')
    assert not result['success']
    assert 'Unsupported' in result['error']
    print(f"  [OK] Unsupported type error: {result['error']}\n")


def run_all_tests():
    """Run all integration tests."""
    print("=" * 60)
    print("Integration Tests: Import Service")
    print("=" * 60)
    print()
    
    try:
        test_detect_import_type()
        test_import_single_player()
        test_import_multiple_players()
        test_upsert_behavior()
        test_error_handling()
        
        print("=" * 60)
        print("All integration tests passed! (5/5)")
        print("=" * 60)
        return 0
    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
