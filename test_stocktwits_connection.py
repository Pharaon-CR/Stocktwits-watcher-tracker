import unittest
import requests

class TestStocktwitsAPI(unittest.TestCase):
    def setUp(self):
        self.base_url = "https://api.stocktwits.com/api/2/streams/symbol/"
        self.symbol = "AAPL"  # Test with a popular symbol

    def test_stocktwits_access_and_watcher(self):
        url = f"{self.base_url}{self.symbol}.json"
        response = requests.get(url)
        self.assertEqual(response.status_code, 200, f"Failed to access Stocktwits for {self.symbol}")

        data = response.json()
        # Stocktwits symbol response contains a 'symbol' dict with 'watchlist_count'
        self.assertIn("symbol", data, "Missing 'symbol' in Stocktwits response")
        self.assertIn("watchlist_count", data["symbol"], "Missing 'watchlist_count' in Stocktwits symbol data")
        watcher_count = data["symbol"]["watchlist_count"]
        self.assertIsInstance(watcher_count, int, "Watcher count is not an integer")
        print(f"Watcher count for {self.symbol}: {watcher_count}")

if __name__ == "__main__":
    unittest.main()