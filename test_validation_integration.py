#!/usr/bin/env python3
"""
Test script to verify validation integration works correctly.
This tests both front-only and front+back processing scenarios.
"""

import sys
import logging
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from extract_taxi_receipts.core import _validate_extracted_data, _call_openai

# Set up logging to see validation messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_validation_integration():
    """Test that validation is properly integrated into the extraction flow."""
    
    print("Testing validation integration...")
    
    # Test 1: Test validation function directly
    print("\n1. Testing validation function directly:")
    
    test_data = {
        "paid_at": "2024-07-07 23:43",  # Should trigger date warning (before 2025)
        "fare": 150000,  # Should trigger fare warning (over 100,000)
        "name": "최홍영",  # Should match team member exactly
        "route": "회사-집"
    }
    
    validated = _validate_extracted_data(test_data)
    print(f"Original data: {test_data}")
    print(f"Validated data: {validated}")
    
    # Test 2: Test with team member name correction
    print("\n2. Testing team member name correction:")
    
    test_data_2 = {
        "paid_at": "2025-07-07 23:43",  # Valid date
        "fare": 50000,  # Normal fare
        "name": "박다혜 ",  # Name with trailing space - should be corrected
        "route": "집-회사"
    }
    
    validated_2 = _validate_extracted_data(test_data_2)
    print(f"Original data: {test_data_2}")
    print(f"Validated data: {validated_2}")
    
    # Test 3: Test with unknown team member
    print("\n3. Testing with unknown team member:")
    
    test_data_3 = {
        "paid_at": "2025-07-07 23:43",
        "fare": 30000,
        "name": "홍길동",  # Unknown team member - should remain unchanged
        "route": "야근택시비"
    }
    
    validated_3 = _validate_extracted_data(test_data_3)
    print(f"Original data: {test_data_3}")
    print(f"Validated data: {validated_3}")
    
    # Test 4: Test with missing/empty data
    print("\n4. Testing with missing/empty data:")
    
    test_data_4 = {
        "paid_at": "",
        "fare": None,
        "name": None,
        "route": "회사-집"
    }
    
    validated_4 = _validate_extracted_data(test_data_4)
    print(f"Original data: {test_data_4}")
    print(f"Validated data: {validated_4}")
    
    print("\nValidation integration test completed!")
    print("Check the log messages above to verify warnings are properly generated.")

if __name__ == "__main__":
    test_validation_integration()