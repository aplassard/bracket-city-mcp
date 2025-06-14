import pytest # Import pytest if needed for specific features like raises, skip, fixtures
from src.bracket_city_mcp.game.clue import Clue

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
