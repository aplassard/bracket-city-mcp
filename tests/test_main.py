import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import copy # For deepcopying game state

# Adjust path to import main module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.bracket_city_mcp import main as bracket_city_main
from src.bracket_city_mcp.game.game import Game
# Clue import for type hinting or direct use if needed for setup:
# Imports from src/bracket_city_mcp/tests/test_main_tools.py
from bracket_city_mcp.main import get_clue_context # answer_clue is already imported via bracket_city_main
from bracket_city_mcp.game.clue import Clue # For type hinting or direct use if needed for setup


class TestMainApi(unittest.TestCase): # Renamed class for broader scope
    game_template: Game

    @classmethod
    def setUpClass(cls):
        # Load the game from the dedicated test JSON file once for the class
        # The main 'game' object in bracket_city_main will be patched per test.
        # This ensures that the Game.from_json_file logic is also somewhat tested.
        try:
            cls.game_template = Game.from_json_file('tests/data/test_game.json')
        except Exception as e:
            print(f"Failed to load test game file: tests/data/test_game.json. Error: {e}")
            # If the game file can't be loaded, tests can't run.
            # It's better to raise an error here to make it obvious.
            raise RuntimeError("Could not load tests/data/test_game.json for tests.") from e


    def setUp(self):
        # Create a deep copy of the loaded game template for each test
        # This ensures test isolation, as each test gets a fresh game instance.
        self.game_instance = copy.deepcopy(self.game_template)

        # Reset completion status for all clues
        for clue_obj in self.game_instance.clues.values():
            clue_obj.completed = False
            # Also reset any internal state within Clue if necessary, though current Clue is simple

        # Reset active_clues to only start_clues (initial state)
        # self.game_template.start_clues should have been populated by its __init__
        # and deepcopy should have copied it.
        self.game_instance.active_clues = set(self.game_instance.start_clues)

        self.game_instance.incorrect_guesses = 0

        # Patch the 'game' instance in the main module with our test-specific instance
        self.patcher = patch('src.bracket_city_mcp.main.game', self.game_instance)
        self.mock_main_game_instance = self.patcher.start()

        # Spy on specific methods of the real game_instance if needed for assertions
        # For example, to check if game_instance.answer_clue was called.
        # We are testing the answer_clue *tool* in main.py, which *uses* the game_instance.
        # So, we want the real game_instance.answer_clue to run.
        # We can spy on it to ensure it was called.
        self.game_instance.answer_clue = MagicMock(wraps=self.game_instance.answer_clue)
        # is_complete is a property, if we need to check its access, it's more complex.
        # For now, we'll check the 'game_completed' field in the response directly.


    def tearDown(self):
        self.patcher.stop()

    def test_answer_clue_correct_and_reveals_next(self):
        clue_id = "#DUMMY_CLUE1#"
        answer = "dummy_answer1"

        response = bracket_city_main.answer_clue(clue_id, answer)

        expected_response = {
            "correct": True,
            "message": "Correct!",
            "available_clues": sorted(["#DUMMY_CLUE2#"]), # DUMMY_CLUE2 becomes available
            "game_completed": False
        }
        response["available_clues"].sort()
        self.assertEqual(response, expected_response)
        self.game_instance.answer_clue.assert_called_once_with(clue_id, answer)
        self.assertTrue(self.game_instance.clues[clue_id].completed)
        self.assertIn("#DUMMY_CLUE2#", self.game_instance.active_clues)


    def test_answer_clue_incorrect(self):
        clue_id = "#DUMMY_CLUE1#"
        wrong_answer = "wrong_dummy_answer"
        initial_active_clues = sorted(list(self.game_instance.active_clues))

        response = bracket_city_main.answer_clue(clue_id, wrong_answer)

        expected_response = {
            "correct": False,
            "message": "Incorrect answer.",
            "available_clues": initial_active_clues, # No change in active clues
            "game_completed": False
        }
        response["available_clues"].sort()
        self.assertEqual(response, expected_response)
        self.game_instance.answer_clue.assert_called_once_with(clue_id, wrong_answer)
        self.assertFalse(self.game_instance.clues[clue_id].completed)
        self.assertEqual(self.game_instance.incorrect_guesses, 1)

    def test_answer_clue_not_found(self):
        clue_id = "#NON_EXISTENT_CLUE#"
        answer = "any_answer"
        initial_active_clues = sorted(list(self.game_instance.active_clues))

        response = bracket_city_main.answer_clue(clue_id, answer)

        expected_response = {
            "correct": False,
            "message": f"Clue ID '{clue_id}' not found.",
            "available_clues": initial_active_clues,
            "game_completed": False
        }
        response["available_clues"].sort()
        self.assertEqual(response, expected_response)
        self.game_instance.answer_clue.assert_not_called()

    def test_answer_clue_already_completed(self):
        clue_id = "#DUMMY_CLUE1#"
        answer = "dummy_answer1"

        # First, answer correctly
        bracket_city_main.answer_clue(clue_id, answer)
        self.game_instance.answer_clue.reset_mock() # Reset mock for the next call

        # Try to answer again
        response = bracket_city_main.answer_clue(clue_id, answer)

        expected_response = {
            "correct": False,
            "message": f"Clue '{clue_id}' has already been answered.",
            # DUMMY_CLUE2 should be active after the first correct answer
            "available_clues": sorted(["#DUMMY_CLUE2#"]),
            "game_completed": False
        }
        response["available_clues"].sort()
        self.assertEqual(response, expected_response)
        self.game_instance.answer_clue.assert_not_called() # Not called on the second attempt

    def test_answer_clue_not_active_dependency_not_met(self):
        clue_id = "#DUMMY_CLUE2#" # Depends on #DUMMY_CLUE1#
        answer = "dummy_answer2"
        initial_active_clues = sorted(list(self.game_instance.active_clues)) # Should be just #DUMMY_CLUE1#

        response = bracket_city_main.answer_clue(clue_id, answer)

        expected_response = {
            "correct": False,
            "message": f"Clue '{clue_id}' is not currently available. Solve its dependencies first.",
            "available_clues": initial_active_clues,
            "game_completed": False
        }
        response["available_clues"].sort()
        self.assertEqual(response, expected_response)
        self.game_instance.answer_clue.assert_not_called()

    def test_answer_clue_completes_game(self):
        # Scenario:
        # 1. Answer #DUMMY_CLUE1# correctly.
        # 2. This makes #DUMMY_CLUE2# available.
        # 3. Answer #DUMMY_CLUE2# correctly. This is the last non-end clue.
        #    - game.is_complete should now be True.
        #    - #END_CLUE# should become active.
        # 4. Call answer_clue with #END_CLUE# ID.
        #    - This should trigger the special end-game logic in the main.py tool.

        # Sanity check initial state
        initial_active_clues = {"#DUMMY_CLUE1#"}
        self.assertEqual(self.game_instance.active_clues, initial_active_clues)
        self.assertFalse(self.game_instance.is_complete)

        # 1. Answer #DUMMY_CLUE1#
        bracket_city_main.answer_clue("#DUMMY_CLUE1#", "dummy_answer1")
        self.assertTrue(self.game_instance.clues["#DUMMY_CLUE1#"].completed)
        self.assertIn("#DUMMY_CLUE2#", self.game_instance.active_clues)
        self.assertNotIn("#END_CLUE#", self.game_instance.active_clues) # End clue not yet active
        self.assertFalse(self.game_instance.is_complete)

        # 2. Answer #DUMMY_CLUE2# (the second-to-last, and last solvable clue)
        response_c2 = bracket_city_main.answer_clue("#DUMMY_CLUE2#", "dummy_answer2")

        # Check response from answering C2. Since C2 is the last non-end clue,
        # game.is_complete will become true, and the tool will report game completion.
        self.assertTrue(response_c2["correct"])
        self.assertEqual(response_c2["message"], "Correct! Congratulations! You've completed the game.")
        self.assertTrue(response_c2["game_completed"])

        self.assertTrue(self.game_instance.clues["#DUMMY_CLUE2#"].completed)
        self.assertIn("#END_CLUE#", self.game_instance.active_clues) # End clue is now active

        # Verify game.is_complete is True internally now
        self.assertTrue(self.game_instance.is_complete, "Game.is_complete should be True after solving all non-end clues")

        # 3. "Answer" #END_CLUE# - this should trigger the special completion logic in the tool
        # Any answer string for end clue, it's ignored by the new logic in main.py
        final_response = bracket_city_main.answer_clue("#END_CLUE#", "any_answer")

        expected_score = len(self.game_instance.clues) - self.game_instance.incorrect_guesses

        self.assertTrue(final_response["correct"]) # Correct in the sense of reaching the end
        self.assertEqual(final_response["message"], "You've reached the final clue! Congratulations, the game is complete!")
        self.assertTrue(final_response["game_completed"])
        self.assertEqual(final_response["score"], expected_score)
        # End clue itself is not marked "completed" by Clue.answer_clue() due to "if is_end_clue: return False"
        self.assertFalse(self.game_instance.clues["#END_CLUE#"].completed, "End clue object itself should not be marked completed by its own answer_clue method")

        # Check available clues in final response (should be empty if #END_CLUE# was the only one left)
        # Or could still contain #END_CLUE# if active_clues isn't cleared of it by the tool's special path
        # The current logic in main.py for end clues *does* set available_clues = list(game.active_clues)
        # and game.answer_clue isn't called for end_clues, so #END_CLUE# would remain in active_clues.
        # This is acceptable.
        self.assertIn("#END_CLUE#", final_response["available_clues"])
        self.assertEqual(len(final_response["available_clues"]), 1) # Only end clue should be "active"

if __name__ == '__main__':
    # This allows running the tests directly from this file: python tests/test_main.py
    # Note: The dummy game file 'games/json/20250110.json' is still loaded when
    # 'from src.bracket_city_mcp import main as bracket_city_main' is executed.
    # This is separate from 'tests/data/test_game.json' used by these tests.
    # Ensure 'games/json/20250110.json' exists or the import will fail.
    # A dummy version was created in a previous step.
    unittest.main()

    # --- Tests for get_clue_context (merged from src/bracket_city_mcp/tests/test_main_tools.py) ---

    def test_get_clue_context_no_dependencies(self):
        """Test get_clue_context for a clue with no dependencies, using loaded game."""
        # #DUMMY_CLUE1# from test_game.json has no dependencies
        clue_id_to_test = "#DUMMY_CLUE1#"
        clue_obj = self.game_instance.clues[clue_id_to_test]

        # Mock get_rendered_text for this specific clue object within the live game instance
        # to avoid actual rendering logic if it's complex or not the focus here.
        original_get_rendered_text = clue_obj.get_rendered_text
        clue_obj.get_rendered_text = MagicMock(return_value=f"Rendered {clue_id_to_test}")

        context = get_clue_context(clue_id_to_test)

        self.assertNotIn("error", context)
        self.assertEqual(context["clue_id"], clue_id_to_test)
        clue_obj.get_rendered_text.assert_called_once_with(self.mock_main_game_instance) # game from main
        self.assertEqual(context["rendered_text"], f"Rendered {clue_id_to_test}")
        self.assertFalse(context["is_correctly_answered"]) # Initially false
        self.assertEqual(context["previous_answers"], []) # Initially empty
        self.assertEqual(context["depends_on_clues"], []) # DUMMY_CLUE1 has no dependencies
        self.assertIsNone(context["parent_clue_id"])

        clue_obj.get_rendered_text = original_get_rendered_text # Restore

    def test_get_clue_context_with_dependencies(self):
        """Test get_clue_context for a clue with dependencies, using loaded game."""
        # #DUMMY_CLUE2# from test_game.json depends on #DUMMY_CLUE1#
        clue_id_to_test = "#DUMMY_CLUE2#"
        clue_obj = self.game_instance.clues[clue_id_to_test]
        dependency_id = "#DUMMY_CLUE1#"

        original_get_rendered_text = clue_obj.get_rendered_text
        clue_obj.get_rendered_text = MagicMock(return_value=f"Rendered {clue_id_to_test}")

        context = get_clue_context(clue_id_to_test)

        self.assertNotIn("error", context)
        self.assertEqual(context["clue_id"], clue_id_to_test)
        clue_obj.get_rendered_text.assert_called_once_with(self.mock_main_game_instance)
        self.assertEqual(context["rendered_text"], f"Rendered {clue_id_to_test}")
        self.assertFalse(context["is_correctly_answered"])
        self.assertEqual(context["previous_answers"], [])
        self.assertEqual(context["depends_on_clues"], [dependency_id])
        self.assertEqual(context["parent_clue_id"], dependency_id)

        clue_obj.get_rendered_text = original_get_rendered_text # Restore

    def test_get_clue_context_after_answering_clue(self):
        """Test get_clue_context after answering a clue, using loaded game."""
        clue_id_to_test = "#DUMMY_CLUE1#"
        correct_answer = "dummy_answer1"
        incorrect_answer = "wrong_dummy_answer"
        clue_obj = self.game_instance.clues[clue_id_to_test]

        original_get_rendered_text = clue_obj.get_rendered_text
        clue_obj.get_rendered_text = MagicMock(return_value=f"Rendered {clue_id_to_test}")

        # 1. Answer incorrectly using the main.answer_clue tool
        bracket_city_main.answer_clue(clue_id_to_test, incorrect_answer)

        context_after_incorrect = get_clue_context(clue_id_to_test)
        self.assertFalse(context_after_incorrect["is_correctly_answered"])
        self.assertEqual(context_after_incorrect["previous_answers"], [incorrect_answer])

        # 2. Answer correctly using the main.answer_clue tool
        bracket_city_main.answer_clue(clue_id_to_test, correct_answer)

        context_after_correct = get_clue_context(clue_id_to_test)
        self.assertTrue(context_after_correct["is_correctly_answered"])
        self.assertEqual(context_after_correct["previous_answers"], [incorrect_answer, correct_answer])

        clue_obj.get_rendered_text = original_get_rendered_text # Restore

    def test_get_clue_context_non_existent_clue(self):
        """Test get_clue_context for a non-existent clue_id."""
        context = get_clue_context("#NONEXISTENT#")

        self.assertIn("error", context)
        self.assertEqual(context["error"], "Clue ID '#NONEXISTENT#' not found.")
        self.assertEqual(context["status_code"], 404)
