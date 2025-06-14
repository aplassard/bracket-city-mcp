import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from bracket_city_mcp.game.game import Game

# Path to the game JSON files
VALID_TEST_GAME_FILE = os.path.join(PROJECT_ROOT, "tests", "data", "valid_single_end_clue_game.json")
ORIGINAL_GAME_FILE = os.path.join(PROJECT_ROOT, "games", "json", "20250110.json")

# Use the valid game as the default for the example
DEFAULT_GAME_FILE = VALID_TEST_GAME_FILE
if not os.path.exists(DEFAULT_GAME_FILE):
    print(f"Warning: Default valid game '{VALID_TEST_GAME_FILE}' not found. Trying original game file.")
    DEFAULT_GAME_FILE = ORIGINAL_GAME_FILE


def run_console_game(game_file_path: str):
    """
    Loads a game from a JSON file and allows playing it via the console.
    """
    if not os.path.exists(game_file_path):
        print(f"Error: Game file not found at {game_file_path}")
        alt_path = os.path.join(os.path.dirname(__file__), "..", game_file_path) # Assuming game_file_path was relative
        alt_path = os.path.normpath(alt_path)
        if os.path.exists(alt_path):
            print(f"Found alternative at: {alt_path}. Trying this path.")
            game_file_path = alt_path
        else:
            print(f"Please ensure the path is correct or provide a valid path.")
            return

    try:
        print(f"Attempting to load game from: {game_file_path}...")
        game = Game.from_json_file(game_file_path)
        print(f"Game loaded successfully from {game_file_path}!")
        print(f"Welcome to Bracket City MCP Puzzle.")
        print(f"Number of clues: {len(game.clues)}")
        print(f"Type 'exit' or 'quit' to stop playing.")
        print("---")

    except FileNotFoundError:
        print(f"Error: Could not find the game file at {game_file_path}")
        return
    except ValueError as ve:
        print(f"Error loading game: {ve}")
        print("This game version requires the puzzle to have exactly one end clue.")
        if game_file_path == ORIGINAL_GAME_FILE and os.path.exists(VALID_TEST_GAME_FILE):
            print(f"You could try running the example with the test game: python examples/play_game.py {VALID_TEST_GAME_FILE}")
        return
    except Exception as e:
        print(f"An unexpected error occurred while loading game: {e}")
        return

    while True:
        if not game.active_clues:
            all_completed = True
            for clue_id in game.clues:
                if not game.clues[clue_id].completed:
                    all_completed = False
                    break
            if all_completed:
                print("\nCongratulations! You've completed all clues!")
            else:
                print("\nNo more active clues, but some are still pending. The game might be stuck or completed.")
            break

        print("\nActive Clues:")
        active_clue_ids = sorted(list(game.active_clues))
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
                if game.clues[selected_clue_id].completed:
                    print(f"Clue {selected_clue_id} is now completed.")

                if selected_clue_id in game.end_clues: # Game.end_clues is a list
                    print(f"Clue {selected_clue_id} is the end clue!")
            else:
                if selected_clue_id in game.clues and not game.clues[selected_clue_id].completed:
                     print("Incorrect answer. Try again or pick another clue.")

        except ValueError:
            print("Invalid input. Please enter a number for the clue choice.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            break
        print("---")

    print("Thanks for playing!")

if __name__ == "__main__":
    game_file_to_load = DEFAULT_GAME_FILE
    if len(sys.argv) > 1:
        game_file_to_load = sys.argv[1]
        print(f"Using game file from command line argument: {game_file_to_load}")
    else:
        print(f"Using default game file: {game_file_to_load}")

    run_console_game(game_file_to_load)
