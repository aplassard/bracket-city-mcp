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
