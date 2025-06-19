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
from bracket_city_mcp.puzzle_loader import (
    generate_puzzle_structure,
    parse_game_from_url,
    load_game_data_by_date
)

# Basic HTML structure for testing generate_puzzle_structure
BASIC_HTML_TEMPLATE = """
<!DOCTYPE html><html><head><title>Test</title></head><body>
{answers_list}
{interactive_div}
{solution_h1}
</body></html>
"""

ANSWERS_LIST_VALID = """
<ul id="answers-list">
    <li><h2>CLUE-A The First Clue</h2><span class="clue-text-answer">AnswerA</span></li>
    <li><h2>CLUE-B Another Clue</h2><span class="clue-text-answer">AnswerB</span></li>
</ul>
"""
INTERACTIVE_DIV_VALID = "<div class='html-answers-interactive'>[CLUE-A The First Clue] then [CLUE-B Another Clue]</div>"
SOLUTION_H1_VALID = "<h1>Today's [BRACKET CITY] Final Solution June 1, 1974: FinalAnswer</h1><strong>FinalAnswer</strong>"

VALID_PUZZLE_HTML = BASIC_HTML_TEMPLATE.format(
    answers_list=ANSWERS_LIST_VALID,
    interactive_div=INTERACTIVE_DIV_VALID,
    solution_h1=SOLUTION_H1_VALID
)

class TestGeneratePuzzleStructure(unittest.TestCase):
    def test_gps_success(self):
        data = generate_puzzle_structure(VALID_PUZZLE_HTML)
        self.assertNotIn("error", data)
        self.assertIn("clues", data)
        self.assertIn("CLUE-C1", data["clues"]) # CLUE-A The First Clue
        self.assertEqual(data["clues"]["CLUE-C1"]["answer"], "AnswerA")
        self.assertIn("CLUE-C2", data["clues"]) # CLUE-B Another Clue
        self.assertEqual(data["clues"]["CLUE-C2"]["answer"], "AnswerB")
        self.assertIn("CLUE-ROOT", data["clues"])
        self.assertEqual(data["clues"]["CLUE-ROOT"]["answer"], "FinalAnswer")
        # Depends on will be sorted
        self.assertEqual(data["clues"]["CLUE-ROOT"]["depends_on"], ["CLUE-C1", "CLUE-C2"])
        self.assertEqual(data["clues"]["CLUE-ROOT"]["clue"], "[CLUE-C1] then [CLUE-C2]")


    def test_gps_missing_answers_list(self):
        html_content = BASIC_HTML_TEMPLATE.format(answers_list="", interactive_div=INTERACTIVE_DIV_VALID, solution_h1=SOLUTION_H1_VALID)
        data = generate_puzzle_structure(html_content)
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Could not find the 'answers-list' <ul> element.")

    def test_gps_missing_interactive_div(self):
        html_content = BASIC_HTML_TEMPLATE.format(answers_list=ANSWERS_LIST_VALID, interactive_div="", solution_h1=SOLUTION_H1_VALID)
        data = generate_puzzle_structure(html_content)
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Could not find the 'html-answers-interactive' <div> element.")

    def test_gps_no_clues_in_answers_list(self):
        html_content = BASIC_HTML_TEMPLATE.format(answers_list="<ul id='answers-list'></ul>", interactive_div=INTERACTIVE_DIV_VALID, solution_h1=SOLUTION_H1_VALID)
        data = generate_puzzle_structure(html_content)
        self.assertIn("error", data)
        self.assertEqual(data["error"], "No clues found in the answers list.")

class TestParseGameFromUrl(unittest.TestCase):
    @patch('bracket_city_mcp.puzzle_loader.generate_puzzle_structure')
    @patch('bracket_city_mcp.puzzle_loader.requests.get')
    def test_pgfu_success(self, mock_requests_get, mock_gps):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html>mock html</html>"
        mock_response.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_response

        expected_data = {"clues": {"test": "data"}}
        mock_gps.return_value = expected_data

        result = parse_game_from_url("http://testurl.com/puzzle")

        mock_requests_get.assert_called_once_with("http://testurl.com/puzzle", timeout=10)
        mock_response.raise_for_status.assert_called_once()
        mock_gps.assert_called_once_with("<html>mock html</html>")
        self.assertEqual(result, expected_data)

    @patch('bracket_city_mcp.puzzle_loader.requests.get')
    def test_pgfu_requests_exception(self, mock_requests_get):
        mock_requests_get.side_effect = requests.exceptions.RequestException("Network fail")
        result = parse_game_from_url("http://testurl.com/puzzle")
        self.assertIn("error", result)
        self.assertIn("Failed to fetch HTML from URL", result["error"])
        self.assertIn("Network fail", result["error"])

    @patch('bracket_city_mcp.puzzle_loader.requests.get')
    def test_pgfu_http_error_status(self, mock_requests_get):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status = MagicMock(side_effect=requests.exceptions.HTTPError("404 Not Found"))
        mock_requests_get.return_value = mock_response

        result = parse_game_from_url("http://testurl.com/404puzzle")
        self.assertIn("error", result)
        self.assertIn("Failed to fetch HTML from URL", result["error"])
        self.assertIn("404 Not Found", result["error"])
        mock_response.raise_for_status.assert_called_once()

    @patch('bracket_city_mcp.puzzle_loader.generate_puzzle_structure')
    @patch('bracket_city_mcp.puzzle_loader.requests.get')
    def test_pgfu_gps_returns_error(self, mock_requests_get, mock_gps):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html>good html</html>"
        mock_response.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_response

        mock_gps.return_value = {"error": "gps processing failed"}

        result = parse_game_from_url("http://testurl.com/goodhtmlbadparse")
        self.assertEqual(result, {"error": "gps processing failed"})
        mock_gps.assert_called_once_with("<html>good html</html>")


class TestLoadGameDataByDate(unittest.TestCase):
    MOCK_JSON_DATA = {"clues": {"CLUE-FILE": {"clue": "From File", "answer": "FileAns"}}}
    MOCK_URL_DATA = {"clues": {"CLUE-URL": {"clue": "From URL", "answer": "UrlAns"}}}

    @patch('bracket_city_mcp.puzzle_loader.parse_game_from_url')
    @patch('bracket_city_mcp.puzzle_loader.json.load')
    @patch('builtins.open', new_callable=mock_open)
    def test_lgdbd_loads_from_file_success(self, mock_file_open, mock_json_load, mock_pgfu):
        mock_json_load.return_value = self.MOCK_JSON_DATA
        date_str = "2023-01-15"
        expected_filepath = "games/json/20230115.json"

        result = load_game_data_by_date(date_str)

        mock_file_open.assert_called_once_with(expected_filepath, 'r', encoding='utf-8')
        mock_json_load.assert_called_once() # With the file handle from mock_open
        self.assertEqual(result, self.MOCK_JSON_DATA)
        mock_pgfu.assert_not_called()

    @patch('bracket_city_mcp.puzzle_loader.parse_game_from_url')
    @patch('builtins.open', side_effect=FileNotFoundError("File not found mock"))
    def test_lgdbd_file_not_found_falls_back_to_url_success(self, mock_file_open, mock_pgfu):
        mock_pgfu.return_value = self.MOCK_URL_DATA
        date_str = "2023-01-16"
        expected_filepath = "games/json/20230116.json"
        expected_url = f"https://ladypuzzle.pro/bracket-city-hints-answers-solution/{date_str}"


        result = load_game_data_by_date(date_str)

        mock_file_open.assert_called_once_with(expected_filepath, 'r', encoding='utf-8')
        mock_pgfu.assert_called_once_with(expected_url)
        self.assertEqual(result, self.MOCK_URL_DATA)

    @patch('bracket_city_mcp.puzzle_loader.parse_game_from_url')
    @patch('builtins.open', side_effect=FileNotFoundError("File not found mock"))
    def test_lgdbd_file_not_found_url_fetch_fails(self, mock_file_open, mock_pgfu):
        mock_pgfu.return_value = {"error": "url fetch failed"}
        date_str = "2023-01-17"
        expected_filepath = "games/json/20230117.json"
        expected_url = f"https://ladypuzzle.pro/bracket-city-hints-answers-solution/{date_str}"

        result = load_game_data_by_date(date_str)

        mock_file_open.assert_called_once_with(expected_filepath, 'r', encoding='utf-8')
        mock_pgfu.assert_called_once_with(expected_url)
        self.assertEqual(result, {"error": "url fetch failed"})

    @patch('bracket_city_mcp.puzzle_loader.parse_game_from_url')
    @patch('bracket_city_mcp.puzzle_loader.json.load', side_effect=json.JSONDecodeError("Decode error", "doc", 0))
    @patch('builtins.open', new_callable=mock_open, read_data="invalid json")
    def test_lgdbd_json_decode_error(self, mock_file_open, mock_json_load, mock_pgfu):
        date_str = "2023-01-18"
        expected_filepath = "games/json/20230118.json"

        result = load_game_data_by_date(date_str)

        mock_file_open.assert_called_once_with(expected_filepath, 'r', encoding='utf-8')
        mock_json_load.assert_called_once()
        self.assertIn("error", result)
        self.assertTrue(result["error"].startswith(f"Error decoding JSON from {expected_filepath}"))
        mock_pgfu.assert_not_called()

    @patch('bracket_city_mcp.puzzle_loader.parse_game_from_url')
    @patch('builtins.open', side_effect=IOError("Disk read error")) # Generic IOError
    def test_lgdbd_other_io_error(self, mock_file_open, mock_pgfu):
        date_str = "2023-01-19"
        expected_filepath = "games/json/20230119.json"

        result = load_game_data_by_date(date_str)

        mock_file_open.assert_called_once_with(expected_filepath, 'r', encoding='utf-8')
        self.assertIn("error", result)
        self.assertTrue(result["error"].startswith(f"IOError reading file {expected_filepath}"))
        mock_pgfu.assert_not_called()

if __name__ == '__main__':
    unittest.main()
