"""A logical knowledge base for making inferences based on information
learned from a game world."""


from collections import namedtuple, defaultdict

from . import Predicate, AndClause, LogicPart

Function = namedtuple('Function', ['predicate', 'argument'])


def isvar(identifier):
    """Returns True if an identifier is a variable."""
    return isinstance(identifier, str) and identifier.isupper()


def unify(x, y, substitution=None):
    """Return a substitution for free variables that makes sentences x
    and y equal."""
    # pylint: disable=too-many-return-statements
    # this function design is not the clearest, but I'm using it more or
    # less as written in the Russell + Norvig textbook
    if substitution is None:
        substitution = {}
    if substitution is False:
        return False
    if x == y:
        return substitution
    if isvar(x) or x in substitution:
        return unify_var(x, y, substitution)
    if isvar(y) or y in substitution:
        return unify_var(y, x, substitution)
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
    """Have to tease out the semantics of this function taken from
    Russell and Norvig."""
    if var in substitution:
        return unify(substitution[var], x, substitution)
    if x in substitution:
        return unify(var, substitution[x], substitution)
    if occur_check(var, x):
        return False
    substitution[var] = x
    return substitution


def occur_check(var, x):
    # pylint: disable=unused-argument
    """Does nothing."""
    return False


class LogicBase:
    """A knowledge base using first order logical entailment."""

    def __init__(self, max_models=5):
        """Initialize the logic base."""
        self.models = [Model()]
        self.implications = []
        self.rules = []
        self.functions = {}
        self.constants = set()
        self.max_models = max_models

    def tell(self, observations):
        """Report observations to the knowledge base."""
        for o in observations:
            if isinstance(o, (tuple, list)):
                o = Predicate(*o)
            self.store(o)
        self.forward_chain()
        self.occams_razor()

    def path(self, goal):
        """Returns a list of sub-goals and, if available, an action
        leading towards the requested goal."""
        return None

    def explore(self):
        for rule in self.rules:
            subs = self.fetch(rule.premise)
            print(subs)
            if not subs:
                continue
            best_sub = sorted(subs, lambda x: len(x))[0]
            return map(lambda x: best_sub[x] if x in best_sub else x,
                       rule.action)
        return None

    def advance(self, action):
        """Advances the time state of the knowledge base and updates the
        action predicate."""
        self.models.append(Model(action=action))
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
        self.constants.union(set(literal.args))
        for arg in literal.args:
            self.constants.add(arg)
        time -= 1
        self.models[time].store(literal.name, literal.args,
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

    def fetch_possible(self, sentence, substitution=None):
        """Returns a list of substitutions for variables that does not
        make a sentence false."""
        if isinstance(sentence, Predicate):
            return self.fetch(sentence, substitution)
        if isinstance(sentence, AndClause):
            substitutions = [{}]
            for predicate in sentence:
                new_subs = []
                for sub in substitutions:
                    new_sub = self.fetch(predicate.substitute(sub))
                    if new_sub is False:
                        continue
                    if new_sub:
                        for s in new_sub:
                            s.update(sub)
                            new_subs.append(s)
                    else:
                        new_subs.append(sub)
                if not new_subs:
                    return []
                substitutions = new_subs
            return substitutions
        return []
        # TO-DO: Test this fetch_possible algorithm

    def fetch(self, sentence, substitution=None):
        """Returns a list of substitutions for variables that makes
        sentence entailed by the knowledge base."""
        substitutions = []
        if isinstance(sentence, Predicate):
            if sentence.time is not None and sentence.time < 0:
                models = self.models[:sentence.time]
            else:
                models = self.models

            matches = set()
            for model in reversed(models):
                result = model.fetch(sentence, matches,
                                     initial_substitution=substitution)
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

    def add_implication(self, implication):
        """Adds an implication to the knowledge base."""
        self.implications.append(implication)

    def forward_chain(self, goal=None):
        """If a rule is entailed by the knowledge base, adds any
        additional knowledge to the knowledge base and repeats."""
        # pylint: disable=unused-argument
        # goal argument for planned feature
        change = False
        for imp in self.implications:
            subs = imp.premise.eval(self)
            if not subs:
                continue
            for sub in subs:
                conclusion = imp.conclusion(self, sub)
                for literal in conclusion:
                    if literal and not self.ask_literal(literal.name,
                                                        literal.args,
                                                        literal.value):
                        self.store(literal)
                        change = True
        if change:
            self.forward_chain()

    def occams_razor(self):
        """Based on observed changes to the state and the current
        action, finds the action rule which would *could* be entailed by
        the knowledge base with the least number of new predicates. Will
        not negate existing predicates. THIS YIELDS AN ASSUMPTION AND
        INFERRENCES MADE ARE NOT SOUND."""
        changed = []
        for predicate in self.models[-1]:
            if not predicate.eval(self, time=-1):
                changed.append(predicate)
        for predicate in changed:
            simplest_count = 2**7
            simplest_rule = None
            for rule in self.rules:
                sub = unify(AndClause((self.action, predicate)),
                            AndClause((rule.action, rule.consequent)))
                count = 0
                predicates = []
                if sub and predicate.value == rule.consequent.value:
                    for clause in rule.premise.args:
                        new_clause = clause.substitute(self, time=-1,
                                                       sub=sub)
                        r = self.fetch(new_clause)
                        if r:
                            for s in r:
                                sub.update(s)
                        else:
                            r = self.ask_literal(
                                new_clause.name,
                                new_clause.args,
                                new_clause.value,
                                time=-1)
                            if r is False:
                                count = -1
                                break
                            if r is None:
                                count += 1
                                predicates.append(new_clause)
                    if 0 <= count < simplest_count:
                        simplest_count = count
                        simplest_rule = (rule, sub, predicates)
            if simplest_rule:
                rule, sub, predicates = simplest_rule
                conclusion = rule.conclusion(self, sub)
                for literal in predicates:
                    self.store(literal)
                for literal in conclusion:
                    self.store(literal)

    def fetch_rules(self, goal):
        """Returns all rules that could satisfy a goal."""
        return [rule for rule in self.rules
                if unify(rule.consequent, goal)]

    @property
    def action(self):
        """Returns the most recent action."""
        return self.models[-1].action

    @property
    def predicates(self):
        """Returns all predicates in the knowledge base."""
        temp_model = Model()
        for model in self.models:
            temp_model.merge(model)
        return temp_model.predicates


class Model:
    """A model of ground truths."""
    def __init__(self, action=None, initial=None):
        self.predicates = defaultdict(dict)
        if action is None:
            action = tuple()
        self.action = action
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

    def fetch(self, sentence, matches=None, initial_substitution=None):
        """Returns all substitutions which makes a sentence valid,
        skipping any predicates in matches and, optionally, starting
        with an initial substitution."""
        substitutions = []
        if matches is None:
            matches = set()
        if isinstance(sentence, Predicate):
            for literal, v in self.predicates[sentence.name].items():
                if literal in matches:
                    continue
                substitution = unify(sentence,
                                     Predicate(sentence.name,
                                               literal),
                                     initial_substitution)
                if substitution is not False:
                    matches.add(literal)
                    if v == sentence.value:
                        substitutions.append(substitution)
            return substitutions, matches
        return None

    def merge(self, other):
        """Merge the values of another model into this one."""
        self.action = other.action
        for predicate in other.predicates:
            self.predicates[predicate].update(
                other.predicates[predicate])

    def __iter__(self):
        for predicate, values in self.predicates.items():
            for args, value in values.items():
                yield Predicate(predicate, args, value)
