# Playwright Auto-Pull Setup Guide

This guide covers setting up and using the Playwright-based auto-pull feature to automatically fetch data from BoardGameArena without manual copy/paste.

## Installation

### 1. Install Python Dependencies

```bash
# Activate virtual environment
# Windows: .\venv\Scripts\Activate.ps1
# Linux/Mac: source venv/bin/activate

# Install updated dependencies (includes Playwright)
pip install -r requirements.txt
```

### 2. Install Playwright Browsers

Playwright requires browser binaries to be installed. Run this one-time setup command:

```bash
playwright install chromium
```

This downloads the Chromium browser that Playwright will use to access BGA.

**Note**: This is a ~200MB download and takes a few minutes.

## Usage

### First-Time Login

1. **Start the application**:
   ```bash
   python app.py
   ```

2. **Navigate to Sync page**: `http://127.0.0.1:5000/sync`

3. **Click "Login to BGA"**:
   - A browser window will open automatically
   - Log in to your BoardGameArena account as you normally would
   - Wait for the page to fully load (you should see your player menu)
   - The browser will close automatically and your session will be saved

4. **Session saved**: Your login session is now saved locally in `.bga_session/session_state.json`

### Pulling Data

Once logged in, you can pull data automatically:

#### Player Statistics

**Single Player**:
```
Enter player ID: 12345
Click "Pull Player Stats"
```

**Multiple Players**:
```
Enter comma-separated IDs: 12345,67890,54321
Click "Pull Player Stats"
```

**Group Members**:
```
Enter: group:123 (or g:123)
Click "Pull Player Stats"
```

The app will:
1. Navigate to each player's profile page
2. Extract all statistics (XP, karma, per-game stats)
3. Automatically import the data into the database
4. Show results (players created/updated, games added, etc.)

### Session Management

**Validate Session**: Check if your saved session is still active
- Click "Validate Session" button
- Useful if you haven't used the app in a while

**Clear Session**: Log out and clear saved credentials
- Click "Clear Session" button
- You'll need to log in again before pulling data

## Features

### Automatic Rate Limiting

The pull service automatically:
- Waits 1 second between each player profile request
- Prevents overwhelming BGA servers
- Shows progress during multi-player pulls

### Session Persistence

Your login session is saved locally and reused:
- No need to log in every time
- Session stored in `.bga_session/` (added to .gitignore)
- Local-only, never sent anywhere

### Error Handling

The system handles common errors:
- Session expired → prompts to log in again
- Network issues → displays error message
- Invalid player IDs → shows validation error

## Supported Data Types

### Currently Implemented

- ✅ **Player Stats**: Fully automated pull and import
  - Overall stats (XP, karma, matches, wins)
  - Per-game statistics (ELO, rank, played, won)
  - Recent game history

### Coming Soon

- 🚧 **Game List**: Pull complete list of BGA games
- 🚧 **Move Stats**: Extract move-by-move game data
- 🚧 **Tournament Stats**: Pull tournament match data

## Architecture

### How It Works

```
User → Login Once → Saved Session
                       ↓
User requests pull → Playwright Browser
                       ↓
                    Navigate BGA Pages
                       ↓
                    Extract Data
                       ↓
                    TSV Format
                       ↓
                    Existing Import Pipeline
                       ↓
                    SQLite Database
```

### Key Components

1. **BGASessionService** (`backend/services/bga_session_service.py`)
   - Manages Playwright browser sessions
   - Saves/loads authentication state
   - Validates sessions

2. **BGAPullBase** (`backend/services/bga_pull_base.py`)
   - Base class for data pulling
   - Rate limiting
   - Safe navigation and extraction

3. **BGAPlayerStatsPuller** (`backend/services/bga_pull_player_stats.py`)
   - Navigates player/group pages
   - Extracts stats data
   - Formats as TSV for import

4. **Import Pipeline** (existing)
   - Parses TSV data
   - Validates and normalizes
   - Upserts to database

## Comparison: Auto-Pull vs Manual Import

| Feature | Manual (Bookmarklet) | Auto-Pull (Playwright) |
|---------|---------------------|------------------------|
| Login required | Yes, in your browser | Yes, once in Playwright |
| Copy/paste needed | Yes, every import | No |
| Group members | Manual list | Auto-discovered |
| Rate limiting | User-controlled | Automatic |
| Session persistence | Browser cookies | Local file |
| Offline use | After export | Requires network |

## Troubleshooting

### "Login timeout or cancelled"

**Cause**: Didn't complete login within 5 minutes
**Solution**: Click "Login to BGA" again and complete login faster

### "Session is invalid or expired"

**Cause**: BGA session expired (typically after 30 days)
**Solution**: Click "Clear Session" then "Login to BGA" to create new session

### "Failed to load session"

**Cause**: Session file corrupted
**Solution**: 
```bash
# Delete session file
rm -rf .bga_session
# Or on Windows:
rmdir /s .bga_session
```
Then log in again.

### "Playwright browser not installed"

**Cause**: Forgot to run `playwright install`
**Solution**: 
```bash
playwright install chromium
```

## Privacy & Security

### Local-Only Storage

- Session data stored in `.bga_session/session_state.json`
- Never sent to any server
- Contains BGA cookies/tokens
- Automatically excluded from git (.gitignore)

### What's Stored

The session file contains:
- BGA authentication cookies
- Local storage data
- Browser context state

### Recommendations

1. Don't share your `.bga_session/` folder
2. Clear session when done if on shared computer
3. Session file is as sensitive as your BGA password - protect it

## Performance

### Speed

- First login: ~5-30 seconds (manual login)
- Subsequent pulls: ~1-2 seconds per player (rate-limited)
- Group of 10 players: ~15-20 seconds total

### Resource Usage

- Browser memory: ~100-200MB during pull
- Browser automatically closed after each operation
- No persistent browser process

## Advanced Usage

### Custom Rate Limiting

Edit `backend/services/bga_pull_base.py`:

```python
# Default is 1 second between requests
rate_limiter = RateLimiter(min_delay_seconds=2.0)  # Slower
```

### Headless vs Headed Mode

Login always uses headed (visible) mode so you can log in.
Pull operations use headless mode (no visible browser).

To debug, edit `bga_session_service.py`:
```python
browser = self.create_browser(headless=False)  # Show browser
```

## Future Enhancements

Planned improvements:

- Background task queue for large pulls
- Progress bars for multi-player imports
- Scheduled auto-sync
- Email notifications on import completion
- Pull history/audit log
