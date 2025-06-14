from mcp.server.fastmcp import FastMCP
from bracket_city_mcp.game.game import Game
from typing import List

# Initialize the game
# TODO: Make the game file path configurable
game = Game.from_json_file("games/json/20250110.json")

# Create the MCP server
mcp = FastMCP("BracketCity")

# Health check endpoint
@mcp.tool()
def health() -> str:
    return "OK"

@mcp.resource("bracketcity://game")
def get_full_game_text() -> str:
    return game.get_rendered_game_text()

@mcp.resource("bracketcity://clue/{clue_id}")
def get_clue_text(clue_id: str) -> str:
    try:
        return game.get_rendered_clue_text(clue_id)
    except ValueError as e:
        # TODO: Return a more appropriate error code
        return str(e)

@mcp.resource("bracketcity://clues/available")
def get_available_clues() -> List[str]:
    return list(game.active_clues)

if __name__ == "__main__":
    # TODO: Make host and port configurable
    mcp.run(host="0.0.0.0", port=8080)

# TODO: Implement tests for the BracketCity MCP server.
# The FastMCP library does not seem to provide a test_client() method.
# A different testing strategy is needed, possibly involving running the
# server in a separate thread/process and using an MCP client to make requests.
# Consult FastMCP documentation or examples for the recommended approach.
