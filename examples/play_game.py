import os
import sys

# Adjust the Python path to include the 'src' directory
# This allows finding the bracket_city_mcp package
# Assumes 'examples' is a sibling of 'src' or this script is run from the project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# Now we can import from our package
from bracket_city_mcp.game.game import Game

# Path to the game JSON file
# Adjust this path if your 'games' directory is located elsewhere relative to 'examples'
DEFAULT_GAME_FILE = os.path.join(PROJECT_ROOT, "games", "json", "20250110.json")

def run_console_game(game_file_path: str):
    """
    Loads a game from a JSON file and allows playing it via the console.
    """
    if not os.path.exists(game_file_path):
        print(f"Error: Game file not found at {game_file_path}")
        print(f"Please ensure the path is correct or provide a valid path.")
        # Attempt to find it relative to where the script is, if in project root.
        alt_path = os.path.join(os.path.dirname(__file__), "..", "games", "json", "20250110.json")
        alt_path = os.path.normpath(alt_path)
        if os.path.exists(alt_path):
            print(f"Found alternative at: {alt_path}. Trying this path.")
            game_file_path = alt_path
        else:
            return


    try:
        game = Game.from_json_file(game_file_path)
        print(f"Game loaded successfully from {game_file_path}!")
        print(f"Welcome to Bracket City MCP Puzzle.")
        print(f"Number of clues: {len(game.clues)}")
        print(f"Type 'exit' or 'quit' to stop playing.")
        print("---")

    except FileNotFoundError:
        print(f"Error: Could not find the game file at {game_file_path}")
        return
    except Exception as e:
        print(f"Error loading game: {e}")
        return

    while True:
        if not game.active_clues:
            all_completed = True
            for clue_id in game.clues:
                if not game.clues[clue_id].completed:
                    all_completed = False
                    break
            if all_completed:
                print("
Congratulations! You've completed all clues!")
            else:
                print("
No more active clues, but some are still pending. The game might be stuck or completed.")
            break

        print("
Active Clues:")
        active_clue_ids = sorted(list(game.active_clues)) # Sort for consistent display
        for i, clue_id in enumerate(active_clue_ids):
            print(f"  {i+1}. {clue_id}: {game.clues[clue_id].clue_text}")

        print("---")
        try:
            choice_str = input("Enter the number of the clue you want to answer (or 'exit'): ")
            if choice_str.lower() in ['exit', 'quit']:
                break

            choice_idx = int(choice_str) - 1
            if not (0 <= choice_idx < len(active_clue_ids)):
                print("Invalid choice. Please enter a number from the list.")
                continue

            selected_clue_id = active_clue_ids[choice_idx]
            answer = input(f"Enter your answer for {selected_clue_id} ('{game.clues[selected_clue_id].clue_text}'): ")

            if game.answer_clue(selected_clue_id, answer):
                print("Correct! Well done.")
                if game.clues[selected_clue_id].completed: # Double check, should be true
                    print(f"Clue {selected_clue_id} is now completed.")
                else: # Should not happen if logic is correct
                    print(f"Clue {selected_clue_id} was answered correctly but not marked completed. (DEBUG)")


                # Check if it was an end clue
                if selected_clue_id in game.end_clues:
                    print(f"Clue {selected_clue_id} is an end clue!")

            else:
                # The Game.answer_clue method returns False if clue not active OR answer wrong.
                # We already know it's active from our selection logic. So it must be a wrong answer.
                if selected_clue_id in game.clues and not game.clues[selected_clue_id].completed:
                     print("Incorrect answer. Try again or pick another clue.")
                else: # Should not happen if game.answer_clue has good conditions
                    print(f"Answer for {selected_clue_id} not accepted. It might be already completed or an issue occurred.")


        except ValueError:
            print("Invalid input. Please enter a number for the clue choice.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            # Potentially break or log for debugging
            break
        print("---")

    print("Thanks for playing!")

if __name__ == "__main__":
    game_file = DEFAULT_GAME_FILE
    if len(sys.argv) > 1:
        game_file = sys.argv[1]
        print(f"Using game file from command line argument: {game_file}")
    else:
        print(f"Using default game file: {game_file}")

    run_console_game(game_file)
