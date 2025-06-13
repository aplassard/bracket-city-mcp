# bracket-city-mcp
Play the bracket city game via MCP server

## Installation
This project uses [uv](https://github.com/astral-sh/uv) for environment and package management, as well as a build tool if configured. To install the necessary dependencies, including development tools, navigate to the project root directory and run:
```bash
uv pip install .[dev]
```
This command will install the package and its dependencies defined in `pyproject.toml`.

## Running Tests
Tests are written using [pytest](https://docs.pytest.org/). To run the test suite, execute the following command from the project root directory:
```bash
uv run pytest
```
