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

    def test_get_clue_context_clue_with_one_child(self): # Renamed
        """Test get_clue_context for a clue that is a dependency for one other clue."""
        # In test_game.json, #DUMMY_CLUE1# is a dependency for #DUMMY_CLUE2#.
        # So, #DUMMY_CLUE2# is a child of #DUMMY_CLUE1#.
        clue_id_to_test = "#DUMMY_CLUE1#"
        expected_child_id = "#DUMMY_CLUE2#"
        clue_obj = self.game_instance.clues[clue_id_to_test]

        original_get_rendered_text = clue_obj.get_rendered_text
        clue_obj.get_rendered_text = MagicMock(return_value=f"Rendered {clue_id_to_test}")

        # Mock the new game method call
        self.game_instance.get_first_dependent_clue_id = MagicMock(return_value=expected_child_id)

        context = get_clue_context(clue_id_to_test)

        self.assertNotIn("error", context)
        self.assertEqual(context["clue_id"], clue_id_to_test)
        clue_obj.get_rendered_text.assert_called_once_with(self.mock_main_game_instance)
        self.assertEqual(context["rendered_text"], f"Rendered {clue_id_to_test}")
        self.assertFalse(context["is_correctly_answered"])
        self.assertEqual(context["previous_answers"], [])
        self.assertEqual(context["depends_on_clues"], [])

        self.game_instance.get_first_dependent_clue_id.assert_called_once_with(clue_id_to_test)
        self.assertEqual(context["parent_clue_id"], expected_child_id)

        clue_obj.get_rendered_text = original_get_rendered_text

    def test_get_clue_context_clue_with_parent_and_one_child(self): # Renamed
        """Test get_clue_context for a clue that has parent dependencies and is a dependency for one other clue."""
        clue_id_to_test = "#DUMMY_CLUE2#"
        expected_parent_id = "#DUMMY_CLUE1#"
        expected_child_id = "#END_CLUE#"

        clue_obj = self.game_instance.clues[clue_id_to_test]
        original_get_rendered_text = clue_obj.get_rendered_text
        clue_obj.get_rendered_text = MagicMock(return_value=f"Rendered {clue_id_to_test}")

        # Mock the new game method call
        self.game_instance.get_first_dependent_clue_id = MagicMock(return_value=expected_child_id)

        context = get_clue_context(clue_id_to_test)

        self.assertNotIn("error", context)
        self.assertEqual(context["clue_id"], clue_id_to_test)
        clue_obj.get_rendered_text.assert_called_once_with(self.mock_main_game_instance)
        self.assertEqual(context["rendered_text"], f"Rendered {clue_id_to_test}")
        self.assertFalse(context["is_correctly_answered"])
        self.assertEqual(context["previous_answers"], [])
        self.assertEqual(context["depends_on_clues"], [expected_parent_id])

        self.game_instance.get_first_dependent_clue_id.assert_called_once_with(clue_id_to_test)
        self.assertEqual(context["parent_clue_id"], expected_child_id)

        clue_obj.get_rendered_text = original_get_rendered_text

    def test_get_clue_context_clue_with_no_children(self):
        """Test get_clue_context for a clue that is not a dependency for any other clue."""
        clue_id_to_test = "#END_CLUE#"
        expected_parent_id = "#DUMMY_CLUE2#"
        clue_obj = self.game_instance.clues[clue_id_to_test]

        original_get_rendered_text = clue_obj.get_rendered_text
        clue_obj.get_rendered_text = MagicMock(return_value=f"Rendered {clue_id_to_test}")

        # Mock the new game method call
        self.game_instance.get_first_dependent_clue_id = MagicMock(return_value=None)

        context = get_clue_context(clue_id_to_test)

        self.assertNotIn("error", context)
        self.assertEqual(context["clue_id"], clue_id_to_test)
        clue_obj.get_rendered_text.assert_called_once_with(self.mock_main_game_instance)
        self.assertEqual(context["rendered_text"], f"Rendered {clue_id_to_test}")
        self.assertFalse(context["is_correctly_answered"])
        self.assertEqual(context["previous_answers"], [])
        self.assertEqual(context["depends_on_clues"], [expected_parent_id])

        self.game_instance.get_first_dependent_clue_id.assert_called_once_with(clue_id_to_test)
        self.assertIsNone(context["parent_clue_id"])

        clue_obj.get_rendered_text = original_get_rendered_text

    def test_get_clue_context_clue_with_multiple_children(self):
        """Test get_clue_context for a clue with multiple children."""
        clue_id_to_test = "#MULTI_CHILD_PARENT#"
        expected_first_child_id = "#CHILD1#" # This is what the mocked method should return

        # We still need parent_clue in self.game_instance.clues for get_clue_context to find it
        parent_clue = Clue(clue_id=clue_id_to_test, clue_text="Parent", answer="ansP", depends_on=[])
        self.game_instance.clues[clue_id_to_test] = parent_clue

        original_get_rendered_text = parent_clue.get_rendered_text # Should be on the actual Clue obj
        parent_clue.get_rendered_text = MagicMock(return_value=f"Rendered {clue_id_to_test}")

        # Mock the new game method call to return the first child
        self.game_instance.get_first_dependent_clue_id = MagicMock(return_value=expected_first_child_id)

        context = get_clue_context(clue_id_to_test)

        self.assertNotIn("error", context)
        self.assertEqual(context["clue_id"], clue_id_to_test)
        parent_clue.get_rendered_text.assert_called_once_with(self.mock_main_game_instance)

        self.game_instance.get_first_dependent_clue_id.assert_called_once_with(clue_id_to_test)
        self.assertEqual(context["parent_clue_id"], expected_first_child_id)

        parent_clue.get_rendered_text = original_get_rendered_text


    def test_get_clue_context_after_answering_clue(self):
        """Test get_clue_context after answering a clue, using loaded game."""
        clue_id_to_test = "#DUMMY_CLUE1#"
        correct_answer = "dummy_answer1"
        incorrect_answer = "wrong_dummy_answer"
        expected_child_id = "#DUMMY_CLUE2#" # Child of #DUMMY_CLUE1#
        clue_obj = self.game_instance.clues[clue_id_to_test]

        original_get_rendered_text = clue_obj.get_rendered_text
        clue_obj.get_rendered_text = MagicMock(return_value=f"Rendered {clue_id_to_test}")

        # Mock the get_first_dependent_clue_id method for this test too
        self.game_instance.get_first_dependent_clue_id = MagicMock(return_value=expected_child_id)

        # 1. Answer incorrectly using the main.answer_clue tool
        bracket_city_main.answer_clue(clue_id_to_test, incorrect_answer)

        context_after_incorrect = get_clue_context(clue_id_to_test)
        self.assertFalse(context_after_incorrect["is_correctly_answered"])
        self.assertEqual(context_after_incorrect["previous_answers"], [incorrect_answer])
        self.assertEqual(context_after_incorrect["parent_clue_id"], expected_child_id)
        # Check call count for the mock after first call to get_clue_context
        self.game_instance.get_first_dependent_clue_id.assert_called_with(clue_id_to_test)
        call_count_after_first_answer = self.game_instance.get_first_dependent_clue_id.call_count


        # 2. Answer correctly using the main.answer_clue tool
        bracket_city_main.answer_clue(clue_id_to_test, correct_answer)

        context_after_correct = get_clue_context(clue_id_to_test)
        self.assertTrue(context_after_correct["is_correctly_answered"])
        self.assertEqual(context_after_correct["previous_answers"], [incorrect_answer, correct_answer])
        self.assertEqual(context_after_correct["parent_clue_id"], expected_child_id)
        # Check call count incremented
        self.assertEqual(self.game_instance.get_first_dependent_clue_id.call_count, call_count_after_first_answer + 1)


        clue_obj.get_rendered_text = original_get_rendered_text # Restore

    def test_get_clue_context_non_existent_clue(self):
        """Test get_clue_context for a non-existent clue_id."""
        context = get_clue_context("#NONEXISTENT#")

        self.assertIn("error", context)
        self.assertEqual(context["error"], "Clue ID '#NONEXISTENT#' not found.")
        self.assertEqual(context["status_code"], 404)

    def test_get_clue_context_for_production_end_clue(self):
        """
        Tests get_clue_context for the end clue of the production game file.
        This is more of an integration test for this specific case.
        """
        prod_game_file = "games/json/20250110.json"
        # Ensure the production game file path is correct relative to the project root
        # Assuming tests are run from the project root or PYTHONPATH is set up.
        if not os.path.exists(prod_game_file):
             self.skipTest(f"Production game file {prod_game_file} not found.")

        prod_game = Game.from_json_file(prod_game_file)
        end_clue_id = "CLUE-C19" # As per recent rename

        # Ensure CLUE-C19 is indeed an end clue in this game instance
        # (i.e., nothing depends on it according to prod_game.adj)
        self.assertEqual(prod_game.adj.get(end_clue_id, []), [],
                         f"{end_clue_id} is expected to have no children in {prod_game_file}")

        with patch('src.bracket_city_mcp.main.game', prod_game):
            context = get_clue_context(end_clue_id)

        self.assertNotIn("error", context, f"get_clue_context returned an error for {end_clue_id}")
        self.assertEqual(context.get("clue_id"), end_clue_id)
        self.assertFalse(context.get("is_correctly_answered"),
                         f"End clue {end_clue_id} should not be answered by default.")

        # Verify parent_clue_id using the actual game logic (which calls get_first_dependent_clue_id)
        # For an end clue like CLUE-C19, it should have no children.
        self.assertIsNone(context.get("parent_clue_id"),
                          f"parent_clue_id for end clue {end_clue_id} should be None.")

        # Additionally, verify that the get_first_dependent_clue_id method on the prod_game
        # was indeed called by the get_clue_context tool.
        # To do this, we need to spy on prod_game.get_first_dependent_clue_id
        prod_game.get_first_dependent_clue_id = MagicMock(wraps=prod_game.get_first_dependent_clue_id)

        with patch('src.bracket_city_mcp.main.game', prod_game):
            get_clue_context(end_clue_id) # Call it again with the spy in place

        prod_game.get_first_dependent_clue_id.assert_called_once_with(end_clue_id)
