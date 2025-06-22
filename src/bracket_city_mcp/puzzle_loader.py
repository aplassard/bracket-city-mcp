import sys
import json
import requests

# Note: The main() function and if __name__ == '__main__' block from
# scripts/parse_game_html.py are intentionally omitted as this is now a module.

from datetime import datetime

def load_game_data_by_date(date_str: str) -> dict:
    """
    Loads game data for a given date from a specific JSON file URL.
    Validates the date format and range.

    Args:
        date_str (str): The date of the puzzle in "YYYY-MM-DD" format.

    Returns:
        dict: A dictionary containing the puzzle data, or an error dictionary
              if loading/fetching/parsing fails or date is invalid.
    """
    try:
        # Validate date format
        parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return {"error": "Invalid date format. Expected YYYY-MM-DD."}

    # Define valid date range
    min_date = datetime(2025, 1, 1)
    max_date = datetime(2025, 6, 16)

    if not (min_date <= parsed_date <= max_date):
        return {"error": "Date is outside the valid range (2025-01-01 to 2025-06-16)."}

    # Construct the new URL
    url = f"https://raw.githubusercontent.com/aplassard/bracket-city-mcp/refs/heads/add-game-history/games/json/{date_str}.json"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        game_data = response.json()
        return game_data
    except requests.exceptions.RequestException as e:
        # Log to stderr or use proper logging if available
        print(f"Error fetching game data from {url}: {e}", file=sys.stderr)
        return {"error": f"Failed to fetch game data from URL: {url}. Error: {e}"}
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {url}: {e}", file=sys.stderr)
        return {"error": f"Error decoding JSON from {url}: {e}"}
    except Exception as e: # Catch any other unexpected errors
        print(f"An unexpected error occurred while loading game data for {date_str}: {e}", file=sys.stderr)
        return {"error": f"An unexpected error occurred while loading game data for {date_str}: {e}"}
