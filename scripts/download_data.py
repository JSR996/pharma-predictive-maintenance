"""
Download NASA CMAPSS Turbofan Engine Degradation Dataset (FD001–FD004).
Run this once before training: python scripts/download_data.py
"""

import os
import urllib.request

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "backend", "data")

# FD001 files served as plain text from a public GitHub mirror of the NASA
# CMAPSS dataset (the original data.nasa.gov endpoint is no longer reachable).
MIRROR = "https://raw.githubusercontent.com/hankroark/Turbofan-Engine-Degradation/master/CMAPSSData"
FILES = ["train_FD001.txt", "test_FD001.txt", "RUL_FD001.txt"]

FALLBACK_INSTRUCTIONS = """
Automatic download failed. Manual steps:
1. Go to: https://www.kaggle.com/datasets/behrad3d/nasa-cmaps
2. Download and extract the ZIP
3. Place these files in backend/data/:
   - train_FD001.txt
   - test_FD001.txt
   - RUL_FD001.txt
"""


def download():
    os.makedirs(DATA_DIR, exist_ok=True)

    # Check if already downloaded
    if os.path.exists(os.path.join(DATA_DIR, "train_FD001.txt")):
        print("✅ CMAPSS data already present in backend/data/")
        return

    print("Downloading CMAPSS FD001 dataset...")
    try:
        for name in FILES:
            dest = os.path.join(DATA_DIR, name)
            urllib.request.urlretrieve(f"{MIRROR}/{name}", dest)
            print(f"   ✓ {name}")
        print(f"✅ Downloaded to {DATA_DIR}")

    except Exception as e:
        print(f"⚠️  Auto-download failed: {e}")
        print(FALLBACK_INSTRUCTIONS)


if __name__ == "__main__":
    download()
