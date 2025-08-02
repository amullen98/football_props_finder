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

# Load environment variables
load_dotenv()


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
        
        # Test College Football Data API
        print("\n🏈 Testing College Football Data API Integration...")
        
        cfb_stats_result = fetch_cfb_player_data(2023, 1, 'regular')
        
        print("\n" + "=" * 80)
        print("🏁 API TEST SUMMARY")
        print("=" * 80)
        print(f"PrizePicks NFL: {'✅ SUCCESS' if nfl_result['success'] else '❌ FAILED'}")
        print(f"PrizePicks CFB: {'✅ SUCCESS' if cfb_result['success'] else '❌ FAILED'}")
        print(f"NFL Player Stats: {'✅ SUCCESS' if nfl_stats_result['success'] else '❌ FAILED'}")
        print(f"CFB Player Stats: {'✅ SUCCESS' if cfb_stats_result['success'] else '❌ FAILED'}")
        print("=" * 80)
        
    else:
        print("💥 Environment validation failed!")
        print("Please fix the configuration issues before proceeding.")