"""
Common utilities and error handling patterns for football data parsers.

This module provides standardized error handling patterns and utility functions
that are used across all parsers in the football prop insights system.
"""

import json
import os
from typing import Any, Dict, List, Union


class ParserError(Exception):
    """Base exception class for parser-related errors."""
    pass


class JSONParseError(ParserError):
    """Raised when JSON parsing fails."""
    pass


class FileNotFoundError(ParserError):
    """Raised when input file cannot be found."""
    pass


class DataStructureError(ParserError):
    """Raised when expected data structure is missing or invalid."""
    pass


def safe_load_json(file_path_or_data: Union[str, Dict, List]) -> Any:
    """
    Safely load JSON data from file path or pre-loaded data.
    
    Args:
        file_path_or_data: Either a file path string or pre-loaded JSON data
        
    Returns:
        Parsed JSON data
        
    Raises:
        FileNotFoundError: If file path doesn't exist
        JSONParseError: If JSON parsing fails
    """
    # If it's already parsed data (dict or list), return as-is
    if isinstance(file_path_or_data, (dict, list)):
        return file_path_or_data
    
    # If it's a string, treat as file path
    if isinstance(file_path_or_data, str):
        if not os.path.exists(file_path_or_data):
            raise FileNotFoundError(f"Input file not found: {file_path_or_data}")
        
        try:
            with open(file_path_or_data, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise JSONParseError(f"Failed to parse JSON from {file_path_or_data}: {e}")
        except Exception as e:
            raise ParserError(f"Unexpected error loading {file_path_or_data}: {e}")
    
    raise ParserError(f"Invalid input type: expected str, dict, or list, got {type(file_path_or_data)}")


def safe_get_nested(data: Dict, keys: List[str], default: Any = None) -> Any:
    """
    Safely get nested dictionary values with error handling.
    
    Args:
        data: Dictionary to search
        keys: List of keys to traverse (e.g., ['boxscore', 'players'])
        default: Default value if key path doesn't exist
        
    Returns:
        Value at the nested key path or default value
    """
    try:
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current
    except (TypeError, KeyError):
        return default


def validate_required_fields(data: Dict, required_fields: List[str], context: str = "") -> None:
    """
    Validate that required fields exist in data dictionary.
    
    Args:
        data: Dictionary to validate
        required_fields: List of required field names
        context: Context string for error messages
        
    Raises:
        DataStructureError: If any required fields are missing
    """
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        context_str = f" in {context}" if context else ""
        raise DataStructureError(f"Missing required fields{context_str}: {missing_fields}")


def safe_get_list(data: Dict, key: str, default: List = None) -> List:
    """
    Safely get a list value from dictionary with validation.
    
    Args:
        data: Dictionary to search
        key: Key to look for
        default: Default value if key doesn't exist or isn't a list
        
    Returns:
        List value or default
    """
    if default is None:
        default = []
    
    value = data.get(key, default)
    return value if isinstance(value, list) else default


def print_parser_summary(parser_name: str, total_records: int, success_count: int, errors: List[str] = None):
    """
    Print a standardized summary of parser results.
    
    Args:
        parser_name: Name of the parser (e.g., "PrizePicks")
        total_records: Total number of records processed
        success_count: Number of successfully parsed records
        errors: List of error messages (optional)
    """
    print(f"\n{parser_name} Parser Results:")
    print(f"  📊 Total Records Found: {total_records}")
    print(f"  ✅ Successfully Parsed: {success_count}")
    
    if total_records > 0:
        success_rate = (success_count / total_records) * 100
        print(f"  📈 Success Rate: {success_rate:.1f}%")
    
    if errors:
        print(f"  ❌ Errors: {len(errors)}")
        for error in errors[:3]:  # Show first 3 errors
            print(f"    - {error}")
        if len(errors) > 3:
            print(f"    ... and {len(errors) - 3} more errors")
    
    print()