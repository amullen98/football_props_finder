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
        
        print("\n" + "=" * 80)
        print("🏁 PRIZEPICKS API TEST SUMMARY")
        print("=" * 80)
        print(f"NFL API: {'✅ SUCCESS' if nfl_result['success'] else '❌ FAILED'}")
        print(f"CFB API: {'✅ SUCCESS' if cfb_result['success'] else '❌ FAILED'}")
        print("=" * 80)
        
    else:
        print("💥 Environment validation failed!")
        print("Please fix the configuration issues before proceeding.")