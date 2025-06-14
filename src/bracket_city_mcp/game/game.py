import json
from collections import defaultdict, deque # Added deque for topological sort
from .clue import Clue

class Game:
    def __init__(self, game_data: dict):
        """
        Initializes a Game object from parsed JSON data.

        Args:
            game_data: A dictionary representing the game's data,
                       typically loaded from a JSON file. It should
                       have a "clues" key containing a dictionary of
                       clue information.
        Raises:
            ValueError: If the game does not have exactly one end clue.
        """
        self.clues: dict[str, Clue] = {}
        # adj: dependency_id -> [list of clue_ids that depend on it]
        self.adj: defaultdict[str, list[str]] = defaultdict(list)
        # rev_adj: clue_id -> [list of clue_ids it depends on]
        self.rev_adj: defaultdict[str, list[str]] = defaultdict(list)

        if "clues" in game_data:
            for clue_id, clue_info in game_data["clues"].items():
                self.clues[clue_id] = Clue(
                    clue_id=clue_id,
                    clue_text=clue_info.get("clue", ""),
                    answer=clue_info.get("answer", ""),
                    depends_on=clue_info.get("depends_on", [])
                )

        self._build_graph()
        self._perform_initial_sort()

        # Set is_end_clue flag for the identified end clue(s)
        # This is done after _perform_initial_sort populates self.end_clues
        for clue_id, clue_obj in self.clues.items():
            if clue_id in self.end_clues:
                clue_obj.is_end_clue = True
                clue_obj.answer = "" # Ensure end clues have no answer

        if len(self.end_clues) != 1:
            raise ValueError(
                f"Game must have exactly one end clue. "
                f"Found {len(self.end_clues)} end clues: {self.end_clues}"
            )

        self.active_clues: set[str] = set(self.start_clues)
        self.incorrect_guesses: int = 0

    @classmethod
    def from_json_file(cls, filepath: str) -> 'Game':
        """
        Loads a game from a JSON file.

        Args:
            filepath: The path to the JSON file.

        Returns:
            A Game instance.

        Raises:
            FileNotFoundError: If the filepath does not exist.
            json.JSONDecodeError: If the file is not valid JSON.
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            game_data = json.load(f)
        return cls(game_data)

    @property
    def is_complete(self) -> bool:
        """
        Checks if all non-end clues in the game are completed.
        The game is considered complete if every clue, except for the
        designated end clue, has its 'completed' attribute set to True.
        """
        # Ensure there is an end clue identified.
        # The constructor should ensure self.end_clues has exactly one item.
        if not self.end_clues:
            # This case should ideally not be reached if constructor logic is sound.
            return False

        end_clue_id = self.end_clues[0]

        for clue_id, clue_obj in self.clues.items():
            if clue_id == end_clue_id:
                continue  # Skip the end clue itself

            # If any non-end clue is not completed, the game is not complete.
            if not clue_obj.completed:
                return False

        # All non-end clues are completed.
        return True

    def _build_graph(self):
        """
        Builds the adjacency lists for clue dependencies.
        Populates self.adj (dependency -> dependents) and
        self.rev_adj (clue -> dependencies).
        """
        for clue_id, clue_obj in self.clues.items():
            # For rev_adj: clue_id -> [list of dependencies]
            # Record all dependencies for the current clue_id
            if clue_obj.depends_on:
                for dependency_id in clue_obj.depends_on:
                    if dependency_id in self.clues: # Ensure dependency exists
                        self.rev_adj[clue_id].append(dependency_id)

            # For adj: dependency_id -> [list of clues that depend on it]
            # For each dependency of the current clue_obj, add clue_id to its list of dependents
            if clue_obj.depends_on:
                for dependency_id in clue_obj.depends_on:
                    if dependency_id in self.clues: # Ensure dependency exists
                        self.adj[dependency_id].append(clue_id)

            if clue_id not in self.adj:
                self.adj[clue_id] = []
            if clue_id not in self.rev_adj:
                self.rev_adj[clue_id] = []


    def _perform_initial_sort(self):
        """
        Identifies start clues (no dependencies) and end clues (nothing depends on them).
        Populates self.start_clues and self.end_clues.
        This isn't a full topological sort of the path, but rather identifies
        initial nodes and terminal nodes of the graph.
        """
        self.start_clues: list[str] = []
        self.end_clues: list[str] = []

        for clue_id in self.clues:
            # Start clues are those not present as keys in rev_adj (or have empty dependency lists)
            if not self.rev_adj[clue_id]:
                self.start_clues.append(clue_id)

            # End clues are those not present as keys in adj (or have empty dependent lists)
            if not self.adj[clue_id]:
                self.end_clues.append(clue_id)

        self.start_clues.sort()
        self.end_clues.sort()

    def answer_clue(self, clue_id: str, provided_answer: str) -> bool:
        """
        Attempts to answer a clue.

        Args:
            clue_id: The ID of the clue to answer.
            provided_answer: The provided answer string.

        Returns:
            True if the answer was correct, False otherwise.
            Returns False if the clue is not active or does not exist.
        """
        if clue_id not in self.clues:
            return False

        if clue_id not in self.active_clues:
            return False

        clue_to_answer = self.clues[clue_id]

        is_correct = clue_to_answer.answer_clue(provided_answer)

        if is_correct:
            self.active_clues.discard(clue_id)
            self._reveal_new_clues(clue_id)
        else:
            # Only increment incorrect guesses for actual clues, not end clues
            if not clue_to_answer.is_end_clue:
                self.incorrect_guesses += 1

        return is_correct

    def _reveal_new_clues(self, completed_clue_id: str):
        """
        Reveals new clues based on a completed clue.
        A clue is revealed if it's not already completed and all its
        dependencies are completed. Revealed clues are added to self.active_clues.

        Args:
            completed_clue_id: The ID of the clue that was just completed.
        """
        if completed_clue_id not in self.adj:
            return # This clue has no dependents

        for potential_new_clue_id in self.adj[completed_clue_id]:
            if potential_new_clue_id not in self.clues:
                continue

            potential_clue_obj = self.clues[potential_new_clue_id]
            if potential_clue_obj.completed:
                continue

            all_dependencies_met = True
            if potential_new_clue_id in self.rev_adj:
                for dependency_id in self.rev_adj[potential_new_clue_id]:
                    if dependency_id not in self.clues or not self.clues[dependency_id].completed:
                        all_dependencies_met = False
                        break

            if all_dependencies_met:
                self.active_clues.add(potential_new_clue_id)

    def __repr__(self):
        return f"Game(clues={len(self.clues)}, active_clues={len(self.active_clues)}, start_clues={len(self.start_clues)}, end_clues={len(self.end_clues)})"

    def get_rendered_clue_text(self, clue_id: str) -> str:
        """
        Gets the rendered text of a specific clue, resolving dependencies.

        Args:
            clue_id: The ID of the clue to render.

        Returns:
            The rendered text of the clue.

        Raises:
            ValueError: If the clue_id does not exist.
        """
        if clue_id not in self.clues:
            raise ValueError(f"Clue ID '{clue_id}' not found in game.")

        clue_obj = self.clues[clue_id]
        return clue_obj.get_rendered_text(self)

    def get_rendered_game_text(self) -> str:
        """
        Gets the rendered text of the entire game, starting from the end clue.
        Assumes there is exactly one end clue.

        Returns:
            The rendered text of the game.
        """
        end_clue_id = self.end_clues[0]
        return self.get_rendered_clue_text(end_clue_id)

    def get_first_dependent_clue_id(self, clue_id: str) -> str | None:
        """
        Gets the ID of the first clue that depends on the given clue_id.

        This is determined by looking at the game's adjacency list (self.adj),
        which maps a clue ID to a list of other clue IDs that have it as a dependency.

        Args:
            clue_id: The ID of the clue for which to find the first dependent.

        Returns:
            The ID of the first dependent clue if one exists, otherwise None.
            Returns None if the provided clue_id itself does not exist in the game.
        """
        if clue_id not in self.clues:
            # Or raise ValueError(f"Clue ID '{clue_id}' not found in game.")
            # For consistency with get_rendered_clue_text, raising an error might be better,
            # but the subtask specified None is fine for this context.
            return None

        children_clues = self.adj.get(clue_id, [])
        return children_clues[0] if children_clues else None
