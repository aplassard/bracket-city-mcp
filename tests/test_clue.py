import pytest # Import pytest if needed for specific features like raises, skip, fixtures
from src.bracket_city_mcp.game.clue import Clue
from src.bracket_city_mcp.game.game import Game # Though using MockGame, good to have for context


# Helper MockGame class for testing Clue.get_rendered_text
class MockGame:
    def __init__(self, clues_dict=None):
        self.clues = clues_dict if clues_dict else {}

def test_clue_initialization():
    clue = Clue(clue_id="#C1#",
                clue_text="Test clue text",
                answer="Test Answer",
                depends_on=["#C0#"])
    assert clue.clue_id == "#C1#"
    assert clue.clue_text == "Test clue text"
    assert clue.answer == "Test Answer"
    assert clue.depends_on == ["#C0#"]
    assert not clue.completed

def test_answer_clue_correct():
    clue = Clue(clue_id="#C1#", clue_text="text", answer="Correcto", depends_on=[])
    result = clue.answer_clue("Correcto")
    assert result
    assert clue.completed

def test_answer_clue_correct_case_insensitive():
    clue = Clue(clue_id="#C1#", clue_text="text", answer="CaSeSeNsItIvE", depends_on=[])
    result = clue.answer_clue("casesensitive")
    assert result
    assert clue.completed

    clue2 = Clue(clue_id="#C2#", clue_text="text", answer="answer", depends_on=[])
    result2 = clue2.answer_clue("ANSWER")
    assert result2
    assert clue2.completed

def test_answer_clue_correct_with_whitespace():
    clue = Clue(clue_id="#C1#", clue_text="text", answer="Answer", depends_on=[])
    result = clue.answer_clue("  Answer  ")
    assert result
    assert clue.completed

def test_answer_clue_incorrect():
    clue = Clue(clue_id="#C1#", clue_text="text", answer="Correct", depends_on=[])
    result = clue.answer_clue("Incorrect")
    assert not result
    assert not clue.completed

def test_answer_clue_empty_provided_answer():
    clue = Clue(clue_id="#C1#", clue_text="text", answer="NotEmpty", depends_on=[])
    result = clue.answer_clue("")
    assert not result
    assert not clue.completed

def test_answer_clue_empty_actual_answer():
    clue = Clue(clue_id="#C1#", clue_text="text", answer="", depends_on=[])

    result_correct = clue.answer_clue("")
    assert result_correct
    assert clue.completed

    # Resetting for next test part within the same function
    clue.completed = False

    result_incorrect = clue.answer_clue("not empty")
    assert not result_incorrect
    assert not clue.completed

# It's good practice to remove the if __name__ == '__main__': block
# as pytest handles test discovery and execution.


# Tests for Clue.get_rendered_text()

def test_get_rendered_text_completed_clue():
    c1 = Clue(clue_id="#C1#", clue_text="Text C1", answer="Ans C1", depends_on=[])
    c1.completed = True
    mock_game = MockGame(clues_dict={"#C1#": c1})
    assert c1.get_rendered_text(mock_game) == "Ans C1"

def test_get_rendered_text_uncompleted_no_dependencies():
    c1 = Clue(clue_id="#C1#", clue_text="Text C1", answer="Ans C1", depends_on=[])
    mock_game = MockGame(clues_dict={"#C1#": c1})
    assert c1.get_rendered_text(mock_game) == "Text C1"

def test_get_rendered_text_uncompleted_one_dependency_not_completed():
    c1 = Clue(clue_id="#C1#", clue_text="Text C1", answer="Ans C1", depends_on=[])
    c2 = Clue(clue_id="#C2#", clue_text="Text C2 #C1#", answer="Ans C2", depends_on=["#C1#"])
    mock_game = MockGame(clues_dict={"#C1#": c1, "#C2#": c2})
    assert c2.get_rendered_text(mock_game) == "Text C2 [Text C1]"

def test_get_rendered_text_uncompleted_one_dependency_completed():
    c1 = Clue(clue_id="#C1#", clue_text="Text C1", answer="Ans C1", depends_on=[])
    c1.completed = True
    c2 = Clue(clue_id="#C2#", clue_text="Text C2 #C1#", answer="Ans C2", depends_on=["#C1#"])
    mock_game = MockGame(clues_dict={"#C1#": c1, "#C2#": c2})
    assert c2.get_rendered_text(mock_game) == "Text C2 Ans C1"

def test_get_rendered_text_uncompleted_multiple_dependencies_all_uncompleted():
    c1 = Clue(clue_id="#C1#", clue_text="Text C1", answer="Ans C1", depends_on=[])
    c2 = Clue(clue_id="#C2#", clue_text="Text C2 #C1#", answer="Ans C2", depends_on=["#C1#"])
    c3 = Clue(clue_id="#C3#", clue_text="Text C3 #C2#", answer="Ans C3", depends_on=["#C2#"])
    mock_game = MockGame(clues_dict={"#C1#": c1, "#C2#": c2, "#C3#": c3})
    assert c3.get_rendered_text(mock_game) == "Text C3 [Text C2 [Text C1]]"

def test_get_rendered_text_uncompleted_multiple_dependencies_inner_completed():
    c1 = Clue(clue_id="#C1#", clue_text="Text C1", answer="Ans C1", depends_on=[])
    c1.completed = True
    c2 = Clue(clue_id="#C2#", clue_text="Text C2 #C1#", answer="Ans C2", depends_on=["#C1#"])
    c3 = Clue(clue_id="#C3#", clue_text="Text C3 #C2#", answer="Ans C3", depends_on=["#C2#"])
    mock_game = MockGame(clues_dict={"#C1#": c1, "#C2#": c2, "#C3#": c3})
    assert c3.get_rendered_text(mock_game) == "Text C3 [Text C2 Ans C1]"

def test_get_rendered_text_uncompleted_multiple_dependencies_middle_completed():
    c1 = Clue(clue_id="#C1#", clue_text="Text C1", answer="Ans C1", depends_on=[])
    c1.completed = True # Must be completed for C2 to be completed with its answer
    c2 = Clue(clue_id="#C2#", clue_text="Text C2 #C1#", answer="Ans C2", depends_on=["#C1#"])
    c2.completed = True # This is the key for this test
    c3 = Clue(clue_id="#C3#", clue_text="Text C3 #C2#", answer="Ans C3", depends_on=["#C2#"])
    mock_game = MockGame(clues_dict={"#C1#": c1, "#C2#": c2, "#C3#": c3})
    assert c3.get_rendered_text(mock_game) == "Text C3 Ans C2"

def test_get_rendered_text_dependency_id_substring_of_another():
    c1 = Clue(clue_id="#C1#", clue_text="A", answer="Ans C1", depends_on=[])
    c11 = Clue(clue_id="#C11#", clue_text="B", answer="Ans C11", depends_on=[])
    c2 = Clue(clue_id="#C2#", clue_text="Test #C1# and #C11#", answer="Ans C2", depends_on=["#C1#", "#C11#"])
    mock_game = MockGame(clues_dict={"#C1#": c1, "#C11#": c11, "#C2#": c2})
    assert c2.get_rendered_text(mock_game) == "Test [A] and [B]"

def test_get_rendered_text_dependency_id_substring_of_another_one_completed():
    c1 = Clue(clue_id="#C1#", clue_text="A", answer="Ans C1", depends_on=[])
    c1.completed = True
    c11 = Clue(clue_id="#C11#", clue_text="B", answer="Ans C11", depends_on=[])
    c2 = Clue(clue_id="#C2#", clue_text="Test #C1# and #C11#", answer="Ans C2", depends_on=["#C1#", "#C11#"])
    mock_game = MockGame(clues_dict={"#C1#": c1, "#C11#": c11, "#C2#": c2})
    assert c2.get_rendered_text(mock_game) == "Test Ans C1 and [B]"


def test_get_rendered_text_diamond_dependency():
    #     C1
    #    /  \
    #   C2  C3
    #    \  /
    #     C4
    c1 = Clue(clue_id="#C1#", clue_text="Text C1", answer="Ans C1", depends_on=[])
    c2 = Clue(clue_id="#C2#", clue_text="Loves #C1#", answer="Ans C2", depends_on=["#C1#"])
    c3 = Clue(clue_id="#C3#", clue_text="Hates #C1#", answer="Ans C3", depends_on=["#C1#"])
    c4 = Clue(clue_id="#C4#", clue_text="End #C2# #C3#", answer="Ans C4", depends_on=["#C2#", "#C3#"])
    mock_game = MockGame(clues_dict={"#C1#": c1, "#C2#": c2, "#C3#": c3, "#C4#": c4})
    assert c4.get_rendered_text(mock_game) == "End [Loves [Text C1]] [Hates [Text C1]]"

def test_get_rendered_text_diamond_dependency_c1_completed():
    c1 = Clue(clue_id="#C1#", clue_text="Text C1", answer="Ans C1", depends_on=[])
    c1.completed = True
    c2 = Clue(clue_id="#C2#", clue_text="Loves #C1#", answer="Ans C2", depends_on=["#C1#"])
    c3 = Clue(clue_id="#C3#", clue_text="Hates #C1#", answer="Ans C3", depends_on=["#C1#"])
    c4 = Clue(clue_id="#C4#", clue_text="End #C2# #C3#", answer="Ans C4", depends_on=["#C2#", "#C3#"])
    mock_game = MockGame(clues_dict={"#C1#": c1, "#C2#": c2, "#C3#": c3, "#C4#": c4})
    assert c4.get_rendered_text(mock_game) == "End [Loves Ans C1] [Hates Ans C1]"

def test_get_rendered_text_diamond_dependency_c2_completed():
    # C2 completed means its text will be its answer.
    # C1 must be completed for C2 to be completed.
    c1 = Clue(clue_id="#C1#", clue_text="Text C1", answer="Ans C1", depends_on=[])
    c1.completed = True
    c2 = Clue(clue_id="#C2#", clue_text="Loves #C1#", answer="Ans C2", depends_on=["#C1#"])
    c2.completed = True # This makes C2 output "Ans C2"
    c3 = Clue(clue_id="#C3#", clue_text="Hates #C1#", answer="Ans C3", depends_on=["#C1#"])
    # C3 is not completed, so it will render [Hates Ans C1]
    c4 = Clue(clue_id="#C4#", clue_text="End #C2# #C3#", answer="Ans C4", depends_on=["#C2#", "#C3#"])
    mock_game = MockGame(clues_dict={"#C1#": c1, "#C2#": c2, "#C3#": c3, "#C4#": c4})
    assert c4.get_rendered_text(mock_game) == "End Ans C2 [Hates Ans C1]"
