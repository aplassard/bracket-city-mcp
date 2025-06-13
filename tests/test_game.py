import unittest
import os
from src.bracket_city_mcp.game.game import Game
from src.bracket_city_mcp.game.clue import Clue

# Determine the correct path to the JSON file relative to this test file.
# Assumes tests are run from the root of the project or that the path is resolvable.
# If tests/ is a subdir of the project root, and games/ is another subdir of project root:
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GAME_JSON_PATH = os.path.join(BASE_DIR, "games", "json", "20250110.json")
# Fallback if the above doesn't work in the execution environment, try a simpler relative path
if not os.path.exists(GAME_JSON_PATH):
    GAME_JSON_PATH = os.path.join("games", "json", "20250110.json")


class TestGame(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Load the game once for all tests in this class."""
        if not os.path.exists(GAME_JSON_PATH):
            raise FileNotFoundError(
                f"Test game JSON file not found at calculated path: {GAME_JSON_PATH}. "
                f"BASE_DIR: {BASE_DIR}, CWD: {os.getcwd()}"
            )
        cls.game_instance = Game.from_json_file(GAME_JSON_PATH)

    def setUp(self):
        """Create a fresh game instance for each test to ensure independence."""
        # Re-load the game from the JSON file for each test to reset state
        self.game = Game.from_json_file(GAME_JSON_PATH)

    def test_game_loading_from_json(self):
        self.assertIsInstance(self.game, Game)
        self.assertTrue(len(self.game.clues) > 0, "Game should have clues loaded.")
        # Check a specific clue to see if it's loaded correctly
        self.assertIn("#C1#", self.game.clues)
        self.assertEqual(self.game.clues["#C1#"].answer, "pig")

    def test_initial_start_clues(self):
        # Expected start clues from 20250110.json (those with empty "depends_on")
        # #C1#, #C2#, #C7#, #C9#, #C15#, #C17#
        expected_start_clues = {"#C1#", "#C2#", "#C7#", "#C9#", "#C15#", "#C17#"}
        self.assertEqual(set(self.game.start_clues), expected_start_clues,
                         f"Start clues do not match. Got: {self.game.start_clues}")
        self.assertEqual(self.game.active_clues, expected_start_clues,
                         "Initial active clues should be the start clues.")

    def test_initial_end_clues(self):
        # Expected end clues from 20250110.json (clues not depended upon by any other clue)
        # #C6#, #C14#, #C18#
        # Note: #C11# has an empty answer, but is depended upon by #C12#.
        #       #C4# -> #C5# -> #C6#
        #       #C13# & #C8# -> #C14#
        #       #C16# & #C17# -> #C18#
        expected_end_clues = {"#C6#", "#C14#", "#C18#"}
        self.assertEqual(set(self.game.end_clues), expected_end_clues,
                         f"End clues do not match. Got: {self.game.end_clues}")

    def test_answer_clue_correct_start_clue(self):
        clue_id_to_answer = "#C1#" # Depends on: [], Answer: "pig"
        self.assertIn(clue_id_to_answer, self.game.active_clues, "Start clue should be active.")

        result = self.game.answer_clue(clue_id_to_answer, "pig")
        self.assertTrue(result, "Answer should be correct.")
        self.assertTrue(self.game.clues[clue_id_to_answer].completed, "Clue should be marked completed.")
        self.assertNotIn(clue_id_to_answer, self.game.active_clues, "Completed clue should be removed from active.")

        # Check if #C6# (depends on #C1#, #C5#) becomes active.
        # For #C6# to be active, #C5# also needs to be completed.
        # #C5# depends on #C4# -> #C3# -> #C2#. So #C6# won't be active yet.
        self.assertNotIn("#C6#", self.game.active_clues, "#C6# should not be active yet.")

    def test_answer_clue_incorrect(self):
        clue_id_to_answer = "#C1#"
        self.assertIn(clue_id_to_answer, self.game.active_clues)

        result = self.game.answer_clue(clue_id_to_answer, "wrong answer")
        self.assertFalse(result, "Answer should be incorrect.")
        self.assertFalse(self.game.clues[clue_id_to_answer].completed, "Clue should not be marked completed.")
        self.assertIn(clue_id_to_answer, self.game.active_clues, "Incorrectly answered clue should remain active.")

    def test_answer_clue_not_active(self):
        # #C3# depends on #C2# and should not be active initially.
        clue_id_to_answer = "#C3#"
        self.assertNotIn(clue_id_to_answer, self.game.active_clues, "#C3# should not be active initially.")

        result = self.game.answer_clue(clue_id_to_answer, "body") # Correct answer for #C3#
        self.assertFalse(result, "Should not be able to answer an inactive clue.")
        self.assertFalse(self.game.clues[clue_id_to_answer].completed, "Inactive clue should not be marked completed.")

    def test_answer_clue_non_existent(self):
        result = self.game.answer_clue("#NONEXISTENT#", "any answer")
        self.assertFalse(result, "Answering a non-existent clue should fail.")

    def test_clue_reveal_logic(self):
        # Scenario: Answer #C2# (den), then #C3# (body) should become active.
        # #C2# (den) - start clue
        # #C3# (body) - depends on #C2#

        self.assertIn("#C2#", self.game.active_clues)
        self.assertNotIn("#C3#", self.game.active_clues)

        # Answer #C2# correctly
        res_c2 = self.game.answer_clue("#C2#", "den")
        self.assertTrue(res_c2)
        self.assertTrue(self.game.clues["#C2#"].completed)
        self.assertNotIn("#C2#", self.game.active_clues)

        # Now #C3# should be active
        self.assertIn("#C3#", self.game.active_clues, "#C3# should be revealed and active.")

        # Answer #C3# correctly
        res_c3 = self.game.answer_clue("#C3#", "body")
        self.assertTrue(res_c3)
        self.assertTrue(self.game.clues["#C3#"].completed)
        self.assertNotIn("#C3#", self.game.active_clues)

        # #C4# (bound) depends on #C3#. It should now be active.
        self.assertIn("#C4#", self.game.active_clues, "#C4# should be revealed and active.")

    def test_complex_reveal_multiple_dependencies(self):
        # #C6# depends on #C1# (pig) and #C5# (pig)
        # #C1# is a start clue.
        # #C5# depends on #C4# (bound) -> #C3# (body) -> #C2# (den)
        # We need to answer #C1#, #C2#, #C3#, #C4#, #C5# to activate #C6#

        # Initial state for relevant clues
        self.assertIn("#C1#", self.game.active_clues)
        self.assertIn("#C2#", self.game.active_clues)
        self.assertNotIn("#C3#", self.game.active_clues)
        self.assertNotIn("#C4#", self.game.active_clues)
        self.assertNotIn("#C5#", self.game.active_clues)
        self.assertNotIn("#C6#", self.game.active_clues)

        # Answer #C1# -> "pig"
        self.assertTrue(self.game.answer_clue("#C1#", "pig"))
        self.assertNotIn("#C6#", self.game.active_clues, "#C6# needs #C5# too.")

        # Answer #C2# -> "den"
        self.assertTrue(self.game.answer_clue("#C2#", "den"))
        self.assertIn("#C3#", self.game.active_clues)
        self.assertNotIn("#C6#", self.game.active_clues)

        # Answer #C3# -> "body"
        self.assertTrue(self.game.answer_clue("#C3#", "body"))
        self.assertIn("#C4#", self.game.active_clues)
        self.assertNotIn("#C6#", self.game.active_clues)

        # Answer #C4# -> "bound"
        self.assertTrue(self.game.answer_clue("#C4#", "bound"))
        self.assertIn("#C5#", self.game.active_clues)
        self.assertNotIn("#C6#", self.game.active_clues)

        # Answer #C5# -> "pig"
        self.assertTrue(self.game.answer_clue("#C5#", "pig"))
        # NOW #C6# should be active because both #C1# and #C5# are complete
        self.assertIn("#C6#", self.game.active_clues, "#C6# should be active now.")

        # Answer #C6# -> "nomer"
        self.assertTrue(self.game.answer_clue("#C6#", "nomer"))
        self.assertTrue(self.game.clues["#C6#"].completed)
        self.assertNotIn("#C6#", self.game.active_clues)


if __name__ == '__main__':
    # This allows running the tests directly from this file
    # For more complex setups, a test runner like 'python -m unittest discover' is preferred.
    if not os.path.exists(GAME_JSON_PATH):
        print(f"ERROR: Test game JSON file not found at {GAME_JSON_PATH}")
        print(f"BASE_DIR: {BASE_DIR}, CWD: {os.getcwd()}")
        print("Please ensure the 'games/json/20250110.json' file is accessible.")
    else:
        unittest.main()
