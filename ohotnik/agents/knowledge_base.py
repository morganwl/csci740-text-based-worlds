"""Knowledge base for text-based game agents."""

from itertools import zip_longest
import os
import sqlite3

con = sqlite3.connect(':memory:')

KB_SCHEMA = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'kb_schema.sql')


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
        for prop, variables, value in model.items():
            current_value = self.ask_value(prop, variables)
            if current_value != value:
                changed.set(prop, variables, current_value)
                self.set(prop, variables, value)
        return changed

    def merge(self, model):
        """Adds values from another model to current model so long as
        they do not conflict with values in this model."""
        for prop, args in model.items():
            if self.ask_value(prop, *args[:-1]) is None:
                self.set(prop, *args)

    # Private API
    def set(self, prop, variables, value):
        """Directly sets a value in the model, bypassing any additional
        actions that might be performed by the Tell method."""
        raise NotImplementedError()


class SQL_KnowledgeBase(KnowledgeBase):
    """SQL implementation of knowledge base."""

    def __init__(self, connection=None):
        """Creates a new KnowledgeBase using a database connection. If
        no connection is provide, instantiates an SQLite database in
        memory. (This is useful for temporary models.)"""
        if connection is None:
            connection = sqlite3.connect(':memory:')
        self.connection = connection
        if self.is_blank():
            self.create_tables()

    def tell(self, observation):
        """Assigns a property to a variable in the knowledge base.
        Observations should be of the for (prop, variables, value). It
        is currently the responsibility of the parser to find the KBName
        for the appropriate variable."""
        prop, variables, value = observation
        arity = len(variables)
        cursor = self.connection.cursor()
        if not self.has_predicate(prop, cursor):
            self.add_predicate(prop, arity, cursor)
        if not self.has_properties(arity, cursor):
            self.add_properties(arity, cursor)
        self.set(prop, variables, value, cursor)
        self.connection.commit()

    def ask(self, observation):
        prop, variables, value = observation
        arity = len(variables)
        table = self.proptable(arity)
        vars_where = self.vars_where(variables, arity)
        cursor = self.connection.cursor()
        cursor.execute(
            (f"SELECT Value from {table} WHERE "
             f"Predicate = ? AND {vars_where};"),
            (prop, *variables))
        fetch = cursor.fetchone()
        if fetch is None:
            return None
        return bool(fetch[0]) == value

    def set(self, prop, variables, value, cursor=None):
        """Assigns a value to a property in the knowledge base; performs
        no error checking or additional record keeping."""
        arity = len(variables)
        table = f'Properties_{arity}'
        var_columns = ', '.join([f'Arg{i+1}' for i in range(arity)])
        var_params = ', '.join(['?'] * arity)
        if cursor is None:
            cursor = self.connection.cursor()
        prop_id = self.get_prop(prop, variables, cursor)
        if prop_id is None:
            cursor.execute(
                (f"INSERT INTO {table} " +
                 f"(Predicate, {var_columns}, Value) VALUES " +
                 f"(?, {var_params}, ?)"),
                (prop, *variables, value))
        else:
            cursor.execute(
                f"UPDATE {table} SET Predicate = ?, ?, Value = ? " +
                "WHERE Prop_ID = ?",
                f'Properties_{arity}', prop,
                ', '.join([f'Arg{i+1} = {var}'
                           for i, var in enumerate(variables)]),
                value, prop_id)

    def create_tables(self):
        """Initializes a new, blank knowledge base."""
        with open(KB_SCHEMA) as fh:
            schema = fh.read()
        self.connection.executescript(schema)

    def is_blank(self):
        """Returns True if the database is blank (i.e. no tables have
        been created yet.)"""
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table';")
        return cursor.fetchall() == []

    def has_predicate(self, predicate, cursor=None):
        """Returns True if a predicate exists in the knowledge base."""
        if cursor is None:
            cursor = self.connection.cursor()
        cursor.execute(
            "SELECT Name FROM Predicates WHERE Name=?;",
            [predicate])
        return cursor.fetchone() is not None

    def add_predicate(self, predicate, arity, cursor=None):
        """Adds a predicate to the knowledge base."""
        if cursor is None:
            cursor = self.connection.cursor()
        cursor.execute(
            "INSERT INTO Predicates values(?, ?);",
            (predicate, arity))

    def has_properties(self, arity, cursor=None):
        """Returns True if a table for the properties of the given arity
        exists."""
        if cursor is None:
            cursor = self.connection.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND " +
            "name=?", (f'Properties_{arity}',))
        return cursor.fetchone() is not None

    def add_properties(self, arity, cursor=None):
        """Adds a table for properties of a given arity."""
        arity = int(arity)
        table = f'Properties_{arity}'
        if cursor is None:
            cursor = self.connection.cursor()
        cursor.execute(
            '\n'.join([f"CREATE TABLE {table} (",
                       "Prop_ID INTEGER PRIMARY KEY AUTOINCREMENT,",
                       '\n'.join([
                           f'Arg{i+1} TEXT NOT NULL,'
                           for i in range(arity)]),
                       "Predicate TEXT NOT NULL,"
                       "Value);"]))

    def get_prop(self, prop, variables, cursor=None):
        """Returns the Prop_ID for a specific property."""
        arity = len(variables)
        table = f'Properties_{arity}'
        if cursor is None:
            cursor = self.connection.cursor()
        cursor.execute(
            f"SELECT Prop_ID from {table} WHERE Predicate = ? AND ?",
            (prop,
             ' AND '.join([f'Arg{i+1} = {var}'
                           for i, var in enumerate(variables)])))
        return cursor.fetchone()

    @staticmethod
    def proptable(arity):
        return f'Properties_{arity}'

    @staticmethod
    def vars_where(variables, arity=None):
        """Creates a 'WHERE Argi = ?' SQL statement with the appropriate
        number of arguments."""
        if arity is None:
            arity = len(variables)
        return ' AND '.join([f'Arg{i+1} = ?' for i in range(arity)])


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
    kb = SQL_KnowledgeBase()
    kb.tell(('exit', ('room1-1', 'south'), False))
    print(kb.ask(('exit', ('room1-1', 'south'), False)))

# action(open, o) and door(o) and at(P, location(door)) and
# !locked(door) implies next(!closed(door))

# action(go, o) and exit(location(P), o) and !blocked(location(P), o)
# implies next(at(P, destination(location(P), o)) and !at(P,
# location(P))
