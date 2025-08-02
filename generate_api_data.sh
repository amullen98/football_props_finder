#!/bin/bash

# Football Prop Insights - API Data Generator
# Usage: ./generate_api_data.sh <api_type> [additional_params...]

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to display help
show_help() {
    echo -e "${BLUE}🏈 Football Prop Insights - API Data Generator${NC}"
    echo ""
    echo "Usage: ./generate_api_data.sh <api_type> [additional_params...]"
    echo ""
    echo "Available API Types:"
    echo "  prizepicks-nfl    - PrizePicks NFL projections"
    echo "  prizepicks-cfb    - PrizePicks College Football projections"
    echo "  nfl-stats         - NFL Game IDs (requires: year week type)"
    echo "  nfl-boxscore      - NFL Player Stats (requires: event_id)"
    echo "  nfl-week-boxscores - ALL NFL Player Stats for a week (requires: year week type)"
    echo "  cfb-stats         - College Football Data (requires: year week season_type)"
    echo "  all               - Run all APIs with default parameters"
    echo ""
    echo "Examples:"
    echo "  ./generate_api_data.sh prizepicks-nfl"
    echo "  ./generate_api_data.sh prizepicks-cfb"
    echo "  ./generate_api_data.sh nfl-stats 2023 1 2"
    echo "  ./generate_api_data.sh nfl-boxscore 401220225"
    echo "  ./generate_api_data.sh nfl-week-boxscores 2023 1 2"
    echo "  ./generate_api_data.sh cfb-stats 2023 1 regular"
    echo "  ./generate_api_data.sh all"
    echo ""
    echo "Parameters for nfl-stats:"
    echo "  year    - NFL season year (e.g., 2023)"
    echo "  week    - Week number (1-18)"
    echo "  type    - Game type (2=regular season, 1=preseason, 3=postseason)"
    echo ""
    echo "Parameters for nfl-boxscore:"
    echo "  event_id - NFL game event ID (e.g., 401220225)"
    echo ""
    echo "Parameters for nfl-week-boxscores:"
    echo "  year    - NFL season year (e.g., 2023)"
    echo "  week    - Week number (1-18)"
    echo "  type    - Game type (2=regular season, 1=preseason, 3=postseason)"
    echo ""
    echo "Parameters for cfb-stats:"
    echo "  year         - CFB season year (e.g., 2023)"
    echo "  week         - Week number (1-15)"
    echo "  season_type  - Season type (regular, postseason, both)"
    echo ""
}

# Function to run PrizePicks NFL
run_prizepicks_nfl() {
    echo -e "${BLUE}🏈 Fetching PrizePicks NFL data...${NC}"
    python3 -c "
from src.api_client import fetch_prizepicks_data
result = fetch_prizepicks_data('nfl')
print(f'✅ Success: {result[\"success\"]}, Records: {result.get(\"record_count\", 0)}')
"
}

# Function to run PrizePicks CFB
run_prizepicks_cfb() {
    echo -e "${BLUE}🏈 Fetching PrizePicks College Football data...${NC}"
    python3 -c "
from src.api_client import fetch_prizepicks_data
result = fetch_prizepicks_data('cfb')
print(f'✅ Success: {result[\"success\"]}, Records: {result.get(\"record_count\", 0)}')
"
}

# Function to run NFL Stats
run_nfl_stats() {
    local year=${1:-2023}
    local week=${2:-1}
    local type=${3:-2}
    
    echo -e "${BLUE}🏈 Fetching NFL Stats data (Year: $year, Week: $week, Type: $type)...${NC}"
    python3 -c "
from src.api_client import fetch_nfl_game_ids
result = fetch_nfl_game_ids($year, $week, $type)
print(f'✅ Success: {result[\"success\"]}, Games: {result.get(\"game_count\", 0)}')
"
}

# Function to run NFL Boxscore
run_nfl_boxscore() {
    local event_id=${1}
    
    if [ -z "$event_id" ]; then
        echo -e "${RED}❌ Error: event_id parameter is required${NC}"
        echo "Usage: ./generate_api_data.sh nfl-boxscore <event_id>"
        echo "Example: ./generate_api_data.sh nfl-boxscore 401220225"
        exit 1
    fi
    
    echo -e "${BLUE}🏈 Fetching NFL Boxscore Data (Event ID: $event_id)...${NC}"
    python3 -c "
from src.api_client import fetch_nfl_boxscore
result = fetch_nfl_boxscore('$event_id')
print(f'✅ Success: {result[\"success\"]}, Players: {result.get(\"players_count\", 0)}')
"
}

# Function to run NFL Week Boxscores
run_nfl_week_boxscores() {
    local year=${1}
    local week=${2}
    local type=${3}
    
    if [ -z "$year" ] || [ -z "$week" ] || [ -z "$type" ]; then
        echo -e "${RED}❌ Error: nfl-week-boxscores requires 3 parameters: year week type${NC}"
        echo "Usage: ./generate_api_data.sh nfl-week-boxscores <year> <week> <type>"
        echo "Example: ./generate_api_data.sh nfl-week-boxscores 2023 1 2"
        exit 1
    fi
    
    echo -e "${BLUE}🏈 Fetching ALL NFL Boxscores for Week (Year: $year, Week: $week, Type: $type)...${NC}"
    echo -e "${YELLOW}⚠️  Warning: This will fetch detailed stats for ALL games in the week${NC}"
    echo -e "${YELLOW}   This may take several minutes and use multiple API calls${NC}"
    echo ""
    
    python3 -c "
from src.api_client import fetch_nfl_week_boxscores
result = fetch_nfl_week_boxscores($year, $week, $type)
print(f'✅ Week Success: {result[\"success\"]}, Games Processed: {result.get(\"games_processed\", 0)}/{result.get(\"total_games\", 0)}')
"
}

# Function to run CFB Stats
run_cfb_stats() {
    local year=${1:-2023}
    local week=${2:-1}
    local season_type=${3:-regular}
    
    echo -e "${BLUE}🏈 Fetching College Football Data (Year: $year, Week: $week, Season: $season_type)...${NC}"
    python3 -c "
from src.api_client import fetch_cfb_player_data
result = fetch_cfb_player_data($year, $week, '$season_type')
print(f'✅ Success: {result[\"success\"]}, Games: {result.get(\"game_count\", 0)}')
"
}

# Function to run all APIs
run_all() {
    echo -e "${YELLOW}🚀 Running all APIs with default parameters...${NC}"
    echo ""
    
    run_prizepicks_nfl
    echo ""
    
    run_prizepicks_cfb
    echo ""
    
    run_nfl_stats 2023 1 2
    echo ""
    
    run_nfl_boxscore 401220225
    echo ""
    
    run_cfb_stats 2023 1 regular
    echo ""
    
    echo -e "${GREEN}🎉 All API calls completed!${NC}"
}

# Main script logic
if [ $# -eq 0 ]; then
    echo -e "${RED}❌ Error: No API type specified${NC}"
    echo ""
    show_help
    exit 1
fi

case "$1" in
    "help"|"-h"|"--help")
        show_help
        ;;
    "prizepicks-nfl")
        run_prizepicks_nfl
        ;;
    "prizepicks-cfb")
        run_prizepicks_cfb
        ;;
    "nfl-stats")
        if [ $# -lt 4 ]; then
            echo -e "${RED}❌ Error: nfl-stats requires 3 parameters: year week type${NC}"
            echo "Example: ./generate_api_data.sh nfl-stats 2023 1 2"
            exit 1
        fi
        run_nfl_stats "$2" "$3" "$4"
        ;;
    "nfl-boxscore")
        if [ $# -lt 2 ]; then
            echo -e "${RED}❌ Error: nfl-boxscore requires 1 parameter: event_id${NC}"
            echo "Example: ./generate_api_data.sh nfl-boxscore 401220225"
            exit 1
        fi
        run_nfl_boxscore "$2"
        ;;
    "nfl-week-boxscores")
        if [ $# -lt 4 ]; then
            echo -e "${RED}❌ Error: nfl-week-boxscores requires 3 parameters: year week type${NC}"
            echo "Example: ./generate_api_data.sh nfl-week-boxscores 2023 1 2"
            exit 1
        fi
        run_nfl_week_boxscores "$2" "$3" "$4"
        ;;
    "cfb-stats")
        if [ $# -lt 4 ]; then
            echo -e "${RED}❌ Error: cfb-stats requires 3 parameters: year week season_type${NC}"
            echo "Example: ./generate_api_data.sh cfb-stats 2023 1 regular"
            exit 1
        fi
        run_cfb_stats "$2" "$3" "$4"
        ;;
    "all")
        run_all
        ;;
    *)
        echo -e "${RED}❌ Error: Unknown API type '$1'${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}✅ Data generation completed successfully!${NC}"
echo -e "${BLUE}📁 Check the api_data/ directory for saved JSON files${NC}"