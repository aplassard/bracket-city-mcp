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
