


# PRD – Data Parsing for API Integration (PrizePicks, CollegeFootballData, NFL RapidAPI)

## ✅ Overview

We are implementing the data parsing logic for all external APIs used in the football gambling project. Each parser should extract structured dictionaries that can later be inserted into the database, used in the suggestion engine, and displayed on the UI. This PRD defines the parsing logic for:

- PrizePicks NFL Projections  
- College Football Player Stats  
- NFL Game ID List  
- NFL Box Score Player Stats  

## 🔧 Requirements (General)

- Each parser should:
  - Output a list of Python dictionaries, one per record
  - Include key fields: player name, stat type, value, game context
  - Be ready for database insertion
  - Print or return output for manual inspection
- Create a folder `parsers/` and put each parser in its own file:
  - `parse_prizepicks.py`
  - `parse_cfb_stats.py`
  - `parse_nfl_game_ids.py`
  - `parse_nfl_boxscore.py`

---

## 🔍 PrizePicks NFL Projections

**Source:** `nfl_projections.json`  
**Structure:**
- `data[]`: contains projections and references to players, teams, markets
- `included[]`: metadata (`type == "new_player"`, `"team"`, `"market"`)

**Steps:**
1. Create lookup dictionaries from `included[]`
2. Loop through `data[]`:
   - Extract:
     - `player_name` (from `new_player`)
     - `team` (from `team`)
     - `stat_type` and `line_score`
     - `game_time` and `opponent` (from `market`)
     - `projection_id`

**Output Example:**
```json
{
  "player_name": "Josh Allen",
  "team": "BUF",
  "opponent": "NYJ",
  "stat_type": "pass_yards",
  "line_score": 248.5,
  "game_time": "2024-09-10T17:00:00Z",
  "projection_id": "11370225"
}
```

---

## 🏈 College Football Player Stats

**Source:** `players_2023_week1_regular.json`  
**Filter positions:** `"QB"`, `"WR"`, `"RB"`  
**Note:** For RBs, track `receivingYards` only

**Steps:**
- Loop through all entries:
  - Filter by position
  - For QBs: get `passYards`, `completions`, etc.
  - For WRs: get `receivingYards`, `receptions`, etc.
  - For RBs: extract only `receivingYards`
  - Also include `week`, `gameId`, `startTime`, `opponent`

**Output Example:**
```json
{
  "player": "Drake Maye",
  "team": "North Carolina",
  "opponent": "South Carolina",
  "position": "QB",
  "week": 1,
  "game_id": "401547353",
  "passYards": 269,
  "completions": 24,
  "att": 36,
  "passTD": 2,
  "start_time": "2023-09-02T23:30:00.000Z"
}
```

---

## 📋 NFL Game ID List

**Source:** `games_2023_week1_type2.json`  
**Structure:**  
`{ "items": [{ "eventid": "401547353" }, ...] }`

**Steps:**
- Extract `eventid` from each item
- Return a flat list of game IDs

**Output Example:**
```json
{
  "week": 1,
  "year": 2023,
  "game_ids": [
    "401547353",
    "401547403",
    "401547397"
  ]
}
```

---

## 📊 NFL Box Score Player Stats

**Source:** `boxscore_<eventid>.json`  
**Endpoint:** `https://nfl-api-data.p.rapidapi.com/nfl-boxscore?id=<eventid>`

**Steps:**
- Iterate over `players.items()`
- For each player:
  - If position is `"QB"`, `"WR"`, or `"RB"`:
    - For **QB**: extract from `passing` → `yards`, `completions`, `attempts`, `touchdowns`, `interceptions`
    - For **WR**: extract from `receiving` → `yards`, `receptions`, `targets`, `touchdowns`
    - For **RB**: extract only `receiving.yards`

**Output Example:**
```json
{
  "player": "Christian McCaffrey",
  "team": "SF",
  "position": "RB",
  "game_id": "401220225",
  "stat_type": "receiving",
  "receiving_yards": 43
}
```