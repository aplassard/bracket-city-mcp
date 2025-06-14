from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .game import Game


class Clue:
    def __init__(self, clue_id: str, clue_text: str, answer: str, depends_on: list[str]):
        """
        Initializes a Clue object.

        Args:
            clue_id: The unique identifier for the clue (e.g., "#C1#").
            clue_text: The text of the clue.
            answer: The correct answer to the clue.
            depends_on: A list of clue IDs that this clue depends on.
        """
        self.clue_id = clue_id
        self.clue_text = clue_text
        self.answer = answer
        self.depends_on = depends_on
        self.completed = False

    def __repr__(self):
        return f"Clue(id='{self.clue_id}', completed={self.completed}, depends_on={self.depends_on})"

    def answer_clue(self, provided_answer: str) -> bool:
        """
        Checks if the provided answer is correct for this clue.
        Updates the completion status if the answer is correct.

        Args:
            provided_answer: The answer provided by the user.

        Returns:
            True if the answer is correct, False otherwise.
        """
        # Case-insensitive comparison
        if provided_answer.strip().lower() == self.answer.strip().lower():
            self.completed = True
            return True
        return False

    def get_rendered_text(self, game: 'Game') -> str:
        if self.completed:
            return self.answer

        current_text = self.clue_text
        for dependency_id in self.depends_on:
            dependent_clue = game.clues[dependency_id]
            # Recursively get the text from the dependent clue
            rendered_dependency_text = dependent_clue.get_rendered_text(game)

            # If the dependent clue is NOT completed, its entire rendered output
            # (which might include its own resolved dependencies) should be bracketed.
            if not dependent_clue.completed:
                rendered_dependency_text = f"[{rendered_dependency_text}]"

            current_text = current_text.replace(dependency_id, rendered_dependency_text)
        return current_text
