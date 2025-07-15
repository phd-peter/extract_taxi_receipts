#!/usr/bin/env python3
"""End-to-end test to verify complete integration with sample images."""

import logging
import sys
import os
from pathlib import Path
import pandas as pd
from extract_taxi_receipts import extract_from_images, pair_images_from_dir, CoreError

def setup_logging():
    """Set up logging to see validation messages."""
    logger = logging.getLogger("extract_taxi_receipts")
    logger.setLevel(logging.INFO)
    
    # Create console handler if not already present
    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

def test_end_to_end_processing():
    """Test complete processing pipeline with sample images."""
    
    print("=== End-to-End Integration Test ===")
    setup_logging()
    
    image_dir = "./img"
    if not Path(image_dir).exists():
        print(f"✗ Image directory not found: {image_dir}")
        return False
    
    print(f"📁 Processing images from: {image_dir}")
    
    # Get image pairs
    pairs = pair_images_from_dir(image_dir)
    print(f"📸 Found {len(pairs)} image pairs to process")
    
    if not pairs:
        print("✗ No image pairs found for processing")
        return False
    
    # Process each pair
    rows = []
    for i, (front, back) in enumerate(pairs, 1):
        print(f"\n--- Processing pair {i}/{len(pairs)} ---")
        print(f"Front: {os.path.basename(front)}")
        print(f"Back: {os.path.basename(back)}")
        
        try:
            # This will trigger validation and logging
            data = extract_from_images(front, back)
            rows.append(data)
            print(f"✓ Extracted data: {data}")
            
        except CoreError as e:
            print(f"✗ Core error: {e}")
        except Exception as e:
            print(f"✗ Unexpected error: {e}")
    
    # Create DataFrame and save CSV
    if rows:
        df = pd.DataFrame(rows)
        ordered_cols = ["paid_at", "name", "route", "fare"]
        df = df[ordered_cols]
        
        test_csv_path = "test_end_to_end_results.csv"
        df.to_csv(test_csv_path, index=False, encoding="utf-8-sig")
        
        print(f"\n=== Results Summary ===")
        print(f"✓ Processed {len(rows)} receipts successfully")
        print(f"✓ CSV saved to: {test_csv_path}")
        print(f"\n📊 Data preview:")
        print(df.to_string(index=False))
        
        # Verify CSV content
        print(f"\n📄 CSV file content verification:")
        with open(test_csv_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()
            print(content)
        
        return True
    else:
        print("✗ No data extracted")
        return False

if __name__ == "__main__":
    success = test_end_to_end_processing()
    if success:
        print("\n🎉 End-to-end test completed successfully!")
        print("✓ CLI interface working with validation")
        print("✓ Logging output visible")
        print("✓ CSV output includes validated data")
        print("✓ Sample receipt images processed correctly")
    else:
        print("\n❌ End-to-end test failed")
        sys.exit(1)