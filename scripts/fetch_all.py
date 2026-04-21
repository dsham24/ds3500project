import subprocess
import sys
import os

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

scripts = [
    ("FRED API", "fetch_fred.py"),
    ("Census Bureau API", "fetch_census.py"),
    ("Zillow Static Data", "fetch_zillow.py"),
]

if __name__ == "__main__":
    print("Starting data acquisition...")

    for name, script in scripts:
        print(f"\nFetching {name}...")
        script_path = os.path.join(SCRIPTS_DIR, script)
        result = subprocess.run([sys.executable, script_path], capture_output=False)

        if result.returncode != 0:
            print(f"  {name} finished with errors (exit code {result.returncode})")
        else:
            print(f"  {name} done")

    data_dir = os.path.join(SCRIPTS_DIR, "..", "data")
    if os.path.exists(data_dir):
        print("\nFiles saved to data/:")
        for f in sorted(os.listdir(data_dir)):
            fpath = os.path.join(data_dir, f)
            size_kb = os.path.getsize(fpath) / 1024
            print(f"  {f} ({size_kb:.1f} KB)")

    print("\nAll sources fetched.")
