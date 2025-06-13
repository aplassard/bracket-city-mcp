import pytest
import os
from src.bracket_city_mcp.game.game import Game

# --- Path Setup ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ORIGINAL_GAME_JSON_PATH_CONFIG = os.path.join(BASE_DIR, "games", "json", "20250110.json")
if not os.path.exists(ORIGINAL_GAME_JSON_PATH_CONFIG):
    ORIGINAL_GAME_JSON_PATH_CONFIG = os.path.join("games", "json", "20250110.json") # Fallback

VALID_GAME_JSON_PATH_CONFIG = os.path.join(BASE_DIR, "tests", "data", "valid_single_end_clue_game.json")
if not os.path.exists(VALID_GAME_JSON_PATH_CONFIG):
    VALID_GAME_JSON_PATH_CONFIG = os.path.join("tests", "data", "valid_single_end_clue_game.json") # Fallback

# --- Pytest Fixtures ---

@pytest.fixture(scope="session")
def original_game_json_path() -> str:
    if not os.path.exists(ORIGINAL_GAME_JSON_PATH_CONFIG):
        pytest.skip(f"Original game file not found at {ORIGINAL_GAME_JSON_PATH_CONFIG}, skipping tests that use it.")
    return ORIGINAL_GAME_JSON_PATH_CONFIG

@pytest.fixture(scope="session")
def valid_game_json_path() -> str:
    if not os.path.exists(VALID_GAME_JSON_PATH_CONFIG):
        pytest.fail(f"Valid test game JSON file not found at: {VALID_GAME_JSON_PATH_CONFIG}")
    return VALID_GAME_JSON_PATH_CONFIG

@pytest.fixture
def valid_game(valid_game_json_path: str) -> Game:
    """Provides a fresh, valid Game instance for each test function."""
    return Game.from_json_file(valid_game_json_path)

# --- Test Functions ---

def test_game_loading_valid_json(valid_game: Game):
    assert isinstance(valid_game, Game)
    assert len(valid_game.clues) == 4, "Valid game should have 4 clues loaded."
    assert "#S1#" in valid_game.clues
    assert valid_game.clues["#S1#"].answer == "A1"

def test_loading_invalid_game_multiple_end_clues(original_game_json_path: str):
    with pytest.raises(ValueError, match="Game must have exactly one end clue. Found 3 end clues"):
        Game.from_json_file(original_game_json_path)

def test_loading_game_no_end_clues_raises_error():
    invalid_data_no_end_circular = {
         "clues": {
            "#C1#": {"clue": "c1", "answer": "a1", "depends_on": ["#C2#"]},
            "#C2#": {"clue": "c2", "answer": "a2", "depends_on": ["#C1#"]}
        }
    }
    with pytest.raises(ValueError, match="Game must have exactly one end clue. Found 0 end clues"):
        Game(invalid_data_no_end_circular)

def test_initial_start_clues_valid_game(valid_game: Game):
    expected_start_clues = {"#S1#", "#S2#"}
    assert set(valid_game.start_clues) == expected_start_clues
    assert valid_game.active_clues == expected_start_clues

def test_initial_end_clue_valid_game(valid_game: Game):
    expected_end_clues = ["#E1#"]
    assert valid_game.end_clues == expected_end_clues

def test_answer_clue_correct_start_clue_valid_game(valid_game: Game):
    clue_id_to_answer = "#S1#"
    assert clue_id_to_answer in valid_game.active_clues

    result = valid_game.answer_clue(clue_id_to_answer, "A1")
    assert result
    assert valid_game.clues[clue_id_to_answer].completed
    assert clue_id_to_answer not in valid_game.active_clues
    assert "#M1#" in valid_game.active_clues

def test_answer_clue_incorrect_valid_game(valid_game: Game):
    clue_id_to_answer = "#S1#"
    assert clue_id_to_answer in valid_game.active_clues

    result = valid_game.answer_clue(clue_id_to_answer, "wrong answer")
    assert not result
    assert not valid_game.clues[clue_id_to_answer].completed
    assert clue_id_to_answer in valid_game.active_clues

def test_answer_clue_not_active_valid_game(valid_game: Game):
    clue_id_to_answer = "#M1#"
    assert clue_id_to_answer not in valid_game.active_clues

    result = valid_game.answer_clue(clue_id_to_answer, "A3")
    assert not result
    assert not valid_game.clues[clue_id_to_answer].completed

def test_answer_clue_non_existent_valid_game(valid_game: Game):
    result = valid_game.answer_clue("#NONEXISTENT#", "any answer")
    assert not result

def test_clue_reveal_logic_to_reach_end_clue_valid_game(valid_game: Game):
    game = valid_game # Use the fixture
    assert "#S1#" in game.active_clues
    assert "#S2#" in game.active_clues
    assert "#M1#" not in game.active_clues
    assert "#E1#" not in game.active_clues

    assert game.answer_clue("#S1#", "A1")
    assert "#M1#" in game.active_clues, "#M1# should be active after #S1#."
    assert "#E1#" not in game.active_clues

    assert game.answer_clue("#S2#", "A2")
    assert "#M1#" in game.active_clues
    assert "#E1#" not in game.active_clues, "#E1# should not be active yet, needs #M1#."

    assert game.answer_clue("#M1#", "A3")
    assert "#E1#" in game.active_clues, "#E1# should be active now."

    assert game.answer_clue("#E1#", "A4")
    assert game.clues["#E1#"].completed
    assert "#E1#" not in game.active_clues
    assert game.active_clues == set(), "No clues should be active after end clue is solved."

# Remove if __name__ == '__main__': block
