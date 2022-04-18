#!/usr/bin/env python3

"""Plays a single game using a single agent."""

import argparse
import os
from time import sleep

import textworld
from textworld.agents import NaiveAgent


def get_root():
    """Returns the root directory for finding games and agents."""
    if 'VIRTUAL_ENV' in os.environ:
        return os.path.dirname(os.environ['VIRTUAL_ENV'])
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def parse_args():
    """Parse command line arguments and return them as kwargs."""
    root_dir = get_root()
    parser = argparse.ArgumentParser()
    parser.add_argument('game', nargs='?',
                        default=os.path.join(root_dir, 'games',
                                             'zork1.z5'))
    parser.add_argument('agent', nargs='?',
                        default=NaiveAgent)
    return vars(parser.parse_args())


def main(game, agent, move_limit=100, quiet=False, pause=.5):
    """Runs a single agent through a single game."""
    env = textworld.start(game)
    game_state = env.reset()
    agent = agent()
    reward, done = 0, False
    if not quiet:
        print(game_state['raw'])
    sleep(pause)
    moves = 0
    while not done:
        moves += 1
        command = agent.act(game_state, reward, done)
        if not quiet:
            print(command)
        game_state, reward, done = env.step(command)
        if not quiet:
            print(game_state['raw'])
        sleep(pause)
        if moves >= move_limit:
            done = True
    return moves, game_state['score']


if __name__ == '__main__':
    parsed_args = parse_args()
    main(**parsed_args)
