"""RoverTwo, a simple agent that looks for directions in location
descriptions, and attempts to follow them."""

DIRECTIONS = ['north', 'south', 'east', 'west', 'up', 'down',
              'northwest', 'northeast', 'southwest', 'southeast']
REJECTIONS = ["I don't know the word"]
MODES = [EXPLORATION, EXPLOITATION] = [1, 2]
DEBUG = True

from random import shuffle

from . import LogicBase, Predicate, AndClause, Implication, \
    LinearImplication

RULES = [
    LinearImplication(
        ('go', 'DIRECTION'),
        AndClause([
            Predicate('at', ('player', 'LOCATION')),
            Predicate('exit', ('LOCATION', 'DIRECTION'),
                      carry=True),
            Predicate('connects',
                      ('LOCATION', 'DIRECTION', 'DESTINATION'),
                      carry=True)]),
        Predicate('at', ('player', 'DESTINATION')))]


def tokenize(s):
    """Yields lower-cased tokens from a string, split by white space and
    punctuation."""
    buffer = []
    for c in s:
        if c.isalnum():
            buffer.append(c.lower())
        elif buffer:
            yield ''.join(buffer)
            buffer = []
    if buffer:
        yield ''.join(buffer)


def split_location(s):
    """Returns a cleaned (location, description) pair."""
    # TO-DO: This is a clumsy-ass way of doing this
    # import pdb
    # pdb.set_trace()
    lines = (line for line in s.split('\n'))
    line = ''
    while line == '':
        try:
            line = next(lines)
            # print('>', line)
        except StopIteration:
            return '', ''
    location = clean(line)
    description = '\n'.join([line for line in lines if line != ''])
    # print(location)
    # print(description)
    return location, description


def clean(s):
    """Returns a cleaned version of the string with punctuation and
    trailing spaces removed."""
    return ' '.join(tokenize(s))


class RoverTwo:
    """Simple roving agent."""

    def __init__(self, seed=None):
        self.know_surroundings = False
        self.location = None
        self.loc_description = ''
        self.last_command = ('',)
        self.goals = []
        self.exploration_goals = []
        self.mode = EXPLORATION
        self.kb = LogicBase()
        for rule in RULES:
            self.kb.add_rule(rule)
        self.last_parse = None
        self.current_goal = None

    # API
    def reset(self, env) -> None:
        """Optionally reset environment flags."""
        pass

    def act(self, game_state, reward, done) -> str:
        """Acts upon the current game state."""
        # parse game state
        observations = self.parse(game_state)

        # tell knowledge base
        self.kb.advance(self.last_command)
        self.kb.tell(observations)
        # ask knowledge base for next move
        action = None
        if not self.know_surroundings:
            self.current_goal = 'knowledge'
            action = ('look',)
            self.know_surroundings = True
        elif self.goals:
            path = self.kb.path(self.goals[-1])
            if path:
                self.current_goal = path
                action = ('go', path[0])
        else:
            action = self.act_explore()

        self.last_command = action
        return ' '.join(action)

    def finish(self, game_state, reward, done):
        """Notify the agent that the game has finished."""
        pass

    def debug_info(self):
        predicates = self.kb.predicates
        return {
            'location': self.location,
            'last_parse': self.last_parse,
            'goals': self.goals,
            'predicates': predicates,
            'exploration_goals': self.exploration_goals,
            'current goal': self.current_goal,
        }

    # Implementation
    def act_explore(self):
        """Return an action that helps to uncover new knowledge."""
        dest, direction = self.kb.explore()
        if dest:
            self.exploration_goals.append((dest, direction))
        if self.exploration_goals:
            dest, direction = self.exploration_goals[-1]
            if dest == self.location:
                self.exploration_goals.pop()
                self.current_goal = (dest, direction)
                return ('go', direction)
            path = self.kb.path(self.location, dest)
            if path:
                self.current_goal = path
                return ('go', path[0])
        # new_exploration = [(self.location, d) for d in DIRECTIONS
        #     if self.kb.ask('go', self.location, d) is None]
        # if new_exploration:
        #     dest, direction = new_exploration.pop()
        #     self.exploration_goals.extend(new_exploration)
        #     self.current_goal = (dest, direction)
        #     return f'go {direction}'
        exits = [d for d in DIRECTIONS]

        shuffle(exits)
        if exits:
            direction = exits.pop()
            self.current_goal = direction
            return ('go', direction)
        self.current_goal = 'knowledge'
        return ('look',)

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
        msg = game_state['feedback']

        if self.is_rejection(msg):
            return observations
        if self.last_command and self.last_command[0] == 'go':
            if self.is_move(msg):
                observations = self.parse_move(msg)
            else:
                observations = [('exit', (self.location,
                                 self.last_command[1],),
                                 False)]
            return observations
        # Assume input is in response to the 'look' command
        if self.last_command == ('look',) and '\n' in msg:
            location, feedback = split_location(msg)
            for word in tokenize(feedback):
                if word in DIRECTIONS:
                    observations.append(('exit', (location, word)))
            observations.append(('at', ('player', location)))
            self.location = location
        return observations

    def parse_move(self, msg):
        location, feedback = split_location(msg)
        observations = [('exit', (location, word))
                        for word in tokenize(feedback)
                        if word in DIRECTIONS]
        observations.append(('at', ('player', location)))
        if self.location:
            observations.append(
                ('at', ('player', self.location), False))
        self.location = location
        return observations

    def is_rejection(self, msg):
        for r in REJECTIONS:
            if msg.startswith(r):
                if DEBUG:
                    self.last_parse = 'rejection'
                return True

    def is_move(self, msg):
        if '\n' not in msg:
            return False
        lines = msg.split('\n')
        if lines[0].endswith('.'):
            return False
        if DEBUG:
            self.last_parse = 'move'
        return True
