

# 🏈 Football Prop Insights – Project Overview

## 🚀 Goal
Build a system that tracks quarterback (QB) and wide receiver (WR) prop betting lines and performance stats from multiple data sources (NFL and college), stores that data in a PostgreSQL database, and generates weekly over/under betting suggestions. Optionally, a frontend dashboard may be created to visualize insights.

---

## 📦 Scope

### 1. Data Sources

**Betting Lines**
- **PrizePicks API** (No auth required)  
  `https://api.prizepicks.com/projections?league_id=9&per_page=250&single_stat=true&in_game=true&state_code=CA&game_mode=pickem`

- **Underdog Fantasy API** (No auth required)  
  `https://api.underdogfantasy.com/beta/v6/over_under_lines`

**Player Performance Stats**
- **NFL API (RapidAPI - Creativesdev)**
  - Game/Event IDs:  
    `https://nfl-api-data.p.rapidapi.com/nfl-weeks-events?year=2023&week=1&type=2`
  - Player Box Scores:  
    `https://nfl-api-data.p.rapidapi.com/nfl-boxscore?eventId=<GAME_ID>`
  - Auth via RapidAPI key

- **College Football Data API**
  - Game stats by week:  
    `https://api.collegefootballdata.com/games/players?year=<YEAR>&week=<WEEK>&seasonType=regular`
  - Auth via personal API key (`CFB_API_KEY`)

---

## 🧠 Key Features (By Step)

### ✅ Step 1: API Connectivity
- Call and print data from each external API:
  - 1a. PrizePicks
  - 1b. Underdog
  - 2a. NFL stats (via RapidAPI)
  - 2b. College stats (via CollegeFootballData)
- Return raw data to the terminal or log it for inspection
- Include test functions to validate each API returns data successfully

### ✅ Step 2: Data Parsing
- Parse relevant information into dictionaries:
  - For props: player name, team, opponent, prop line, date, platform
  - For stats: player name, team, opponent, passing/receiving yards, completions, attempts, TDs
- Include manual test functions to print the parsed dictionaries

### ✅ Step 3: Database Integration
- PostgreSQL schema with SQLAlchemy
- Tables: `qb_props`, `qb_stats`, `wr_props`, `wr_stats`, `defense_stats`, `suggestions`
- Insert parsed dictionaries into database
- Include CLI or FastAPI routes to verify inserts

### ✅ Step 4: Suggestion Engine
- Compare prop lines vs. recent performance + defensive matchup
- Output suggestion (Over/Under/No Play), confidence score, and notes
- Store in `suggestions` table
- Create a test runner to validate logic against sample data

### ✅ Step 5: Optional Web Dashboard
- View QB/WR suggestions with confidence levels and filters
- Show historical stats, accuracy tracking, defensive matchups
- Manual triggers for data ingestion
- Deploy via Vercel or Netlify if needed

---

## 🧪 Testing & Validation
Each step includes:
- Manual test functions for local validation
- FastAPI endpoints (e.g., `/fetch/qb-props`) for easy triggering
- Logging to file or stdout

---

## 🔧 Tech Stack
- **Python 3.11+**
- **FastAPI** (for endpoints)
- **SQLAlchemy** + **PostgreSQL** (for persistence)
- **Requests** (for API calls)
- **APScheduler** (optional, for scheduling tasks)
- **Jinja or React** (for frontend, optional)