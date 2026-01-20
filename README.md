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
- **Privacy-Focused**: No BGA credentials stored, uses browser-based data export
- **Comprehensive Stats**: Import player stats, game lists, match details, and tournament data
- **Modern UI**: Built with Tailwind CSS for a clean, responsive interface

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

### 6. Run the Application

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

### Importing Data

1. **Install Bookmarklets**: 
   - Visit the Tools page at `http://127.0.0.1:5000/tools`
   - Drag the "📊 BGA Player Stats" button to your bookmarks bar
   - Or click "Copy Code" for mobile installation

2. **Export from BGA**: 
   - Visit any player profile or group page on BoardGameArena
   - Click the bookmarklet from your bookmarks
   - Wait for the data to be collected and displayed

3. **Copy Data**: 
   - Select all text in the bookmarklet's output box (Ctrl+A / Cmd+A)
   - Copy the text (Ctrl+C / Cmd+C)

4. **Import**: 
   - Navigate to `http://127.0.0.1:5000/import`
   - Paste the data into the textarea
   - Click "Import Data"

5. **Browse**: View your imported statistics in the app

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for detailed import workflow.

## Development Phases

The project is being developed in phases:

- **Phase 1** (Current): Player Stats - Complete vertical slice
  - Player statistics import and browsing
  - Database foundation
  - Basic UI components
- **Phase 2**: Additional import types (Game List, Move Stats, Tournaments)
- **Phase 3**: Advanced features (search, filtering, export, CRUD operations)

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

## Next Steps

After setup, proceed with:
1. Sprint 1: Database models and initialization
2. Sprint 2: Flask application skeleton
3. Sprint 3: Player stats parser

See [docs/SPRINT_PLAN.md](docs/SPRINT_PLAN.md) for the complete roadmap.
