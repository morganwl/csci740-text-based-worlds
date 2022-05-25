"""Tests the RoverOne agent."""

import os
import sys
import unittest

TEST_DIR = os.path.dirname(__file__)
MAIN_DIR = os.path.join(TEST_DIR, os.pardir)

sys.path.insert(0, MAIN_DIR)

from ohotnik.agents import RoverOne, RoverKnowledge


class TestRoverKnowledge(unittest.TestCase):
    """Tests RoverOne's specialized knowledge base."""
    def setUp(self):
        self.kb = RoverKnowledge()

    def test_ask_tell(self):
        """Tests to see if knowledge can be told and asked of the kb."""
        kb = self.kb
        kb.tell(('exit', 'simple room', 'north'))
        kb.tell(('exit', 'simple room', 'south'))
        kb.tell(('go', 'simple room', 'north', 'kitchen'))
        self.assertTrue(kb.ask('exit', 'simple room', 'north'))
        self.assertTrue(kb.ask('exit', 'simple room', 'south'))
        self.assertEqual(kb.ask('go', 'simple room', 'north'),
                         'kitchen')
        self.assertFalse(kb.ask('exit', 'simple room', 'west'))
        self.assertFalse(kb.ask('exit', 'kitchen', 'south'))
        self.assertIsNone(kb.ask('go', 'simple room', 'south'))
        self.assertIsNone(kb.ask('go', 'kitchen', 'south'))

    def test_path(self):
        kb = self.kb
        kb.tell(('go', 'simple room', 'north', 'kitchen'))
        kb.tell(('go', 'kitchen', 'west', 'pantry'))
        kb.tell(('go', 'pantry', 'down', 'basement'))
        self.assertEqual(kb.path('simple room', 'basement'),
                         ['north', 'west', 'down'])
        # self.assertIsNone(kb.path('simple room', 'attic'))


class TestRoverOne(unittest.TestCase):
    """Tests RoverOne agent."""
    def setUp(self):
        self.agent = RoverOne()

    def test_parse(self):
        """Parse should accept a game_state and return a list of
        observations."""
        agent = self.agent
        agent.last_command = 'look'
        game_state = {"feedback":
                      ("Simple Room\n"
                       "This is a blank room with bare, scratched wood "
                       "floors and no furniture. One doorway leads "
                       "north to the kitchen and another leads south.")}
        observations = agent.parse(game_state)
        self.assertEqual(observations,
                         [('exit', 'simple room', 'north'),
                          ('exit', 'simple room', 'south')])
