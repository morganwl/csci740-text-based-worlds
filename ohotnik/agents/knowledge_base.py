"""A logical knowledge base for making inferences based on information
learned from a game world."""

from collections import namedtuple, defaultdict

from logic_parts import Predicate, FunctionNode, Implication, AndClause

Function = namedtuple('Function', ['predicate', 'argument'])


class LogicBase:
    """A knowledge base using first order logical entailment."""

    def __init__(self):
        """Initialize the logic base."""
        self.prior_model = defaultdict(dict)
        self.post_model = defaultdict(dict)
        self.rules = []
        self.functions = {}
        self.constants = set()

    def update(self, observations):
        """Report observations to the posterior model of the knowledge
        base."""
        for o in observations:
            if isinstance(o, tuple):
                o = Predicate(*o, posterior=True)
            self.store(o)
        self.forward_chain()

    def tell(self, observations):
        """Report observations to the knowledge base."""
        for o in observations:
            if isinstance(o, tuple):
                o = Predicate(*o)
            self.store(o)
        self.forward_chain()

    def advance(self):
        """Advances the time state of the knowledge base."""

    def entails(self, sentence):
        """Returns True if a sentence is entailed by the knowledge base,
        False if a sentence is contradicted by the knowledge base, and
        None if not enough information is present in the knowledge
        base."""
        return sentence.eval(self)

    def store(self, sentence):
        """Stores a sentence in the knowledge base."""
        if isinstance(sentence, Predicate):
            for arg in sentence.args:
                if not isinstance(arg, str):
                    raise ValueError('Predicates in tell can only contain evaluated constants')
                self.constants.add(arg)
            if sentence.posterior:
                self.post_model[sentence.name][tuple(sentence.args)] = \
                    sentence.value
            else:
                self.prior_model[sentence.name][tuple(sentence.args)] = \
                    sentence.value

    def ask_posterior_literal(self, predicate, args, value):
        """Compares a literal to the posteriod model and, if absent,
        compares it to the prior model."""
        if (predicate in self.post_model and
                tuple(args) not in self.post_model[predicate]):
            return self.post_model[predicate][tuple(args)] is value
        return self.ask_literal(predicate, args, value)

    def ask_literal(self, predicate, args, value, posterior=False):
        """Compares a literal to the prior model."""
        if posterior:
            return self.ask_posterior_literal(predicate, args, value)
        if predicate not in self.prior_model:
            return None
        if tuple(args) not in self.prior_model[predicate]:
            return None
        return self.prior_model[predicate][tuple(args)] is value

    def ask_function(self, function, args, posterior=False):
        """Returns the name of the constant referred to by a function,
        if one exists."""
        if function in self.functions:
            predicate, argument = self.functions[function]
            result = self.fetch(['X'], Predicate(
                predicate, args[:argument] + ['X'] + args[argument:],
                posterior=posterior))
            if result:
                return result[0]
        return None

    def fetch(self, variables, sentence):
        """Returns a list of substitutions for variables that makes
        sentence entailed by the knowledge base."""
        substitutions = []
        if isinstance(sentence, Predicate):
            if sentence.posterior:
                model = self.post_model
            else:
                model = self.prior_model
            for literal in model[sentence.name]:
                if sentence.value != \
                        model[sentence.name][literal]:
                    continue
                substitution = self.unify(variables, sentence, literal)
                if substitution is not None:
                    substitutions.append(substitution)
        return substitutions
                
    def unify(self, variables, sentence, literal):
        """Returns the substitution that makes sentence match literal."""
        if isinstance(sentence, Predicate):
            for a, b in zip(sentence.args, literal):
                if a in variables:
                    substitution = b
                    continue
                if a != b:
                    return None
        return substitution

    def add_function(self, name, predicate, argument):
        """Adds a logical function to the knowledge base."""
        self.functions[name] = (Function(predicate, argument))

    def add_rule(self, rule):
        self.rules.append(rule)

    def forward_chain(self):
        """If a rule is entailed by the knowledge base, adds any
        additional knowledge to the knowledge base and repeats."""
        change = False
        for rule in self.rules:
            if rule.premise.eval(self) and \
                    rule.consequent.eval(self) is None:
                self.store(rule.conclusion())
                change = True
        if change:
            self.forward_chain()


if __name__ == '__main__':
    kb = LogicBase()

    kb.add_function('location', 'at', 1)
    kb.add_function('destination', 'connects', 2)
    kb.add_function('last_action', 'action', 1)
    kb.add_function('action_obj_1', 'action_obj', 1)

    rules = [
        Implication(
            AndClause([
                Predicate('action_obj', ['go', 'south'], posterior=True),
                Predicate('at', ['player', FunctionNode('location',
                                                        ['player'],
                                                        posterior=True)]
                          )]),
            Predicate('connects', [FunctionNode('location', ['player'],
                                                posterior=False),
                                   'south',
                                   FunctionNode('location', ['player'],
                                                posterior=True)])
        )
    ]

    for rule in rules:
        kb.add_rule(rule)


    kb.tell([Predicate('room', ['living room']),
             Predicate('exit', ['living room', 'south']),
             Predicate('at', ['player', 'living room']),
             ])

    kb.update([Predicate('action', ['action_obj']),
               Predicate('action_obj', ['go', 'south']),
               Predicate('at', ['player', 'dining room']),
               ])

    print(kb.entails
          (Predicate('exit', ['living room', 'south'])))
    print(kb.entails
          (Predicate('exit', ['living room', 'north'])))
    print(kb.entails(
        Predicate('connects', ['living room', 'south', 'dining room'])))
    print(kb.entails(
        Predicate('exit', [FunctionNode('location', ['player']), 'south'])))
    print(kb.entails(
        Predicate('dead end', ['living room'], False)))

