# BGA Stats App - Sprint Plan

This document breaks down the development work into small, manageable sprints. Each sprint is designed to be completable in 1-3 days of focused development.

## Sprint Overview

### Phase 1 Sprints (Player Stats - Vertical Slice)

| Sprint | Name | Duration | Focus |
|--------|------|----------|-------|
| Sprint 0 | Project Setup | 1-2 hours | Environment & dependencies |
| Sprint 1 | Database Foundation | 4-6 hours | Models & initialization |
| Sprint 2 | Flask App Skeleton | 3-4 hours | Basic app structure |
| Sprint 3 | Player Stats Parser | 4-6 hours | Import parsing logic |
| Sprint 4 | Import Service & API | 4-6 hours | Backend import pipeline |
| Sprint 5 | Base Frontend & Import UI | 4-6 hours | Import page |
| Sprint 6 | Players List API & UI | 3-4 hours | List players |
| Sprint 7 | Player Detail API & UI | 4-5 hours | Individual player view |
| Sprint 8 | Integration & Testing | 4-6 hours | End-to-end testing |
| Sprint 9 | Polish & Refinement | 3-4 hours | UX improvements |

**Total Phase 1**: ~35-50 hours (approximately 5-7 working days)

---

## Sprint 0: Project Setup

**Duration**: 1-2 hours  
**Goal**: Set up development environment and project structure

### Tasks

- [ ] Create project directory structure
  - [ ] `backend/` directory
  - [ ] `frontend/templates/` directory
  - [ ] `frontend/static/css/` directory
  - [ ] `frontend/static/js/` directory
- [ ] Set up Python virtual environment
  - [ ] Create `venv/`
  - [ ] Activate virtual environment
- [ ] Create `requirements.txt` with dependencies
  - [ ] Flask>=2.3.0
  - [ ] SQLAlchemy>=2.0.0
- [ ] Install Python dependencies
- [ ] Initialize Tailwind CSS
  - [ ] Create `package.json`
  - [ ] Install Tailwind CSS CLI
  - [ ] Create `tailwind.config.js`
  - [ ] Create `frontend/static/css/input.css`
- [ ] Create basic `.gitignore`
- [ ] Update `README.md` with setup instructions

### Deliverables

- Project structure created
- Virtual environment working
- Dependencies installed
- Tailwind CSS configured
- Development environment ready

### Acceptance Criteria

- Can run `flask --version` successfully
- Can run `tailwindcss --version` successfully
- Can import Flask and SQLAlchemy in Python
- Project structure matches documentation

### Testing

- Run `python -c "import flask; import sqlalchemy; print('OK')"` - should succeed
- Run `tailwindcss --help` - should show help

---

## Sprint 1: Database Foundation

**Duration**: 4-6 hours  
**Goal**: Create database models and initialization logic

### Tasks

- [ ] Create `backend/models.py`
  - [ ] Import SQLAlchemy components
  - [ ] Set up `Base` declarative base
  - [ ] Define `Game` model
    - [ ] Fields: `id`, `bga_game_id` (unique), `name`, `display_name`, `status`, `premium`, `created_at`, `updated_at`
  - [ ] Define `Player` model
    - [ ] Fields: `id`, `bga_player_id` (unique), `name`, `xp`, `karma`, `matches_total`, `wins_total`, `abandoned`, `timeout`, `recent_matches`, `last_seen_days`, `created_at`, `updated_at`
  - [ ] Define `PlayerGameStat` model
    - [ ] Fields: `id`, `player_id` (FK), `game_id` (FK), `elo`, `rank`, `played`, `won`, `imported_at`, `created_at`, `updated_at`
    - [ ] Unique constraint on `(player_id, game_id)`
  - [ ] Define relationships (Player -> PlayerGameStat, Game -> PlayerGameStat)
- [ ] Create `backend/db.py` (database initialization)
  - [ ] Create database engine (SQLite)
  - [ ] Create `init_db()` function to create tables
  - [ ] Create `get_session()` function for database sessions
- [ ] Create `backend/config.py` (configuration)
  - [ ] Database path configuration
  - [ ] Flask secret key generation/loading
- [ ] Test database creation
  - [ ] Run `init_db()` manually
  - [ ] Verify `bga_stats.db` is created
  - [ ] Verify tables exist using SQLite browser

### Deliverables

- `backend/models.py` with all Phase 1 models
- `backend/db.py` with database initialization
- `backend/config.py` with configuration
- SQLite database file created on first run

### Acceptance Criteria

- All three models defined with correct fields
- Database file is created in project root
- All tables are created successfully
- Models can be instantiated and saved to database
- Unique constraints work (no duplicate players by `bga_player_id`)

### Testing

```python
# Manual test script
from backend.models import Player, Game, PlayerGameStat
from backend.db import init_db, get_session

init_db()
session = get_session()

# Create test player
player = Player(bga_player_id=12345, name="TestPlayer", xp=1000)
session.add(player)
session.commit()

# Verify
assert session.query(Player).count() == 1
```

---

## Sprint 2: Flask App Skeleton

**Duration**: 3-4 hours  
**Goal**: Create basic Flask application structure

### Tasks

- [ ] Create `backend/app.py`
  - [ ] Flask application factory pattern
  - [ ] Load configuration from `config.py`
  - [ ] Initialize database on app creation
  - [ ] Register error handlers (404, 500)
  - [ ] Create `create_app()` function
- [ ] Create `backend/routes/__init__.py`
- [ ] Create `backend/routes/main.py`
  - [ ] `GET /` - Homepage route (redirects to import or players)
  - [ ] Health check route `GET /health` (returns JSON status)
- [ ] Create `backend/routes/api.py` (placeholder)
  - [ ] Empty file, will be populated in later sprints
- [ ] Update `backend/app.py` to register route blueprints
- [ ] Create simple `frontend/templates/base.html`
  - [ ] HTML5 structure
  - [ ] Include Tailwind CSS (link to output.css)
  - [ ] Include jQuery (CDN or local)
  - [ ] Basic navigation placeholder
  - [ ] Content block for child templates
- [ ] Create `frontend/templates/home.html`
  - [ ] Simple welcome page
- [ ] Build initial Tailwind CSS (`npm run build-css`)
- [ ] Test Flask app runs
  - [ ] `flask run` starts successfully
  - [ ] Can access homepage in browser
  - [ ] Health check endpoint works

### Deliverables

- Working Flask application
- Base template with Tailwind CSS
- Homepage route
- Health check endpoint

### Acceptance Criteria

- Flask app starts without errors
- Homepage loads in browser
- Tailwind CSS styles are applied
- Navigation structure exists (even if empty)

### Testing

- Run `flask run` - should start on port 5000
- Visit `http://127.0.0.1:5000` - should see homepage
- Visit `http://127.0.0.1:5000/health` - should return JSON `{"status": "ok"}`

---

## Sprint 3: Player Stats Parser

**Duration**: 4-6 hours  
**Goal**: Implement parser for Player Stats import format

### Tasks

- [ ] Create `backend/parsers/__init__.py`
- [ ] Create `backend/parsers/player_stats_parser.py`
  - [ ] Define `parse_player_stats(raw_text)` function
  - [ ] Split input into lines
  - [ ] Skip empty lines
  - [ ] Detect row types:
    - [ ] XP row (second column is "XP")
    - [ ] Recent games row (second column is "Recent games")
    - [ ] Per-game row (6 columns, second column is game name)
  - [ ] Parse XP row:
    - [ ] Extract: player_name, xp_value, karma, total_matches, total_wins
    - [ ] Validate numeric fields
  - [ ] Parse Recent games row:
    - [ ] Extract: player_name, abandoned, timeout, recent_matches, last_seen_days
    - [ ] Validate numeric fields
  - [ ] Parse per-game rows:
    - [ ] Extract: player_name, game_name, elo, rank, played, won
    - [ ] Handle empty rank and non-numeric ELO ("N/A")
    - [ ] Validate numeric fields where applicable
  - [ ] Group rows by player
  - [ ] Return structured data (list of dicts)
  - [ ] Error handling:
    - [ ] Invalid row format exceptions
    - [ ] Missing required fields
    - [ ] Type conversion errors
- [ ] Create `backend/parsers/exceptions.py`
  - [ ] `ParserError` base exception
  - [ ] `ValidationError` for invalid input
  - [ ] `ParseError` for parsing failures
- [ ] Write unit tests (optional, recommended)
  - [ ] Test with sample Player Stats export
  - [ ] Test XP row parsing
  - [ ] Test Recent games row parsing
  - [ ] Test per-game row parsing
  - [ ] Test error cases

### Deliverables

- Working Player Stats parser
- Error handling for invalid input
- Structured output (dict/list format)

### Acceptance Criteria

- Parser accepts TSV text (from bookmarklet export)
- Correctly identifies XP, Recent games, and per-game rows
- Returns structured data ready for database insertion
- Handles edge cases (empty rank, "N/A" ELO, missing fields)
- Provides descriptive error messages

### Testing

```python
# Manual test
from backend.parsers.player_stats_parser import parse_player_stats

sample = """JohnDoe	XP	45000	95	1250	650
JohnDoe	Recent games	2	1	45	3
JohnDoe	Ticket to Ride	1500	42	150	75
JohnDoe	Carcassonne	1650	25	200	110"""

result = parse_player_stats(sample)
assert len(result) == 1  # One player
assert result[0]['name'] == 'JohnDoe'
assert result[0]['xp'] == 45000
assert len(result[0]['game_stats']) == 2
```

---

## Sprint 4: Import Service & API

**Duration**: 4-6 hours  
**Goal**: Implement backend import pipeline and API endpoint

### Tasks

- [ ] Create `backend/services/__init__.py`
- [ ] Create `backend/services/import_service.py`
  - [ ] `detect_import_type(raw_text)` function
    - [ ] Analyze input format (tab vs semicolon delimiter)
    - [ ] Check for Player Stats signatures (XP row, Recent games row)
    - [ ] Return import type string
  - [ ] `import_player_stats(session, parsed_data)` function
    - [ ] For each player in parsed data:
      - [ ] Upsert Player (find by `bga_player_id`, update or create)
      - [ ] Update overall stats (XP, karma, totals, recent)
      - [ ] For each game stat:
        - [ ] Upsert Game (find by name, create if new)
        - [ ] Upsert PlayerGameStat (find by player_id + game_id, update or create)
    - [ ] Return import results:
      - [ ] Players created/updated count
      - [ ] Games created/updated count
      - [ ] Game stats created/updated count
  - [ ] `import_data(import_type, raw_text)` main function
    - [ ] Get database session
    - [ ] Route to appropriate parser
    - [ ] Parse data
    - [ ] Call appropriate import function
    - [ ] Commit transaction
    - [ ] Return results dict
- [ ] Create `backend/routes/api.py`
  - [ ] `POST /api/import` endpoint
    - [ ] Accept JSON: `{"type": "player_stats", "data": "..."}` or `{"data": "..."}` (auto-detect)
    - [ ] Accept file upload (optional for Phase 1)
    - [ ] Call import service
    - [ ] Return JSON response:
      ```json
      {
        "success": true,
        "import_type": "player_stats",
        "results": {
          "players_created": 3,
          "players_updated": 0,
          "games_created": 5,
          "game_stats_created": 10
        },
        "errors": []
      }
      ```
    - [ ] Handle errors gracefully (return error response)
- [ ] Test import endpoint
  - [ ] Use sample Player Stats export
  - [ ] POST to `/api/import`
  - [ ] Verify data is stored in database
  - [ ] Verify response contains correct counts

### Deliverables

- Import service with upsert logic
- Import API endpoint
- Idempotent imports (re-import updates, doesn't duplicate)

### Acceptance Criteria

- Import API accepts Player Stats data
- Data is correctly stored in database
- Re-importing same data updates records (no duplicates)
- Response includes creation/update counts
- Errors are returned as JSON with descriptive messages

### Testing

```bash
# Manual test with curl
curl -X POST http://127.0.0.1:5000/api/import \
  -H "Content-Type: application/json" \
  -d '{"type": "player_stats", "data": "JohnDoe\tXP\t45000\t95\t1250\t650\n..."}'
```

---

## Sprint 5: Base Frontend & Import UI

**Duration**: 4-6 hours  
**Goal**: Create import page UI

### Tasks

- [ ] Update `frontend/templates/base.html`
  - [ ] Add navigation bar (Home, Import, Players)
  - [ ] Add jQuery CDN (or local file)
  - [ ] Improve styling with Tailwind
- [ ] Create `frontend/templates/import.html`
  - [ ] Extends base template
  - [ ] Import form:
    - [ ] Textarea for pasting export data (large, multi-line)
    - [ ] File upload input (optional, Phase 1 can be basic)
    - [ ] Import type selector (dropdown: Auto-detect, Player Stats, etc.)
    - [ ] Import button
  - [ ] Message area (for success/error messages)
  - [ ] Loading state indicator (hidden by default)
- [ ] Create `frontend/static/js/import.js`
  - [ ] Form submission handler
  - [ ] Collect form data (textarea value or file)
  - [ ] Show loading state (disable button, show spinner)
  - [ ] AJAX POST to `/api/import`
  - [ ] Handle success response:
    - [ ] Display success message with counts
    - [ ] Hide loading state
    - [ ] Optionally redirect to players list
  - [ ] Handle error response:
    - [ ] Display error message
    - [ ] Hide loading state
    - [ ] Show error details
- [ ] Update main routes to include import page
  - [ ] `GET /import` route in `backend/routes/main.py`
- [ ] Style with Tailwind CSS
  - [ ] Form styling (centered, max-width, padding)
  - [ ] Button styling (primary color, hover states)
  - [ ] Message styling (success: green, error: red)
  - [ ] Responsive design (mobile-friendly)
- [ ] Test import UI end-to-end
  - [ ] Paste sample Player Stats export
  - [ ] Click Import
  - [ ] Verify success message appears
  - [ ] Verify data appears in database

### Deliverables

- Functional import page
- JavaScript for import form submission
- Styled UI with Tailwind CSS

### Acceptance Criteria

- Import page loads correctly
- User can paste export data
- Import button triggers AJAX request
- Loading state is visible during import
- Success/error messages are displayed
- UI is responsive (works on mobile)

### Testing

- Visit `http://127.0.0.1:5000/import`
- Paste sample Player Stats export
- Click Import
- Verify success message with counts
- Verify data in database (check SQLite file)

---

## Sprint 6: Players List API & UI

**Duration**: 3-4 hours  
**Goal**: Display list of imported players

### Tasks

- [ ] Create `GET /api/players` endpoint in `backend/routes/api.py`
  - [ ] Query all players from database
  - [ ] Return JSON array:
    ```json
    [
      {
        "id": 1,
        "bga_player_id": 12345,
        "name": "JohnDoe",
        "xp": 45000,
        "karma": 95,
        "matches_total": 1250,
        "wins_total": 650,
        "url": "/players/1"
      },
      ...
    ]
    ```
  - [ ] Optionally support pagination (Phase 1: return all)
- [ ] Create `frontend/templates/players.html`
  - [ ] Extends base template
  - [ ] Page title "Players"
  - [ ] Players table:
    - [ ] Columns: Name, XP, Karma, Matches, Wins, Actions
    - [ ] Links to player detail pages
  - [ ] Empty state message (if no players)
  - [ ] "Import Data" link
- [ ] Create `frontend/static/js/players.js`
  - [ ] Fetch players on page load (AJAX GET `/api/players`)
  - [ ] Render players table dynamically
  - [ ] Handle empty state
  - [ ] Add click handlers for player links
- [ ] Add `GET /players` route in `backend/routes/main.py`
  - [ ] Render `players.html` template
- [ ] Style with Tailwind CSS
  - [ ] Table styling (striped rows, hover effects)
  - [ ] Responsive table (scrollable on mobile)
  - [ ] Link styling
- [ ] Test players list
  - [ ] Import some player data
  - [ ] Navigate to `/players`
  - [ ] Verify players are displayed
  - [ ] Verify links work

### Deliverables

- Players list API endpoint
- Players list page
- JavaScript for fetching and rendering players

### Acceptance Criteria

- Players list page loads
- All imported players are displayed
- Player links navigate to detail pages
- Empty state shows helpful message
- Table is responsive

### Testing

- Import Player Stats data
- Visit `http://127.0.0.1:5000/players`
- Verify all players appear in table
- Click a player link - should navigate to detail page

---

## Sprint 7: Player Detail API & UI

**Duration**: 4-5 hours  
**Goal**: Display individual player statistics

### Tasks

- [ ] Create `GET /api/players/<id>` endpoint in `backend/routes/api.py`
  - [ ] Query player by ID
  - [ ] Include related game stats (join PlayerGameStat and Game)
  - [ ] Return JSON:
    ```json
    {
      "id": 1,
      "bga_player_id": 12345,
      "name": "JohnDoe",
      "xp": 45000,
      "karma": 95,
      "matches_total": 1250,
      "wins_total": 650,
      "abandoned": 2,
      "timeout": 1,
      "recent_matches": 45,
      "last_seen_days": 3,
      "game_stats": [
        {
          "game_name": "Ticket to Ride",
          "elo": "1500",
          "rank": "42",
          "played": 150,
          "won": 75
        },
        ...
      ]
    }
    ```
  - [ ] Handle 404 if player not found
- [ ] Create `frontend/templates/player_detail.html`
  - [ ] Extends base template
  - [ ] Player name as page title
  - [ ] Overall stats section:
    - [ ] XP, Karma, Total Matches, Total Wins
    - [ ] Display as cards or grid
  - [ ] Recent games section:
    - [ ] Abandoned, Timeout, Recent Matches, Last Seen
  - [ ] Per-game statistics table:
    - [ ] Columns: Game Name, ELO, Rank, Played, Won
    - [ ] Sortable (optional, Phase 1: basic table)
  - [ ] Back to Players link
- [ ] Create `frontend/static/js/player_detail.js`
  - [ ] Extract player ID from URL
  - [ ] Fetch player data (AJAX GET `/api/players/<id>`)
  - [ ] Render overall stats
  - [ ] Render recent games stats
  - [ ] Render game stats table
  - [ ] Handle 404 error (player not found)
- [ ] Add `GET /players/<id>` route in `backend/routes/main.py`
  - [ ] Render `player_detail.html` template
- [ ] Style with Tailwind CSS
  - [ ] Stats cards (grid layout, colored backgrounds)
  - [ ] Table styling (consistent with players list)
  - [ ] Responsive layout
- [ ] Test player detail page
  - [ ] Navigate to player detail from players list
  - [ ] Verify all stats are displayed correctly
  - [ ] Verify game stats table has data

### Deliverables

- Player detail API endpoint
- Player detail page
- JavaScript for fetching and rendering player data

### Acceptance Criteria

- Player detail page loads
- Overall stats (XP, karma, totals) are displayed
- Recent games stats are displayed
- Per-game statistics table is displayed with correct data
- Navigation works (back to players list)

### Testing

- Import Player Stats data
- Navigate to a player detail page
- Verify all stats sections are populated
- Verify game stats table shows games
- Test with player that has no games (edge case)

---

## Sprint 8: Integration & Testing

**Duration**: 4-6 hours  
**Goal**: End-to-end testing and bug fixes

### Tasks

- [ ] End-to-end test import workflow
  - [ ] Start with empty database
  - [ ] Import Player Stats export with multiple players
  - [ ] Verify players appear in list
  - [ ] Verify player detail pages work
- [ ] Test idempotency
  - [ ] Import same export twice
  - [ ] Verify no duplicates created
  - [ ] Verify updated counts in import response
- [ ] Test error handling
  - [ ] Invalid input format
  - [ ] Missing required fields
  - [ ] Malformed rows (should skip, not fail entire import)
  - [ ] Empty input
- [ ] Fix any bugs discovered
  - [ ] Parser edge cases
  - [ ] Database constraint violations
  - [ ] UI rendering issues
- [ ] Test edge cases
  - [ ] Player with no games
  - [ ] Empty rank field
  - [ ] "N/A" ELO value
  - [ ] Very large imports (100+ players)
- [ ] Performance testing (optional)
  - [ ] Import time for large datasets
  - [ ] Page load times
- [ ] Cross-browser testing (optional)
  - [ ] Chrome, Firefox, Safari
- [ ] Mobile responsiveness testing
  - [ ] Test on mobile device or browser dev tools

### Deliverables

- All test scenarios pass
- Bug fixes applied
- Edge cases handled

### Acceptance Criteria

- All Phase 1 acceptance criteria met
- Import → Browse workflow works end-to-end
- Error handling works correctly
- No critical bugs remain

### Testing Scenarios

1. **First Import**: Empty DB → Import → Browse
2. **Re-Import**: Same data → No duplicates
3. **Invalid Input**: Bad format → Error message
4. **Partial Valid Data**: Mix of valid/invalid → Valid imported, errors reported
5. **Edge Cases**: Empty rank, N/A ELO, no games

---

## Sprint 9: Polish & Refinement

**Duration**: 3-4 hours  
**Goal**: Improve UX and code quality

### Tasks

- [ ] Improve error messages
  - [ ] More descriptive validation errors
  - [ ] User-friendly error messages in UI
- [ ] Add loading states
  - [ ] Spinner animations
  - [ ] Skeleton screens (optional)
- [ ] Improve styling
  - [ ] Consistent spacing and colors
  - [ ] Better typography
  - [ ] Improved table styling
- [ ] Add navigation improvements
  - [ ] Breadcrumbs (optional)
  - [ ] Active page highlighting
- [ ] Add helpful UI elements
  - [ ] Tooltips for unclear fields
  - [ ] Confirmation messages
  - [ ] Success animations
- [ ] Code cleanup
  - [ ] Add docstrings to functions
  - [ ] Remove debug print statements
  - [ ] Organize imports
- [ ] Update documentation
  - [ ] README.md with usage instructions
  - [ ] Inline code comments where needed

### Deliverables

- Polished UI
- Improved error messages
- Clean, documented code

### Acceptance Criteria

- UI is visually appealing
- Error messages are helpful
- Code is well-documented
- User can complete import workflow without confusion

---

## Future Phase Sprints (Out of Scope for Phase 1)

### Phase 2: Additional Import Types

- **Sprint 10**: Game List Import
- **Sprint 11**: Game List UI
- **Sprint 12**: Move Stats Import
- **Sprint 13**: Match Detail UI
- **Sprint 14**: Tournament Stats Import
- **Sprint 15**: Tournament Detail UI

### Phase 3: Quality & Usability

- **Sprint 16**: Search & Filtering
- **Sprint 17**: Edit/Delete CRUD Operations
- **Sprint 18**: Export Functionality
- **Sprint 19**: Import History/Audit
- **Sprint 20**: Performance Optimization

---

## Sprint Management Notes

### Sprint Duration Guidelines

- **Short sprints (1-2 hours)**: Simple setup tasks
- **Medium sprints (3-4 hours)**: Feature implementation
- **Long sprints (4-6 hours)**: Complex features or integration

### Sprint Completion Criteria

Each sprint is considered complete when:
- [ ] All tasks are done
- [ ] Deliverables are working
- [ ] Acceptance criteria are met
- [ ] Testing is completed

### Sprint Review

After each sprint:
1. Review what was completed
2. Test deliverables
3. Note any blockers or issues
4. Adjust next sprint if needed

### Sprint Retrospective

At end of Phase 1:
1. What went well?
2. What could be improved?
3. What patterns emerged?
4. How to apply learnings to Phase 2?

---

## Tracking Progress

### Sprint Status

- 🟢 **Not Started**: Sprint not yet begun
- 🟡 **In Progress**: Sprint currently being worked on
- 🔵 **Blocked**: Sprint blocked by dependency or issue
- ✅ **Complete**: Sprint finished and tested

### Progress Tracking

Update this document as sprints are completed:
- [ ] Sprint 0: Project Setup - [Status]
- [ ] Sprint 1: Database Foundation - [Status]
- [ ] Sprint 2: Flask App Skeleton - [Status]
- ... (continue for all sprints)

---

## Estimated Timeline

**Phase 1 (9 Sprints)**: 35-50 hours total

- **Week 1**: Sprints 0-4 (Setup through Import Service)
- **Week 2**: Sprints 5-9 (Frontend through Polish)

**For one developer working part-time (4 hours/day)**:
- Phase 1: ~2 weeks
- Complete app (all phases): ~4-6 weeks

**For one developer working full-time (8 hours/day)**:
- Phase 1: ~1 week
- Complete app (all phases): ~2-3 weeks