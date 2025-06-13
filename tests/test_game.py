import unittest
import os
from src.bracket_city_mcp.game.game import Game
# Clue might not be directly used here but good to have if tests evolve
# from src.bracket_city_mcp.game.clue import Clue

# --- Path Setup ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Path to the original game JSON (now considered invalid due to multiple end clues)
ORIGINAL_GAME_JSON_PATH = os.path.join(BASE_DIR, "games", "json", "20250110.json")
if not os.path.exists(ORIGINAL_GAME_JSON_PATH):
    ORIGINAL_GAME_JSON_PATH = os.path.join("games", "json", "20250110.json") # Fallback

# Path to the new valid game JSON (single end clue)
VALID_GAME_JSON_PATH = os.path.join(BASE_DIR, "tests", "data", "valid_single_end_clue_game.json")
if not os.path.exists(VALID_GAME_JSON_PATH):
    VALID_GAME_JSON_PATH = os.path.join("tests", "data", "valid_single_end_clue_game.json") # Fallback


class TestGame(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Load the valid game once for all tests in this class."""
        if not os.path.exists(VALID_GAME_JSON_PATH):
            raise FileNotFoundError(f"Valid test game JSON file not found at: {VALID_GAME_JSON_PATH}")
        cls.valid_game_instance = Game.from_json_file(VALID_GAME_JSON_PATH)

        # Check if the original (now invalid) game file exists for specific tests
        cls.original_game_file_exists = os.path.exists(ORIGINAL_GAME_JSON_PATH)
        if not cls.original_game_file_exists:
            print(f"Warning: Original game file {ORIGINAL_GAME_JSON_PATH} not found. Some tests will be skipped.")


    def setUp(self):
        """Create a fresh valid game instance for each test to ensure independence."""
        self.game = Game.from_json_file(VALID_GAME_JSON_PATH) # Default to valid game

    def test_game_loading_valid_json(self):
        self.assertIsInstance(self.game, Game)
        self.assertTrue(len(self.game.clues) == 4, "Valid game should have 4 clues loaded.")
        self.assertIn("#S1#", self.game.clues)
        self.assertEqual(self.game.clues["#S1#"].answer, "A1")

    def test_loading_invalid_game_multiple_end_clues(self):
        if not self.original_game_file_exists:
            self.skipTest(f"Original game file not found at {ORIGINAL_GAME_JSON_PATH}")

        with self.assertRaisesRegex(ValueError, "Game must have exactly one end clue. Found 3 end clues"):
            Game.from_json_file(ORIGINAL_GAME_JSON_PATH)

    def test_loading_game_no_end_clues_raises_error(self):
        # Test with a game structure that would result in zero end clues
        # For example, a circular dependency or a single clue that points to itself (though _build_graph might prevent some of this)
        # More simply, a game where all clues are depended upon by others.
        invalid_data_no_end = {
            "clues": {
                "#C1#": {"clue": "c1", "answer": "a1", "depends_on": []},
                "#C2#": {"clue": "c2", "answer": "a2", "depends_on": ["#C1#"]}
            }
        }
        # In this setup, #C1# is depended on by #C2#, and #C2# is not depended on by anything.
        # So this test case definition is wrong. Let's fix it.
        # #C1# depends on #C2#, #C2# depends on #C1# -> 0 end clues
        invalid_data_no_end_circular = {
             "clues": {
                "#C1#": {"clue": "c1", "answer": "a1", "depends_on": ["#C2#"]},
                "#C2#": {"clue": "c2", "answer": "a2", "depends_on": ["#C1#"]}
            }
        }
        with self.assertRaisesRegex(ValueError, "Game must have exactly one end clue. Found 0 end clues"):
            Game(invalid_data_no_end_circular)


    def test_initial_start_clues_valid_game(self):
        expected_start_clues = {"#S1#", "#S2#"}
        self.assertEqual(set(self.game.start_clues), expected_start_clues)
        self.assertEqual(self.game.active_clues, expected_start_clues)

    def test_initial_end_clue_valid_game(self):
        # From valid_single_end_clue_game.json
        expected_end_clues = ["#E1#"] # Stored as a list
        self.assertEqual(self.game.end_clues, expected_end_clues,
                         f"End clues do not match. Got: {self.game.end_clues}")

    def test_answer_clue_correct_start_clue_valid_game(self):
        clue_id_to_answer = "#S1#" # Answer: A1
        self.assertIn(clue_id_to_answer, self.game.active_clues)

        result = self.game.answer_clue(clue_id_to_answer, "A1")
        self.assertTrue(result)
        self.assertTrue(self.game.clues[clue_id_to_answer].completed)
        self.assertNotIn(clue_id_to_answer, self.game.active_clues)

        # #M1# depends on #S1#. It should now be active.
        self.assertIn("#M1#", self.game.active_clues)

    def test_answer_clue_incorrect_valid_game(self):
        clue_id_to_answer = "#S1#"
        self.assertIn(clue_id_to_answer, self.game.active_clues)

        result = self.game.answer_clue(clue_id_to_answer, "wrong answer")
        self.assertFalse(result)
        self.assertFalse(self.game.clues[clue_id_to_answer].completed)
        self.assertIn(clue_id_to_answer, self.game.active_clues)

    def test_answer_clue_not_active_valid_game(self):
        clue_id_to_answer = "#M1#" # Depends on #S1#
        self.assertNotIn(clue_id_to_answer, self.game.active_clues)

        result = self.game.answer_clue(clue_id_to_answer, "A3") # Correct answer for #M1#
        self.assertFalse(result)
        self.assertFalse(self.game.clues[clue_id_to_answer].completed)

    def test_answer_clue_non_existent_valid_game(self):
        result = self.game.answer_clue("#NONEXISTENT#", "any answer")
        self.assertFalse(result)

    def test_clue_reveal_logic_to_reach_end_clue_valid_game(self):
        # #S1# (A1), #S2# (A2) -> start
        # #M1# (A3) depends on #S1#
        # #E1# (A4) depends on #S2#, #M1# -> end

        self.assertIn("#S1#", self.game.active_clues)
        self.assertIn("#S2#", self.game.active_clues)
        self.assertNotIn("#M1#", self.game.active_clues)
        self.assertNotIn("#E1#", self.game.active_clues)

        # Answer #S1# -> "A1"
        self.assertTrue(self.game.answer_clue("#S1#", "A1"))
        self.assertIn("#M1#", self.game.active_clues, "#M1# should be active after #S1#.")
        self.assertNotIn("#E1#", self.game.active_clues) # #E1# also needs #S2#

        # Answer #S2# -> "A2"
        self.assertTrue(self.game.answer_clue("#S2#", "A2"))
        self.assertIn("#M1#", self.game.active_clues) # #M1# still active (if not answered) or was already active
        # #E1# needs #M1# to be completed first.
        self.assertNotIn("#E1#", self.game.active_clues, "#E1# should not be active yet, needs #M1#.")

        # Answer #M1# -> "A3"
        self.assertTrue(self.game.answer_clue("#M1#", "A3"))
        # Now #E1# should be active as #S2# and #M1# are complete.
        self.assertIn("#E1#", self.game.active_clues, "#E1# should be active now.")

        # Answer #E1# -> "A4"
        self.assertTrue(self.game.answer_clue("#E1#", "A4"))
        self.assertTrue(self.game.clues["#E1#"].completed)
        self.assertNotIn("#E1#", self.game.active_clues)
        self.assertEqual(self.game.active_clues, set(), "No clues should be active after end clue is solved.")

if __name__ == '__main__':
    unittest.main()
