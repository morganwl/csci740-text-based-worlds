#!/usr/bin/env python3

"""Compare the performance of several agents on a series of benchmark
games."""

import os

from textworld.agents import NaiveAgent
import driver


def get_root():
    """Returns the root directory for finding games and agents."""
    if 'VIRTUAL_ENV' in os.environ:
        return os.path.dirname(os.environ['VIRTUAL_ENV'])
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


DEFAULT_AGENTS = (NaiveAgent,)
DEFAULT_GAMES = ('zork1.z5',)
DEFAULT_GAMES_DIR = os.path.join(get_root(), 'games')
DEFAULT_MOVE_LIMIT = 1000


def main(agents=DEFAULT_AGENTS, games=DEFAULT_GAMES,
         games_dir=DEFAULT_GAMES_DIR, move_limit=DEFAULT_MOVE_LIMIT):
    """Runs a specified set of agents through a specified set of games
    and reports their overall performance."""
    results = []
    for game in games:
        if not game.startswith('/'):
            game = os.path.join(games_dir, game)
        for agent in agents:
            moves, score = 0, 0
            while moves < move_limit:
                playthrough = driver.main(game, agent,
                                          move_limit=move_limit - moves,
                                          quiet=True,
                                          pause=0)
                moves += playthrough[0]
                score = max(score, playthrough[1])
            results.append([game, agent.__name__, score, moves])
    print(results)
    # todo: track total starts, track success rates, track exploration


if __name__ == '__main__':
    main()
