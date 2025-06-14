import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import copy # For deepcopying game state

# Adjust path to import main module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.bracket_city_mcp import main as bracket_city_main
from src.bracket_city_mcp.game.game import Game
# Clue import is not strictly needed here anymore as we use a real Game object
# from src.bracket_city_mcp.game.clue import Clue

class TestAnswerClueTool(unittest.TestCase):
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
        # Solve DUMMY_CLUE1
        bracket_city_main.answer_clue("#DUMMY_CLUE1#", "dummy_answer1")
        self.game_instance.answer_clue.reset_mock()

        # Solve DUMMY_CLUE2, which should make END_CLUE available (and it's the last one)
        bracket_city_main.answer_clue("#DUMMY_CLUE2#", "dummy_answer2")
        self.game_instance.answer_clue.reset_mock()

        # END_CLUE has an empty answer string in test_game.json
        end_clue_id = "#END_CLUE#"
        end_clue_answer = ""

        response = bracket_city_main.answer_clue(end_clue_id, end_clue_answer)

        expected_total_clues = len(self.game_instance.clues)
        expected_score = expected_total_clues - self.game_instance.incorrect_guesses

        expected_response = {
            "correct": True, # Assuming empty answer is "correct" for auto-completed end clues
            "message": "Correct! Congratulations! You've completed the game.",
            "available_clues": [], # No more clues available
            "game_completed": True,
            "score": expected_score
        }
        response["available_clues"].sort()
        self.assertEqual(response, expected_response)
        self.game_instance.answer_clue.assert_called_once_with(end_clue_id, end_clue_answer)
        self.assertTrue(self.game_instance.clues[end_clue_id].completed)
        self.assertTrue(self.game_instance.is_complete)

if __name__ == '__main__':
    # This allows running the tests directly from this file: python tests/test_main.py
    # Note: The dummy game file 'games/json/20250110.json' is still loaded when
    # 'from src.bracket_city_mcp import main as bracket_city_main' is executed.
    # This is separate from 'tests/data/test_game.json' used by these tests.
    # Ensure 'games/json/20250110.json' exists or the import will fail.
    # A dummy version was created in a previous step.
    unittest.main()
