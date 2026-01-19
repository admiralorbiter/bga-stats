# Phase 1 - Vertical Slice Scope Definition

## Goal

Implement a minimal working vertical slice that demonstrates the complete import-to-browse workflow for **one** data type, proving the architecture and patterns before expanding to other import types.

## Selected Import Type: Player Stats

**Rationale**: Player Stats provides the most immediate value to users (comprehensive player statistics) and has a well-defined, structured format that's easier to implement as a first pass.

## Phase 1 Deliverables

### 1. Backend Foundation

#### Database Models
- [ ] `Player` model (from `backend/models.py`)
- [ ] `Game` model (minimal, referenced by player stats)
- [ ] `PlayerGameStat` model (player-game relationship with ELO, rank, etc.)
- [ ] Database initialization script
- [ ] SQLite database file creation on first run

#### Parser Implementation
- [ ] `backend/parsers/player_stats_parser.py`
  - Parse TSV format (XP row, Recent games row, per-game rows)
  - Validate input format
  - Return structured data (dict/list of dicts)
  - Error handling with descriptive messages

#### Import Service
- [ ] `backend/services/import_service.py`
  - Route input to appropriate parser based on type
  - Normalize parsed data
  - Dedupe/upsert logic (handle re-imports idempotently)
  - Return import results (counts, errors)

#### API Routes
- [ ] `POST /api/import` - Accept import data (JSON payload with `type` and `data` or raw text)
- [ ] `GET /api/players` - List all players (JSON)
- [ ] `GET /api/players/<id>` - Get single player with game stats (JSON)
- [ ] `GET /api/games` - List all games (minimal, for future expansion)

#### Flask App Structure
- [ ] `backend/app.py` - Flask application factory
- [ ] Basic configuration (SQLite path, secret key)
- [ ] Database initialization
- [ ] Route registration
- [ ] Error handlers

### 2. Frontend Foundation

#### Templates
- [ ] `frontend/templates/base.html` - Base template with Tailwind CSS
- [ ] `frontend/templates/import.html` - Import interface
  - Text area for pasting export data
  - File upload option (optional)
  - Import type selector (defaults to auto-detect)
  - Import button
  - Success/error message display
- [ ] `frontend/templates/players.html` - Players list page
  - Table of players
  - Basic search/filter (optional, Phase 1 minimal)
  - Links to player detail
- [ ] `frontend/templates/player_detail.html` - Individual player view
  - Overall stats (XP, karma, totals)
  - Recent games stats (abandoned, timeout, last seen)
  - Table of per-game statistics (ELO, rank, played, won)
  - Edit/delete buttons (for future CRUD)

#### JavaScript (jQuery)
- [ ] `frontend/static/js/import.js` - Import page behavior
  - Submit import form via AJAX
  - Display loading state
  - Show success/error messages
  - Redirect to players list on success
- [ ] `frontend/static/js/players.js` - Players list behavior
  - Fetch players via API
  - Render player table
  - Handle search/filter (if implemented)
- [ ] `frontend/static/js/player_detail.js` - Player detail behavior
  - Fetch player data via API
  - Render stats and game table

#### Tailwind CSS
- [ ] Basic styling for all pages
- [ ] Responsive layout (mobile-friendly)
- [ ] Form styling
- [ ] Table styling

### 3. Core Features

#### Import Functionality
- [ ] Accept raw TSV text (paste or file upload)
- [ ] Auto-detect Player Stats format (or allow manual selection)
- [ ] Parse and validate input
- [ ] Handle XP row, Recent games row, and per-game rows
- [ ] Upsert players (update if exists, create if new)
- [ ] Upsert player-game stats (merge with existing)
- [ ] Return import summary (records created/updated)

#### Browse Functionality
- [ ] List all imported players
- [ ] View individual player details
- [ ] Display overall stats (XP, karma, totals, recent)
- [ ] Display per-game statistics table

#### Error Handling
- [ ] Validation errors shown to user
- [ ] Parsing errors logged and reported
- [ ] Database errors handled gracefully

## Out of Scope for Phase 1

- Other import types (Game List, Move Stats, Tournament Stats) - Phase 2
- Advanced search/filtering - Phase 3
- Edit/delete CRUD operations - Phase 3
- Export functionality - Phase 3
- Import history/audit - Phase 3
- Advanced deduplication strategies - Phase 3

## Acceptance Criteria

### Functional Requirements

1. **Import Flow**:
   - User can paste Player Stats export into import page
   - App successfully parses and validates the input
   - Data is stored in SQLite database
   - User sees success message with record counts

2. **Browse Flow**:
   - User can navigate to Players list page
   - All imported players are visible in a table
   - Clicking a player shows their detail page
   - Detail page displays:
     - Overall stats (XP, karma, total matches/wins)
     - Recent games stats (abandoned, timeout, recent matches, last seen)
     - Per-game statistics table (game name, ELO, rank, played, won)

3. **Idempotency**:
   - Re-importing the same export updates existing records (no duplicates)
   - Import summary shows "updated" vs "created" counts

4. **Error Handling**:
   - Invalid input shows clear error message
   - Malformed rows are skipped with error logged
   - Partial imports succeed (valid rows imported, invalid rows reported)

### Technical Requirements

1. **Code Quality**:
   - Parser is isolated and testable
   - Database models follow SQLAlchemy best practices
   - API routes return consistent JSON format
   - Frontend JavaScript is organized and maintainable

2. **User Experience**:
   - Pages load in < 1 second (for small datasets)
   - Import feedback is clear (loading, success, error)
   - UI is responsive (works on mobile)
   - Navigation between pages is intuitive

3. **Documentation**:
   - Code has inline comments where complex
   - README updated with Phase 1 setup instructions
   - Import workflow documented

## Test Scenarios

### Scenario 1: First Import
1. Start with empty database
2. Import Player Stats export with 3 players
3. Verify: 3 players in database, each with their game stats
4. Verify: Players list shows 3 players
5. Verify: Each player detail page shows correct stats

### Scenario 2: Re-Import
1. Import same export again
2. Verify: No duplicate players created
3. Verify: Stats are updated (if export data changed)
4. Verify: Import summary shows "updated" counts

### Scenario 3: Invalid Input
1. Import malformed TSV (missing columns, wrong format)
2. Verify: Error message is shown
3. Verify: No partial data imported
4. Verify: Error message indicates what went wrong

### Scenario 4: Partial Valid Data
1. Import export with mix of valid and invalid rows
2. Verify: Valid rows are imported
3. Verify: Invalid rows are skipped
4. Verify: Error summary shows which rows failed

## Success Metrics

- **Time to Complete**: Phase 1 should be completable in 1-2 days of focused development
- **Code Reusability**: Parser pattern should be easily replicable for other import types
- **User Satisfaction**: A user can successfully import and browse their player stats without confusion

## Next Steps After Phase 1

1. Gather feedback on import/browse UX
2. Refine patterns based on Phase 1 learnings
3. Expand to Phase 2 (other import types)
4. Add Phase 3 features (search, edit, export, audit)

## Dependencies

Phase 1 depends on:
- ✅ Documentation complete (ARCHITECTURE.md, DATA_FORMATS.md, DEVELOPMENT.md)
- ✅ Flask and SQLAlchemy installed
- ✅ Tailwind CSS build process configured
- ✅ Development environment setup

## Estimated Implementation Order

1. Database models and initialization
2. Basic Flask app structure (routes, app factory)
3. Player Stats parser
4. Import service and API route
5. Import UI (HTML + JavaScript)
6. Players list API route and UI
7. Player detail API route and UI
8. Testing and refinement