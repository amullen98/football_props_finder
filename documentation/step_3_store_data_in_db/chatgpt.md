


## 🗃️ PostgreSQL Setup & Connection

Before creating the database tables, ensure PostgreSQL is running and accessible.

### Step 1: (Re)Create the database

From the terminal or `psql` shell:
```bash
createdb football_props
```

If `football_props` already exists and you want a clean setup:
```bash
dropdb football_props
createdb football_props
```

### Step 2: Connect from tools (like Cursor or Python)

Use the following configuration:
- Host: `localhost`
- Port: `5432`
- Database: `football_props`
- User: `andrew`

No password is required if using local peer authentication.

Now you're ready to execute the table creation statements.


## 🧱 Database Design: `prop_lines` Table

We will use **one shared table** for both NFL and College Football data, with a `league` column to distinguish between them. This approach keeps queries unified, reduces code duplication, and supports filtering by league.

### Table: `prop_lines`

| Field           | Type        | Notes                                                                 |
|----------------|-------------|-----------------------------------------------------------------------|
| `id`            | SERIAL      | Primary key                                                          |
| `player_id`     | TEXT        | From PrizePicks or generated ID                                      |
| `player_name`   | TEXT        | Full player name                                                     |
| `team`          | TEXT        | Abbreviated team code (e.g., `LSU`, `NE`)                            |
| `opponent`      | TEXT        | Abbreviated opponent team code                                       |
| `position`      | TEXT        | QB, WR, RB                                                           |
| `stat_type`     | TEXT        | e.g., `"Pass Yards"`, `"Receiving Yards"`                            |
| `line_score`    | NUMERIC     | The projection line (e.g., 235.5)                                    |
| `game_time`     | TIMESTAMP   | ISO datetime string                                                  |
| `league`        | TEXT        | `"nfl"` or `"college"`                                               |
| `source`        | TEXT        | e.g., `"PrizePicks"`                                                 |
| `odds_type`     | TEXT        | e.g., `"standard"`, `"flex"`                                         |
| `season`        | INTEGER     | e.g., 2025                                                           |
| `projection_id` | TEXT        | Original projection UUID                                             |
| `created_at`    | TIMESTAMP   | Timestamp of data insertion (auto-filled by DB)                      |

### Why One Table?

- All fields are shared across NFL and CFB
- `league` allows easy filtering
- Enables unified querying and reporting
- Cleaner ingestion and API design

---


---

## 📘 Table: `player_stats`

This table stores actual player performance stats gathered weekly from CollegeFootballData and NFL RapidAPI sources. It complements the `prop_lines` table by representing what players actually achieved.

| Field            | Type      | Notes                                                                 |
|------------------|-----------|-----------------------------------------------------------------------|
| `id`             | SERIAL    | Primary key                                                          |
| `player_id`      | TEXT      | Links to player identity (consistent with `prop_lines`)              |
| `player_name`    | TEXT      | Redundant but helpful for querying                                   |
| `team`           | TEXT      | Team name or abbreviation                                            |
| `opponent`       | TEXT      | Opponent team name or abbreviation                                   |
| `position`       | TEXT      | QB, WR, RB                                                           |
| `stat_type`      | TEXT      | `"passing"` or `"receiving"`                                        |
| `passing_yards`  | NUMERIC   | Nullable — only for QBs                                              |
| `completions`    | INTEGER   | Nullable — only for QBs                                              |
| `attempts`       | INTEGER   | Nullable — only for QBs                                              |
| `receiving_yards`| NUMERIC   | Nullable — only for WRs and RBs                                      |
| `receptions`     | INTEGER   | Nullable — only for WRs and RBs                                      |
| `targets`        | INTEGER   | Nullable — only for WRs and RBs                                      |
| `game_id`        | TEXT      | Foreign key to game metadata                                         |
| `season`         | INTEGER   | e.g., 2023                                                           |
| `league`         | TEXT      | `"college"` or `"nfl"`                                               |
| `source`         | TEXT      | `"CollegeFootballData"` or `"RapidAPI"`                              |
| `created_at`     | TIMESTAMP | Auto-filled at time of insert                                        |

This schema supports all tracked positions and stat types across leagues. Fields are normalized but flexible for different stat categories.

---

## 📘 Table: `games_processed`

This table stores the list of game IDs that have been processed for a given league, week, and season. It helps prevent redundant ingestion and supports referencing stats or projections by game context.

| Field         | Type      | Notes                                           |
|---------------|-----------|-------------------------------------------------|
| `id`          | SERIAL    | Primary key                                     |
| `game_id`     | TEXT      | Unique game ID from the source API              |
| `week`        | INTEGER   | Week number of the season                       |
| `year`        | INTEGER   | Season year (e.g., 2023)                        |
| `league`      | TEXT      | `"nfl"` or `"college"`                          |
| `source`      | TEXT      | Source of the game ID (e.g., `"RapidAPI"`)     |
| `created_at`  | TIMESTAMP | Auto-filled timestamp at time of insertion      |


---

## 📘 Table: `players`

This table stores player metadata that can be reused across both props and stat tracking, useful for linking aliases or additional player info in the future.

| Field         | Type      | Notes                                       |
|---------------|-----------|---------------------------------------------|
| `id`          | SERIAL    | Primary key                                 |
| `player_id`   | TEXT      | External player ID (used in other tables)   |
| `name`        | TEXT      | Full player name                            |
| `position`    | TEXT      | QB, WR, RB, etc.                            |
| `team`        | TEXT      | Team abbreviation                           |
| `league`      | TEXT      | `"nfl"` or `"college"`                      |
| `source`      | TEXT      | Source of the player info (e.g., `"PP"`)    |
| `created_at`  | TIMESTAMP | Timestamp of record creation                |

---

## 📘 Table: `teams`

This table stores metadata about each team, helpful for matching abbreviations and enriching opponent lookups.

| Field         | Type      | Notes                                         |
|---------------|-----------|-----------------------------------------------|
| `id`          | SERIAL    | Primary key                                   |
| `name`        | TEXT      | Full team name (e.g., "Alabama Crimson Tide") |
| `abbreviation`| TEXT      | Short team code (e.g., "ALA", "KC")           |
| `league`      | TEXT      | `"nfl"` or `"college"`                        |
| `source`      | TEXT      | Source of the team info                       |
| `created_at`  | TIMESTAMP | Auto-filled timestamp                         |

These two reference tables will support cleaner joins, deduplication, and more flexible lookup logic across different datasets.

---

## 🔄 Data Ingestion Mapping

Once parsing is complete, insert data into these tables:

- `prop_lines`: For all player projections (PrizePicks CFB/NFL).
  - Use fields like: `player_id`, `player_name`, `team`, `opponent`, `position`, `stat_type`, `line_score`, `game_time`, `league`, `source`, `odds_type`, `season`, `projection_id`.

- `player_stats`: For actual performance stats (CollegeFootballData + NFL RapidAPI).
  - Use: `player_id`, `player_name`, `team`, `opponent`, `position`, `stat_type`, appropriate stat values (e.g., `passing_yards`, `receptions`), `game_id`, `season`, `league`, `source`.

- `games_processed`: For tracking already ingested game IDs by `week`, `season`, and `league`.

- `players`: Optional metadata table for reusable player info.

- `teams`: Optional team reference table used during normalization.

Each parser should return a dictionary structure matching the destination table fields.