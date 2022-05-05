#!/usr/bin/env python3

"""Compare the performance of several agents on a series of benchmark
games."""

import os
import sys

from textworld.agents import NaiveAgent
import driver
from driver import get_root

OHOTNIK_ROOT = get_root()
OHOTNIK_GAMES = os.path.join(OHOTNIK_ROOT, 'games')

try:
    from ohotnik.agents import RoverOne
except ModuleNotFoundError:
    sys.path.insert(0, OHOTNIK_ROOT)
    from ohotnik.agents import RoverOne

DEFAULT_AGENTS = (NaiveAgent, RoverOne)
DEFAULT_GAMES_DIR = os.path.join(get_root(), 'games')
DEFAULT_GAMES = [game for game in os.listdir(DEFAULT_GAMES_DIR)
                 if os.path.splitext(game)[1] in ['.z5', '.z8']]
DEFAULT_MOVE_LIMIT = 1000
DEFAULT_PLAY_COUNT = 1


def main(agents=DEFAULT_AGENTS, games=DEFAULT_GAMES,
         games_dir=DEFAULT_GAMES_DIR, move_limit=DEFAULT_MOVE_LIMIT,
         play_count=DEFAULT_PLAY_COUNT):
    """Runs a specified set of agents through a specified set of games
    and reports their overall performance."""
    results = []
    for game in games:
        if not game.startswith('/'):
            game_path = os.path.join(games_dir, game)
        else:
            game_path = game
        for agent in agents:
            sum_score = 0
            sum_moves = 0
            sum_locations = 0
            for i in range(play_count):
                moves, score, won = 0, 0, False
                while moves < move_limit and not won:
                    playthrough = driver.main(game_path, agent,
                                              move_limit=move_limit - moves,
                                              quiet=True,
                                              pause=0)
                    moves += playthrough[0]
                    score = max(score, playthrough[1])
                    locations = playthrough[2]
                    won = playthrough[3]
                sum_score += score
                sum_moves += moves
                sum_locations += locations
            score = sum_score / play_count
            moves = sum_moves / play_count
            locations = sum_locations / play_count
            results.append([game, agent.__name__,
                            int(score), int(moves),
                            int(locations)])
    for result in results:
        print(result)
    # todo: track total starts, track success rates, track exploration


if __name__ == '__main__':
    main()
