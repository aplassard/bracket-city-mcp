import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
import sys

# Attempt to import requests for requests.exceptions.RequestException
# This is for type hinting and direct use in tests.
# If 'requests' is not available in the testing environment and causes issues,
# this might need to be handled (e.g., by creating a dummy exception class for tests).
try:
    import requests
except ImportError:
    # Define a dummy exception if requests is not installed.
    # This allows tests to run and reference requests.exceptions.RequestException
    # when requests itself is mocked out.
    class RequestsModuleMock:
        class exceptions:
            class RequestException(IOError): pass # Inherit from a built-in exception
    requests = RequestsModuleMock()


# Functions to test from the puzzle_loader module
from bracket_city_mcp.puzzle_loader import load_game_data_by_date
from datetime import datetime # Used for direct datetime object creation in tests if needed

class TestLoadGameDataByDate(unittest.TestCase):
    MOCK_SUCCESS_DATA = {"game": "data", "day": "Tuesday"}

    @patch('bracket_city_mcp.puzzle_loader.requests.get')
    def test_load_success_from_url(self, mock_requests_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.MOCK_SUCCESS_DATA
        mock_response.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_response

        date_str = "2025-03-15" # Valid date within range
        expected_url = f"https://raw.githubusercontent.com/aplassard/bracket-city-mcp/refs/heads/add-game-history/games/json/{date_str}.json"

        result = load_game_data_by_date(date_str)

        mock_requests_get.assert_called_once_with(expected_url, timeout=10)
        mock_response.raise_for_status.assert_called_once()
        mock_response.json.assert_called_once()
        self.assertEqual(result, self.MOCK_SUCCESS_DATA)

    def test_load_date_too_early(self):
        date_str = "2024-12-31"
        result = load_game_data_by_date(date_str)
        self.assertEqual(result, {"error": "Date is outside the valid range (2025-01-01 to 2025-06-16)."})

    def test_load_date_too_late(self):
        date_str = "2025-06-17"
        result = load_game_data_by_date(date_str)
        self.assertEqual(result, {"error": "Date is outside the valid range (2025-01-01 to 2025-06-16)."})

    def test_load_invalid_date_format(self):
        date_str = "invalid-date-format"
        result = load_game_data_by_date(date_str)
        self.assertEqual(result, {"error": "Invalid date format. Expected YYYY-MM-DD."})

    def test_load_invalid_date_format_month_day_swapped(self):
        date_str = "2025-15-03" # Invalid month
        result = load_game_data_by_date(date_str)
        self.assertEqual(result, {"error": "Invalid date format. Expected YYYY-MM-DD."})

    @patch('bracket_city_mcp.puzzle_loader.requests.get')
    def test_load_network_error(self, mock_requests_get):
        date_str = "2025-02-20" # Valid date
        expected_url = f"https://raw.githubusercontent.com/aplassard/bracket-city-mcp/refs/heads/add-game-history/games/json/{date_str}.json"

        # Configure the mock to raise RequestException
        mock_requests_get.side_effect = requests.exceptions.RequestException("Simulated network failure")

        result = load_game_data_by_date(date_str)

        mock_requests_get.assert_called_once_with(expected_url, timeout=10)
        self.assertIn("error", result)
        self.assertTrue(result["error"].startswith(f"Failed to fetch game data from URL: {expected_url}"))
        self.assertIn("Simulated network failure", result["error"])

    @patch('bracket_city_mcp.puzzle_loader.requests.get')
    def test_load_http_error(self, mock_requests_get):
        date_str = "2025-03-10" # Valid date
        expected_url = f"https://raw.githubusercontent.com/aplassard/bracket-city-mcp/refs/heads/add-game-history/games/json/{date_str}.json"

        mock_response = MagicMock()
        mock_response.status_code = 404
        # Configure raise_for_status to simulate an HTTPError
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Client Error: Not Found for url")
        mock_requests_get.return_value = mock_response

        result = load_game_data_by_date(date_str)

        mock_requests_get.assert_called_once_with(expected_url, timeout=10)
        mock_response.raise_for_status.assert_called_once()
        self.assertIn("error", result)
        self.assertTrue(result["error"].startswith(f"Failed to fetch game data from URL: {expected_url}"))
        self.assertIn("404 Client Error", result["error"])


    @patch('bracket_city_mcp.puzzle_loader.requests.get')
    def test_load_json_decode_error(self, mock_requests_get):
        date_str = "2025-04-01" # Valid date
        expected_url = f"https://raw.githubusercontent.com/aplassard/bracket-city-mcp/refs/heads/add-game-history/games/json/{date_str}.json"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        # Configure json() method to raise JSONDecodeError
        mock_response.json.side_effect = json.JSONDecodeError("Expecting value", "document text", 0)
        mock_requests_get.return_value = mock_response

        result = load_game_data_by_date(date_str)

        mock_requests_get.assert_called_once_with(expected_url, timeout=10)
        mock_response.raise_for_status.assert_called_once()
        mock_response.json.assert_called_once()
        self.assertIn("error", result)
        self.assertTrue(result["error"].startswith(f"Error decoding JSON from {expected_url}"))
        self.assertIn("Expecting value", result["error"])

if __name__ == '__main__':
    unittest.main()
