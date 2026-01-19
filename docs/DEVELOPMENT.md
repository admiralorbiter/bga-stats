# BGA Stats App - Development Guide

This guide covers local setup, running the application, and the complete import workflow.

## Prerequisites

- Python 3.8 or higher
- Node.js 16+ and npm (for Tailwind CSS build)
- Git (for version control)

## Local Setup

### 1. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Windows (CMD):
venv\Scripts\activate.bat
# Linux/Mac:
source venv/bin/activate
```

### 2. Install Python Dependencies

Create `requirements.txt` with:
```
Flask>=2.3.0
SQLAlchemy>=2.0.0
```

Then install:
```bash
pip install -r requirements.txt
```

### 3. Install Tailwind CSS

#### Option A: Using Tailwind CLI (Recommended)

```bash
# Install Tailwind CSS CLI globally
npm install -g tailwindcss

# Initialize Tailwind config in project root
tailwindcss init

# Create input CSS file: frontend/static/css/input.css
```

#### Option B: Using npm scripts

```bash
# Initialize package.json in project root
npm init -y

# Install Tailwind as dev dependency
npm install -D tailwindcss

# Initialize Tailwind
npx tailwindcss init
```

### 4. Configure Tailwind

Edit `tailwind.config.js`:
```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./frontend/templates/**/*.html",
    "./frontend/static/js/**/*.js",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

Create `frontend/static/css/input.css`:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

### 5. Build Tailwind CSS

```bash
# Build CSS (run this whenever you change Tailwind classes)
tailwindcss -i ./frontend/static/css/input.css -o ./frontend/static/css/output.css --watch
```

Or add to `package.json` scripts:
```json
{
  "scripts": {
    "build-css": "tailwindcss -i ./frontend/static/css/input.css -o ./frontend/static/css/output.css",
    "watch-css": "tailwindcss -i ./frontend/static/css/input.css -o ./frontend/static/css/output.css --watch"
  }
}
```

### 6. Project Structure

After setup, your project should look like:
```
bga-stats/
├── backend/
│   ├── app.py
│   ├── models.py
│   ├── parsers/
│   ├── routes/
│   └── services/
├── frontend/
│   ├── templates/
│   └── static/
│       ├── css/
│       │   ├── input.css
│       │   └── output.css
│       └── js/
├── docs/
├── venv/
├── requirements.txt
├── tailwind.config.js
└── README.md
```

## Running the Application

### Development Mode

```bash
# Activate virtual environment
# Windows: .\venv\Scripts\Activate.ps1
# Linux/Mac: source venv/bin/activate

# Set Flask environment variables (optional, for development)
# Windows PowerShell:
$env:FLASK_APP="backend/app.py"
$env:FLASK_ENV="development"
# Linux/Mac:
export FLASK_APP=backend/app.py
export FLASK_ENV=development

# Run Flask development server
flask run
# Or: python -m flask run
# Or: python backend/app.py (if __main__ block configured)
```

The application will be available at `http://127.0.0.1:5000`

### Production Mode

For production-like setup:
```bash
# Use production WSGI server (e.g., gunicorn)
pip install gunicorn
gunicorn -w 4 backend.app:app
```

## Database Initialization

### First Run

On first run, the database will be created automatically via SQLAlchemy:

```python
# In app.py or models.py
from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bga_stats.db'

# Initialize database
from backend.models import Base, engine
Base.metadata.create_all(engine)
```

### Database Location

SQLite database file: `bga_stats.db` (in project root or configurable path)

### Database Migrations

For schema changes, use Flask-Migrate (optional):

```bash
pip install flask-migrate

# Initialize migrations
flask db init

# Create migration
flask db migrate -m "Description"

# Apply migration
flask db upgrade
```

## Import Workflow

### Step 1: Run Bookmarklet on BGA

1. **Log into BoardGameArena** in your browser
2. Navigate to the appropriate page:
   - **Game List**: `https://boardgamearena.com/gamelist`
   - **Player Stats**: `https://boardgamearena.com/player?id=12345` or group page
   - **Move Stats**: `https://boardgamearena.com/gamereview?table=12345678`
   - **Tournament Stats**: `https://boardgamearena.com/tournament?id=12345`
3. **Run the corresponding bookmarklet**:
   - Click the bookmarklet in your browser's bookmarks bar
   - Or copy/paste the bookmarklet code into browser console
4. **Wait for export to complete**:
   - Bookmarklet will populate a textarea with the export data
   - Some bookmarklets (PlayerStats, TournamentStats) show "Loading..." progress

### Step 2: Copy Export Data

1. **Select all text** in the export textarea (Ctrl+A / Cmd+A)
2. **Copy** the text (Ctrl+C / Cmd+C)
3. Or use the "Select All" functionality if the bookmarklet provides it

### Step 3: Import into Flask App

1. **Navigate to import page**: `http://127.0.0.1:5000/import`
2. **Choose import method**:
   - **Option A**: Paste into text area
     - Click in the textarea
     - Paste (Ctrl+V / Cmd+V)
   - **Option B**: Upload file
     - Click "Choose File" or drag-and-drop
     - Select a `.txt`, `.tsv`, or `.csv` file containing the export
3. **Select import type** (if auto-detection is ambiguous):
   - Game List
   - Move Stats
   - Player Stats
   - Tournament Stats
4. **Click "Import"** button
5. **Review import results**:
   - Success message with record counts
   - Error summary if validation fails
   - Preview of imported data (optional)

### Step 4: Browse Imported Data

After successful import:
- Navigate to **Games** page to see imported games
- Navigate to **Players** page to see imported players
- Navigate to **Matches** page to see imported matches
- Navigate to **Tournaments** page to see imported tournaments

## Development Workflow

### Making Changes

1. **Backend changes**:
   - Edit Python files in `backend/`
   - Flask auto-reloads on file changes (in development mode)
   - Restart server if needed

2. **Frontend changes**:
   - Edit HTML templates in `frontend/templates/`
   - Edit JavaScript in `frontend/static/js/`
   - Rebuild Tailwind CSS if class changes: `npm run build-css`

3. **Database schema changes**:
   - Update models in `backend/models.py`
   - Create migration (if using Flask-Migrate)
   - Or manually recreate database: delete `bga_stats.db` and restart app

### Testing

#### Manual Testing

1. **Import Testing**:
   - Use sample export data from bookmarklets
   - Test each import type
   - Verify data appears correctly in browse pages

2. **Validation Testing**:
   - Test with invalid/malformed input
   - Verify error messages are helpful
   - Test edge cases (empty rows, missing columns)

#### Automated Testing (Optional)

Create `tests/` directory and use pytest:

```bash
pip install pytest pytest-flask

# Run tests
pytest
```

### Debugging

#### Flask Debug Mode

Ensure `FLASK_ENV=development` is set for:
- Auto-reload on code changes
- Detailed error pages
- Debug toolbar (if installed)

#### Database Inspection

Use SQLite browser or command-line:

```bash
# Install sqlite3 CLI (usually pre-installed)
sqlite3 bga_stats.db

# Browse tables
.tables

# Query data
SELECT * FROM players LIMIT 10;
```

#### Logging

Add logging to Flask app:

```python
import logging
app.logger.setLevel(logging.DEBUG)
app.logger.debug('Debug message')
```

## Common Issues

### Issue: Tailwind CSS not applying

**Solution**:
- Ensure `output.css` is built: `npm run build-css`
- Check that HTML includes: `<link href="/static/css/output.css" rel="stylesheet">`
- Verify `tailwind.config.js` content paths include your templates

### Issue: Import fails silently

**Solution**:
- Check browser console for JavaScript errors
- Check Flask console for Python exceptions
- Enable Flask debug mode for detailed error pages
- Review parser logs for validation errors

### Issue: Database locked errors

**Solution**:
- Ensure only one Flask process is running
- Close any SQLite browser connections
- SQLite doesn't handle concurrent writes well

### Issue: Bookmarklet output format changed

**Solution**:
- Update corresponding parser in `backend/parsers/`
- Test with new export format
- Update `docs/DATA_FORMATS.md` if format changed

## Deployment Notes

### Local-First Deployment

Since this is a local-first app:
- Users run it on their own machine
- No need for cloud hosting
- Consider creating an installer (e.g., PyInstaller) for non-technical users

### PyInstaller Example (Optional)

```bash
pip install pyinstaller

# Create executable
pyinstaller --onefile --add-data "frontend;frontend" backend/app.py

# Result: standalone executable that users can run
```

## Environment Variables

Optional configuration via environment variables:

```bash
# Database path (default: bga_stats.db in project root)
export DATABASE_PATH=/path/to/database.db

# Flask secret key (for sessions)
export SECRET_KEY=your-secret-key-here

# Debug mode
export FLASK_ENV=development
```

Access in Flask:
```python
import os
app.config['DATABASE_PATH'] = os.getenv('DATABASE_PATH', 'bga_stats.db')
```

## Next Steps

After completing Phase 0 (documentation):
1. Implement Flask app scaffolding
2. Create database models
3. Implement first parser (Player Stats recommended)
4. Build import UI
5. Build browse UI for imported data