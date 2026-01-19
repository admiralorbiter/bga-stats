"""
Manual test script for Sprint 1 database setup.
Run this to verify models, database creation, and basic CRUD operations.

Usage:
    python backend/test_db.py
"""

from backend.models import Player, Game, PlayerGameStat
from backend.db import init_db, get_session


def test_database():
    """
    Run comprehensive tests on the database setup.
    Tests model creation, relationships, and constraints.
    """
    print("=== Testing Database Setup ===\n")
    
    # Initialize database
    print("1. Initializing database...")
    init_db()
    print("   [OK] Database initialized\n")
    
    # Get session
    session = get_session()
    
    try:
        # Test 1: Create a Player
        print("2. Testing Player creation...")
        player = Player(
            bga_player_id=12345,
            name="TestPlayer",
            xp=50000,
            karma=95,
            matches_total=1500,
            wins_total=800
        )
        session.add(player)
        session.commit()
        print(f"   [OK] Player created: {player.name} (ID: {player.id})\n")
        
        # Test 2: Create a Game
        print("3. Testing Game creation...")
        game = Game(
            bga_game_id=42,
            name="ticket",
            display_name="Ticket to Ride",
            status="published",
            premium=True
        )
        session.add(game)
        session.commit()
        print(f"   [OK] Game created: {game.display_name} (ID: {game.id})\n")
        
        # Test 3: Create PlayerGameStat
        print("4. Testing PlayerGameStat creation...")
        stat = PlayerGameStat(
            player_id=player.id,
            game_id=game.id,
            elo="1500",
            rank="42",
            played=150,
            won=75
        )
        session.add(stat)
        session.commit()
        print(f"   [OK] PlayerGameStat created (ID: {stat.id})\n")
        
        # Test 4: Query with relationships
        print("5. Testing relationships...")
        queried_player = session.query(Player).filter_by(bga_player_id=12345).first()
        print(f"   Player: {queried_player.name}")
        print(f"   Game stats count: {len(queried_player.game_stats)}")
        for stat in queried_player.game_stats:
            print(f"     - {stat.game.display_name}: ELO {stat.elo}, Played {stat.played}")
        print()
        
        # Test 5: Unique constraint
        print("6. Testing unique constraint...")
        try:
            duplicate_player = Player(bga_player_id=12345, name="Duplicate")
            session.add(duplicate_player)
            session.commit()
            print("   [FAIL] Duplicate player was allowed")
        except Exception as e:
            session.rollback()
            print("   [OK] Unique constraint working (duplicate rejected)\n")
        
        # Test 6: Count records
        print("7. Verifying record counts...")
        player_count = session.query(Player).count()
        game_count = session.query(Game).count()
        stat_count = session.query(PlayerGameStat).count()
        print(f"   Players: {player_count}")
        print(f"   Games: {game_count}")
        print(f"   Stats: {stat_count}\n")
        
        print("=== All Tests Passed! ===")
        
    except Exception as e:
        print(f"\n[ERROR] Error occurred: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == '__main__':
    test_database()
