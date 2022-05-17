"""Grammatical elements of a logical sentence."""


class LogicPart:

    def eval(self, kb):
        """Evaluates a KnowledgePart within the context of a knowledge
        base."""
        raise NotImplementedError


class AndClause:

    def __init__(self, clauses, posterior=None):
        self.clauses = clauses
        self.posterior = posterior

    def eval(self, kb, posterior=None):
        if self.posterior is not None:
            posterior = self.posterior
        for clause in self.clauses:
            result = clause.eval(kb, posterior)
            if result is not True:
                return result
        return True


class Implication:
    """An implication node."""

    def __init__(self, premise, consequent):
        self.premise = premise
        self.consequent = consequent

    def eval(self, kb, posterior=None):
        """Evaluates the truth of the implication given a knowledge
        base."""
        consequent = self.consequent.eval(kb, posterior)
        if consequent:
            return True
        premise = self.premise.eval(kb, posterior)
        if premise is False:
            return True
        if consequent is None or premise is None:
            return None
        return False

    def conclusion(self):
        return self.consequent


class LinearImplication:
    """A linear implication is an implicaion where the truth of the
    premise in the prior node implies changes in the posterior node."""


class Predicate:
    """Predicate node."""

    def __init__(self, name, args, value=True, posterior=None):
        self.name = name
        self.args = args
        self.value = value
        self.posterior = posterior

    def eval(self, kb, posterior=None):
        """Evaluates the truth of the predicate given a knowledge
        base."""
        if self.posterior is not None:
            posterior = self.posterior
        for i, arg in enumerate(self.args):
            if isinstance(arg, FunctionNode):
                arg = arg.eval(kb, posterior)
                if arg is None:
                    return None
                self.args[i] = arg
        return kb.ask_literal(self.name, self.args, self.value,
                              self.posterior)


class FunctionNode:
    """Function node."""

    def __init__(self, name, args, posterior=None):
        self.name = name
        self.args = args
        self.posterior = posterior

    def eval(self, kb, posterior=None):
        if self.posterior is not None:
            posterior = self.posterior
        for i, arg in enumerate(self.args):
            if isinstance(arg, FunctionNode):
                arg = arg.eval(kb, posterior)
                if arg is None:
                    return None
                self.args[i] = arg
        return kb.ask_function(self.name, self.args, posterior)
