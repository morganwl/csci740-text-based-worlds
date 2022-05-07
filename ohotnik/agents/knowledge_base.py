"""Knowledge base for text-based game agents."""

from itertools import zip_longest


class KnowledgeBase:
    """Base knowledge base class."""

    # public API
    def tell(self, observation):
        raise NotImplementedError()

    def ask_value(self, prop, *args):
        raise NotImplementedError()

    def ask_true(self, prop, *args):
        raise NotImplementedError()

    def path(self, location, destination):
        raise NotImplementedError()

    def explore(self):
        raise NotImplementedError()

    def update(self, model):
        """Updates current model with values from another model and
        returns a model with old values."""
        changed = type(self)()
        for prop, args in model.items():
            current_value = self.ask_value(prop, *args[:-1])
            if current_value != args[-1]:
                changed.set(prop, *args[:-1], current_value)
                self.set(prop, *args)
        return changed
             
    def merge(self, model):
        """Adds values from another model to current model so long as
        they do not conflict with values in this model."""
        for prop, args in model.items():
            if self.ask_value(prop, *args[:-1]) is None:
                self.set(prop, *args)

    # Private API
    def set(self, prop, *args):
        """Directly sets a value in the model, bypassing any additional
        actions that might be performed by the Tell method."""
        raise NotImplementedError()


class Variable:
    """Object in the knowledge base."""
    def __init__(self, name, properties=None):
        self.name = name
        if properties is None:
            properties = {}
        self.properties = properties

    def tell(self, prop):
        parent = self.properties
        for i in range(len(prop) - 2):
            if prop[i] not in parent:
                parent[prop[i]] = {}
            parent = parent[prop[i]]
        key, value = prop[-2:]
        parent[key] = value

    def ask_value(self, prop):
        parent = self.properties
        for i in range(len(prop) - 1):
            if prop[i] not in parent:
                return None
            parent = parent[prop[i]]
        return parent.get(prop[-1], None)

    def ask_true(self, prop):
        parent = self.properties
        for i in range(len(prop) - 2):
            if prop[i] not in parent:
                return False
            parent = parent[prop[i]]
        return parent.get(prop[-2], None) == prop[-1]


class Rule:
    """Rule for actions."""
    def __init__(self, objects, outcomes, conditions=None): 
        self.objects = objects
        self.outcomes = outcomes
        # conditions are organized into (object, object ..., general)
        if conditions is None:
            conditions = []
        self.conditions = conditions

    def valid(self, objects, model):
        for obj, conditions in zip_longest(objects, self.conditions):
            for prop, args in conditions:
                if obj is None:
                    if not model.ask_true((prop,) + args):
                        return False
                elif not model.ask_true((prop, obj) + args):
                    return False
        return True

    def perform(self, objects, model):
        if not self.valid(objects, model):
            return None
        delta = type(model)()
        for obj, outcomes in zip_longest(objects, self.outcomes):
            for prop, args in outcomes:
                if obj is None:
                    delta.tell((prop,) + args)
                else:
                    delta.tell((prop, obj) + args)
        return delta


if __name__ == '__main__':
    player = Variable('Player')
    room1 = Variable('Room 1')
    room2 = Variable('Room 2')
    room1.tell(('exit', 'north', True))
    room1.tell(('connects', room1, 'north', room2))
    player.tell(('at', room1))
    print(room1.ask_value(('exit', 'north')))
# action(open, o) and door(o) and at(P, location(door)) and
# !locked(door) implies next(!closed(door))

# action(go, o) and exit(location(P), o) and !blocked(location(P), o)
# implies next(at(P, destination(location(P), o)) and !at(P,
# location(P))
