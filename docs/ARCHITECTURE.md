# BGA Stats App - Architecture Documentation

## Overview

The BGA Stats App is a local-first Flask web application that enables users to import, store, browse, and export BoardGameArena statistics. The application accepts data exported from browser bookmarklets and provides a CRUD interface for managing game statistics offline.

## Core Principles

### 1. Local-First Architecture
- All data is stored in a local SQLite database
- No cloud services or remote databases required
- Users maintain full control over their data
- Works completely offline after initial data import

### 2. Browser-Assisted Data Acquisition
- **No backend credential management**: The application never handles BGA login credentials
- Users must be logged into BGA in their browser to run bookmarklets
- Data is exported from bookmarklets and then imported into the app
- This design ensures users maintain control over their BGA authentication

### 3. Import-Based Workflow
- Data flows from BGA → Browser (via bookmarklets) → Flask App (via import)
- Each bookmarklet produces a specific export format
- Import is explicit and user-initiated (paste or file upload)

## System Architecture

### High-Level Data Flow

```
┌─────────────┐
│   User      │
│  (Browser)  │
└──────┬──────┘
       │
       │ 1. Runs bookmarklet while logged into BGA
       ▼
┌─────────────────────────┐
│  BGA Website            │
│  (boardgamearena.com)   │
└──────┬──────────────────┘
       │
       │ 2. Bookmarklet extracts data from DOM/API
       ▼
┌─────────────────────────┐
│  Export Text/CSV/TSV    │
│  (copied to clipboard)  │
└──────┬──────────────────┘
       │
       │ 3. User pastes/uploads into Flask app
       ▼
┌─────────────────────────┐
│  Flask Application      │
│  - Parse & Validate     │
│  - Normalize            │
│  - Upsert to DB         │
└──────┬──────────────────┘
       │
       │ 4. Store in local database
       ▼
┌─────────────────────────┐
│  SQLite Database        │
│  (local file)           │
└─────────────────────────┘
```

## Module Structure

### Backend (`backend/`)

#### `app.py`
- Flask application entry point
- Application factory pattern (if using blueprints)
- Database initialization
- Route registration

#### `models.py`
- SQLAlchemy ORM models
- Database schema definitions
- Relationships between entities

#### `parsers/`
- **Purpose**: Isolated parsing logic for each bookmarklet export type
- **Files**:
  - `game_list_parser.py` - Parses GameList.js exports
  - `move_stats_parser.py` - Parses MoveStats.js exports
  - `player_stats_parser.py` - Parses PlayerStats.js exports
  - `tournament_stats_parser.py` - Parses TournamentStats.js exports
- **Benefits**: Changes to BGA HTML/API only affect the relevant parser

#### `routes/`
- API routes (`/api/*`)
  - `POST /api/import` - Import data endpoint
  - `GET /api/games`, `/api/games/<id>` - Game data
  - `GET /api/players`, `/api/players/<id>` - Player data
  - `GET /api/matches`, `/api/matches/<table_id>` - Match data
  - `GET /api/tournaments`, `/api/tournaments/<id>` - Tournament data
- HTML page routes
  - Serve templates for browsing/searching

#### `services/`
- Business logic layer
- `import_service.py` - Import pipeline orchestration
- `dedupe_service.py` - Handle idempotent imports
- `export_service.py` - Generate CSV/JSON exports

### Frontend (`frontend/`)

#### `templates/`
- Jinja2 HTML templates
- Pages:
  - `import.html` - Import interface
  - `games.html` - Games list
  - `players.html` - Players list
  - `player_detail.html` - Individual player stats
  - `matches.html` - Matches list
  - `match_detail.html` - Match moves timeline
  - `tournaments.html` - Tournaments list
  - `tournament_detail.html` - Tournament details

#### `static/`
- `css/` - Tailwind CSS build output
- `js/` - jQuery-powered UI behavior
  - API calls
  - Form handling
  - Dynamic content updates

## Database Schema

### Core Tables

#### `games`
- `id` (PK, auto-increment)
- `bga_game_id` (unique) - BGA's internal game ID
- `name` - Internal game name
- `display_name` - Human-readable display name
- `status` - Game status (alpha, beta, published)
- `premium` - Boolean: is premium game
- `created_at`, `updated_at` - Timestamps

#### `players`
- `id` (PK, auto-increment)
- `bga_player_id` (unique) - BGA's internal player ID
- `name` - Player display name
- `xp` - Experience points
- `karma` - Reputation percentage
- `matches_total` - Total matches played
- `wins_total` - Total wins
- `abandoned` - Abandoned matches count
- `timeout` - Timeout count
- `recent_matches` - Recent matches (last 60 days)
- `last_seen_days` - Days since last online
- `created_at`, `updated_at` - Timestamps

#### `player_game_stats`
- `id` (PK, auto-increment)
- `player_id` (FK to players)
- `game_id` (FK to games)
- `elo` - ELO rating for this game
- `rank` - Rank in this game
- `played` - Matches played in this game
- `won` - Wins in this game
- `imported_at` - When this stat was imported
- Unique constraint on `(player_id, game_id)`

#### `matches`
- `id` (PK, auto-increment)
- `bga_table_id` (unique) - BGA's table ID
- `game_name` - Name of the game (string, may link to games table later)
- `imported_at` - Import timestamp
- `created_at`, `updated_at` - Timestamps

#### `match_moves`
- `id` (PK, auto-increment)
- `match_id` (FK to matches)
- `move_no` - Move number
- `player_name` - Player name (string, may link to players later)
- `datetime_local` - Local datetime string
- `datetime_excel` - Excel datetime serial value
- `remaining_time` - Remaining time for player

#### `tournaments`
- `id` (PK, auto-increment)
- `bga_tournament_id` (unique) - BGA's tournament ID
- `name` - Tournament name
- `game_name` - Game name
- `start_time` - Tournament start datetime
- `end_time` - Tournament end datetime
- `rounds` - Number of rounds
- `round_limit` - Round time limit (hours)
- `total_matches` - Total match count
- `timeout_matches` - Matches that timed out
- `player_count` - Number of players
- `created_at`, `updated_at` - Timestamps

#### `tournament_matches`
- `id` (PK, auto-increment)
- `tournament_id` (FK to tournaments)
- `bga_table_id` - BGA table ID
- `is_timeout` - Boolean: did match timeout
- `progress` - Match progress percentage

#### `tournament_match_players`
- `id` (PK, auto-increment)
- `tournament_match_id` (FK to tournament_matches)
- `player_name` - Player name
- `remaining_time_seconds` - Remaining time in seconds
- `points` - Points earned in match

### Optional: Import History Table
- Track import operations for audit/debugging
- `id`, `import_type`, `raw_text_length`, `records_created`, `records_updated`, `imported_at`

## Constraints and Design Decisions

### Security Constraints

1. **No Credential Storage**: The app never stores or handles BGA login credentials
2. **Local-Only**: Data stays on the user's machine unless explicitly exported
3. **No External Network Calls**: Backend doesn't make HTTP requests to BGA
4. **Input Validation**: All imported data is validated and sanitized

### Technical Constraints

1. **SQLite Limitations**: 
   - Single-user (not suitable for concurrent writes from multiple processes)
   - Simpler than PostgreSQL, but sufficient for local-first use case
2. **Import Format**: Must handle existing bookmarklet output formats (TSV/CSV)
3. **Idempotency**: Re-importing same data shouldn't create duplicates

## Threat Model

### What We Protect Against

1. **Data Loss**: SQLite database corruption
   - Mitigation: Regular backups (user responsibility, but app can export JSON)
2. **Invalid Data**: Malformed imports
   - Mitigation: Validation in parsers, error reporting to user
3. **SQL Injection**: User-provided data in queries
   - Mitigation: SQLAlchemy ORM (parameterized queries)

### What We Don't Protect Against

1. **BGA Authentication**: User must handle their own BGA login
2. **Bookmarklet Security**: Bookmarklets run with user's BGA session
3. **Malicious Bookmarklets**: User responsibility to use trusted bookmarklets

## Module Boundaries

### Parser Isolation
- Each parser is independent
- Parsers should not depend on each other
- Parser output is normalized data structures (dicts/lists)
- Parsers throw descriptive errors for invalid input

### Service Layer
- Services orchestrate parsers + database operations
- Import service handles the full import pipeline:
  1. Route raw input to appropriate parser
  2. Parse and validate
  3. Normalize data
  4. Dedupe/upsert into database
  5. Return import results

### Route Layer
- Routes are thin: receive request, call service, return response
- API routes return JSON
- HTML routes render templates

### Frontend
- jQuery makes AJAX calls to API routes
- Templates render data from backend
- No business logic in frontend JavaScript

## Extension Points

### Future Enhancements

1. **JSON Export Format**: Update bookmarklets to output structured JSON
   - Add version field for schema evolution
   - Parsers can detect and handle multiple versions

2. **Database Migration**: SQLite → PostgreSQL if multi-user needed
   - SQLAlchemy abstraction makes this feasible
   - Add connection pooling and migration scripts

3. **Search/Filter**: Add full-text search capabilities
   - SQLite FTS5 extension
   - Frontend search UI

4. **Analytics**: Derived statistics and visualizations
   - Compute win rates, trends
   - Chart generation library

5. **Export Formats**: Additional export options
   - Excel files
   - PDF reports

## Non-Goals

- Backend-based web scraping of BGA
- Multi-user account management
- Cloud deployment or remote databases
- Real-time data synchronization with BGA
- Authentication/authorization system (single-user app)