-- ============================================================================
-- Football Props Finder - Database Schema Creation Script
-- ============================================================================
-- This script creates all necessary tables for storing prop betting lines,
-- player statistics, and metadata for the Football Props Finder project.
--
-- Usage: psql -h localhost -d football_props -f setup_database.sql
-- ============================================================================

-- Ensure we're connected to the correct database
\echo 'Creating tables in database:' :DBNAME

-- ============================================================================
-- Table: prop_lines
-- Stores prop betting lines from various sources (PrizePicks, etc.)
-- ============================================================================

CREATE TABLE IF NOT EXISTS prop_lines (
    id SERIAL PRIMARY KEY,
    player_id TEXT NOT NULL,
    player_name TEXT NOT NULL,
    team TEXT NOT NULL,
    opponent TEXT,
    position TEXT NOT NULL CHECK (position IN ('QB', 'WR', 'RB', 'TE')),
    stat_type TEXT NOT NULL,
    line_score NUMERIC,
    game_time TIMESTAMP,
    league TEXT NOT NULL CHECK (league IN ('nfl', 'college')),
    source TEXT NOT NULL,
    odds_type TEXT DEFAULT 'standard',
    season INTEGER NOT NULL CHECK (season >= 2000 AND season <= 2030),
    projection_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_prop_lines_player_id ON prop_lines(player_id);
CREATE INDEX IF NOT EXISTS idx_prop_lines_league_season ON prop_lines(league, season);
CREATE INDEX IF NOT EXISTS idx_prop_lines_team ON prop_lines(team);
CREATE INDEX IF NOT EXISTS idx_prop_lines_game_time ON prop_lines(game_time);
CREATE INDEX IF NOT EXISTS idx_prop_lines_stat_type ON prop_lines(stat_type);

-- ============================================================================
-- Table: player_stats
-- Stores actual player performance statistics from games
-- ============================================================================

CREATE TABLE IF NOT EXISTS player_stats (
    id SERIAL PRIMARY KEY,
    player_id TEXT NOT NULL,
    player_name TEXT NOT NULL,
    team TEXT NOT NULL,
    opponent TEXT,
    position TEXT NOT NULL CHECK (position IN ('QB', 'WR', 'RB', 'TE')),
    stat_type TEXT NOT NULL CHECK (stat_type IN ('passing', 'receiving', 'rushing')),
    
    -- QB-specific stats (nullable for non-QBs)
    passing_yards NUMERIC,
    completions INTEGER,
    attempts INTEGER,
    passing_touchdowns INTEGER,
    interceptions INTEGER,
    sacks INTEGER,
    sack_yards_lost INTEGER,
    
    -- WR/RB-specific stats (nullable for QBs)
    receiving_yards NUMERIC,
    receptions INTEGER,
    targets INTEGER,
    receiving_touchdowns INTEGER,
    
    -- RB-specific stats (nullable for others)
    rushing_yards NUMERIC,
    rushing_attempts INTEGER,
    rushing_touchdowns INTEGER,
    
    -- Game metadata
    game_id TEXT NOT NULL,
    week INTEGER,
    game_date DATE,
    season INTEGER NOT NULL CHECK (season >= 2000 AND season <= 2030),
    league TEXT NOT NULL CHECK (league IN ('nfl', 'college')),
    source TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_player_stats_player_id ON player_stats(player_id);
CREATE INDEX IF NOT EXISTS idx_player_stats_game_id ON player_stats(game_id);
CREATE INDEX IF NOT EXISTS idx_player_stats_league_season ON player_stats(league, season);
CREATE INDEX IF NOT EXISTS idx_player_stats_team ON player_stats(team);
CREATE INDEX IF NOT EXISTS idx_player_stats_week ON player_stats(week);
CREATE INDEX IF NOT EXISTS idx_player_stats_position ON player_stats(position);

-- ============================================================================
-- Table: games_processed
-- Tracks which games have been processed to prevent duplicate ingestion
-- ============================================================================

CREATE TABLE IF NOT EXISTS games_processed (
    id SERIAL PRIMARY KEY,
    game_id TEXT NOT NULL UNIQUE,
    week INTEGER NOT NULL,
    year INTEGER NOT NULL CHECK (year >= 2000 AND year <= 2030),
    league TEXT NOT NULL CHECK (league IN ('nfl', 'college')),
    source TEXT NOT NULL,
    game_type INTEGER DEFAULT 2, -- For NFL: 1=preseason, 2=regular, 3=postseason
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for tracking and lookup
CREATE INDEX IF NOT EXISTS idx_games_processed_league_year_week ON games_processed(league, year, week);
CREATE INDEX IF NOT EXISTS idx_games_processed_source ON games_processed(source);

-- ============================================================================
-- Table: players
-- Reference table for player metadata and deduplication
-- ============================================================================

CREATE TABLE IF NOT EXISTS players (
    id SERIAL PRIMARY KEY,
    player_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    position TEXT CHECK (position IN ('QB', 'WR', 'RB', 'TE', 'K', 'DEF')),
    team TEXT,
    league TEXT NOT NULL CHECK (league IN ('nfl', 'college')),
    source TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for player lookups
CREATE INDEX IF NOT EXISTS idx_players_name ON players(name);
CREATE INDEX IF NOT EXISTS idx_players_team_league ON players(team, league);
CREATE INDEX IF NOT EXISTS idx_players_position ON players(position);

-- ============================================================================
-- Table: teams
-- Reference table for team metadata and abbreviation normalization
-- ============================================================================

CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    abbreviation TEXT NOT NULL,
    league TEXT NOT NULL CHECK (league IN ('nfl', 'college')),
    conference TEXT, -- For college: SEC, Big 10, etc. For NFL: AFC, NFC
    division TEXT,   -- For college: East, West, etc. For NFL: North, South, East, West
    source TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure unique team abbreviations per league
    UNIQUE(abbreviation, league)
);

-- Create indexes for team lookups
CREATE INDEX IF NOT EXISTS idx_teams_abbreviation ON teams(abbreviation);
CREATE INDEX IF NOT EXISTS idx_teams_league ON teams(league);
CREATE INDEX IF NOT EXISTS idx_teams_name ON teams(name);

-- ============================================================================
-- Create triggers for updated_at timestamps
-- ============================================================================

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to players table
CREATE TRIGGER update_players_updated_at 
    BEFORE UPDATE ON players 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Summary and verification
-- ============================================================================

-- Display created tables
\echo ''
\echo '============================================================================'
\echo 'Database schema creation completed!'
\echo '============================================================================'
\echo ''

-- List all created tables
\echo 'Created tables:'
\dt

\echo ''
\echo 'Table sizes (should all be 0 for new setup):'
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats 
WHERE schemaname = 'public' 
    AND tablename IN ('prop_lines', 'player_stats', 'games_processed', 'players', 'teams')
ORDER BY tablename, attname;

\echo ''
\echo '============================================================================'
\echo 'Setup complete! Ready for data insertion.'
\echo '============================================================================'