import unittest
from src.bracket_city_mcp.game.clue import Clue

class TestClue(unittest.TestCase):

    def test_clue_initialization(self):
        clue = Clue(clue_id="#C1#",
                    clue_text="Test clue text",
                    answer="Test Answer",
                    depends_on=["#C0#"])
        self.assertEqual(clue.clue_id, "#C1#")
        self.assertEqual(clue.clue_text, "Test clue text")
        self.assertEqual(clue.answer, "Test Answer")
        self.assertEqual(clue.depends_on, ["#C0#"])
        self.assertFalse(clue.completed)

    def test_answer_clue_correct(self):
        clue = Clue(clue_id="#C1#", clue_text="text", answer="Correcto", depends_on=[])
        result = clue.answer_clue("Correcto")
        self.assertTrue(result)
        self.assertTrue(clue.completed)

    def test_answer_clue_correct_case_insensitive(self):
        clue = Clue(clue_id="#C1#", clue_text="text", answer="CaSeSeNsItIvE", depends_on=[])
        result = clue.answer_clue("casesensitive")
        self.assertTrue(result)
        self.assertTrue(clue.completed)

        clue2 = Clue(clue_id="#C2#", clue_text="text", answer="answer", depends_on=[])
        result2 = clue2.answer_clue("ANSWER")
        self.assertTrue(result2)
        self.assertTrue(clue2.completed)

    def test_answer_clue_correct_with_whitespace(self):
        clue = Clue(clue_id="#C1#", clue_text="text", answer="Answer", depends_on=[])
        result = clue.answer_clue("  Answer  ")
        self.assertTrue(result)
        self.assertTrue(clue.completed)

    def test_answer_clue_incorrect(self):
        clue = Clue(clue_id="#C1#", clue_text="text", answer="Correct", depends_on=[])
        result = clue.answer_clue("Incorrect")
        self.assertFalse(result)
        self.assertFalse(clue.completed)

    def test_answer_clue_empty_provided_answer(self):
        clue = Clue(clue_id="#C1#", clue_text="text", answer="NotEmpty", depends_on=[])
        result = clue.answer_clue("")
        self.assertFalse(result)
        self.assertFalse(clue.completed)

    def test_answer_clue_empty_actual_answer(self):
        # Test case where actual answer might be empty (as seen in sample JSON for #C11#)
        clue = Clue(clue_id="#C1#", clue_text="text", answer="", depends_on=[])

        # Answering correctly with empty string
        result_correct = clue.answer_clue("")
        self.assertTrue(result_correct)
        self.assertTrue(clue.completed)

        # Resetting for next test
        clue.completed = False

        # Answering incorrectly
        result_incorrect = clue.answer_clue("not empty")
        self.assertFalse(result_incorrect)
        self.assertFalse(clue.completed)

if __name__ == '__main__':
    unittest.main()
