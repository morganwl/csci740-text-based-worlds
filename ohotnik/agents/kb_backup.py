"""Knowledge base for text-based game agents."""

from collections import namedtuple
from itertools import zip_longest
import os
import sqlite3

from ohotnik.agents.logic import RoverLogicParser

con = sqlite3.connect(':memory:')

KB_SCHEMA = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'kb_schema.sql')

Function = namedtuple('Function', ['predicate', 'arity', 'argument'])


class KnowledgeBase:
    """Base knowledge base class."""

    # public API
    def tell(self, observation):
        """Report observations to the knowledge base."""
        raise NotImplementedError()

    def ask_value(self, prop, *args):
        """Ask the knowledge base for the value of a particular
        sentence."""
        raise NotImplementedError()

    def ask_true(self, prop, *args):
        """Ask the knowledge base if a sentence is True."""
        raise NotImplementedError()

    def path(self, location, destination):
        """Returns the sequence of actions leading from the current
        location to the desired location, if one exists."""
        raise NotImplementedError()

    def explore(self):
        """Returns an action likely to yield information useful to the
        knowledge base."""
        raise NotImplementedError()

    def update(self, model):
        """Updates current model with values from another model and
        returns a model with old values."""
        changed = type(self)()
        for prop, variables, value in model.items():
            current_value = self.ask_value(prop, variables)
            if current_value != value:
                changed.store(prop, variables, current_value)
                self.store(prop, variables, value)
        return changed

    def merge(self, model):
        """Adds values from another model to current model so long as
        they do not conflict with values in this model."""
        for prop, args in model.items():
            if self.ask_value(prop, *args[:-1]) is None:
                self.store(prop, *args)

    # Private API
    def store(self, prop, variables, value):
        """Directly store a value in the model, bypassing any additional
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
        else:
            self.load_functions()

    def tell(self, observation):
        """Assigns a property to a variable in the knowledge base.
        Observations should be of the for (prop, variables, value).
        Variable names should correspond to ParserNames, but are
        expected to refer to be unique with regards to all objects
        within a certain Tell statement."""
        prop, variables, value = observation
        arity = len(variables)
        cursor = self.connection.cursor()
        variables = self.add_variables(variables, cursor)
        if not self.has_predicate(prop, cursor):
            self.add_predicate(prop, arity, cursor)
        if not self.has_properties(arity, cursor):
            self.add_properties(arity, cursor)
        self.store(prop, variables, value, cursor)
        self.connection.commit()

    def entails(self, sentence, cursor=None):
        parser = RoverLogicParser()
        return self.entails_tree(parser.parse(sentence))

    def load_functions(self):
        """Loads all functions from the database into memory for easy
        access."""
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT Name, Predicate, Arity, Argument FROM Functions ")
        self.functions = {}
        for row in cursor.fetchall():
            self.functions[row[0]] = Function(row[1:])



    def eval_op(self, tree, cursor=None):
        if isinstance(tree, (bool, type(None))):
            return tree
        if cursor is None:
            cursor = self.connection.cursor()
        operator = tree[0]
        if operator in ('&', '|', '!'):
            return self.eval_bool(operator, tree[1], cursor)
        if tree[0] in ('->', ':'):
            return self.eval_implication(operator, tree[1], cursor)
        return self.eval_predicate(operator, tree[1], cursor)

    def entails_tree(self, sentence, cursor=None):
        """Given a sentence as a prefix syntax tree, returns True if
        that sentence is entailed by the KB, False if that sentence is
        not entailed, or None if insufficient information is contained
        in the KB."""
        print(sentence)
        if isinstance(sentence, (bool, type(None))):
            return sentence
        if cursor is None:
            cursor = self.connection.cursor()
        if sentence[0] in ('&', '|', '!'):
            return self.entails_bool(sentence, cursor)
        return self.fetch(sentence, cursor)

    def eval_bool(self, operator, sentence, cursor=None):
        """Given a sentence known to have a boolean operator, return
        True if that sentence is entailed, False if that sentence is not
        entailed, and None if there is not enough information."""
        if cursor is None:
            cursor = self.connection.cursor()
        for term in sentence:
            term = self.entails_tree(term, cursor)
            # if isinstance(term, str):
            #     raise Exception('Poorly formed sentence.')
            if operator == '&' and not term:
                return False
            if operator == '|' and term:
                return True
            if operator == '!':
                return not term
        return operator == '&'

    # def eval_predicate(self, operator, sentence, cursor):
    #     """Given a sentence that is known to be either a Predicate or
    #     Function query, return the value of that Predicate or
    #     Function."""
    #     if isinstance(sentence, str):
    #         return sentence
    #     if cursor is None:
    #         cursor = self.connection.cursor()
    #     operator = sentence[0]
    #     cursor.execute(
    #         "SELECT Name FROM Functions WHERE Name = ?",
    #         (operator,))
    #     if cursor.fetchone() is not None:
    #         return self.fetch_function(sentence, cursor)
    #     return self.fetch_predicate(sentence, cursor)

    def fetch_predicate(self, predicate, cursor=None):
        """Queries the knowledge base for a predicate and returns its
        attributes or None if it does not exist."""
        if cursor is None:
            cursor = self.connection.cursor()
        return cursor.execute(
            ("SELECT Arity, Implicit FROM Predicates "
             "WHERE Name = ?"),
            (predicate,)).fetchone()

    def fetch_property(self, predicate, params, arity, implicit,
                       cursor=None):
        """Queries the knowledge base for a property (predicate applied
        to ground terms) and returns truth of that property or None if
        it is not known."""
        result = cursor.execute(
            (f"SELECT Value FROM Properties_{arity} WHERE "
             "Predicate = ? AND " + 
             ' AND '.join([f'Arg{i} = ?' for i in range(arity)])),
            params).fetchone()
        if result is None:
            if implicit:
                return False
            return None
        return bool(result[0])

    # def fetch(self, query


    def eval_predicate(self, predicate, sentence, cursor=None):
        if cursor is None:
            cursor = self.connection.cursor()

        # Return None if Predicate does not exist
        attributes = self.fetch_predicate(predicate)
        if attributes is None:
            return None
        arity, implicit = attributes

        # Check arity
        if arity != len(sentence):
            msg = (f'Predicate {predicate} expected {arity} arguments '
                   f'but got {len(sentence)}')
            raise Exception(msg)

        params = [predicate]
        for term in sentence[1:]:
            term = self.eval_term(term, cursor)
            if term is None and not implicit:
                return None
            params.append(term)

        result = cursor.execute(
            (f"SELECT Value FROM Properties_{arity} WHERE "
             "Predicate = ? AND " + 
             ' AND '.join([f'Arg{i} = ?' for i in range(arity)])),
            params).fetchone()
        if result is None:
            if implicit:
                return False
            return None
        return bool(result[0])

    def fetch_function(self, sentence, cursor):
        if cursor is None:
            cursor = self.connection.cursor()
        function = sentence[0]
        result = cursor.execute(
            ("SELECT Predicate, Argument, Arity FROM Functions "
             "INNER JOIN PREDICATES ON "
             "Functions.Predicate = Predicates.Name "
             "AND Functions.Name = ?"),
            (function,)).fetchone()
        if result is None:
            return None
        predicate, argument, arity = result

        params = [predicate]
        for term in sentence[1:]:
            term = self.fetch(term, cursor)
            if term is None:
                return None
            params.append(term)

        result = cursor.execute(
            (f"SELECT Arg{argument} FROM Properties_{arity} WHERE "
             "Predicate = ? AND " +
             " AND ".join([f'Arg{i} = ?' for i in range(arity)
                           if i != argument])),
            params).fetchone()
        if result is None:
            return None
        return result[0]

    def ask(self, query):
        """Queries the knowledge base for a predicate with explicit
        variables. Returns True if the value of the predicate matches the
        provided value. Returns None if the answer is not contained in
        the knowledge base."""
        prop, variables, value = query
        arity = len(variables)
        table = self.proptable(arity)
        vars_where = self.vars_where(arity)
        cursor = self.connection.cursor()
        cursor.execute(
            (f"SELECT Value from {table} WHERE "
             f"Predicate = ? AND {vars_where};"),
            (prop, *variables))
        fetch = cursor.fetchone()
        if fetch is None:
            return None
        return bool(fetch[0]) == value

    def ask_vars(self, query):
        """Returns a list of all vars for which the query is True."""

    def store(self, prop, variables, value, cursor=None):
        """Assigns a value to a property in the knowledge base; performs
        no error checking or additional record keeping."""
        arity = len(variables)
        table = f'Properties_{arity}'
        var_columns = ', '.join([f'Arg{i}' for i in range(arity)])
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
                ', '.join([f'Arg{i} = {var}'
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

    def expand_function(self, function, variables, cursor=None):
        """Returns the KB_Name of the variable referenced by a
        function."""
        if cursor is None:
            cursor = self.connection.cursor()
        sql_select_on(cursor, ('Predicate', 'Argument', 'Arity'),
                      ('Functions', 'Predicate'), ('Predicates', 'Name'),
                      where=(('Functions.Name',), (function,)))
        # cursor.execute(
        #     ("SELECT (Predicate, Argument, Arity) FROM Functions "
        #      "WHERE Name = ?;"),
        #     (function,))
        (predicate, argument, arity) = cursor.fetchone()
        sql_select_on(cursor, 'KBName', ('Variables', 'KBName'),
                      (f'Properties_{arity}', f'Arg{argument}'),
                      where=(('Predicate',), (predicate,)),
                      variables=variables, exclude=argument)
        result = cursor.fetchone()
        if result:
            return result[0]
        return None

    def add_variables(self, variables, cursor=None):
        """Adds variables based on parser names and returns the
        KBName."""
        # TO-DO: Create a new KBName
        if cursor is None:
            cursor = self.connection.cursor()
        kb_names = []
        for var in variables:
            name = cursor.execute(
                "SELECT KBName FROM Variables WHERE ParserName = ?",
                (var,)).fetchone()
            if name is not None:
                name = name[0]
            else:
                name = var
                cursor.execute(
                    "INSERT INTO Variables VALUES (?, ?)",
                    (name, var))
            kb_names.append(name)
        return kb_names

    def has_predicate(self, predicate, cursor=None):
        """Returns True if a predicate exists in the knowledge base."""
        if cursor is None:
            cursor = self.connection.cursor()
        cursor.execute(
            "SELECT Name FROM Predicates WHERE Name=?;",
            (predicate,))
        return cursor.fetchone() is not None

    def add_predicate(self, predicate, arity, cursor=None):
        """Adds a predicate to the knowledge base."""
        if cursor is None:
            cursor = self.connection.cursor()
        cursor.execute(
            "INSERT INTO Predicates values(?, ?, FALSE);",
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
                           f'Arg{i} TEXT NOT NULL,'
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
             ' AND '.join([f'Arg{i} = {var}'
                           for i, var in enumerate(variables)])))
        return cursor.fetchone()

    def add_function(self, name, predicate, argument, cursor=None):
        """Adds a new function to the knowledge base."""
        if cursor is None:
            cursor = self.connection.cursor()
        cursor.execute(
            "INSERT INTO Functions VALUES (?, ?, ?)",
            (name, predicate, argument))

    @staticmethod
    def proptable(arity):
        return f'Properties_{arity}'

    @staticmethod
    def vars_where(arity, exclude=None):
        """Creates a 'WHERE Argi = ?' SQL statement with the appropriate
        number of arguments."""
        return ' AND '.join([f'Arg{i} = ?' for i in range(arity)
                             if i != exclude])


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


def sql_select():
    """Performs an SQL select command."""


def sql_select_on(cursor, columns, left, right,
                  variables=None, exclude=None, where=None):
    """Performs an SQL select command on an inner join."""
    if not isinstance(columns, str):
        columns = ', '.join(columns)
    left_tab, left_col = left
    right_tab, right_col = right
    sql = [(f"SELECT {columns} FROM {left_tab} "
            f"INNER JOIN {right_tab} "
            f"ON {left_tab}.{left_col} = {right_tab}.{right_col} ")]
    params = []
    if variables:
        arity = len(variables)
        if exclude:
            arity += 1
        sql.append(vars_where(arity, exclude))
        params.extend(variables)
    if where:
        sql.extend([f'{variable} = ?' for variable in where[0]])
        params.extend(where[1])
    cursor.execute(' AND '.join(sql), params)


def vars_where(arity, exclude=None):
    """Creates a 'WHERE Argi = ?' SQL statement with the appropriate
    number of arguments."""
    return ' AND '.join([f'Arg{i} = ?' for i in range(arity)
                         if i != exclude])


# At any point, the KB keeps two models: the model of the state before
# an action is taken, and the model of the state after an action is
# taken. For a linear implication operator, all terms on the left side
# of the operator are assumed to reference the prior model, and all
# terms to the right side of the operator are assumed to reference the
# posterior model.
#
# For a traditional implication, it is often useful to reference models
# explicitly. In this case, the '-' operator refers to the prior
# model and the '+' operator refers to the posterior model. When no
# model is specified, all the model is selected by context.
rules = [
    '+action_obj(go, D), $exit(location(p), D) : at(p, destination(D))',
    '+action_obj(go, D), !(=, at(p), +at(p)) > connections(at(p), D, +at(p))'
]


if __name__ == '__main__':
    kb = SQL_KnowledgeBase()
    kb.add_function('location', 'at', 1)
    kb.add_function('destination', 'connects', 2)
    kb.add_function('last_action', 'action', 1)
    kb.add_function('action_obj_1', 'action_obj', 1)

    kb.tell(('exit', ('room1-1', 'south'), True))
    kb.tell(('connects', ('room1-1', 'south', 'room2-1'), True))
    kb.tell(('at', ('~', 'room1-1'), True))
    kb.tell(('action', ('action_obj'), True))
    kb.tell(('action_obj', ('go', 'south'), True))

    # print(kb.ask(('exit', ('room1-1', 'south'), False)))
    # print(kb.ask(('exit', ('room2-1', 'south'), True)))
    # print(kb.ask(('connects', ('room1-1', 'south', 'room2-1'), True)))
    # print(kb.expand_function('destination', ('room1-1', 'south')))
    print(kb.entails('exit(room1-1, south)'))
    print(kb.entails('connects(room1-1, south, destination(room1-1, south))'))
    print(kb.entails('action_obj(go, south)'))
    print(kb.entails('(action_obj(go, action_obj_1(go)) & exit(location(p), action_obj_1(go)))'))


# action(open, o) and door(o) and at(P, location(door)) and
# !locked(door) implies next(!closed(door))

# action(go, o) and exit(location(P), o) and !blocked(location(P), o)
# implies next(at(P, destination(location(P), o)) and !at(P,
# location(P))
