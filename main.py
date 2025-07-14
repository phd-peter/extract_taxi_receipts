
import os
import sys
import datetime as dt
from pathlib import Path
from typing import List, Tuple, Dict
import pandas as pd
from extract_taxi_receipts import (
    extract_from_images,
    pair_images_from_dir,
    CoreError,
)

# ---------------------------------------------------------------------------
# CLI entry point – minimal wrapper around shared core layer
# ---------------------------------------------------------------------------

def process_directory(image_dir: str = "./img") -> str:
    """Scan `image_dir`, pair images, extract data, and save to CSV."""

    rows: List[Dict] = []

    for front, back in pair_images_from_dir(image_dir):
        try:
            data = extract_from_images(front, back)
            rows.append(data)
            print(f"✓ Parsed {os.path.basename(front)} → {data}")
        except CoreError as e:
            print(f"✗ Failed on {front}: {e}")

    df = pd.DataFrame(rows)
    if not df.empty:
        # Ensure consistent column order
        ordered_cols = ["paid_at", "name", "route", "fare"]
        df = df[ordered_cols]

    ts = dt.datetime.now().strftime("%Y%m%d_%H%M")
    out_path = f"receipts_{ts}.csv"
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"\nSaved {len(df)} rows → {out_path}")
    return out_path


if __name__ == "__main__":
    target_dir = sys.argv[1] if len(sys.argv) >= 2 else "./img"
    if not Path(target_dir).exists():
        print(f"Directory not found: {target_dir}")
        sys.exit(1)

    process_directory(target_dir)