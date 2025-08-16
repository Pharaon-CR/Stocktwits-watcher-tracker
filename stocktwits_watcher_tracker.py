import requests
import csv
import os
import datetime

SYMBOLS_FILE = "symbols.txt"
CSV_FILE = "watchers_trend.csv"
STOCKTWITS_API = "https://api.stocktwits.com/api/2/symbols/show/{}.json"

def read_symbols(symbols_file):
    symbols = []
    with open(symbols_file, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                symbols.append(line)
    return symbols

def fetch_watcher_count(symbol):
    url = STOCKTWITS_API.format(symbol)
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data["symbol"]["followers"]
    except Exception as e:
        print(f"[ERROR] {symbol}: {e}")
        return None

def collect_data(symbols):
    counts = {}
    for symbol in symbols:
        count = fetch_watcher_count(symbol)
        counts[symbol] = count
    return counts

def write_csv_row(date_str, counts, csv_file):
    header = ["date"] + [f"{sym}_watcher" for sym in counts.keys()]
    row = [date_str] + [counts[sym] if counts[sym] is not None else "" for sym in counts.keys()]

    file_exists = os.path.isfile(csv_file)
    # If file exists, check if header matches; if not, rewrite header.
    if not file_exists:
        with open(csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerow(row)
    else:
        with open(csv_file, "r", newline="") as f:
            reader = csv.reader(f)
            existing_header = next(reader, None)
        if existing_header != header:
            # Rewrite file with new header and data
            print("[INFO] Header changed. Rewriting CSV with new structure.")
            with open(csv_file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(header)
                writer.writerow(row)
        else:
            with open(csv_file, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(row)

def main():
    today = datetime.date.today().isoformat()
    symbols = read_symbols(SYMBOLS_FILE)
    if not symbols:
        print("[ERROR] No symbols found in symbol file.")
        return
    counts = collect_data(symbols)
    write_csv_row(today, counts, CSV_FILE)

if __name__ == "__main__":
    main()