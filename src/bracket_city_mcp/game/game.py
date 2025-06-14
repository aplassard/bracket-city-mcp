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

        # These will be properly implemented in the next steps
        self._build_graph()
        self._perform_initial_sort()

        # Check for the single end clue requirement
        if len(self.end_clues) != 1:
            raise ValueError(
                f"Game must have exactly one end clue. "
                f"Found {len(self.end_clues)} end clues: {self.end_clues}"
            )

        self.active_clues: set[str] = set(self.start_clues)

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

            # Ensure all clues are keys in adj and rev_adj, even if they have no connections
            # This helps in _perform_initial_sort for identifying start/end clues correctly.
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

        # Sort for deterministic behavior, though not strictly necessary for functionality
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
            # Or raise an error, e.g., ValueError(f"Clue ID {clue_id} not found.")
            return False

        if clue_id not in self.active_clues:
            # Clue is not currently available to be answered.
            # You might want to provide more specific feedback to the user here.
            return False

        clue_to_answer = self.clues[clue_id]

        # The Clue object's answer_clue method handles case-insensitivity
        # and updates its own 'completed' status.
        is_correct = clue_to_answer.answer_clue(provided_answer)

        if is_correct:
            # Remove from active_clues as it's now completed.
            # It won't be added back by _reveal_new_clues because it's completed.
            self.active_clues.discard(clue_id)

            # Now, check if this completion reveals new clues.
            self._reveal_new_clues(clue_id)

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
                continue # Should not happen if graph is built correctly

            potential_clue_obj = self.clues[potential_new_clue_id]
            if potential_clue_obj.completed:
                continue # Already completed, nothing to do

            # Check if all dependencies for this potential new clue are met
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
