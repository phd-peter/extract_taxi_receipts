#!/usr/bin/env python3
"""Integration test to verify validation logging and functionality."""

import logging
import sys
import os
from io import StringIO
from extract_taxi_receipts.core import _validate_extracted_data

def test_validation_logging():
    """Test that validation functions produce expected log output."""
    
    # Set up logging to capture output
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.WARNING)
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    logger = logging.getLogger("extract_taxi_receipts")
    logger.addHandler(handler)
    logger.setLevel(logging.WARNING)
    
    print("Testing validation with various data scenarios...")
    
    # Test 1: Valid data (should not produce warnings)
    print("\n1. Testing valid data (no warnings expected):")
    valid_data = {
        "paid_at": "2025-07-15 14:30",
        "fare": 25000,
        "name": "최홍영",
        "route": "회사-집"
    }
    result = _validate_extracted_data(valid_data)
    print(f"   Input: {valid_data}")
    print(f"   Output: {result}")
    
    # Test 2: Name correction
    print("\n2. Testing name correction:")
    name_correction_data = {
        "paid_at": "2025-07-15 14:30",
        "fare": 25000,
        "name": "최홍영님",  # Should be corrected
        "route": "회사-집"
    }
    result = _validate_extracted_data(name_correction_data)
    print(f"   Input: {name_correction_data}")
    print(f"   Output: {result}")
    print(f"   Name corrected: {name_correction_data['name']} → {result['name']}")
    
    # Test 3: Date warning (before 2025)
    print("\n3. Testing date validation warning:")
    old_date_data = {
        "paid_at": "2024-12-31 23:59",  # Should trigger warning
        "fare": 25000,
        "name": "최홍영",
        "route": "회사-집"
    }
    result = _validate_extracted_data(old_date_data)
    print(f"   Input: {old_date_data}")
    print(f"   Output: {result}")
    
    # Test 4: High fare warning
    print("\n4. Testing high fare validation warning:")
    high_fare_data = {
        "paid_at": "2025-07-15 14:30",
        "fare": 150000,  # Should trigger warning
        "name": "최홍영",
        "route": "회사-집"
    }
    result = _validate_extracted_data(high_fare_data)
    print(f"   Input: {high_fare_data}")
    print(f"   Output: {result}")
    
    # Test 5: Multiple validation issues
    print("\n5. Testing multiple validation issues:")
    multiple_issues_data = {
        "paid_at": "2024-01-01 00:00",  # Old date
        "fare": 200000,  # High fare
        "name": "박다혜님",  # Name correction needed
        "route": "회사-집"
    }
    result = _validate_extracted_data(multiple_issues_data)
    print(f"   Input: {multiple_issues_data}")
    print(f"   Output: {result}")
    
    # Get captured log output
    log_output = log_capture.getvalue()
    print(f"\n=== CAPTURED LOG OUTPUT ===")
    if log_output.strip():
        print(log_output)
    else:
        print("No warnings logged (this might indicate an issue)")
    
    # Clean up
    logger.removeHandler(handler)
    handler.close()
    
    return log_output

if __name__ == "__main__":
    print("=== Integration Test: Validation Logging ===")
    log_output = test_validation_logging()
    
    # Verify expected warnings are present
    expected_warnings = [
        "Date is before 2025",
        "High fare amount detected"
    ]
    
    print(f"\n=== VERIFICATION ===")
    for warning in expected_warnings:
        if warning in log_output:
            print(f"✓ Found expected warning: {warning}")
        else:
            print(f"✗ Missing expected warning: {warning}")
    
    print("\n=== Integration test completed ===")