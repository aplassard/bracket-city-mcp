import pytest
import os
from bracket_city_mcp.game import Game

# --- Path Setup ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ORIGINAL_GAME_JSON_PATH_CONFIG = os.path.join(BASE_DIR, "games", "json", "20250110.json")
if not os.path.exists(ORIGINAL_GAME_JSON_PATH_CONFIG):
    ORIGINAL_GAME_JSON_PATH_CONFIG = os.path.join("games", "json", "20250110.json")

VALID_GAME_JSON_PATH_CONFIG = os.path.join(BASE_DIR, "tests", "data", "valid_single_end_clue_game.json")
if not os.path.exists(VALID_GAME_JSON_PATH_CONFIG):
    VALID_GAME_JSON_PATH_CONFIG = os.path.join("tests", "data", "valid_single_end_clue_game.json")

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

def test_loading_invalid_game_multiple_end_clues(): # Remove original_game_json_path fixture
    # Construct the path to the new test file relative to this test file's directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    invalid_game_path = os.path.join(current_dir, "data", "invalid_multiple_end_clues_game.json")

    # Ensure the new test file exists before running the test
    if not os.path.exists(invalid_game_path):
        pytest.fail(f"Test data file not found: {invalid_game_path}")

    with pytest.raises(ValueError, match=r"Game must have exactly one end clue\. Found 3 end clues: \['#END1#', '#END2#', '#END3#'\]"):
        Game.from_json_file(invalid_game_path)

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

# --- Tests for End Clue Functionality in Game ---

def test_game_loads_end_clue_correctly(valid_game: Game):
    """Tests that the game correctly identifies and sets up the end clue."""
    assert len(valid_game.end_clues) == 1, "Should be exactly one end clue."
    end_clue_id = valid_game.end_clues[0]
    assert end_clue_id == "#E1#", "The end clue ID should be #E1# for the valid_game fixture."

    end_clue = valid_game.clues[end_clue_id]
    assert end_clue.is_end_clue, "The identified end clue should have is_end_clue=True."
    assert end_clue.answer == "", "The answer for the end clue should be cleared on game load."
    assert not end_clue.completed, "End clue should not be initially completed."

# --- Tests for Incorrect Guesses ---

def test_game_incorrect_guesses_initialization(valid_game: Game):
    """Test that incorrect_guesses is initialized to 0."""
    assert valid_game.incorrect_guesses == 0

def test_game_incorrect_guesses_increment(valid_game: Game):
    """Test that incorrect_guesses increments correctly."""
    # Ensure #S1# is active
    assert "#S1#" in valid_game.active_clues

    # First incorrect guess
    result = valid_game.answer_clue("#S1#", "WrongAnswer")
    assert not result
    assert valid_game.incorrect_guesses == 1
    assert "#S1#" in valid_game.active_clues # Clue should still be active
    assert not valid_game.clues["#S1#"].completed

    # Second incorrect guess on the same clue
    result = valid_game.answer_clue("#S1#", "AnotherWrongAnswer")
    assert not result
    assert valid_game.incorrect_guesses == 2
    assert "#S1#" in valid_game.active_clues
    assert not valid_game.clues["#S1#"].completed

    # Correct answer
    result = valid_game.answer_clue("#S1#", "A1") # A1 is the correct answer for #S1#
    assert result
    assert valid_game.incorrect_guesses == 2 # Should not increment on correct answer
    assert "#S1#" not in valid_game.active_clues # Clue should now be completed and inactive
    assert valid_game.clues["#S1#"].completed

    # Attempt to answer already completed clue (incorrectly)
    result = valid_game.answer_clue("#S1#", "WrongAnswerAgain")
    assert not result # Should fail as clue is not active
    assert valid_game.incorrect_guesses == 2 # Should not increment if clue is not active/already completed

    # Attempt to answer a different active clue incorrectly
    assert "#S2#" in valid_game.active_clues
    result = valid_game.answer_clue("#S2#", "WrongAnswerForS2")
    assert not result
    assert valid_game.incorrect_guesses == 3


def test_game_incorrect_guesses_not_incremented_for_end_clue(valid_game: Game):
    """Test that incorrect_guesses is not incremented when attempting to answer an end clue."""
    # Complete prerequisite clues to make #E1# active
    assert valid_game.answer_clue("#S1#", "A1") # Correct answer for #S1#
    assert valid_game.answer_clue("#S2#", "A2") # Correct answer for #S2#
    assert valid_game.answer_clue("#M1#", "A3") # Correct answer for #M1#

    assert "#E1#" in valid_game.active_clues, "End clue #E1# should be active."

    initial_incorrect_guesses = valid_game.incorrect_guesses

    # Attempt to "answer" the end clue
    result = valid_game.answer_clue("#E1#", "AnyAttemptForEndClue")
    assert not result, "Answering an end clue should return False."
    assert valid_game.incorrect_guesses == initial_incorrect_guesses, \
        "Incorrect guesses should not change when answering an end clue."
    assert not valid_game.clues["#E1#"].completed, "End clue should not be marked completed."
    assert "#E1#" in valid_game.active_clues, "End clue should remain active."

# --- Tests for is_complete property ---

def test_game_is_complete_initial(valid_game: Game):
    """Test that a new game is not complete."""
    assert not valid_game.is_complete

def test_game_is_complete_becomes_true(valid_game: Game):
    """Test that the game becomes complete after all non-end clues are solved."""
    assert not valid_game.is_complete

    # Answer all non-end clues
    valid_game.answer_clue("#S1#", "A1")
    valid_game.answer_clue("#S2#", "A2")
    valid_game.answer_clue("#M1#", "A3")

    assert valid_game.clues["#S1#"].completed
    assert valid_game.clues["#S2#"].completed
    assert valid_game.clues["#M1#"].completed
    assert not valid_game.clues["#E1#"].completed # End clue should not be completed

    assert valid_game.is_complete, "Game should be complete now."

def test_game_is_complete_true_even_if_end_clue_answered(valid_game: Game):
    """Test that is_complete remains true after all non-end clues are solved, even if an attempt is made on the end clue."""
    valid_game.answer_clue("#S1#", "A1")
    valid_game.answer_clue("#S2#", "A2")
    valid_game.answer_clue("#M1#", "A3")

    assert valid_game.is_complete, "Game should be complete before attempting end clue."

    # Attempt to answer the end clue
    valid_game.answer_clue("#E1#", "AttemptOnEndClue")

    assert not valid_game.clues["#E1#"].completed, "End clue should not be completed."
    assert valid_game.is_complete, "Game should still be complete."


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

    # Attempt to answer the end clue. This should fail as end clues cannot be "answered".
    result_on_end_clue = game.answer_clue("#E1#", "A4") # A4 is its "answer" in JSON, but should be ignored
    assert not result_on_end_clue, "Attempting to answer an end clue should return False."
    assert not game.clues["#E1#"].completed, "End clue #E1# should not be marked as completed."

    # The end clue, once active, might remain active as it cannot be "completed" by answering.
    # This depends on the desired game flow: does an "end clue" mean the game ends when it's *revealed*,
    # or when an action is taken on it? Given current Clue logic, it cannot be completed.
    # If game.is_complete is the true measure of game completion, then active_clues can have the end clue.
    assert "#E1#" in game.active_clues, "End clue #E1# should remain in active_clues."

    # Check that all other clues are completed and inactive
    assert game.clues["#S1#"].completed and "#S1#" not in game.active_clues
    assert game.clues["#S2#"].completed and "#S2#" not in game.active_clues
    assert game.clues["#M1#"].completed and "#M1#" not in game.active_clues

    # Therefore, active_clues should only contain the end clue if it's revealed.
    assert game.active_clues == {"#E1#"}, "Only the end clue should be active if all others are solved."

    # And the game should be considered complete because all non-end clues are done.
    assert game.is_complete, "Game should be marked as complete."


def test_get_rendered_clue_text_valid_clue():
    game_data = {
        "clues": {
            "#C1#": {"clue": "Text C1", "answer": "Ans C1"},
            "#C2#": {"clue": "Text C2 uses #C1#", "answer": "Ans C2", "depends_on": ["#C1#"]}
        }
    }
    game = Game(game_data)

    assert game.get_rendered_clue_text("#C1#") == "Text C1"
    assert game.get_rendered_clue_text("#C2#") == "Text C2 uses [Text C1]"

    assert game.answer_clue("#C1#", "Ans C1")

    assert game.get_rendered_clue_text("#C1#") == "Ans C1"
    assert game.get_rendered_clue_text("#C2#") == "Text C2 uses Ans C1"

def test_get_rendered_clue_text_invalid_clue():
    game_data = {
        "clues": {
            "#C1#": {"clue": "Text C1", "answer": "Ans C1"}
        }
    }
    game = Game(game_data)
    with pytest.raises(ValueError, match="Clue ID '#NONEXISTENT#' not found in game."):
        game.get_rendered_clue_text("#NONEXISTENT#")

def test_get_rendered_game_text_simple_case_uncompleted():
    game_data = {
        "clues": {
            "#C1#": {"clue": "Text C1", "answer": "Ans C1"},
            "#END#": {"clue": "End clue depends on #C1#", "answer": "Game Over", "depends_on": ["#C1#"]}
        }
    }
    game = Game(game_data)
    # Now, end clues resolve dependencies.
    assert game.get_rendered_game_text() == "End clue depends on [Text C1]"

def test_get_rendered_game_text_simple_case_dependency_completed():
    game_data = {
        "clues": {
            "#C1#": {"clue": "Text C1", "answer": "Ans C1"},
            "#END#": {"clue": "End clue depends on #C1#", "answer": "Game Over", "depends_on": ["#C1#"]}
        }
    }
    game = Game(game_data)
    game.answer_clue("#C1#", "Ans C1")
    # End clue resolves its dependency #C1# to "Ans C1".
    assert game.get_rendered_game_text() == "End clue depends on Ans C1"

def test_get_rendered_game_text_after_end_clue_dependencies_met_and_attempted_answer():
    """
    Tests rendered game text when end clue's dependencies are met.
    Attempting to "answer" the end clue itself doesn't change its completed status
    or its answer (which is "" for end clues). So it still renders its text.
    """
    game_data = {
        "clues": {
            "#C1#": {"clue": "Text C1", "answer": "Ans C1"},
            "#END#": {"clue": "End clue depends on #C1#", "answer": "ThisIsIgnored", "depends_on": ["#C1#"]}
        }
    }
    game = Game(game_data)
    game.answer_clue("#C1#", "Ans C1") # Dependency met

    # Attempt to answer the end clue. This does not complete it.
    game.answer_clue("#END#", "AnyAnswer")

    end_clue = game.clues["#END#"]
    assert not end_clue.completed
    assert end_clue.is_end_clue
    assert end_clue.answer == ""

    # Game text should be the end clue's text with dependencies resolved.
    assert game.get_rendered_game_text() == "End clue depends on Ans C1"

    # Hypothetically, if the end clue *was* completed (e.g. by manual override for a test)
    # it should render its answer (which is "").
    end_clue.completed = True
    assert game.get_rendered_game_text() == ""
    end_clue.completed = False # reset

def test_get_rendered_game_text_complex_dependencies():
    game_data = {
        "clues": {
            "#C1#": {"clue": "Text C1", "answer": "Ans C1"},
            "#C2#": {"clue": "Text C2 uses #C1#", "answer": "Ans C2", "depends_on": ["#C1#"]},
            "#END#": {"clue": "End clue uses #C2#", "answer": "ThisWillBeIgnored", "depends_on": ["#C2#"]}
        }
    }
    game = Game(game_data)

    # Initial render: #END# resolves #C2#, which resolves #C1#. All uncompleted.
    assert game.get_rendered_game_text() == "End clue uses [Text C2 uses [Text C1]]"

    game.answer_clue("#C1#", "Ans C1") # #C1 is completed
    # #END# resolves #C2#, which resolves #C1# to "Ans C1". #C2# still uncompleted.
    assert game.get_rendered_game_text() == "End clue uses [Text C2 uses Ans C1]"

    game.answer_clue("#C2#", "Ans C2") # #C2 is completed
    # #END# resolves #C2# to "Ans C2".
    assert game.get_rendered_game_text() == "End clue uses Ans C2"

    # Attempting to answer #END# does not change its completed status.
    game.answer_clue("#END#", "AttemptToEndIt")
    end_clue = game.clues["#END#"]
    assert not end_clue.completed
    assert end_clue.is_end_clue
    assert end_clue.answer == ""
    # So, it still renders its text with resolved dependencies.
    assert game.get_rendered_game_text() == "End clue uses Ans C2"

    # Hypothetically, if the end clue *was* completed
    end_clue.completed = True
    assert game.get_rendered_game_text() == "" # It would render its answer (empty string)


# --- Tests for Game.get_first_dependent_clue_id ---

def test_get_first_dependent_clue_id_one_child(valid_game: Game):
    """Test getting the first dependent for clues that have exactly one child."""
    # From valid_single_end_clue_game.json:
    # #S1# is parent to #M1#
    # #S2# is parent to #E1# (via #M1# also, but #S2# directly makes #E1# dependent)
    # #M1# is parent to #E1#
    assert valid_game.get_first_dependent_clue_id("#S1#") == "#M1#"
    # Note: The way adj is built, if #E1# depends on #S2# and #M1#,
    # then #S2# will have #E1# in its adj list, and #M1# will also have #E1# in its adj list.
    # So, for #S2#, #E1# is a child. For #M1#, #E1# is also a child.
    assert valid_game.get_first_dependent_clue_id("#S2#") == "#E1#"
    assert valid_game.get_first_dependent_clue_id("#M1#") == "#E1#"

def test_get_first_dependent_clue_id_no_children(valid_game: Game):
    """Test getting the first dependent for a clue that has no children."""
    # #E1# is the end clue and nothing depends on it.
    assert valid_game.get_first_dependent_clue_id("#E1#") is None

def test_get_first_dependent_clue_id_non_existent_clue(valid_game: Game):
    """Test getting the first dependent for a non-existent clue ID."""
    assert valid_game.get_first_dependent_clue_id("NON_EXISTENT_CLUE") is None

def test_get_first_dependent_clue_id_multiple_children():
    """Test getting the first dependent for a clue with multiple children."""
    # Create a custom game setup for this specific scenario
    game_data_multi_child = {
        "clues": {
            "#PARENT#": {"clue": "Parent", "answer": "AP", "depends_on": []},
            "#CHILD1#": {"clue": "Child 1", "answer": "AC1", "depends_on": ["#PARENT#"]},
            "#CHILD2#": {"clue": "Child 2", "answer": "AC2", "depends_on": ["#PARENT#"]},
            "#CHILD3#": {"clue": "Child 3", "answer": "AC3", "depends_on": ["#PARENT#"]},
            # #END# now depends on all children to ensure it's the only end clue
            "#END#": {"clue": "End", "answer": "AE", "depends_on": ["#CHILD1#", "#CHILD2#", "#CHILD3#"]}
        }
    }
    game = Game(game_data_multi_child)

    # Verify that #END# is indeed the only end clue
    assert game.end_clues == ["#END#"], f"Expected only #END# as end clue, got {game.end_clues}"

    # The order in game.adj[#PARENT#] depends on the iteration order of clues during _build_graph.
    # Based on dict definition order (Python 3.7+), #CHILD1# should be first.
    assert game.adj.get("#PARENT#") == ["#CHILD1#", "#CHILD2#", "#CHILD3#"], "Children order in adj list is not as expected"
    assert game.get_first_dependent_clue_id("#PARENT#") == "#CHILD1#"

    # Test children; they should now all point to #END# as their first dependent.
    assert game.get_first_dependent_clue_id("#CHILD1#") == "#END#"
    assert game.get_first_dependent_clue_id("#CHILD2#") == "#END#"
    assert game.get_first_dependent_clue_id("#CHILD3#") == "#END#"
