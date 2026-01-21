# BGA Stats App

A local-first Flask web application for importing, storing, browsing, and managing BoardGameArena statistics.

## Overview

BGA Stats App allows you to:
- Import statistics exported from BoardGameArena using bookmarklets
- Store all data locally in a SQLite database
- Browse and analyze your gaming statistics offline
- Maintain full control over your data

## Features

- **Local-First**: All data stored on your machine, no cloud dependencies
- **Auto-Pull Data**: Automatically fetch statistics from BGA using Playwright (no copy/paste!)
- **Manual Import**: Alternative browser bookmarklet method for data export
- **Browse & View**: Interactive players list and detailed per-player game statistics
- **Comprehensive Stats**: Import player stats, game lists, match details, and tournament data
- **Modern UI**: Built with Tailwind CSS for a clean, responsive interface
- **Session Management**: Login once, pull data anytime

## Prerequisites

Before you begin, ensure you have:
- **Python 3.8 or higher** - [Download Python](https://www.python.org/downloads/)
- **Node.js 16+ and npm** - [Download Node.js](https://nodejs.org/)
- **Git** (optional) - For cloning the repository

## Quick Start

### 1. Clone or Download Repository

```bash
git clone https://github.com/yourusername/bga-stats.git
cd bga-stats
```

### 2. Set Up Python Environment

Create and activate a virtual environment:

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

Verify installation:
```bash
python -c "import flask; import sqlalchemy; print('Python: OK')"
```

### 4. Install Node.js Dependencies

```bash
npm install
```

### 5. Build Tailwind CSS

```bash
npm run build-css
```

For development with auto-rebuild on changes:
```bash
npm run watch-css
```

### 6. Install Playwright Browsers (for auto-pull feature)

```bash
playwright install chromium
```

This is required only if you want to use the auto-pull feature. Skip if you only plan to use manual bookmarklet imports.

### 7. Run the Application

```bash
# Make sure virtual environment is activated
python app.py
```

The application will be available at: `http://127.0.0.1:5000`

## Development Workflow

### Activating Virtual Environment

Always activate the virtual environment before working on the project:

**Windows PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### Running Development Server

```bash
# Run the application
python app.py

# The app runs in development mode by default
# Access at http://127.0.0.1:5000
```

### Watching CSS Changes

In a separate terminal, run:
```bash
npm run watch-css
```

This will automatically rebuild CSS when you modify templates or add Tailwind classes.

## Project Structure

```
bga-stats/
├── backend/                 # Flask application
│   ├── parsers/            # Import format parsers
│   ├── routes/             # API and page routes
│   ├── services/           # Business logic
│   ├── app.py              # Flask app entry point
│   ├── models.py           # Database models
│   ├── db.py               # Database initialization
│   └── config.py           # Configuration
├── frontend/               # Frontend assets
│   ├── templates/          # Jinja2 HTML templates
│   └── static/
│       ├── css/            # Tailwind CSS
│       └── js/             # JavaScript files
├── bookmarklet-tool/       # Bookmarklet scripts for BGA
├── docs/                   # Documentation
├── venv/                   # Python virtual environment (git-ignored)
├── node_modules/           # Node dependencies (git-ignored)
├── requirements.txt        # Python dependencies
├── package.json            # Node.js configuration
└── tailwind.config.js      # Tailwind CSS configuration
```

## Usage

### Method 1: Auto-Pull (Recommended)

**No copy/paste required!**

1. **Navigate to Sync page**: `http://127.0.0.1:5000/sync`

2. **Login once**: 
   - Click "Login to BGA"
   - A browser window opens - log in as normal
   - Window closes automatically, session saved

3. **Pull data**:
   - Your player ID is automatically displayed after login
   - Click "Use My ID" to auto-fill your ID, or enter other player IDs
   - Enter player IDs (e.g., `12345,67890`) or group ID (e.g., `group:123`)
   - Click "Pull Player Stats"
   - Data is automatically imported!

4. **View your stats**:
   - Navigate to "Players" in the top menu
   - See all imported players with win rates, matches, and XP
   - Click "View Details" to see per-game statistics

See [docs/PLAYWRIGHT_SETUP.md](docs/PLAYWRIGHT_SETUP.md) for detailed auto-pull guide.

### Method 2: Manual Import (Bookmarklet)

**Traditional copy/paste method:**

1. **Install Bookmarklets**: 
   - Visit the Tools page at `http://127.0.0.1:5000/tools`
   - Drag the "📊 BGA Player Stats" button to your bookmarks bar

2. **Export from BGA**: 
   - Visit any player profile or group page on BoardGameArena
   - Click the bookmarklet from your bookmarks
   - Wait for the data to be collected and displayed

3. **Copy & Import**: 
   - Copy all text from the bookmarklet output
   - Navigate to `http://127.0.0.1:5000/import`
   - Paste and click "Import Data"

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for detailed manual workflow.

## Development Phases

The project is being developed in phases:

- **Phase 1** (✅ Complete): Player Stats - Complete vertical slice
  - ✅ Player statistics import (auto-pull and manual)
  - ✅ Database foundation with SQLAlchemy models
  - ✅ Players list and detail views
  - ✅ Session management with Playwright
  - ✅ Modern UI with Tailwind CSS
- **Phase 2** (✅ Complete): Additional import types
  - ✅ Game List, Move Stats, Tournaments parsers
  - ✅ Games browsing (list and detail views)
  - ✅ Tournaments browsing (list and detail views)
  - ✅ Auto-pull for Game List
  - ✅ Auto-pull for Tournament Stats
- **Phase 3** (Planned): Advanced features
  - Search, filtering, sorting
  - Data export and analytics
  - CRUD operations for manual data management

See [docs/SPRINT_PLAN.md](docs/SPRINT_PLAN.md) for detailed sprint breakdown.

## Documentation

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - System architecture and design decisions
- [DATA_FORMATS.md](docs/DATA_FORMATS.md) - Import format specifications
- [DEVELOPMENT.md](docs/DEVELOPMENT.md) - Development guide and workflows
- [PHASE1_SCOPE.md](docs/PHASE1_SCOPE.md) - Phase 1 scope and deliverables
- [SPRINT_PLAN.md](docs/SPRINT_PLAN.md) - Sprint-by-sprint implementation plan

## Testing

### Manual Testing

Test the import workflow:
```bash
# 1. Start the app
python app.py

# 2. Navigate to http://127.0.0.1:5000/tools
# 3. Install the bookmarklet
# 4. Visit a BGA player page and run the bookmarklet
# 5. Copy the output and import at http://127.0.0.1:5000/import
# 6. Verify data appears in the database
```

### Verification Commands

```bash
# Check Python dependencies
python -c "import flask; import sqlalchemy; print('OK')"

# Check Flask version
flask --version

# Check Tailwind version
npx tailwindcss --version

# Verify CSS build
cat frontend/static/css/output.css | head -n 10
```

## Troubleshooting

### Tailwind CSS Not Applying

- Ensure `output.css` is built: `npm run build-css`
- Verify templates include: `<link href="/static/css/output.css" rel="stylesheet">`
- Check `tailwind.config.js` content paths

### Import Fails Silently

- Check browser console for JavaScript errors
- Check Flask console for Python exceptions
- Enable Flask debug mode: `$env:FLASK_ENV="development"`

### Database Locked Errors

- Ensure only one Flask process is running
- Close any SQLite browser connections
- SQLite doesn't handle concurrent writes well

## Contributing

This is currently a personal project. For questions or suggestions, please open an issue.

## License

[Your chosen license]

## Current Status

**Completed Features:**
- ✅ Sprints 0-11: Full workflow for Players, Games, and Tournaments
- ✅ Database models for all data types (players, games, stats, matches, tournaments)
- ✅ Parsers for all bookmarklet formats
- ✅ Players list and detail pages with win rate analytics
- ✅ Games list and detail pages with filtering
- ✅ Tournaments list and detail pages with match data
- ✅ Auto-pull for Player Stats, Game List, and Tournament Stats
- ✅ Session management with automatic player ID detection

**Next Up:**
- Sprint 12+: Matches & Moves browsing and auto-pull
- Advanced filtering and search
- Data analytics and visualizations

See [docs/SPRINT_PLAN.md](docs/SPRINT_PLAN.md) for the complete roadmap.
