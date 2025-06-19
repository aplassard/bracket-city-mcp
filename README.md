# bracket-city-mcp

Play the bracket city game via MCP server.

## Project Overview

Bracket City MCP is a server designed for playing text-based adventure games. It utilizes the Multi-Character Protocol (MCP) to allow clients to interact with the game world, retrieve information, and progress through the narrative by solving clues.

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for environment and package management.
Note: This project requires Python 3.10 or newer.

1.  **Create and activate a virtual environment**:
    It's recommended to use a virtual environment for managing project dependencies.
    ```bash
    uv venv .venv  # Create a virtual environment in .venv
    source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate
    ```
    This creates a new virtual environment in a directory named `.venv` and then activates it.

2.  **Install dependencies**:
    With the virtual environment activated, install the package in editable mode along with its development dependencies:
    ```bash
    uv pip install -e .[dev]
    ```
    The `-e` flag installs the project in "editable" mode, meaning changes to the source code are immediately reflected when running the project. The `.[dev]` part ensures that development dependencies (like `pytest` and other testing tools) are also installed.

## Running the Server

To start the Bracket City MCP server:

1.  **Ensure your virtual environment is active** and dependencies are installed (see Installation).
2.  **Run the main server script**:
    ```bash
    uv run bracket-city-mcp
    ```
    This command becomes available after you've installed the package using `uv pip install -e .[dev]` as described in the Installation section.
    Currently, the server will run on `0.0.0.0` at port `8080`. These are hardcoded for now, but making them configurable is a planned enhancement.

## MCP Tools and Resources

The server exposes the following MCP tools and resources for interacting with the game:

### Tools

*   **`health` (GET)**
    *   Purpose: Performs a simple health check of the server.
    *   Parameters: None.
    *   Returns: "OK" if the server is running.

*   **`get_clue_context` (GET)**
    *   Purpose: Retrieves detailed information about a specific clue.
    *   Parameters:
        *   `clue_id` (string): The ID of the clue.
    *   Returns: A JSON object with the clue's text, completion status, previous answers, dependencies, etc.

*   **`answer_clue` (POST)**
    *   Purpose: Submits an answer for a specific clue.
    *   Parameters:
        *   `clue_id` (string): The ID of the clue being answered.
        *   `answer` (string): The proposed answer.
    *   Returns: A JSON object indicating if the answer was correct, a message, currently available clues, and game completion status.

*   **`load_puzzle_by_date` (POST)**
    *   Purpose: Loads a puzzle from a pre-existing local JSON file, by date. This updates the currently active game on the server. Assumes JSON files are located in a path like `games/json/{YYYYMMDD}.json`.
    *   Parameters:
        *   `date_str` (string): The date of the puzzle in "YYYYMMDD" format (e.g., "20240101").
    *   Returns: A JSON object indicating success or failure.
        *   Example Success: `{"status": "success", "message": "Successfully loaded puzzle for date 20240101 from games/json/20240101.json.", "rendered_game_text": "..."}`
        *   Example Error: `{"status": "error", "message": "Puzzle file not found: games/json/19990101.json"}`
    *   Example MCP Call (JSON body for POST):
        ```json
        {
          "tool": "load_puzzle_by_date",
          "args": {
            "date_str": "20240101"
          }
        }
        ```

*   **`load_puzzle_from_url` (POST)**
    *   Purpose: Loads a puzzle directly from its URL on `ladypuzzle.pro` for a given date. This fetches the HTML, parses it, and updates the currently active game on the server.
    *   Parameters:
        *   `date_str` (string): The date of the puzzle in "YYYY-MM-DD" format (e.g., "2024-03-08"). The tool constructs the URL from this date.
    *   Returns: A JSON object indicating success or failure.
        *   Example Success: `{"status": "success", "message": "Successfully loaded puzzle for date 2024-03-08 from URL.", "rendered_game_text": "[Clue 1 Answer] then [Clue 2 Answer]..."}`
        *   Example Error: `{"status": "error", "message": "Failed to fetch HTML from URL: https://ladypuzzle.pro/bracket-city-hints-answers-solution/2024-03-09. Error: 404 Client Error..."}`
    *   Example MCP Call (JSON body for POST):
        ```json
        {
          "tool": "load_puzzle_from_url",
          "args": {
            "date_str": "2024-03-08"
          }
        }
        ```

### Resources

*   **`bracketcity://game` (GET)**
    *   Purpose: Retrieves the full game text, showing all clues and their current state.
    *   Parameters: None.

*   **`bracketcity://clue/{clue_id}` (GET)**
    *   Purpose: Retrieves the rendered text for a specific clue.
    *   Parameters:
        *   `clue_id` (string): The ID of the clue (part of the URL path).

*   **`bracketcity://clues/available` (GET)**
    *   Purpose: Retrieves a list of IDs for all currently available (active) clues.
    *   Parameters: None.

## Running Tests

Tests are written using [pytest](https://docs.pytest.org/). To run the test suite effectively:

1.  **Ensure your virtual environment is active** (see Installation section if you haven't set one up).
2.  **Ensure dependencies are installed** (including development dependencies, as shown above).
3.  **Run pytest**:
    With the virtual environment active and dependencies installed (including development dependencies via `uv pip install -e .[dev]`), you can run `pytest` from the root of the project:
    ```bash
    pytest
    ```
    This command will automatically discover and run all tests in the `tests` directory.

## Loading Puzzle Data

The server can load puzzle data in a couple of ways:

1.  **Default Puzzle on Start**:
    When the server starts, it loads a default puzzle. Currently, this is configured in `src/bracket_city_mcp/main.py` to load from a specific JSON file (e.g., `games/json/2025-03-07.json`).

2.  **Loading from Local JSON Files (via MCP)**:
    Puzzles can be pre-processed into JSON data files (typically stored in the `games/json/` directory, named by date like `YYYYMMDD.json`). The `load_puzzle_by_date` MCP tool can then be used to load these puzzles into the server, making them the active game. This was the primary way to switch puzzles after the server starts.

3.  **Loading Directly from URL (via MCP - New Workflow)**:
    The `load_puzzle_from_url` MCP tool provides a more direct, Python-driven workflow. Instead of manually downloading HTML files and converting them to JSON, this tool accepts a date (in "YYYY-MM-DD" format), constructs the appropriate URL for `ladypuzzle.pro`, fetches the HTML content, parses it, and loads it as the active game. This entire process happens within the Python application, leveraging the `scripts.parse_game_html.parse_game_from_url` function. This method bypasses the need for intermediate shell scripts or manual file handling for fetching new daily puzzles.

Both `load_puzzle_by_date` and `load_puzzle_from_url` allow changing the active game dynamically while the server is running.
