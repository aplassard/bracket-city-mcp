import pytest
from src.bracket_city_mcp.game.clue import Clue
from src.bracket_city_mcp.game.game import Game


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

    clue.completed = False

    result_incorrect = clue.answer_clue("not empty")
    assert not result_incorrect
    assert not clue.completed


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
    c1 = Clue(clue_id="#C1#", clue_text="Text C1", answer="Ans C1", depends_on=[])
    c1.completed = True
    c2 = Clue(clue_id="#C2#", clue_text="Loves #C1#", answer="Ans C2", depends_on=["#C1#"])
    c2.completed = True
    c3 = Clue(clue_id="#C3#", clue_text="Hates #C1#", answer="Ans C3", depends_on=["#C1#"])
    c4 = Clue(clue_id="#C4#", clue_text="End #C2# #C3#", answer="Ans C4", depends_on=["#C2#", "#C3#"])
    mock_game = MockGame(clues_dict={"#C1#": c1, "#C2#": c2, "#C3#": c3, "#C4#": c4})
    assert c4.get_rendered_text(mock_game) == "End Ans C2 [Hates Ans C1]"


# --- Tests for End Clue Functionality ---

def test_end_clue_initialization():
    """Test that an end clue is initialized correctly."""
    clue = Clue(clue_id="#E1#",
                clue_text="This is the end.",
                answer="ShouldBeIgnored",
                depends_on=[],
                is_end_clue=True)
    assert clue.is_end_clue
    assert clue.answer == "", "Answer for an end clue should be an empty string."
    assert not clue.completed

def test_end_clue_answer_clue():
    """Test that attempting to answer an end clue always fails and doesn't complete it."""
    clue = Clue(clue_id="#E1#",
                clue_text="Final text.",
                answer="OriginalAnswer", # This should be ignored by __init__
                depends_on=[],
                is_end_clue=True)

    assert clue.answer == "", "End clue answer should be blank after init."

    result = clue.answer_clue("AnyAttempt")
    assert not result, "answer_clue on an end clue should return False."
    assert not clue.completed, "End clue should not be marked as completed."

    result_empty_answer = clue.answer_clue("") # Even with empty string
    assert not result_empty_answer, "answer_clue on an end clue should return False even for empty string."
    assert not clue.completed, "End clue should still not be marked as completed."


def test_end_clue_get_rendered_text_resolves_dependencies():
    """
    Test that get_rendered_text for an end clue now resolves dependencies
    and returns its answer (empty string) if hypothetically completed.
    """
    c1 = Clue(clue_id="#C1#", clue_text="DepText", answer="DepAns", depends_on=[], is_end_clue=False)
    # Ensure the end_clue's answer is set to "" by __init__ due to is_end_clue=True
    end_clue = Clue(clue_id="#END#", clue_text="Final: #C1#", answer="ThisWillBeBlanked", depends_on=["#C1#"], is_end_clue=True)

    assert end_clue.answer == "" # Verify __init__ logic for end clues

    mock_game = MockGame(clues_dict={"#C1#": c1, "#END#": end_clue})

    # Case 1: Dependency not completed
    c1.completed = False
    end_clue.completed = False # Ensure end_clue is not completed for this part
    assert end_clue.get_rendered_text(mock_game) == "Final: [DepText]"

    # Case 2: Dependency completed
    c1.completed = True
    end_clue.completed = False # Ensure end_clue is not completed for this part
    assert end_clue.get_rendered_text(mock_game) == "Final: DepAns"

    # Case 3: End clue itself (hypothetically) marked completed
    # Its answer is "", so it should return ""
    c1.completed = False # Reset c1 completion for clarity, though it won't be used by end_clue if end_clue is completed
    end_clue.completed = True # Manually set for testing this specific path
    assert end_clue.get_rendered_text(mock_game) == "", \
        "Completed end clue should return its answer (which is an empty string)."

    # Reset for safety if other tests use these instances, though pytest usually isolates.
    end_clue.completed = False


# --- Tests for previous_answers functionality (merged from src/bracket_city_mcp/tests/test_clue.py) ---

def test_clue_initialization_includes_previous_answers():
    """Test that a Clue object is initialized with an empty previous_answers list."""
    clue = Clue(clue_id="#C1#", clue_text="What is 2+2?", answer="4", depends_on=[])
    assert clue.previous_answers == []

def test_answer_clue_correct_updates_previous_answers():
    """Test answering a clue correctly updates previous_answers."""
    clue = Clue(clue_id="#C1#", clue_text="What is 2+2?", answer="4", depends_on=[])

    is_correct = clue.answer_clue("4")
    assert is_correct
    assert clue.completed
    assert clue.previous_answers == ["4"]

    # Second attempt (still correct, but already completed)
    is_correct_again = clue.answer_clue(" 4 ") # Test with spaces, original casing stored
    assert is_correct_again
    assert clue.completed
    assert clue.previous_answers == ["4", " 4 "]

def test_answer_clue_incorrect_updates_previous_answers():
    """Test answering a clue incorrectly updates previous_answers."""
    clue = Clue(clue_id="#C2#", clue_text="What is the capital of France?", answer="Paris", depends_on=[])

    is_correct = clue.answer_clue("London")
    assert not is_correct
    assert not clue.completed
    assert clue.previous_answers == ["London"]

    is_correct_again = clue.answer_clue("Berlin")
    assert not is_correct_again
    assert not clue.completed
    assert clue.previous_answers == ["London", "Berlin"]

def test_answer_clue_case_insensitivity_and_storage_for_previous_answers():
    """Test that answer checking is case-insensitive but stores original case in previous_answers."""
    clue = Clue(clue_id="#C3#", clue_text="Type 'Test'", answer="Test", depends_on=[])

    clue.answer_clue("test") # Lowercase
    assert clue.previous_answers == ["test"]

    clue.completed = False
    clue.answer_clue("TEST") # Uppercase
    assert clue.previous_answers == ["test", "TEST"]

    clue.completed = False
    clue.answer_clue("TeSt") # Mixed case
    assert clue.previous_answers == ["test", "TEST", "TeSt"]

def test_answer_clue_end_clue_updates_previous_answers():
    """Test that an end clue attempt updates previous_answers."""
    end_clue = Clue(clue_id="#END#", clue_text="Final puzzle.", answer="", depends_on=[], is_end_clue=True)

    end_clue.answer_clue("anything")
    assert end_clue.previous_answers == ["anything"] # Still records the attempt
    assert not end_clue.completed # Should not be completed
