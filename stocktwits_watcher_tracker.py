#!/usr/bin/env python3
"""
Stocktwits Watchlist Tracker

INSTRUCTIONS:
-------------
- List your stock symbols (one per line) in a file named 'symbols.txt' in the same directory as this script.
- Lines starting with '#' or blank lines are ignored.
- Example symbols.txt:
    # List your stock symbols here, one per line.
    ENLV
    IOBT
    BTAI

- Run this script to fetch the current 'watchlist_count' for each symbol from Stocktwits, and append results to 'stocktwits_watchers.csv'.
- The CSV will be created with columns: date, symbol, watchers, if it doesn't exist.
- You can update 'symbols.txt' at any time to track different symbols; the script adapts automatically.

REQUIREMENTS:
-------------
- Python 3.x
- Standard libraries only: requests, csv, datetime, os, time

USAGE:
------
    python stocktwits_watchlist_tracker.py
"""

import os
import csv
import requests
import time
from datetime import datetime

# Editable configuration
SYMBOLS_FILE = "symbols.txt"
CSV_FILE = "stocktwits_watchers.csv"
API_URL_TEMPLATE = "https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json"
MAX_RETRIES = 5
RETRY_WAIT = 15  # seconds to wait on rate-limit or server error

# Headers to mimic a real browser (helps bypass basic anti-bot checks)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/115.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://stocktwits.com/",
    "Connection": "keep-alive",
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

def fetch_watchlist_count(symbol):
    """
    Fetch the watchlist_count for a given symbol from Stocktwits API.
    Handles rate limiting with retries.
    Returns (watchlist_count, None) on success, (None, error_message) on failure.
    """
    url = API_URL_TEMPLATE.format(symbol=symbol)
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, timeout=10, headers=HEADERS)
            if resp.status_code == 429:
                # Rate limited
                print(f"Rate limited on {symbol}. Waiting {RETRY_WAIT} seconds and retrying ({attempt}/{MAX_RETRIES})...")
                time.sleep(RETRY_WAIT)
                continue
            elif resp.status_code == 403:
                # Forbidden, possibly blocked by anti-bot
                print(f"HTTP 403 Forbidden for {symbol}. Possible anti-bot block. Waiting {RETRY_WAIT} seconds and retrying ({attempt}/{MAX_RETRIES})...")
                time.sleep(RETRY_WAIT)
                continue
            elif resp.status_code >= 500:
                # Server error
                print(f"Server error for {symbol}. Waiting {RETRY_WAIT} seconds and retrying ({attempt}/{MAX_RETRIES})...")
                time.sleep(RETRY_WAIT)
                continue
            elif resp.status_code != 200:
                err = f"HTTP {resp.status_code} for {symbol}: {resp.text}"
                return None, err
            data = resp.json()
            count = data.get("symbol", {}).get("watchlist_count")
            if count is None:
                return None, f"No 'watchlist_count' in response for {symbol}"
            return count, None
        except requests.RequestException as e:
            print(f"Network error for {symbol}: {e}. Waiting {RETRY_WAIT} seconds and retrying ({attempt}/{MAX_RETRIES})...")
            time.sleep(RETRY_WAIT)
    return None, f"Failed to fetch data for {symbol} after {MAX_RETRIES} attempts."

def ensure_csv(csv_file):
    """Ensure the CSV file exists with appropriate headers."""
    if not os.path.exists(csv_file):
        with open(csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "symbol", "watchers"])

def append_to_csv(csv_file, date_str, symbol, watchers):
    """Append a single row to the CSV file."""
    with open(csv_file, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([date_str, symbol, watchers])

def main():
    # Step 1: Read symbols
    symbols = read_symbols(SYMBOLS_FILE)
    if not symbols:
        print("No symbols to process. Please check your 'symbols.txt'.")
        return

    # Step 2: Ensure CSV file exists
    ensure_csv(CSV_FILE)

    # Step 3: For each symbol, fetch and log watcher count
    date_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    for symbol in symbols:
        watchers, error = fetch_watchlist_count(symbol)
        if error:
            print(f"[{date_str}] {symbol}: ERROR - {error}")
            continue
        append_to_csv(CSV_FILE, date_str, symbol, watchers)
        print(f"[{date_str}] {symbol}: {watchers}")

if __name__ == "__main__":
    main()
