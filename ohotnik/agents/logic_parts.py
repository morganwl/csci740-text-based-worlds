"""Grammatical elements of a logical sentence."""


class LogicPart:

    def __init__(self):
        self.operator = None

    def eval(self, kb):
        """Evaluates a KnowledgePart within the context of a knowledge
        base."""
        raise NotImplementedError
    
    @property
    def name(self):
        return self.operator


class AndClause(LogicPart):

    def __init__(self, clauses, time=None):
        self.operator = '&'
        self.clauses = clauses
        self.time = time

    def eval(self, kb, time=None):
        if self.time is not None:
            time = self.time
        substitutions = [{}]
        for clause in self.clauses:
            new_subs = []
            for sub in substitutions:
                result = clause.eval(kb, time, sub)
                if result:
                    for r in result:
                        r.update(sub)
                        new_subs.append(r)
            if not new_subs:
                return False
            substitutions = new_subs
        return substitutions


class Implication(LogicPart):
    """An implication node."""

    def __init__(self, premise, consequent):
        self.operator = '->'
        self.premise = premise
        self.consequent = consequent

    def eval(self, kb, time=None):
        """Evaluates the truth of the implication given a knowledge
        base."""
        consequent = self.consequent.eval(kb, time)
        if consequent:
            return True
        premise = self.premise.eval(kb, time)
        if premise is False:
            return True
        if consequent is None or premise is None:
            return None
        return False

    def conclusion(self, kb, sub):
        return self.consequent.substitute(kb, sub=sub)

    @property
    def args(self):
        return (self.premise, self.consequent,)


class LinearImplication(LogicPart):
    """A linear implication is an implicaion where the truth of the
    premise in the prior node implies changes in the posterior node."""


class Predicate(LogicPart):
    """Predicate node."""

    def __init__(self, name, args, value=True, time=None):
        self.operator = name
        self.args = tuple(args)
        self.value = value
        self.time = time

    def substitute(self, kb, time, sub=None):
        if self.time is not None:
            time = self.time
        if sub is None:
            sub = {}
        args = []
        for arg in self.args:
            if isinstance(arg, FunctionNode):
                arg = arg.eval(kb, time, sub)
                if arg is None:
                    return None
            if arg in sub:
                arg = sub[arg]
            args.append(arg)
        return type(self)(self.name, args, self.value, time)

    def eval(self, kb, time=None, sub=None):
        """Evaluates the truth of the predicate given a knowledge
        base."""
        if self.time is not None:
            time = self.time
        if sub is None:
            sub = {}
        args = []
        for arg in self.args:
            if isinstance(arg, FunctionNode):
                arg = arg.eval(kb, time, sub)
                if arg is None:
                    return None
            if arg in sub:
                arg = sub[arg]
            args.append(arg)
        return kb.fetch(self.substitute(kb, time, sub))


class FunctionNode(LogicPart):
    """Function node."""

    def __init__(self, name, args, time=None):
        self.operator = name
        self.args = tuple(args)
        self.time = time

    def eval(self, kb, time=None, sub=None):
        if self.time is not None:
            time = self.time
        if sub is None:
            sub = {}
        args = []
        for arg in self.args:
            if isinstance(arg, FunctionNode):
                arg = arg.eval(kb, time, sub)
                if arg is None:
                    return None
            if arg in sub:
                arg = sub[arg]
            args.append(arg)
        return kb.ask_function(self.name, tuple(args), time)


class UniquenessConstraint(LogicPart):
    """Constraints the predicate so that, if one predicate is True, for
    all other constants in the specified argument, that predicate is
    False."""
    def __init__(self, predicate, argument):
        self.operator = 'unique'
        self.predicate = predicate
        self.args = args
        self.argument = 1

    def eval(self, kb, time=None):
        pass
