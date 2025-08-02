"""
Football Prop Insights - Step 1: API Connectivity & Data Validation

This module provides functions to connect to and validate data from:
- PrizePicks API (prop betting lines)
- Underdog Fantasy API (prop betting lines)  
- NFL Player Stats API (via RapidAPI)
- College Football Data API (player statistics)

Each function includes comprehensive error handling and data validation.
"""

import os
import requests
import json
from dotenv import load_dotenv
from typing import Dict, Any, Optional
from pathlib import Path

# Load environment variables
load_dotenv()


def save_api_data(data: Any, api_folder: str, filename: str) -> None:
    """
    Save API response data to JSON file.
    
    Args:
        data: The data to save (usually API response)
        api_folder: Subfolder name under api_data (e.g., 'prizepicks', 'nfl_stats')
        filename: Name of the JSON file (e.g., 'nfl_projections.json')
    """
    try:
        # Create directory structure
        base_dir = Path("api_data")
        api_dir = base_dir / api_folder
        api_dir.mkdir(parents=True, exist_ok=True)
        
        # Save data to file
        filepath = api_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Data saved to: {filepath}")
        
    except Exception as e:
        print(f"⚠️  Failed to save data to {api_folder}/{filename}: {str(e)}")


def validate_environment_variables() -> bool:
    """
    Validate that all required environment variables are set.
    
    Returns:
        bool: True if all required variables are present, False otherwise
    """
    print("=" * 60)
    print("🔍 VALIDATING ENVIRONMENT VARIABLES")
    print("=" * 60)
    
    required_vars = {
        'RAPIDAPI_KEY': 'RapidAPI key for NFL player stats',
        'RAPIDAPI_HOST': 'RapidAPI host for NFL API',
        'CFB_API_KEY': 'College Football Data API key'
    }
    
    missing_vars = []
    
    for var_name, description in required_vars.items():
        value = os.getenv(var_name)
        if value:
            print(f"✅ {var_name}: SET ({description})")
        else:
            print(f"❌ {var_name}: MISSING ({description})")
            missing_vars.append(var_name)
    
    if missing_vars:
        print("\n🚨 ERROR: Missing required environment variables!")
        print("Please check your .env file and ensure the following variables are set:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nRefer to setup.md for configuration instructions.")
        print("=" * 60)
        return False
    
    print("\n✅ All required environment variables are configured!")
    print("=" * 60)
    return True


def print_api_separator(api_name: str) -> None:
    """Print a visual separator for API test results."""
    print("\n" + "=" * 80)
    print(f"🌐 TESTING {api_name.upper()} API")
    print("=" * 80)


def print_response_summary(api_name: str, success: bool, record_count: int = 0, 
                          sample_data: Optional[Dict[Any, Any]] = None) -> None:
    """Print a formatted summary of API response."""
    status = "SUCCESS ✅" if success else "FAILED ❌"
    print(f"\n📊 {api_name} API Status: {status}")
    
    if success and record_count > 0:
        print(f"📈 Records Retrieved: {record_count}")
        
        if sample_data:
            print(f"\n📋 Sample Record:")
            print("-" * 40)
            print(json.dumps(sample_data, indent=2, default=str))
            print("-" * 40)
    
    print("=" * 80)


def fetch_prizepicks_data(league: str = 'nfl') -> Dict[str, Any]:
    """
    Fetch prop betting data from PrizePicks API for specified league.
    
    Args:
        league (str): League to fetch data for ('nfl' or 'cfb')
        
    Returns:
        Dict[str, Any]: Response data with success status and results
    """
    print_api_separator(f"PrizePicks {league.upper()}")
    
    # Define league-specific endpoints
    league_configs = {
        'nfl': {
            'league_id': 9,
            'name': 'NFL'
        },
        'cfb': {
            'league_id': 15,
            'name': 'College Football'
        }
    }
    
    if league.lower() not in league_configs:
        error_msg = f"Invalid league '{league}'. Supported leagues: nfl, cfb"
        print(f"❌ ERROR: {error_msg}")
        return {
            'success': False,
            'error': error_msg,
            'data': None
        }
    
    config = league_configs[league.lower()]
    league_name = config['name']
    
    # Build API URL
    base_url = "https://api.prizepicks.com/projections"
    params = {
        'league_id': config['league_id'],
        'per_page': 250,
        'single_stat': 'true',
        'in_game': 'true',
        'state_code': 'CA',
        'game_mode': 'prizepools'
    }
    
    try:
        print(f"🔗 Calling PrizePicks API for {league_name}...")
        print(f"🌐 URL: {base_url}")
        print(f"📋 Parameters: {params}")
        
        # Add headers to appear more like a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        response = requests.get(base_url, params=params, headers=headers, timeout=30)
        
        print(f"📡 HTTP Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                
                # Validate response structure
                if 'data' in data:
                    projections = data['data']
                    record_count = len(projections)
                    
                    print(f"✅ Successfully retrieved {record_count} {league_name} projections")
                    
                    # Save raw API data to file
                    filename = f"{league.lower()}_projections.json"
                    save_api_data(data, "prizepicks", filename)
                    
                    # Get sample record for display
                    sample_record = projections[0] if projections else None
                    
                    print_response_summary(f"PrizePicks {league_name}", True, record_count, sample_record)
                    
                    return {
                        'success': True,
                        'league': league_name,
                        'record_count': record_count,
                        'data': data
                    }
                else:
                    error_msg = "Response missing 'data' field"
                    print(f"❌ Response validation failed: {error_msg}")
                    print(f"📄 Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dictionary'}")
                    print_response_summary(f"PrizePicks {league_name}", False)
                    
                    return {
                        'success': False,
                        'error': error_msg,
                        'data': data
                    }
                    
            except json.JSONDecodeError as e:
                error_msg = f"Failed to parse JSON response: {str(e)}"
                print(f"❌ JSON Error: {error_msg}")
                print(f"📄 Raw response: {response.text[:200]}...")
                print_response_summary(f"PrizePicks {league_name}", False)
                
                return {
                    'success': False,
                    'error': error_msg,
                    'data': None
                }
        else:
            error_msg = f"HTTP {response.status_code}: {response.reason}"
            print(f"❌ HTTP Error: {error_msg}")
            print(f"📄 Response content: {response.text[:200]}...")
            print_response_summary(f"PrizePicks {league_name}", False)
            
            return {
                'success': False,
                'error': error_msg,
                'data': None
            }
            
    except requests.exceptions.Timeout:
        error_msg = "Request timeout (30 seconds)"
        print(f"❌ Timeout Error: {error_msg}")
        print_response_summary(f"PrizePicks {league_name}", False)
        
        return {
            'success': False,
            'error': error_msg,
            'data': None
        }
        
    except requests.exceptions.ConnectionError as e:
        error_msg = f"Connection error: {str(e)}"
        print(f"❌ Connection Error: {error_msg}")
        print_response_summary(f"PrizePicks {league_name}", False)
        
        return {
            'success': False,
            'error': error_msg,
            'data': None
        }
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"❌ Unexpected Error: {error_msg}")
        print_response_summary(f"PrizePicks {league_name}", False)
        
        return {
            'success': False,
            'error': error_msg,
            'data': None
        }


def fetch_nfl_game_ids(year: int = 2023, week: int = 1, type_param: int = 2) -> Dict[str, Any]:
    """
    Fetch NFL game events and IDs from RapidAPI NFL Data service.
    
    Args:
        year (int): NFL season year (default: 2023)
        week (int): NFL week number (default: 1)
        type_param (int): Game type (2 = regular season, default: 2)
        
    Returns:
        Dict[str, Any]: Response data with success status and results
    """
    print_api_separator("NFL Player Stats (RapidAPI)")
    
    # Get required environment variables
    rapidapi_key = os.getenv('RAPIDAPI_KEY')
    rapidapi_host = os.getenv('RAPIDAPI_HOST')
    
    if not rapidapi_key or not rapidapi_host:
        error_msg = "Missing required RapidAPI credentials (RAPIDAPI_KEY or RAPIDAPI_HOST)"
        print(f"❌ Authentication Error: {error_msg}")
        print_response_summary("NFL Player Stats", False)
        return {
            'success': False,
            'error': error_msg,
            'data': None
        }
    
    # Build API URL and headers
    base_url = f"https://{rapidapi_host}/nfl-weeks-events"
    params = {
        'year': year,
        'week': week,
        'type': type_param
    }
    
    headers = {
        'X-RapidAPI-Key': rapidapi_key,
        'X-RapidAPI-Host': rapidapi_host,
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    try:
        print(f"🔗 Calling NFL API for {year} season, week {week}...")
        print(f"🌐 URL: {base_url}")
        print(f"📋 Parameters: {params}")
        print(f"🔑 Using RapidAPI Host: {rapidapi_host}")
        
        response = requests.get(base_url, params=params, headers=headers, timeout=30)
        
        print(f"📡 HTTP Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                
                # Validate response structure (NFL API uses 'items' instead of 'events')
                if 'items' in data and isinstance(data['items'], list):
                    games = data['items']
                    game_count = len(games)
                    total_count = data.get('count', game_count)
                    
                    print(f"✅ Successfully retrieved {game_count} NFL games (total: {total_count})")
                    
                    # Save raw API data to file
                    filename = f"games_{year}_week{week}_type{type_param}.json"
                    save_api_data(data, "nfl_stats", filename)
                    
                    # Get sample record for display
                    sample_record = games[0] if games else None
                    
                    print_response_summary("NFL Player Stats", True, game_count, sample_record)
                    
                    return {
                        'success': True,
                        'year': year,
                        'week': week,
                        'game_count': game_count,
                        'total_count': total_count,
                        'data': data
                    }
                else:
                    error_msg = "Response missing 'items' field or invalid format"
                    print(f"❌ Response validation failed: {error_msg}")
                    print(f"📄 Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dictionary'}")
                    print_response_summary("NFL Player Stats", False)
                    
                    return {
                        'success': False,
                        'error': error_msg,
                        'data': data
                    }
                    
            except json.JSONDecodeError as e:
                error_msg = f"Failed to parse JSON response: {str(e)}"
                print(f"❌ JSON Error: {error_msg}")
                print(f"📄 Raw response: {response.text[:200]}...")
                print_response_summary("NFL Player Stats", False)
                
                return {
                    'success': False,
                    'error': error_msg,
                    'data': None
                }
                
        elif response.status_code == 401:
            error_msg = "Authentication failed - Invalid RapidAPI key"
            print(f"❌ Authentication Error: {error_msg}")
            print("🔍 Please verify your RAPIDAPI_KEY in the .env file")
            print_response_summary("NFL Player Stats", False)
            
            return {
                'success': False,
                'error': error_msg,
                'data': None
            }
            
        elif response.status_code == 403:
            error_msg = "Access forbidden - Check API subscription or rate limits"
            print(f"❌ Authorization Error: {error_msg}")
            print("🔍 You may have exceeded your RapidAPI rate limit or subscription plan")
            print_response_summary("NFL Player Stats", False)
            
            return {
                'success': False,
                'error': error_msg,
                'data': None
            }
            
        else:
            error_msg = f"HTTP {response.status_code}: {response.reason}"
            print(f"❌ HTTP Error: {error_msg}")
            print(f"📄 Response content: {response.text[:200]}...")
            print_response_summary("NFL Player Stats", False)
            
            return {
                'success': False,
                'error': error_msg,
                'data': None
            }
            
    except requests.exceptions.Timeout:
        error_msg = "Request timeout (30 seconds)"
        print(f"❌ Timeout Error: {error_msg}")
        print_response_summary("NFL Player Stats", False)
        
        return {
            'success': False,
            'error': error_msg,
            'data': None
        }
        
    except requests.exceptions.ConnectionError as e:
        error_msg = f"Connection error: {str(e)}"
        print(f"❌ Connection Error: {error_msg}")
        print_response_summary("NFL Player Stats", False)
        
        return {
            'success': False,
            'error': error_msg,
            'data': None
        }
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"❌ Unexpected Error: {error_msg}")
        print_response_summary("NFL Player Stats", False)
        
        return {
            'success': False,
            'error': error_msg,
            'data': None
        }


def fetch_nfl_boxscore(event_id: str) -> Dict[str, Any]:
    """
    Fetch detailed NFL boxscore data including player statistics for a specific game.
    
    Args:
        event_id: The event/game ID to fetch boxscore for
        
    Returns:
        Dict containing success status and boxscore data
    """
    print_api_separator("NFL Boxscore API")
    print(f"🏈 Fetching NFL boxscore data for event: {event_id}")
    
    try:
        # Validate environment variables
        api_key = os.getenv('RAPIDAPI_KEY')
        api_host = os.getenv('RAPIDAPI_HOST')
        
        if not api_key or not api_host:
            error_msg = "Missing required NFL API credentials in environment variables"
            print(f"❌ {error_msg}")
            return {'success': False, 'error': error_msg, 'event_id': event_id}
        
        # API endpoint for boxscore
        url = f"https://{api_host}/nfl-boxscore"
        params = {'id': event_id}
        
        headers = {
            'X-RapidAPI-Key': api_key,
            'X-RapidAPI-Host': api_host
        }
        
        print(f"🔗 Making request to: {url}")
        print(f"📋 Parameters: {params}")
        
        # Make the API request
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
        print(f"📡 Response status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                
                # Validate response structure
                if 'boxscore' in data and isinstance(data['boxscore'], dict):
                    boxscore = data['boxscore']
                    
                    # Count teams and players
                    teams_count = len(boxscore.get('teams', []))
                    players_data = boxscore.get('players', [])
                    players_count = 0
                    
                    for team_data in players_data:
                        for stat_category in team_data.get('statistics', []):
                            athletes = stat_category.get('athletes', [])
                            players_count += len(athletes)
                    
                    print(f"✅ Successfully retrieved boxscore for event {event_id}")
                    print(f"📊 Found {teams_count} teams with {players_count} total player stat entries")
                    
                    # Save raw API data to file
                    filename = f"boxscore_{event_id}.json"
                    save_api_data(data, "nfl_boxscore", filename)
                    
                    # Get sample player for display
                    sample_player = None
                    if players_data and len(players_data) > 0:
                        first_team = players_data[0]
                        if 'statistics' in first_team and len(first_team['statistics']) > 0:
                            first_stat = first_team['statistics'][0]
                            if 'athletes' in first_stat and len(first_stat['athletes']) > 0:
                                athlete = first_stat['athletes'][0]
                                sample_player = {
                                    'name': athlete.get('athlete', {}).get('displayName', 'Unknown'),
                                    'position': first_stat.get('name', 'Unknown'),
                                    'stats': athlete.get('stats', [])
                                }
                    
                    print_response_summary(f"NFL Boxscore (Event {event_id})", True, players_count, sample_player)
                    
                    return {
                        'success': True,
                        'event_id': event_id,
                        'teams_count': teams_count,
                        'players_count': players_count,
                        'data': data
                    }
                else:
                    error_msg = f"Invalid response structure - missing 'boxscore' field"
                    print(f"❌ {error_msg}")
                    return {'success': False, 'error': error_msg, 'event_id': event_id}
                    
            except json.JSONDecodeError as e:
                error_msg = f"Failed to decode JSON response: {e}"
                print(f"❌ {error_msg}")
                return {'success': False, 'error': error_msg, 'event_id': event_id}
                
        elif response.status_code == 401:
            error_msg = "Authentication failed - check your RapidAPI key"
            print(f"❌ HTTP 401: {error_msg}")
            return {'success': False, 'error': error_msg, 'event_id': event_id}
            
        elif response.status_code == 403:
            error_msg = "Access forbidden - check your RapidAPI subscription and host header"
            print(f"❌ HTTP 403: {error_msg}")
            return {'success': False, 'error': error_msg, 'event_id': event_id}
            
        elif response.status_code == 404:
            error_msg = f"Event ID {event_id} not found"
            print(f"❌ HTTP 404: {error_msg}")
            return {'success': False, 'error': error_msg, 'event_id': event_id}
            
        else:
            error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
            print(f"❌ {error_msg}")
            return {'success': False, 'error': error_msg, 'event_id': event_id}
            
    except requests.exceptions.Timeout:
        error_msg = "Request timed out - API may be slow"
        print(f"❌ {error_msg}")
        return {'success': False, 'error': error_msg, 'event_id': event_id}
        
    except requests.exceptions.ConnectionError:
        error_msg = "Connection error - check your internet connection"
        print(f"❌ {error_msg}")
        return {'success': False, 'error': error_msg, 'event_id': event_id}
        
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        print(f"❌ {error_msg}")
        return {'success': False, 'error': error_msg, 'event_id': event_id}


def fetch_nfl_week_boxscores(year: int = 2023, week: int = 1, type_param: int = 2) -> Dict[str, Any]:
    """
    Fetch detailed NFL boxscore data for ALL games in a specific week.
    
    Args:
        year: NFL season year (default: 2023)
        week: Week number 1-18 (default: 1)
        type_param: Game type - 1=preseason, 2=regular season, 3=postseason (default: 2)
        
    Returns:
        Dict containing success status and summary of all games processed
    """
    print_api_separator("NFL Week Boxscores")
    print(f"🏈 Fetching ALL NFL boxscores for {year} Season, Week {week}, Type {type_param}")
    
    try:
        # Step 1: Get all game IDs for the week
        print(f"📋 Step 1: Getting game IDs for the week...")
        games_result = fetch_nfl_game_ids(year, week, type_param)
        
        if not games_result['success']:
            error_msg = f"Failed to get game IDs: {games_result.get('error', 'Unknown error')}"
            print(f"❌ {error_msg}")
            return {'success': False, 'error': error_msg, 'games_processed': 0}
        
        # Extract game IDs from the result
        games_data = games_result.get('data', {})
        game_items = games_data.get('items', [])
        
        if not game_items:
            error_msg = f"No games found for {year} Season, Week {week}, Type {type_param}"
            print(f"⚠️ {error_msg}")
            return {'success': True, 'warning': error_msg, 'games_processed': 0, 'games': []}
        
        total_games = len(game_items)
        print(f"📊 Found {total_games} games to process")
        print()
        
        # Step 2: Process each game's boxscore
        processed_games = []
        successful_games = 0
        failed_games = 0
        
        for i, game_item in enumerate(game_items, 1):
            game_id = game_item.get('eventid')  # NFL API uses 'eventid' not 'id'
            game_name = f"NFL Game {game_id}" if game_id else f"Game {i}"
            
            print(f"🎯 Processing Game {i}/{total_games}: {game_name} (ID: {game_id})")
            
            if not game_id:
                print(f"⚠️ Skipping game {i}: No game ID found")
                failed_games += 1
                processed_games.append({
                    'game_number': i,
                    'game_id': None,
                    'game_name': game_name,
                    'success': False,
                    'error': 'No game ID found'
                })
                continue
            
            # Fetch boxscore for this specific game
            boxscore_result = fetch_nfl_boxscore(game_id)
            
            game_summary = {
                'game_number': i,
                'game_id': game_id,
                'game_name': game_name,
                'success': boxscore_result['success']
            }
            
            if boxscore_result['success']:
                successful_games += 1
                game_summary.update({
                    'teams_count': boxscore_result.get('teams_count', 0),
                    'players_count': boxscore_result.get('players_count', 0)
                })
                print(f"✅ Game {i} completed successfully: {boxscore_result.get('players_count', 0)} player stats")
            else:
                failed_games += 1
                game_summary['error'] = boxscore_result.get('error', 'Unknown error')
                print(f"❌ Game {i} failed: {boxscore_result.get('error', 'Unknown error')}")
            
            processed_games.append(game_summary)
            print()
            
            # Add small delay between requests to be respectful to the API
            if i < total_games:  # Don't delay after the last game
                import time
                time.sleep(1)  # 1 second delay between requests
        
        # Step 3: Summary
        print("=" * 80)
        print("🏁 WEEKLY BOXSCORE PROCESSING SUMMARY")
        print("=" * 80)
        print(f"📊 Total Games Found: {total_games}")
        print(f"✅ Successfully Processed: {successful_games}")
        print(f"❌ Failed: {failed_games}")
        print(f"📈 Success Rate: {(successful_games/total_games)*100:.1f}%" if total_games > 0 else "0.0%")
        
        if successful_games > 0:
            total_players = sum(game.get('players_count', 0) for game in processed_games if game['success'])
            print(f"👥 Total Player Stats Collected: {total_players}")
        
        print("=" * 80)
        
        # Save week summary data
        week_summary = {
            'year': year,
            'week': week,
            'type': type_param,
            'total_games': total_games,
            'successful_games': successful_games,
            'failed_games': failed_games,
            'games': processed_games
        }
        
        filename = f"week_summary_{year}_week{week}_type{type_param}.json"
        save_api_data(week_summary, "nfl_boxscore", filename)
        
        return {
            'success': successful_games > 0,
            'year': year,
            'week': week,
            'type': type_param,
            'total_games': total_games,
            'successful_games': successful_games,
            'failed_games': failed_games,
            'games_processed': successful_games,
            'games': processed_games
        }
        
    except Exception as e:
        error_msg = f"Unexpected error during week processing: {e}"
        print(f"❌ {error_msg}")
        return {'success': False, 'error': error_msg, 'games_processed': 0}


def fetch_cfb_player_data(year: int = 2023, week: int = 1, season_type: str = 'regular') -> Dict[str, Any]:
    """
    Fetch college football player statistics from CollegeFootballData API.
    
    Args:
        year (int): College football season year (default: 2023)
        week (int): Week number (default: 1)
        season_type (str): Season type - 'regular', 'postseason', or 'both' (default: 'regular')
        
    Returns:
        Dict[str, Any]: Response data with success status and results
    """
    print_api_separator("College Football Data API")
    
    # Get required environment variable
    cfb_api_key = os.getenv('CFB_API_KEY')
    
    if not cfb_api_key:
        error_msg = "Missing required CFB_API_KEY environment variable"
        print(f"❌ Authentication Error: {error_msg}")
        print_response_summary("College Football Data", False)
        return {
            'success': False,
            'error': error_msg,
            'data': None
        }
    
    # Build API URL and headers
    base_url = "https://api.collegefootballdata.com/games/players"
    params = {
        'year': year,
        'week': week,
        'seasonType': season_type
    }
    
    headers = {
        'Authorization': f'Bearer {cfb_api_key}',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json'
    }
    
    try:
        print(f"🔗 Calling CFB API for {year} season, week {week} ({season_type})...")
        print(f"🌐 URL: {base_url}")
        print(f"📋 Parameters: {params}")
        print(f"🔑 Using Bearer token authentication")
        
        response = requests.get(base_url, params=params, headers=headers, timeout=30)
        
        print(f"📡 HTTP Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                
                # Validate response structure (CFB API returns an array of games)
                if isinstance(data, list):
                    games = data
                    game_count = len(games)
                    
                    # Count total player stats across all games
                    total_player_stats = 0
                    for game in games:
                        if 'teams' in game:
                            for team in game['teams']:
                                if 'statistics' in team:
                                    total_player_stats += len(team['statistics'])
                    
                    print(f"✅ Successfully retrieved {game_count} CFB games with {total_player_stats} player stat records")
                    
                    # Save raw API data to file
                    filename = f"players_{year}_week{week}_{season_type}.json"
                    save_api_data(data, "cfb_stats", filename)
                    
                    # Get sample record for display
                    sample_record = games[0] if games else None
                    
                    print_response_summary("College Football Data", True, game_count, sample_record)
                    
                    return {
                        'success': True,
                        'year': year,
                        'week': week,
                        'season_type': season_type,
                        'game_count': game_count,
                        'total_player_stats': total_player_stats,
                        'data': data
                    }
                else:
                    error_msg = "Response is not a list or invalid format"
                    print(f"❌ Response validation failed: {error_msg}")
                    print(f"📄 Response type: {type(data)}")
                    if isinstance(data, dict):
                        print(f"📄 Response keys: {list(data.keys())}")
                    print_response_summary("College Football Data", False)
                    
                    return {
                        'success': False,
                        'error': error_msg,
                        'data': data
                    }
                    
            except json.JSONDecodeError as e:
                error_msg = f"Failed to parse JSON response: {str(e)}"
                print(f"❌ JSON Error: {error_msg}")
                print(f"📄 Raw response: {response.text[:200]}...")
                print_response_summary("College Football Data", False)
                
                return {
                    'success': False,
                    'error': error_msg,
                    'data': None
                }
                
        elif response.status_code == 401:
            error_msg = "Authentication failed - Invalid CFB API key"
            print(f"❌ Authentication Error: {error_msg}")
            print("🔍 Please verify your CFB_API_KEY in the .env file")
            print_response_summary("College Football Data", False)
            
            return {
                'success': False,
                'error': error_msg,
                'data': None
            }
            
        elif response.status_code == 403:
            error_msg = "Access forbidden - Check API subscription or rate limits"
            print(f"❌ Authorization Error: {error_msg}")
            print("🔍 You may have exceeded your CFB API rate limit (1,000/month)")
            print_response_summary("College Football Data", False)
            
            return {
                'success': False,
                'error': error_msg,
                'data': None
            }
            
        else:
            error_msg = f"HTTP {response.status_code}: {response.reason}"
            print(f"❌ HTTP Error: {error_msg}")
            print(f"📄 Response content: {response.text[:200]}...")
            print_response_summary("College Football Data", False)
            
            return {
                'success': False,
                'error': error_msg,
                'data': None
            }
            
    except requests.exceptions.Timeout:
        error_msg = "Request timeout (30 seconds)"
        print(f"❌ Timeout Error: {error_msg}")
        print_response_summary("College Football Data", False)
        
        return {
            'success': False,
            'error': error_msg,
            'data': None
        }
        
    except requests.exceptions.ConnectionError as e:
        error_msg = f"Connection error: {str(e)}"
        print(f"❌ Connection Error: {error_msg}")
        print_response_summary("College Football Data", False)
        
        return {
            'success': False,
            'error': error_msg,
            'data': None
        }
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"❌ Unexpected Error: {error_msg}")
        print_response_summary("College Football Data", False)
        
        return {
            'success': False,
            'error': error_msg,
            'data': None
        }


if __name__ == "__main__":
    print("🏈 Football Prop Insights - API Client Test Suite")
    print("Step 1: API Connectivity & Data Validation")
    print()
    
    # Test environment variable validation
    if validate_environment_variables():
        print("🎉 Environment validation successful!")
        print("Ready to proceed with API testing...")
        print()
        
        # Test PrizePicks API for both leagues
        print("🏈 Testing PrizePicks API Integration...")
        
        # Test NFL
        nfl_result = fetch_prizepicks_data('nfl')
        
        # Test College Football  
        cfb_result = fetch_prizepicks_data('cfb')
        
        # Test NFL Player Stats API
        print("\n🏈 Testing NFL Player Stats API Integration...")
        
        nfl_stats_result = fetch_nfl_game_ids(2023, 1, 2)
        
        # Test NFL Boxscore API (if we got game IDs)
        print("\n🏈 Testing NFL Boxscore API Integration...")
        
        nfl_boxscore_result = {'success': False}
        if nfl_stats_result['success'] and 'data' in nfl_stats_result:
            items = nfl_stats_result['data'].get('items', [])
            if items and len(items) > 0:
                # Use the first game ID we found (NFL API uses 'eventid')
                first_game = items[0]
                game_id = first_game.get('eventid', '401220225')  # fallback to known ID
                nfl_boxscore_result = fetch_nfl_boxscore(game_id)
            else:
                print("⚠️ No game IDs found, using fallback ID for boxscore test")
                nfl_boxscore_result = fetch_nfl_boxscore('401220225')
        else:
            print("⚠️ Game IDs fetch failed, using fallback ID for boxscore test")
            nfl_boxscore_result = fetch_nfl_boxscore('401220225')
        
        # Test NFL Weekly Boxscore API (optional - commented out for regular testing due to time)
        print("\n🏈 NFL Weekly Boxscore API Available...")
        print("ℹ️  Use ./generate_api_data.sh nfl-week-boxscores <year> <week> <type> to fetch ALL games")
        print("ℹ️  Example: ./generate_api_data.sh nfl-week-boxscores 2023 1 2")
        nfl_week_result = {'success': True, 'note': 'Available but not tested in main suite due to time'}
        
        # Uncomment below to test weekly boxscore in main test suite (will take several minutes)
        # print("\n🏈 Testing NFL Weekly Boxscore API Integration...")
        # nfl_week_result = fetch_nfl_week_boxscores(2023, 1, 2)
        
        # Test College Football Data API
        print("\n🏈 Testing College Football Data API Integration...")
        
        cfb_stats_result = fetch_cfb_player_data(2023, 1, 'regular')
        
        print("\n" + "=" * 80)
        print("🏁 API TEST SUMMARY")
        print("=" * 80)
        print(f"PrizePicks NFL: {'✅ SUCCESS' if nfl_result['success'] else '❌ FAILED'}")
        print(f"PrizePicks CFB: {'✅ SUCCESS' if cfb_result['success'] else '❌ FAILED'}")
        print(f"NFL Game IDs: {'✅ SUCCESS' if nfl_stats_result['success'] else '❌ FAILED'}")
        print(f"NFL Boxscore: {'✅ SUCCESS' if nfl_boxscore_result['success'] else '❌ FAILED'}")
        print(f"NFL Week Boxscores: {'✅ AVAILABLE' if nfl_week_result['success'] else '❌ FAILED'}")
        print(f"CFB Player Stats: {'✅ SUCCESS' if cfb_stats_result['success'] else '❌ FAILED'}")
        print("=" * 80)
        
    else:
        print("💥 Environment validation failed!")
        print("Please fix the configuration issues before proceeding.")