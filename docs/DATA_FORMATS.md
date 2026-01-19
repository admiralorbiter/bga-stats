# BGA Stats App - Data Format Documentation

This document describes the exact import formats accepted by the application, corresponding to outputs from each bookmarklet script.

## Import Types

The application supports four import types, each corresponding to a bookmarklet:

1. **Game List** (`GameList.js`)
2. **Move Stats** (`MoveStats.js`)
3. **Player Stats** (`PlayerStats.js`)
4. **Tournament Stats** (`TournamentStats.js`)

## Format Specifications

### 1. Game List Import

**Source**: `GameList.js`  
**Format**: Tab-Separated Values (TSV)  
**Delimiter**: Tab character (`\t`)  
**Encoding**: UTF-8

#### Format Description

Each line represents one game:
```
BGA_GAME_ID\tINTERNAL_NAME\tDISPLAY_NAME\tSTATUS\tPREMIUM_FLAG
```

#### Column Definitions

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| BGA_GAME_ID | Integer | BGA's internal game ID | `42` |
| INTERNAL_NAME | String | Internal game name (slug) | `ticket` |
| DISPLAY_NAME | String | Human-readable display name | `Ticket to Ride` |
| STATUS | String | Game status: `alpha`, `beta`, `published` | `published` |
| PREMIUM_FLAG | Integer | Premium status: `0` (free) or `1` (premium) | `1` |

#### Example

```
1	chess	Chess	published	0
42	ticket	Ticket to Ride	published	1
100	carcassonne	Carcassonne	published	1
```

#### Header Row

The bookmarklet displays a header in the UI but **does not include it in the export**. The parser should not expect a header row.

### 2. Move Stats Import

**Source**: `MoveStats.js`  
**Format**: Semicolon-Delimited Values  
**Delimiter**: Semicolon (`;`)  
**Encoding**: UTF-8

#### Format Description

Each line represents one move in a match:
```
TABLE_ID;GAME_NAME;MOVE_NO;DATETIME_LOCAL;DATETIME_EXCEL;PLAYER_NAME;REMAINING_TIME
```

#### Column Definitions

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| TABLE_ID | Integer | BGA table ID | `12345678` |
| GAME_NAME | String | Name of the game | `Ticket to Ride` |
| MOVE_NO | Integer or "null" | Move number | `5` |
| DATETIME_LOCAL | String | Localized datetime string | `12/25/2023, 3:45:30 PM` |
| DATETIME_EXCEL | String | Excel serial datetime (comma decimal) | `45278,65625` |
| PLAYER_NAME | String | Player's display name | `JohnDoe` |
| REMAINING_TIME | String | Remaining time (may be empty) | `5m 30s` or empty |

#### Notes

- `MOVE_NO` may be the string `"null"` if move number cannot be determined
- `REMAINING_TIME` may be empty/null for some moves
- `DATETIME_EXCEL` uses comma as decimal separator (European format)
- All rows belong to the same match (same `TABLE_ID` and `GAME_NAME`)

#### Example

```
12345678;Ticket to Ride;1;12/25/2023, 3:00:00 PM;45278,62500;JohnDoe;10m
12345678;Ticket to Ride;2;12/25/2023, 3:05:30 PM;45278,62917;JaneSmith;9m 45s
12345678;Ticket to Ride;3;12/25/2023, 3:10:15 PM;45278,63264;JohnDoe;8m 30s
```

#### Header Row

The bookmarklet displays headers in the UI (`Table ID;Game Name;Move No.;Date Time;Excel Time;Player Name;Remaining Time`) but **does not include them in the export text**. The parser should not expect a header row.

### 3. Player Stats Import

**Source**: `PlayerStats.js`  
**Format**: Tab-Separated Values (TSV)  
**Delimiter**: Tab character (`\t`)  
**Encoding**: UTF-8

#### Format Description

**Important**: This format has a special structure with metadata rows followed by per-game rows.

The first two rows are special metadata rows:
1. **XP Row**: Overall player statistics
2. **Recent Games Row**: Recent match history and last seen

Remaining rows are per-game statistics.

#### Row Type 1: XP (Overall Stats)

```
PLAYER_NAME\tXP\tXP_VALUE\tKARMA_PERCENT\tTOTAL_MATCHES\tTOTAL_WINS
```

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| PLAYER_NAME | String | Player's display name | `JohnDoe` |
| Fixed | String | Always `"XP"` | `XP` |
| XP_VALUE | Integer | Experience points | `45000` |
| KARMA_PERCENT | Integer | Reputation percentage (0-100) | `95` |
| TOTAL_MATCHES | Integer | Total matches played | `1250` |
| TOTAL_WINS | Integer | Total wins | `650` |

#### Row Type 2: Recent Games

```
PLAYER_NAME\tRecent games\tABANDONED\tTIMEOUT\tRECENT_MATCHES\tLAST_SEEN_DAYS
```

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| PLAYER_NAME | String | Player's display name | `JohnDoe` |
| Fixed | String | Always `"Recent games"` | `Recent games` |
| ABANDONED | Integer | Abandoned matches (last 60 days) | `2` |
| TIMEOUT | Integer | Timeout count (last 60 days) | `1` |
| RECENT_MATCHES | Integer | Total recent matches (last 60 days) | `45` |
| LAST_SEEN_DAYS | Integer | Days since last online | `3` |

#### Row Type 3: Per-Game Stats

```
PLAYER_NAME\tGAME_NAME\tELO\tRANK\tMATCHES_PLAYED\tWINS
```

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| PLAYER_NAME | String | Player's display name | `JohnDoe` |
| GAME_NAME | String | Game name | `Ticket to Ride` |
| ELO | String | ELO rating (may include text) | `1500` or `"N/A"` |
| RANK | String | Rank number (empty if unranked) | `42` or `""` |
| MATCHES_PLAYED | Integer | Matches played in this game | `150` |
| WINS | Integer | Wins in this game | `75` |

#### Complete Example

```
JohnDoe	XP	45000	95	1250	650
JohnDoe	Recent games	2	1	45	3
JohnDoe	Ticket to Ride	1500	42	150	75
JohnDoe	Carcassonne	1650	25	200	110
JohnDoe	Chess	1800	10	300	180
```

#### Notes

- Multiple players can be in the same export (each player has XP row, Recent games row, then N game rows)
- XP and Recent games rows use fixed second column values (`"XP"` and `"Recent games"`) to identify them
- `RANK` may be empty string if player is unranked
- `ELO` may contain non-numeric text (e.g., "N/A")
- `LAST_SEEN_DAYS` is calculated and may be 0 if seen today

#### Header Row

The bookmarklet UI shows `Player Name\tGame Name\tELO\tRank\tMatches\tWins` but this is **not included in the export**. The parser must detect the row types by content.

### 4. Tournament Stats Import

**Source**: `TournamentStats.js`  
**Format**: Tab-Separated Values (TSV)  
**Delimiter**: Tab character (`\t`)  
**Encoding**: UTF-8

#### Format Description

**Important**: The first row is a tournament summary row, followed by match detail rows.

#### Row Type 1: Tournament Summary

```
TOURNAMENT_ID\tTOURNAMENT_NAME\t\tGAME_NAME\tSTART_TIME\tEND_TIME\tROUNDS\tROUND_LIMIT\tTOTAL_MATCHES\tTIMEOUT_MATCHES\tPLAYER_COUNT
```

**Note**: There is an empty column (two consecutive tabs) between `TOURNAMENT_NAME` and `GAME_NAME`.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| TOURNAMENT_ID | Integer | BGA tournament ID | `12345` |
| TOURNAMENT_NAME | String | Full tournament name | `Championship 2024 • Ticket to Ride` |
| (empty) | - | Empty column | - |
| GAME_NAME | String | Game name | `Ticket to Ride` |
| START_TIME | String | Start datetime (localized) | `1/1/2024, 12:00:00 AM` |
| END_TIME | String | End datetime (localized) | `1/7/2024, 11:59:59 PM` |
| ROUNDS | Integer | Number of rounds | `7` |
| ROUND_LIMIT | Integer | Round time limit (hours) | `24` |
| TOTAL_MATCHES | Integer | Total match count | `50` |
| TIMEOUT_MATCHES | Integer | Matches that timed out | `3` |
| PLAYER_COUNT | Integer | Number of players | `100` |

#### Row Type 2: Match Details

```
TOURNAMENT_ID\tTABLE_ID\tIS_TIMEOUT\tPROGRESS\tPLAYER1_NAME\tPLAYER1_TIME\tPLAYER1_POINTS\tPLAYER2_NAME\tPLAYER2_TIME\tPLAYER2_POINTS\t...
```

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| TOURNAMENT_ID | Integer | BGA tournament ID | `12345` |
| TABLE_ID | Integer | BGA table ID | `98765432` |
| IS_TIMEOUT | Integer | `1` if timeout, `0` otherwise | `0` |
| PROGRESS | Integer | Match progress percentage (0-100) | `100` |
| PLAYER1_NAME | String | First player's name | `JohnDoe` |
| PLAYER1_TIME | Integer | Remaining time in seconds | `3600` |
| PLAYER1_POINTS | Integer | Points earned | `10` |
| PLAYER2_NAME | String | Second player's name | `JaneSmith` |
| PLAYER2_TIME | Integer | Remaining time in seconds | `3200` |
| PLAYER2_POINTS | Integer | Points earned | `5` |
| ... | ... | Additional players (if >2 players) | ... |

**Note**: Player columns repeat for each player (Name, Time, Points). Matches can have 2+ players.

#### Complete Example (2-player match)

```
12345	Championship 2024 • Ticket to Ride		Ticket to Ride	1/1/2024, 12:00:00 AM	1/7/2024, 11:59:59 PM	7	24	50	3	100
12345	98765432	0	100	JohnDoe	3600	10	JaneSmith	3200	5
12345	98765433	1	75	AliceBob	-300	8	CharlieDave	2800	7
```

#### Notes

- Multiple tournaments can be in the same export
- Each tournament starts with a summary row, followed by its match rows
- `PLAYER_TIME` (remaining_time) can be negative (timeout occurred)
- `PROGRESS` is 100 for completed matches, <100 for timed-out matches
- Match rows have variable column count based on player count

#### Header Row

The bookmarklet UI shows `Tournament ID; Table ID; Timeout; Progress; Player1; Time1; Point1; Player2; Time2; Point2` but this is **not included in the export**. The parser must distinguish summary rows from match rows by column count and content.

## Auto-Detection Rules

The application should attempt to automatically detect the import type based on content analysis:

### Detection Strategy

1. **Game List**:
   - All lines have exactly 5 tab-separated columns
   - First column is numeric (BGA game ID)
   - Last column is 0 or 1 (premium flag)
   - Second column matches typical game slug pattern (lowercase, no spaces)

2. **Move Stats**:
   - All lines use semicolon delimiter (not tab)
   - First column is numeric (table ID)
   - Third column is numeric or "null" (move number)
   - Fifth column contains comma as decimal separator (Excel datetime)

3. **Player Stats**:
   - Uses tab delimiter
   - Contains rows with second column `"XP"` or `"Recent games"`
   - Remaining rows have 6 columns and second column is not fixed
   - At least one XP row and one Recent games row present

4. **Tournament Stats**:
   - Uses tab delimiter
   - First line has 11 columns (tournament summary)
   - Contains rows with variable column count (match rows with player data)
   - First column is numeric (tournament/table ID)

### Fallback

If auto-detection is ambiguous, the UI should require manual selection by the user.

## Validation Rules

### Common Validation

- Empty input is rejected
- All lines must use consistent delimiter (no mixed tabs/semicolons)
- No header rows expected (skip if detected)

### Game List Validation

- All rows must have exactly 5 columns
- Column 1: positive integer
- Column 5: must be `0` or `1`
- Column 4: must be one of: `alpha`, `beta`, `published`

### Move Stats Validation

- All rows must use semicolon delimiter
- Column 1: positive integer (table ID)
- Column 3: integer or string "null"
- Column 5: numeric string with comma decimal (Excel format)

### Player Stats Validation

- Must contain at least one XP row and one Recent games row
- XP rows: second column is `"XP"`, third column is integer
- Recent games rows: second column is `"Recent games"`, all numeric columns are integers
- Game rows: exactly 6 columns, columns 5-6 are integers

### Tournament Stats Validation

- First row must have 11 columns (summary row)
- Match rows have at least 7 columns (base columns + at least 1 player)
- Column 3 (IS_TIMEOUT) must be `0` or `1`
- Column 4 (PROGRESS) must be integer 0-100

## Error Handling

### Parsing Errors

When a line cannot be parsed:
- Log the error with line number and content
- Continue processing remaining lines
- Return partial results with error report

### Validation Errors

When validation fails:
- Provide specific error message (which rule failed, which line if applicable)
- Do not import any data (atomic import)
- Show error summary in UI

### Data Type Errors

When a column cannot be converted to expected type:
- Attempt type coercion (e.g., string to integer)
- If coercion fails, mark field as invalid
- Store as NULL/empty if appropriate, or skip row with error

## Future: JSON Export Format (Phase 2)

In a future phase, bookmarklets may be updated to also output structured JSON with versioning:

```json
{
  "version": "1.0",
  "type": "player_stats",
  "exported_at": "2024-01-15T10:30:00Z",
  "data": {
    ...
  }
}
```

Parsers will be extended to:
1. Detect JSON format (check first character is `{`)
2. Parse version field
3. Route to version-specific parser
4. Fall back to TSV/CSV parsing if JSON invalid