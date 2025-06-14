import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Adjust path to import main module
# This assumes 'tests' is a sibling directory to 'src'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.bracket_city_mcp import main as bracket_city_main
from src.bracket_city_mcp.game.clue import Clue # Needed for creating mock Clue objects

class TestAnswerClueTool(unittest.TestCase):

    def setUp(self):
        # Create a mock game object that will be patched into main
        self.mock_game = MagicMock()
        self.mock_game.clues = {}
        self.mock_game.active_clues = set()
        self.mock_game.incorrect_guesses = 0
        self.mock_game.is_complete = False

        # Patch the 'game' instance in the main module
        self.patcher = patch('src.bracket_city_mcp.main.game', self.mock_game)
        self.mock_game_patched = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_answer_clue_correct(self):
        clue_id = "#C1#"
        answer = "Paris"

        mock_clue = MagicMock(spec=Clue)
        mock_clue.completed = False

        self.mock_game_patched.clues = {clue_id: mock_clue}
        self.mock_game_patched.active_clues = {clue_id}
        # self.mock_game_patched.answer_clue.return_value = True # Replaced by side_effect
        self.mock_game_patched.is_complete = False

        def side_effect_answer_clue(cid, ans):
            if cid == clue_id and ans == answer:
                # Simulate that the game logic marks the clue as completed
                # and updates active_clues. For this test, we just remove it.
                self.mock_game_patched.active_clues.discard(clue_id)
                return True
            return False
        self.mock_game_patched.answer_clue.side_effect = side_effect_answer_clue

        expected_response = {
            "correct": True,
            "message": "Correct!",
            "available_clues": [],
            "game_completed": False
        }
        response = bracket_city_main.answer_clue(clue_id, answer)
        self.assertEqual(response, expected_response)
        self.mock_game_patched.answer_clue.assert_called_once_with(clue_id, answer)

    def test_answer_clue_incorrect(self):
        clue_id = "#C1#"
        wrong_answer = "London"

        mock_clue = MagicMock(spec=Clue)
        mock_clue.completed = False

        self.mock_game_patched.clues = {clue_id: mock_clue}
        self.mock_game_patched.active_clues = {clue_id}
        self.mock_game_patched.answer_clue.return_value = False
        self.mock_game_patched.is_complete = False

        expected_response = {
            "correct": False,
            "message": "Incorrect answer.",
            "available_clues": [clue_id],
            "game_completed": False
        }
        response = bracket_city_main.answer_clue(clue_id, wrong_answer)
        self.assertEqual(response, expected_response)
        self.mock_game_patched.answer_clue.assert_called_once_with(clue_id, wrong_answer)

    def test_answer_clue_not_found(self):
        clue_id = "#C_NON_EXISTENT#"
        answer = "Any"
        self.mock_game_patched.clues = {}
        self.mock_game_patched.active_clues = set()

        expected_response = {
            "correct": False,
            "message": f"Clue ID '{clue_id}' not found.",
            "available_clues": [],
            "game_completed": False
        }
        response = bracket_city_main.answer_clue(clue_id, answer)
        self.assertEqual(response, expected_response)
        self.mock_game_patched.answer_clue.assert_not_called()

    def test_answer_clue_already_completed(self):
        clue_id = "#C1#"
        answer = "Paris"

        mock_clue = MagicMock(spec=Clue)
        mock_clue.completed = True

        self.mock_game_patched.clues = {clue_id: mock_clue}
        self.mock_game_patched.active_clues = set()

        expected_response = {
            "correct": False,
            "message": f"Clue '{clue_id}' has already been answered.",
            "available_clues": [],
            "game_completed": False
        }
        response = bracket_city_main.answer_clue(clue_id, answer)
        self.assertEqual(response, expected_response)
        self.mock_game_patched.answer_clue.assert_not_called()

    def test_answer_clue_not_active(self):
        clue_id = "#C2#"
        answer = "Berlin"

        mock_clue_c2 = MagicMock(spec=Clue)
        mock_clue_c2.completed = False

        self.mock_game_patched.clues = {clue_id: mock_clue_c2}
        # C2 is not in active_clues, C1 is.
        self.mock_game_patched.active_clues = {"#C1#"}

        expected_response = {
            "correct": False,
            "message": f"Clue '{clue_id}' is not currently available. Solve its dependencies first.",
            "available_clues": ["#C1#"], # Should return the currently active clues
            "game_completed": False
        }
        response = bracket_city_main.answer_clue(clue_id, answer)
        # Ensure available_clues lists are sorted for comparison if order isn't guaranteed
        response["available_clues"].sort()
        expected_response["available_clues"].sort()
        self.assertEqual(response, expected_response)
        self.mock_game_patched.answer_clue.assert_not_called()

    def test_answer_clue_completes_game(self):
        clue_id = "#C_FINAL#"
        answer = "Victory"

        mock_clue = MagicMock(spec=Clue)
        mock_clue.completed = False

        # Game has two clues in total for score calculation
        self.mock_game_patched.clues = {clue_id: mock_clue, "#C_OTHER#": MagicMock(spec=Clue)}
        self.mock_game_patched.active_clues = {clue_id}
        self.mock_game_patched.incorrect_guesses = 1

        def side_effect_final_answer(cid, ans):
            if cid == clue_id and ans == answer:
                self.mock_game_patched.active_clues.discard(clue_id)
                self.mock_game_patched.is_complete = True
                return True
            return False
        self.mock_game_patched.answer_clue.side_effect = side_effect_final_answer

        expected_score = len(self.mock_game_patched.clues) - self.mock_game_patched.incorrect_guesses
        expected_response = {
            "correct": True,
            "message": "Correct! Congratulations! You've completed the game.",
            "available_clues": [],
            "game_completed": True,
            "score": expected_score
        }
        response = bracket_city_main.answer_clue(clue_id, answer)

        self.assertEqual(response, expected_response)
        self.mock_game_patched.answer_clue.assert_called_once_with(clue_id, answer)

if __name__ == '__main__':
    unittest.main()
