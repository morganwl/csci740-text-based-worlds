"""RoverOne, a simple agent that looks for directions in location
descriptions and attempts to follow them.

Modeled after TextWorld Agent class, but written to be independent of
TextWorld for flexibility"""

# A note on GameStates:
# TextWorld GameStates function as dictionaries with the keys:
# 'last_command', 'raw', 'done', 'feedback', 'won', 'lost', score',
# 'moves', 'location'

# Read description
# Check every word to see if it seems to be a direction
# Add that to knowledge-base

DIRECTIONS = ['north', 'south', 'east', 'west', 'up', 'down', 'left', 'right']
MODES = [EXPLORATION, EXPLOITATION] = [1, 2]


def tokenize(s):
    """Yields lower-cased tokens from a string, split by white space and
    punctuation."""
    buffer = []
    for c in s:
        if c.isalnum() or c == '-':
            buffer.append(c.lower())
        elif buffer:
            yield ''.join(buffer)
            buffer = []


class TreeNode:
    def __init__(self, state, action, parent):
        self.state = state
        self.action = action
        if parent:
            self.depth = parent.depth + 1
        else:
            self.depth = 0
        self.parent = parent

    @property
    def path(self):
        path = []
        node = self
        while node.action:
            path.append(node.action)
            node = node.parent
        return list(reversed(path))


class RoverKnowledge:
    """A KnowledgeBase that only stores information about rooms and
    their connections."""

    predicates = {'exit'}
    functions = {'go'}

    def __init__(self):
        self.locations = {}

    def tell(self, observation):
        """Receive an observation and record it in the knowledge
        base. Observations can be one of two types:

        ('exit', location, direction): a predicate indicating that an
                                       exit exists
        ('go', location, direction, destination): a function of
                                                  location and direction
                                                  returning destination
        """
        if observation[0] == 'exit':
            predicate, location, direction = observation
            self.add_exit(location, direction)
        elif observation[0] == 'go':
            function, location, direction, destination = observation
            self.add_go(location, direction, destination)
        else:
            raise Exception(f'Unknown property {observation[0]}')

    def ask(self, prop, *args):
        """Returns the answer, if any, to a query about the predicate or
        function prop with appropriate arguments. Known properties are
        'exit', 'go'."""
        if prop == 'exit':
            return self.ask_exit(*args)
        if prop == 'go':
            return self.ask_go(*args)
        raise Exception(f'Unknown knowledge base property {prop}')

    def path(self, location, destination):
        """Looks for a path from one state to another and returns one if
        it exists."""
        limit = 1
        reached = set()
        unexplored = True
        while unexplored:
            unexplored = False
            frontier = [TreeNode(location, None, None)]
            reached = set()
            while frontier:
                node = frontier.pop()
                if node.state == destination:
                    return node.path
                if node.depth == limit:
                    unexplored = True
                    continue
                for di, de in self.ask_list(node.state, 'go'):
                    if de not in reached:
                        frontier.append(
                            TreeNode(de, di, node))
                        reached.add(de)
            limit += 1
        return None

    def explore(self, location):
        """Looks for a location with unexplored exits and returns the
        first found location, exit pair."""
        limit = 1
        unexplored = True
        while unexplored:
            unexplored = False
            frontier = [TreeNode(location, None, None)]
            reached = set()
            while frontier:
                node = frontier.pop()
                e = self.unexplored(node.state)
                if e:
                    return node.state, e
                if node.depth == limit:
                    unexplored = True
                    continue
                for di, de in self.ask_list(node.state, 'go'):
                    if de not in reached:
                        frontier.append(
                            TreeNode(de, di, node))
                        reached.add(de)
            limit += 1
        return None, None

    def unexplored(self, location):
        """Returns the first unexplored exit at this location."""
        exits = self.ask_list(location, 'exit')
        for e in exits:
            if self.ask('go', location, e) is None:
                return e
        return None

    def ask_list(self, location, prop):
        obj = self.locations.get(location, None)
        # print(obj)
        if obj is not None:
            obj = obj.get(prop, None)
            # print(obj)
            if obj is not None:
                # print(obj)
                if prop in self.predicates:
                    return obj
                return obj.items()
        return []

    def ask_exit(self, location, direction):
        """Returns True if an exit in a given direction exists from a
        given location."""
        obj = self.locations.get(location, None)
        if obj is not None:
            obj = obj.get('exit', None)
            if obj is not None:
                return direction in obj
        return False
        
    def ask_go(self, location, direction):
        """Returns the value of go(location, direction), or None, if no
        such value is known to exist."""
        obj = self.locations.get(location, None)
        if obj is not None:
            obj = obj.get('go', None)
            if obj is not None:
                return obj.get(direction, None)
        return None

    def add_exit(self, location, direction):
        """Adds an exit predicate to a location in our knowledge base,
        creating the necessary parent objects if necessary."""
        if location not in self.locations:
            self.locations[location] = {}
        if 'exit' not in self.locations[location]:
            self.locations[location]['exit'] = set()
        self.locations[location]['exit'].add(direction)

    def add_go(self, location, direction, destination):
        """Adds a go function to a location in our knowledge base,
        creating the parent objects as necessary."""
        if location not in self.locations:
            self.locations[location] = {}
        if 'go' not in self.locations[location]:
            self.locations[location]['go'] = {}
        if (direction in self.locations[location]['go'] and
                destination != self.locations[location]['go']['direction']):
            raise Exception('Conflicting destinations found.')
        self.locations[location]['go'][direction] = destination


class RoverOne:
    """Simple roving agent."""

    def __init__(self):
        self.know_surroundings = False
        self.location = None
        self.last_command = None
        self.goals = []
        self.exploration_goals = []
        self.mode = EXPLORATION
        self.kb = RoverKnowledge()
        pass

    # API
    def reset(self, env) -> None:
        """Optionally reset environment flags."""
        pass

    def act(self, game_state, reward, done) -> str:
        """Acts upon the current game state."""
        # parse game state
        observations = self.parse(game_state)
        # tell knowledge base
        for o in observations:
            self.kb.tell(o)
        # ask knowledge base for next move
        action = None
        self.know_surroundings = self.last_command == 'look'
        if not self.know_surroundings:
            action = 'look'
        elif self.goals:
            path = self.kb.path(self.location, self.goals[-1])
            if path:
                action = f'go {path[0]}'
        while action is None:
            if self.exploration_goals:
                dest, direction = self.exploration_goals[-1]
                if dest == self.location:
                    self.exploration_goals.pop()
                    action = f'go {direction}'
                    break
                path = self.kb.path(self.location, dest)
                if path:
                    action = f'go {path[0]}'
                    break
            if self.exploration_goals:
                print(self.exploration_goals)
            dest, direction = self.kb.explore(self.location)
            if dest:
                self.exploration_goals.append((dest, direction))
            else:
                self.exploration_goals.extend([
                    (self.location, d) for d in DIRECTIONS])
        self.last_command = action
        return action

    def finish(self, game_state, reward, done):
        """Notify the agent that the game has finished."""
        pass

    # Implementation

    def parse(self, game_state):
        """Parses input from the game_state and returns a list of
        observations."""
        # Input can take a few forms
        # 1. Parser feedback when a command is not understood
        #
        # 2. Game feedback when a command is understood but does not
        # change the world state (includes feedback from examining and
        # also feedback from commands that have no outcome)
        #
        # 3. Game feedback when a command changes the world state
        observations = []

        # Assume input is in response to the 'look' command
        if self.last_command == 'look':
            location, feedback = game_state['feedback'].split('\n', 1)
            self.location = location.lower()
            for word in tokenize(feedback):
                if word in DIRECTIONS:
                    observations.append(('exit', self.location, word))
        return observations
