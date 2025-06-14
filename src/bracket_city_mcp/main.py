from mcp.server.fastmcp import FastMCP
from bracket_city_mcp.game.game import Game
from typing import List, Dict, Any

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

@mcp.tool(name="answer_clue")
def answer_clue(clue_id: str, answer: str) -> Dict[str, Any]:
    response = {
        "correct": False,
        "message": "",
        "available_clues": [],
        "game_completed": False,
    }

    if clue_id not in game.clues:
        response["message"] = f"Clue ID '{clue_id}' not found."
        response["available_clues"] = list(game.active_clues)
        return response

    clue_obj = game.clues[clue_id]

    if clue_obj.is_end_clue:
        game_is_truly_complete = game.is_complete # Checks if all NON-END clues are done
        if game_is_truly_complete:
            response["correct"] = True # User successfully reached the end state
            response["message"] = "You've reached the final clue! Congratulations, the game is complete!"
            response["game_completed"] = True
            response["score"] = len(game.clues) - game.incorrect_guesses
        else:
            # This case implies the end clue became active before all other prerequisites were met,
            # or the user is trying to 'answer' it prematurely.
            response["correct"] = False
            response["message"] = "This is the final clue, but there are other mysteries to solve before the story concludes."
            response["game_completed"] = False # Game isn't fully complete yet

        response["available_clues"] = list(game.active_clues) # Show currently active clues
        return response

    if clue_obj.completed:
        response["message"] = f"Clue '{clue_id}' has already been answered."
        response["available_clues"] = list(game.active_clues)
        return response

    if clue_id not in game.active_clues:
        response["message"] = f"Clue '{clue_id}' is not currently available. Solve its dependencies first."
        # Even if not active, it might be useful to show currently active ones.
        response["available_clues"] = list(game.active_clues)
        return response

    # Attempt to answer the clue
    is_correct = game.answer_clue(clue_id, answer)
    response["correct"] = is_correct

    if is_correct:
        response["message"] = "Correct!"
    else:
        response["message"] = "Incorrect answer."

    # Update available clues after the attempt
    response["available_clues"] = list(game.active_clues)

    # Check for game completion
    game_completed = game.is_complete
    response["game_completed"] = game_completed

    if game_completed:
        response["message"] += " Congratulations! You've completed the game."
        # Calculate score: total clues - incorrect guesses.
        # The end clue itself doesn't count towards "solvable" clues for scoring if it has no answer.
        # However, len(game.clues) includes it. This definition is fine for now.
        score = len(game.clues) - game.incorrect_guesses
        response["score"] = score

    return response

if __name__ == "__main__":
    # TODO: Make host and port configurable
    mcp.run(host="0.0.0.0", port=8080)

# TODO: Implement tests for the BracketCity MCP server.
# The FastMCP library does not seem to provide a test_client() method.
# A different testing strategy is needed, possibly involving running the
# server in a separate thread/process and using an MCP client to make requests.
# Consult FastMCP documentation or examples for the recommended approach.
