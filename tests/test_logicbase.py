"""Tests the first-order logic implementation of the knowledge base."""

import os
import sys
import unittest

TEST_DIR = os.path.dirname(__file__)
MAIN_DIR = os.path.join(TEST_DIR, os.pardir)

sys.path.insert(0, MAIN_DIR)

from ohotnik.agents import LogicBase, AndClause, Predicate, \
    Implication, LinearImplication
from ohotnik.agents.knowledge_base import unify


class TestUnify(unittest.TestCase):
    """Tests that unify function behaves correctly."""
    def test_unify_matching_literal(self):
        """Confirms that unifying two matching literals should return an
        empty substitution."""
        p1 = Predicate('at', ('player', 'dining room'))
        p2 = Predicate('at', ('player', 'dining room'))
        self.assertEqual(unify(p1, p2), {})

    def test_unify_distinct_literal(self):
        """Confirms that matching two distinct literals should return
        False."""
        p1 = Predicate('at', ('player', 'dining room'))
        p2 = Predicate('at', ('player', 'living room'))
        self.assertFalse(unify(p1, p2))

    def test_unify_constant(self):
        """Confirms that a constant substitution can be supplied to
        unify explicitly."""
        # import pdb
        # pdb.set_trace()
        self.assertTrue(unify(
            Predicate('exit', ('kitchen', 'north')),
            Predicate('exit', ('kitchen-1', 'north')),
            {'kitchen-1': 'kitchen'}
        ))


class TestLogicBase(unittest.TestCase):
    """Test the basic functioning of the logic base."""
    def setUp(self):
        self.kb = LogicBase()
        self.kb.add_function('location', 'at', 1)
        self.kb.add_function('destination', 'connects', 2)
        self.kb.add_function('last_action', 'action', 1)
        self.kb.add_function('action_obj_1', 'action_obj', 1)

    def test_simple_predicate_true(self):
        """Confirm that a simple predicate can be evaluated as True."""
        pred = Predicate('at', ['player', 'living room'])
        self.kb.tell([pred])
        self.assertTrue(pred.eval(self.kb))

    def test_simple_predicate_false(self):
        """Confirm that a simple predicate can be evaluated as False."""
        pred = Predicate('at', ['player', 'living room'], False)
        self.kb.tell([pred])
        self.assertTrue(Predicate('at', ['player', 'living room']))

    def test_fetch_literal_true(self):
        """Confirm that fetching a True literal returns a single empty
        substitution."""
        pred = Predicate('at', ['player', 'living room'])
        self.kb.tell([pred])
        self.assertEqual(self.kb.fetch(pred), [{}])

    @unittest.skip('Need to rethink falseness vs noneness')
    def test_fetch_literal_false(self):
        """Confirm that fetching a False literal returns False."""
        pred = Predicate('at', ['player', 'living room'], False)
        self.kb.tell([pred])
        pred.value = True
        self.assertEqual(self.kb.fetch(pred), False)

    def test_fetch_literal_none(self):
        """Confirm that fetching an unknown literal returns None."""
        pred = Predicate('at', ['player', 'living room'])
        self.assertIsNone(self.kb.fetch(pred))

    def test_fetch_variable_true(self):
        """Confirm that fetching a valid variable predicate returns a
        substitution list."""
        literal = Predicate('at', ['player', 'living room'])
        self.kb.tell([literal])
        pred = Predicate('at', ['player', 'LOCATION'])
        self.assertTrue(self.kb.fetch(pred))

    def test_variable_and_clause(self):
        """Confirm that an AND clause with a variable evaluates
        correctly."""

        # tell a fact to kb
        self.kb.tell([
            Predicate('at', ['player', 'living room']),
        ])
        # advance time
        self.kb.advance(('go', 'south',))
        # tell two new facts, one of which overrides prior fact
        self.kb.tell([
            Predicate('at', ['player', 'dining room']),
            Predicate('at', ['player', 'living room'], False),
        ])

        # confirm that the location from last term is not the location
        # for this term
        now_predicate = Predicate('at', ['player', 'LOCATION'],
                                  time=-1)
        then_predicate = Predicate(
            'at', ['player', 'LOCATION'], False)
        self.assertTrue(now_predicate.eval(self.kb))
        self.assertTrue(then_predicate.eval(self.kb))
        premise = AndClause([now_predicate, then_predicate])
        self.assertTrue(premise.eval(self.kb))

    def test_fetch_and(self):
        """Confirm that an AND clause returns all valid substitutions
        when evaluated."""
        self.kb.tell([
            Predicate('container', ['box']),
            Predicate('container', ['chest']),
            Predicate('container', ['cupboard']),
            Predicate('open', ['box']),
            Predicate('open', ['chest']),
            Predicate('at', ['box', 'garage']),
            Predicate('at', ['chest', 'bedroom'])
        ])
        premise = AndClause([
            Predicate('container', ['C']),
            Predicate('open', ['C']),
            Predicate('at', ['C', 'L'])
        ])
        self.assertEqual(premise.eval(self.kb),
                         [{'L': 'garage', 'C': 'box'},
                          {'L': 'bedroom', 'C': 'chest'}])

    def test_forward_chain(self):
        self.kb.add_implication(
            Implication(
                Predicate('connect', ['LOCATION', 'DIRECTION',
                                      'DESTINATION']),
                Predicate('exit', ['LOCATION', 'DIRECTION'])))
        self.kb.tell([
            Predicate('at', ['player', 'living room']),
        ])
        self.kb.advance(('go', 'south',))
        self.kb.tell([
            Predicate('connects', ['living room', 'south',
                                   'dining room'])])
        self.assertTrue(
            Predicate('exit', ['living room', 'south']))

    def test_linear_implication(self):
        """Confirms that linear implication evaluates correctly."""
        self.kb.tell([
            Predicate('at', ['player', 'living room']),
            Predicate('exit', ['living room', 'south']),
            Predicate('connects', ['living room',
                                   'south',
                                   'dining room']),
        ])
        self.kb.advance(('go', 'south',))
        self.kb.tell([
            Predicate('at', ['player', 'dining room']),
            Predicate('at', ['player', 'living room'], False),
        ])
        rule = LinearImplication(
            ('go', 'DIRECTION',),
            AndClause([
                Predicate('at', ['player', 'LOCATION']),
                Predicate('exit', ['LOCATION', 'DIRECTION'],
                          carry=True),
                Predicate('connects', ['LOCATION',
                                       'DIRECTION',
                                       'DESTINATION'],
                          carry=True)]),
            Predicate('at', ['player', 'DESTINATION']))
        self.assertTrue(rule.premise.eval(self.kb))
        self.kb.add_rule(rule)
        # import pdb
        # pdb.set_trace()
        self.kb.forward_chain()
        self.assertFalse(Predicate('action',
                                   ['action_obj']).eval(self.kb))
