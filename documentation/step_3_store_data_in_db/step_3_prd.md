# Product Requirements Document: Database Storage Layer

## Introduction/Overview

This PRD defines the implementation of a PostgreSQL-based storage layer for the Football Prop Insights project. The database will store both prop betting lines and actual player performance statistics, enabling comprehensive analysis and future prop suggestion capabilities. The system will create a unified storage solution that accepts data from our existing parsers (PrizePicks, College Football Data, NFL RapidAPI) and stores it in normalized, queryable tables.

**Problem Statement:** Currently, all football data exists only as parsed JSON files. We need a persistent, queryable database to support analysis, historical tracking, and prop suggestion algorithms.

**Goal:** Create a robust PostgreSQL database layer with all necessary tables, insertion functions, and validation to store parsed football data from multiple sources.

## Goals

1. **Persistent Data Storage:** Create PostgreSQL tables to store prop lines, player stats, and metadata
2. **Data Integration:** Enable seamless insertion of data from existing parsers without modification
3. **Data Quality:** Implement validation to ensure clean, consistent data across all sources
4. **Query Flexibility:** Design schema to support complex analysis queries and reporting
5. **Scalable Architecture:** Create modular database functions that can handle different insertion patterns
6. **Development Efficiency:** Provide clear setup instructions and validation tools for rapid development

## User Stories

**As a developer**, I want to insert parsed PrizePicks data into the database so that prop lines are permanently stored and queryable.

**As a developer**, I want to insert NFL and College Football player stats so that actual performance data is available for analysis.

**As a data analyst**, I want to query player performance vs prop lines so that I can identify betting opportunities and patterns.

**As a developer**, I want validation functions so that bad data doesn't corrupt the database.

**As a developer**, I want batch insertion capabilities so that weekly data loads are efficient.

**As a project maintainer**, I want clear setup instructions so that the database can be recreated on any development machine.

## Functional Requirements

### Database Schema & Tables

1. **The system must create a `prop_lines` table** with fields for player_id, player_name, team, opponent, position, stat_type, line_score, game_time, league, source, odds_type, season, projection_id, and auto-generated id/created_at.

2. **The system must create a `player_stats` table** with fields for player_id, player_name, team, opponent, position, stat_type, passing_yards, completions, attempts, receiving_yards, receptions, targets, game_id, season, league, source, and auto-generated id/created_at.

3. **The system must create a `games_processed` table** with fields for game_id, week, year, league, source, and auto-generated id/created_at.

4. **The system must create a `players` table** with fields for player_id, name, position, team, league, source, and auto-generated id/created_at.

5. **The system must create a `teams` table** with fields for name, abbreviation, league, source, and auto-generated id/created_at.

### Database Connection & Setup

6. **The system must provide PostgreSQL setup instructions** for creating the `football_props` database with proper connection parameters.

7. **The system must create a database connection module** that handles connection management, error handling, and connection pooling for local development.

8. **The system must include SQL DDL scripts** for creating all tables with proper data types, constraints, and indexes.

### Data Insertion Functions

9. **The system must provide direct insertion functions** for each table that accept dictionary data matching the table schema.

10. **The system must provide batch insertion functions** that can handle multiple records efficiently with transaction support.

11. **The system must provide upsert functions** that can handle duplicate data gracefully (insert if new, update if exists).

12. **The system must create parser integration functions** that accept parsed JSON data and route it to appropriate tables.

### Data Validation & Quality

13. **The system must validate required fields** before insertion (player_name, team, stat_type, etc. cannot be null).

14. **The system must validate data types** (numeric fields are numbers, timestamps are valid dates, etc.).

15. **The system must validate foreign key relationships** where applicable (game_id references, player_id consistency).

16. **The system must reject placeholder values** ("Unknown", "TBD", etc.) in critical fields.

17. **The system must log validation errors** with specific details about rejected records.

### Testing & Verification

18. **The system must provide sample data insertion scripts** that demonstrate successful data loading from existing parsed files.

19. **The system must include query validation functions** that verify data was inserted correctly and can be retrieved.

20. **The system must provide data consistency checks** that validate relationships between tables.

## Non-Goals (Out of Scope)

- **Production-scale performance optimization** (indexing strategies, query optimization)
- **Advanced database features** (triggers, stored procedures, views)
- **User authentication/authorization** for database access
- **Database backup and recovery procedures**
- **Web API layer** on top of the database
- **Real-time data streaming** or automatic data updates
- **Advanced analytics** or machine learning model integration
- **Multi-database support** (only PostgreSQL for now)

## Design Considerations

### Database Architecture
- **Single database approach:** All tables in one `football_props` database
- **League differentiation:** Use `league` field instead of separate tables for NFL/CFB
- **Normalized design:** Reference tables for players/teams with foreign keys
- **Flexible stat storage:** Nullable stat fields to accommodate different position types

### Module Structure
```
src/database/
├── __init__.py
├── connection.py      # Database connection management
├── schema.py          # Table creation and DDL
├── insert.py          # Direct insertion functions
├── batch.py           # Batch insertion functions
├── validation.py      # Data validation and quality checks
└── sample_data.py     # Sample insertion and testing
```

### Integration Pattern
- Parsers remain unchanged
- New database modules accept parsed dictionary data
- Clear separation between parsing and storage logic
- Optional database storage (parsers work with or without DB)

## Technical Considerations

### Dependencies
- **psycopg2-binary** for PostgreSQL connectivity
- **python-dotenv** for database connection parameters
- Existing **pathlib, json** for file operations

### Connection Management
- Local PostgreSQL instance on default port 5432
- Database: `football_props`, User: `andrew`, No password (peer auth)
- Connection pooling for batch operations
- Graceful error handling for connection failures

### Data Types & Constraints
- **TEXT** for variable-length strings (names, teams, stat_types)
- **NUMERIC** for stat values that may include decimals
- **INTEGER** for counts and years
- **TIMESTAMP** for time-based fields
- **SERIAL** for auto-incrementing primary keys

### Error Handling Strategy
- **Connection errors:** Graceful fallback, clear error messages
- **SQL errors:** Log specific error with problematic data
- **Validation errors:** Collect all issues, report summary
- **Transaction management:** Rollback on batch failures

## Success Metrics

1. **Schema Creation:** All 5 tables created successfully with proper constraints
2. **Data Insertion:** Successfully insert sample data from all existing parsed files
3. **Data Validation:** Reject invalid/incomplete records with clear error messages
4. **Query Verification:** Retrieve and validate inserted data matches source files
5. **Integration Success:** Database functions work with all existing parser outputs
6. **Performance Baseline:** Insert 1000+ records in under 10 seconds for development use

## Open Questions

1. **Player ID consistency:** Should we standardize player_id generation across all parsers, or handle variations in the database layer?

2. **Historical data strategy:** How should we handle data updates for the same player/game (overwrite, versioning, or duplicate detection)?

3. **Reference data seeding:** Should we pre-populate teams table with known NFL/CFB teams, or build it dynamically from parsed data?

4. **Stat field expansion:** As we add more stat types, should we use a flexible JSON field or continue adding specific columns?

5. **Game ID normalization:** Should we create a unified game identifier system, or preserve source-specific game IDs with source attribution?

## Implementation Phases

### Phase 1: Core Infrastructure
- Database setup and connection module
- Table creation scripts
- Basic insertion functions for prop_lines and player_stats

### Phase 2: Data Integration
- Parser integration functions
- Batch insertion capabilities
- Sample data loading from existing files

### Phase 3: Quality & Validation
- Comprehensive validation functions
- Data consistency checks
- Error handling and logging

### Phase 4: Reference Tables & Advanced Features
- Players and teams tables
- Upsert capabilities
- Advanced query helpers

---

*This PRD serves as the foundation for implementing a robust database storage layer that will enable advanced analysis and prop suggestion capabilities for the Football Prop Insights project.*