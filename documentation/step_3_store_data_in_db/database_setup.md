# PostgreSQL Database Setup Instructions

## Prerequisites

### Verify PostgreSQL Installation

1. **Check PostgreSQL version:**
   ```bash
   psql --version
   ```
   Expected output: `psql (PostgreSQL) 14.x` or higher

2. **Verify PostgreSQL service is running:**
   ```bash
   pg_isready -h localhost -p 5432
   ```
   Expected output: `localhost:5432 - accepting connections`

3. **Test database connection:**
   ```bash
   psql -h localhost -d postgres -c "\l"
   ```
   Should show list of databases without errors

## Database Setup

### Step 1: Create the football_props Database

```bash
# Connect to PostgreSQL and create the database
psql -h localhost -d postgres -c "CREATE DATABASE football_props;"
```

Alternative method using createdb command:
```bash
createdb -h localhost football_props
```

### Step 2: Verify Database Creation

```bash
# List databases to confirm football_props was created
psql -h localhost -d postgres -c "\l" | grep football_props
```

### Step 3: Test Connection to New Database

```bash
# Connect to the new database
psql -h localhost -d football_props -c "SELECT current_database();"
```

Expected output should show: `football_props`

## Connection Configuration

### Database Parameters
- **Host:** `localhost`
- **Port:** `5432` (default)
- **Database:** `football_props`
- **User:** `andrew` (current system user)
- **Password:** Not required (using peer authentication)

### Python Connection String
```python
connection_params = {
    'host': 'localhost',
    'port': 5432,
    'database': 'football_props',
    'user': 'andrew'
}
```

## Troubleshooting

### If PostgreSQL is not running:
```bash
# On macOS with Homebrew:
brew services start postgresql

# On Linux with systemd:
sudo systemctl start postgresql

# Check status:
brew services list | grep postgresql
# or
sudo systemctl status postgresql
```

### If connection fails:
1. Check PostgreSQL is running: `pg_isready`
2. Verify user permissions: `psql -h localhost -d postgres -c "\du"`
3. Check PostgreSQL logs for errors

### If database creation fails:
- Ensure you have CREATE database privileges
- Check disk space availability
- Verify PostgreSQL configuration allows local connections

## Next Steps

After completing this setup:
1. Run the table creation scripts (will be created in next tasks)
2. Test data insertion functions
3. Verify all database operations work correctly

## Database Reset (if needed)

To start fresh:
```bash
# Drop and recreate the database
psql -h localhost -d postgres -c "DROP DATABASE IF EXISTS football_props;"
psql -h localhost -d postgres -c "CREATE DATABASE football_props;"
```

---

**Status: ✅ PostgreSQL is running and ready for football_props database creation**