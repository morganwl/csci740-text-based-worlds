"""A logical knowledge base for making inferences based on information
learned from a game world."""


from collections import namedtuple, defaultdict

from . import Predicate, FunctionNode, Implication, \
    AndClause, LogicPart

Function = namedtuple('Function', ['predicate', 'argument'])


def isvar(identifier):
    """Returns True if an identifier is a variable."""
    return isinstance(identifier, str) and identifier.isupper()


def unify(x, y, substitution=None):
    """Russell and Norvig substitution algorithm"""
    if substitution is None:
        substitution = {}
    if substitution is False:
        return False
    if x == y:
        return substitution
    if isvar(x):
        return unify_var(x, y, substitution)
    if isvar(y):
        return unify_var(x, y, substitution)
    if isinstance(x, LogicPart) and isinstance(y, LogicPart):
        return unify(x.args, y.args,
                     unify(x.operator,
                           y.operator, substitution))
    if isinstance(x, (list, tuple)) and isinstance(y, (list, tuple)):
        return unify(x[1:], y[1:],
                     unify(x[0], y[0],
                           substitution))
    return False


def unify_var(var, x, substitution: dict):
    if var in substitution:
        return unify(substitution[var], x, substitution)
    if x in substitution:
        return unify(var, substitution[x], substitution)
    if occur_check(var, x):
        return False
    substitution[var] = x
    return substitution


def occur_check(var, x):
    return False


class LogicBase:
    """A knowledge base using first order logical entailment."""

    def __init__(self, max_models=5):
        """Initialize the logic base."""
        self.models = [Model()]
        self.rules = []
        self.functions = {}
        self.constants = set()
        self.max_models = max_models

    def tell(self, observations):
        """Report observations to the knowledge base."""
        for o in observations:
            if isinstance(o, tuple):
                o = Predicate(*o)
            self.store(o)
        self.forward_chain()

    def advance(self):
        """Advances the time state of the knowledge base."""
        self.models.append(Model())
        while len(self.models) > self.max_models:
            self.models[0].merge(self.models.pop(1))

    def entails(self, sentence):
        """Returns True if a sentence is entailed by the knowledge base,
        False if a sentence is contradicted by the knowledge base, and
        None if not enough information is present in the knowledge
        base."""
        return sentence.eval(self)

    def store(self, literal, time=0):
        """Stores a literal in the knowledge base."""
        args = []
        for i, arg in enumerate(literal.args):
            if isinstance(arg, FunctionNode):
                arg = arg.eval(self)
            args.append(arg)
            self.constants.add(arg)
        time -= 1
        self.models[time].store(literal.name, tuple(args),
                                literal.value)

    def ask_literal(self, predicate, args, value, time=None):
        """Compares a literal to the knowledge base.."""
        result = None
        if time is not None and time < 0:
            models = self.models[:time]
        else:
            models = self.models
        for model in reversed(models):
            result = model.ask(predicate, args)
            if result is not None:
                return result is value
        return None

    def ask_function(self, function, args, time=None):
        """Returns the name of the constant referred to by a function,
        if one exists."""
        if function in self.functions:
            predicate, argument = self.functions[function]
            result = self.fetch(
                Predicate(predicate,
                          args[:argument] + ('X',) + args[argument:],
                          time=time))
            if result:
                return result[0]['X']
        return None

    def fetch(self, sentence):
        """Returns a list of substitutions for variables that makes
        sentence entailed by the knowledge base."""
        substitutions = []
        if isinstance(sentence, Predicate):
            if sentence.time is not None and sentence.time < 0:
                models = self.models[:sentence.time]
            else:
                models = self.models

            # we need a way to make sure we are only taking the most
            # current value of a predicate. maybe the simplest and most
            # efficient way to do this is returning a match list along
            # with a substitution list.
            matches = set()
            for model in reversed(models):
                result = model.fetch(sentence, matches)
                if result is False:
                    return False
                subs, ms = result
                substitutions.extend(subs)
                matches.update(ms)
        if len(substitutions) == 0:
            return None
        return substitutions

    def add_function(self, name, predicate, argument):
        """Adds a logical function to the knowledge base."""
        self.functions[name] = (Function(predicate, argument))

    def add_rule(self, rule):
        """Add a rule to the knowledge base."""
        self.rules.append(rule)

    def forward_chain(self):
        """If a rule is entailed by the knowledge base, adds any
        additional knowledge to the knowledge base and repeats."""
        change = False
        for rule in self.rules:
            subs = rule.premise.eval(self)
            if not subs:
                continue
            for sub in subs:
                if not rule.consequent.eval(self, sub=sub):
                    self.store(rule.conclusion(self, sub))
                    change = True
                change = True
        if change:
            self.forward_chain()


class Model:
    """A model of ground truths."""
    def __init__(self, initial=None):
        self.predicates = defaultdict(dict)
        if initial is not None:
            self.predicates.update(initial)

    def ask(self, predicate: str, args: tuple):
        """Returns the value of a predicate if it is stored in this
        model."""
        if predicate in self.predicates and \
                args in self.predicates[predicate]:
            return self.predicates[predicate][args]
        return None

    def store(self, predicate: str, args: tuple, value: bool):
        """Stores the value of a predicate."""
        self.predicates[predicate][args] = value

    def fetch(self, sentence, matches=None):
        substitutions = []
        if matches is None:
            matches = set()
        if isinstance(sentence, Predicate):
            for literal, v in self.predicates[sentence.name].items():
                if literal in matches:
                    continue
                substitution = unify(sentence,
                                     Predicate(sentence.name,
                                               literal))
                if substitution is not False:
                    if v != sentence.value:
                        return False
                    substitutions.append(substitution)
                    matches.add(literal)
            return substitutions, matches

    def merge(self, other):
        for predicate in other.predicates:
            self.predicates[predicate].update(other.predicates)


if __name__ == '__main__':
    kb = LogicBase()

    kb.add_function('location', 'at', 1)
    kb.add_function('destination', 'connects', 2)
    kb.add_function('last_action', 'action', 1)
    kb.add_function('action_obj_1', 'action_obj', 1)

    rules = [
        Implication(
            AndClause([
                Predicate('action_obj', ['go', 'south']),
                Predicate('at', ['player', FunctionNode('location',
                                                        ['player'],
                                                        time=-1)],
                          False)]),
            Predicate('connects', [FunctionNode('location', ['player'],
                                                time=-1),
                                   'south',
                                   FunctionNode('location', ['player'],
                                                )])
        )
    ]

    for rule in rules:
        kb.add_rule(rule)

    kb.tell([Predicate('room', ['living room']),
             Predicate('exit', ['living room', 'south']),
             Predicate('at', ['player', 'living room']),
             ])

    kb.advance()
    print(kb.entails(
        Predicate('exit', [FunctionNode('location', ['player']), 'south'])))

    kb.tell([Predicate('action', ['action_obj']),
             Predicate('action_obj', ['go', 'south']),
             Predicate('at', ['player', 'dining room']),
             Predicate('at', ['player', 'living room'], False),
             ])

    print(kb.entails
          (Predicate('exit', ['living room', 'south'])))
    print(kb.entails
          (Predicate('exit', ['living room', 'north'])))
    print(kb.entails(
        Predicate('connects', ['living room', 'south', 'dining room'])))
    print(kb.entails(
        Predicate('exit', [FunctionNode('location', ['player']), 'south'])))
