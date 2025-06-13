# bracket-city-mcp
Play the bracket city game via MCP server

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for environment and package management.
Note: This project requires Python 3.10 or newer.

1.  **Create and activate a virtual environment**:
    It's recommended to use a virtual environment for managing project dependencies.
    ```bash
    uv venv .venv  # Create a virtual environment in .venv
    source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate
    ```
2.  **Install dependencies**:
    With the virtual environment activated, install the package in editable mode along with its development dependencies:
    ```bash
    uv pip install -e .[dev]
    ```
    The `-e` flag installs the project in editable mode, which is useful for development. The `.[dev]` part ensures that development dependencies (like `pytest`) are also installed.

## Running Tests

Tests are written using [pytest](https://docs.pytest.org/). To run the test suite:

1.  **Ensure your virtual environment is active** (see Installation section if you haven't set one up).
2.  **Ensure dependencies are installed** (including development dependencies, as shown above).
3.  **Run pytest**:
    With the virtual environment active and dependencies installed, you can run `pytest` directly:
    ```bash
    pytest
    ```
    Alternatively, `uv run pytest` might work in some setups, but direct execution of `pytest` within an active virtual environment is the most standard approach.
