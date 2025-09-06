#!/usr/bin/env python3
import pandas as pd
import argparse
import subprocess
import time
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description="Replay workload from CSV when system time matches timestamp.")
    parser.add_argument("--csv", type=str, required=True, help="Input CSV file with timestamp and tasks columns")
    parser.add_argument("--sleep", type=int, help="Sleep time per task in seconds", default=5)
    args = parser.parse_args()

    # Load and sort the CSV
    df = pd.read_csv(args.csv, parse_dates=["timestamp"])
    df = df.sort_values("timestamp")

    print(f"Loaded {len(df)} rows from {args.csv}. Waiting for timestamps...")

    triggered = set()

    while len(triggered) < len(df):
        now = datetime.now().replace(microsecond=0)  # ignore microseconds
        # Find rows matching current time
        matches = df[df["timestamp"] == now]
        #print(now)
        for _, row in matches.iterrows():
            idx = row.name
            if idx not in triggered:
                tasks = int(row["tasks"])
                cmd = ["python", "sleep2.py", "--tasks", str(tasks), "--sleep", str(args.sleep)]
                print(f"[{now}] Launching: {' '.join(cmd)}")
                subprocess.Popen(cmd)
                triggered.add(idx)

        time.sleep(1)  # check every second

if __name__ == "__main__":
    main()
