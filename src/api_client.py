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


if __name__ == "__main__":
    print("🏈 Football Prop Insights - API Client Test Suite")
    print("Step 1: Environment Variable Validation")
    print()
    
    # Test environment variable validation
    if validate_environment_variables():
        print("🎉 Environment validation successful!")
        print("Ready to proceed with API testing...")
    else:
        print("💥 Environment validation failed!")
        print("Please fix the configuration issues before proceeding.")