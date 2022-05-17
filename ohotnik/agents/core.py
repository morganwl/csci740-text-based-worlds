"""Abstract base classes."""

# The agent will Tell observations to the Knowledge Base, including the
# action it has just taken.

# The agent will ask the knowledge base if a path exists to its goal.

# If no path exists, the agent will ask the knowledge base for an
# exploration goal.


class KnowledgeBase:
    """Base knowledge bade class."""

    def tell(self, observations):
        """Report observations to the knowledge base."""
        raise NotImplementedError()

    def path(self, sentence):
        """Returns a sequence of actions leading from the current state
        to sentence, if one exists. If no known path exists, returns
        None. If sentence is already entailed, returns an empty list."""
        raise NotImplementedError()

    def explore(self):
        """Returns a reachable goal, with an action to be taken once
        that goal is reached, that will yield knew knowledge. Also
        returns the action in the path to that goal."""
        raise NotImplementedError()
