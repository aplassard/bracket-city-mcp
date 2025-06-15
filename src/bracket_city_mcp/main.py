from mcp.server.fastmcp import FastMCP
from bracket_city_mcp.game.game import Game
from typing import List, Dict, Any

"""
Main module for the BracketCity MCP server.

This module initializes and runs the FastMCP server for the BracketCity game.
It defines MCP tools for interacting with the game, such as
retrieving game state, clue details, and submitting answers.

The current testing strategy for this server involves running it in a separate
thread or process and using an MCP client to make requests, as FastMCP does
not provide a direct test_client() method. This is a known limitation.
"""

# Initialize the game
# TODO: Make the game file path configurable (future enhancement)
game = Game.from_json_file("games/json/20250110.json")

# Create the MCP server
mcp = FastMCP("BracketCity")

# Health check endpoint
@mcp.tool()
def health() -> str:
    """Provides a simple health check for the server."""
    return "OK"

@mcp.tool(name="get_full_game_text")
def get_full_game_text() -> str:
    """Tool to retrieve the full game text, showing all clues and their current state."""
    return game.get_rendered_game_text()

@mcp.tool(name="get_clue_text")
def get_clue_text(clue_id: str) -> str:
    """
    Tool to retrieve the rendered text for a specific clue.

    Args:
        clue_id: The ID of the clue to retrieve.

    Returns:
        The rendered text of the clue, or an error message if the clue is not found.
    """
    try:
        return game.get_rendered_clue_text(clue_id)
    except ValueError as e:
        # TODO: Return a more appropriate error code.
        # Currently returns a plain string error message. A structured error
        # (e.g., a JSON response with an error code) might be more appropriate
        # for machine clients.
        return str(e)

@mcp.tool(name="get_available_clues")
def get_available_clues() -> List[str]:
    """Tool to retrieve a list of IDs for all currently available (active) clues."""
    return list(game.active_clues)

@mcp.tool(name="get_clue_context")
def get_clue_context(clue_id: str) -> Dict[str, Any]:
    """
    Retrieves detailed context for a given clue_id.

    This includes the clue's rendered text, its completion status,
    previous incorrect answers, any clues it depends on, and
    the first clue that depends on it (parent clue).

    Args:
        clue_id: The ID of the clue for which to retrieve context.

    Returns:
        A dictionary containing the clue's context. If the clue_id is
        not found, returns a dictionary with an "error" message and
        a 404 "status_code".
    """
    clue_obj = game.clues.get(clue_id)

    if clue_obj is None:
        return {"error": f"Clue ID '{clue_id}' not found.", "status_code": 404}

    return {
        "clue_id": clue_obj.clue_id,
        "rendered_text": clue_obj.get_rendered_text(game),
        "is_correctly_answered": clue_obj.completed,
        "previous_answers": list(clue_obj.previous_answers),
        "depends_on_clues": list(clue_obj.depends_on), # Ensure it's a list copy
        # Use the new Game method to get the first dependent (child) clue ID
        "parent_clue_id": game.get_first_dependent_clue_id(clue_obj.clue_id),
    }

@mcp.tool(name="answer_clue")
def answer_clue(clue_id: str, answer: str) -> Dict[str, Any]:
    """
    Submits an answer for a given clue and updates the game state.

    This tool checks if the provided answer for the specified clue_id is correct.
    It updates the clue's status, records incorrect guesses, and potentially
    unlocks new clues or completes the game.

    Side effects:
    - If the answer is incorrect, `game.incorrect_guesses` is incremented.
    - If the answer is correct, the clue is marked as completed.
    - `game.active_clues` is updated based on the outcome.
    - If the game is completed, the response will indicate this and include a score.

    Args:
        clue_id: The ID of the clue being answered.
        answer: The proposed answer for the clue.

    Returns:
        A dictionary containing:
        - "correct" (bool): Whether the answer was correct.
        - "message" (str): A message describing the outcome.
        - "available_clues" (List[str]): A list of currently active clue IDs.
        - "game_completed" (bool): Whether the game is now complete.
        - "score" (int, optional): The player's score if the game is completed.
          If the clue_id is not found, or already answered, or not active,
          an appropriate message is returned and the game state remains unchanged
          regarding the specific answer attempt.
    """
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
            response["score"] = game.incorrect_guesses
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
        score = game.incorrect_guesses
        response["score"] = score

    return response

if __name__ == "__main__":
    # TODO: Make host and port configurable (future enhancement for server execution)
    mcp.run(host="0.0.0.0", port=8080)

# TODO: Implement tests for the BracketCity MCP server. (See module docstring for more details)
# The FastMCP library does not seem to provide a test_client() method.
# A different testing strategy is needed, possibly involving running the
# server in a separate thread/process and using an MCP client to make requests.
# Consult FastMCP documentation or examples for the recommended approach.
