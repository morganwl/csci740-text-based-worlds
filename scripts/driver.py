#!/usr/bin/env python3

"""Plays a single game using a single agent."""

import argparse
import os
from time import sleep

from textworld import start, EnvInfos
from ohotnik.agents import RoverOne
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
                        default=RoverOne)
    return vars(parser.parse_args())


def main(game, agent, move_limit=100, quiet=False, pause=.0):
    """Runs a single agent through a single game."""
    infos = EnvInfos(location=True, description=True)
    env = start(game, infos=infos)
    game_state = env.reset()
    agent = agent()
    reward, done = 0, False
    sleep(pause)
    moves = 0
    locations = set()
    while not done:
        locations.add(game_state.description)
        moves += 1
        command = agent.act(game_state, reward, done)
        if not quiet:
            # print(game_state)
            for key, item in agent.debug_info().items():
                print('', key, ':', item)
            input()
            print('>', command)
        game_state, reward, done = env.step(command)
        if not quiet:
            print(env.render())
        sleep(pause)
        if moves >= move_limit:
            done = True
    if 'score' in game_state:
        score = game_state['score']
    else:
        score = 0
    # print('Locations visited:', len(locations))
    # print(game_state)
    # input()
    return moves, score, len(locations), game_state.get('won', False)


if __name__ == '__main__':
    parsed_args = parse_args()
    main(**parsed_args)
