#!/usr/bin/env python3
"""
Stocktwits Watchlist Tracker (Anti-bot Optimized)

INSTRUCTIONS:
-------------
- List your stock symbols (one per line) in a file named 'symbols.txt' in the same directory as this script.
- Lines starting with '#' or blank lines are ignored.
- Example symbols.txt:
    # List your stock symbols here, one per line.
    ENLV
    IOBT
    BTAI

- Run this script weekly via GitHub Actions or locally. Results are appended to 'stocktwits_watchers.csv'.
- All symbols are processed in a single run; the CSV is updated only once per run.
- The script randomizes requests and User-Agents to bypass anti-bot protections as much as possible.

REQUIREMENTS:
-------------
- Python 3.x
- Standard libraries only: requests, csv, datetime, os, time, random

USAGE:
------
    python stocktwits_watchlist_tracker.py
"""

import os
import csv
import requests
import time
import random
from datetime import datetime

SYMBOLS_FILE = "symbols.txt"
CSV_FILE = "stocktwits_watchers.csv"
API_URL_TEMPLATE = "https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json"
MAX_RETRIES = 6  # will use exponential backoff
MIN_SLEEP = 2
MAX_SLEEP = 6

# List of real browser User-Agents to rotate (add more as needed)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/116.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
]

def get_random_headers():
    """Return randomized headers for each request."""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://stocktwits.com/",
        "Connection": "keep-alive",
        "DNT": "1",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
    }

def read_symbols(symbols_file):
    """Read stock symbols from a file, ignoring comments and blank lines."""
    symbols = []
    if not os.path.exists(symbols_file):
        print(f"Symbols file '{symbols_file}' not found.")
        return symbols
    with open(symbols_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            symbols.append(line.upper())
    return symbols

def fetch_watchlist_count(session, symbol):
    """
    Fetch the watchlist_count for a given symbol from Stocktwits API,
    rotating User-Agent and using exponential backoff for retries.
    """
    url = API_URL_TEMPLATE.format(symbol=symbol)
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            headers = get_random_headers()
            resp = session.get(url, timeout=10, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                count = data.get("symbol", {}).get("watchlist_count")
                if count is None:
                    return None, f"No 'watchlist_count' in response for {symbol}"
                return count, None
            elif resp.status_code == 429:
                # Rate limited
                wait = RETRY_WAIT = min(60, (2 ** attempt) + random.randint(0, 5))
                print(f"Rate limited on {symbol}. Waiting {wait} seconds and retrying ({attempt}/{MAX_RETRIES})...")
                time.sleep(wait)
                continue
            elif resp.status_code == 403:
                # Forbidden, likely anti-bot; wait and retry
                wait = RETRY_WAIT = min(90, (2 ** attempt) + random.randint(2, 10))
                print(f"HTTP 403 Forbidden for {symbol}. Waiting {wait} seconds and retrying ({attempt}/{MAX_RETRIES})...")
                time.sleep(wait)
                continue
            elif resp.status_code >= 500:
                # Server error, try again soon
                wait = 5 + random.randint(0, 5)
                print(f"Server error {resp.status_code} for {symbol}. Waiting {wait} seconds and retrying ({attempt}/{MAX_RETRIES})...")
                time.sleep(wait)
                continue
            else:
                return None, f"HTTP {resp.status_code} for {symbol}: {resp.text}"
        except requests.RequestException as e:
            wait = 5 + random.randint(0, 5)
            print(f"Network error for {symbol}: {e}. Waiting {wait} seconds and retrying ({attempt}/{MAX_RETRIES})...")
            time.sleep(wait)
    return None, f"Failed to fetch data for {symbol} after {MAX_RETRIES} attempts."

def ensure_csv(csv_file):
    """Ensure the CSV file exists with appropriate headers."""
    if not os.path.exists(csv_file):
        with open(csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "symbol", "watchers"])

def append_many_to_csv(csv_file, rows):
    """Append multiple rows to the CSV file in one operation."""
    with open(csv_file, "a", newline="") as f:
        writer = csv.writer(f)
        for row in rows:
            writer.writerow(row)

def main():
    symbols = read_symbols(SYMBOLS_FILE)
    if not symbols:
        print("No symbols to process. Please check your 'symbols.txt'.")
        return

    ensure_csv(CSV_FILE)
    session = requests.Session()  # Persist cookies and connection
    date_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    results = []

    for idx, symbol in enumerate(symbols):
        count, error = fetch_watchlist_count(session, symbol)
        if error:
            print(f"[{date_str}] {symbol}: ERROR - {error}")
            continue
        results.append([date_str, symbol, count])
        print(f"[{date_str}] {symbol}: {count}")
        if idx < len(symbols) - 1:
            sleep_time = random.uniform(MIN_SLEEP, MAX_SLEEP)
            print(f"Sleeping {sleep_time:.2f} seconds before next symbol...")
            time.sleep(sleep_time)

    if results:
        append_many_to_csv(CSV_FILE, results)
        print(f"Appended {len(results)} rows to {CSV_FILE}")

if __name__ == "__main__":
    main()
