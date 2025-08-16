# Stocktwits Watcher Tracker
Tracks Stocktwits watcher (follower) counts for your favorite stocks, appending the results to a CSV for trend analysis.

## Setup
1. **Create your symbol list:**  
   - Add stock symbols (one per line, no `$`, comments allowed with `#`) to `symbols.txt`.

2. **Install dependencies:**  
   - Requires Python 3 and the `requests` library:
     ```
     pip install requests
     ```

3. **Run the tracker:**  
   ```
   python stocktwits_watcher_tracker.py
   ```

4. **Automate:**  
   - Schedule with cron (Linux/macOS) or Task Scheduler (Windows) for regular collection.

## Output

- Results are appended to `watchers_trend.csv` with columns like:
  ```
  date,AAPL_watcher,TSLA_watcher,NVDA_watcher
  2025-08-16,1000000,800000,950000
  ```

## Notes

- Edit `symbols.txt` to change which stocks are tracked.
- If a symbol is invalid or data fetch fails, that column will be blank for the run.
- The script is safe for unattended operation and designed for easy automation.
