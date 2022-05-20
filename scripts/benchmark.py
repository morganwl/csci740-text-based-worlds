#!/usr/bin/env python3

"""Compare the performance of several agents on a series of benchmark
games."""

import os
import sys
import time

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
DEFAULT_MOVE_LIMIT = 100
DEFAULT_PLAY_COUNT = 10

def write_table(results, output):
    with open(output, 'w') as fh:
        fh.write(r'\begin{tabular}{l|rrr|rrr}')
        fh.write('\n')
        fh.write(r'\toprule')
        fh.write('\n')
        fh.write(r'\multirow{2}{*}{Game} & ')
        fh.write(r'\multicolumn{3}{c}{Random Agent} & ')
        fh.write(r'\multicolumn{3}{c}{Rover One}\\')
        fh.write('\n')
        fh.write(r'\cmidrule{2-7}')
        fh.write('\n')
        fh.write(r'& Score & Moves & Locations ' * 2)
        fh.write(r'\\')
        fh.write('\n')
        fh.write(r'\midrule')
        fh.write('\n')
        game = None
        for row in results:
            g, a, s, m, l = row
            if g != game:
                if game is not None:
                    fh.write(r'\\')
                    fh.write('\n')
                fh.write(g)
            fh.write(f' & {s} & {m} & {l}')
            game = g
        fh.write(r'\\ \bottomrule')
        fh.write('\n')
        fh.write(r'\end{tabular}')
        fh.write('\n')


def main(agents=DEFAULT_AGENTS, games=DEFAULT_GAMES,
         games_dir=DEFAULT_GAMES_DIR, move_limit=DEFAULT_MOVE_LIMIT,
         play_count=DEFAULT_PLAY_COUNT, output=None):
    """Runs a specified set of agents through a specified set of games
    and reports their overall performance."""
    results = []
    for i, game in enumerate(games):
        print(f'{i:2d} / {len(games)}', end='\r')
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
                                              pause=0,
                                              seed=int(time.time()))
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

    if output:
        write_table(results, output)
    # todo: track total starts, track success rates, track exploration


if __name__ == '__main__':
    output = None
    if len(sys.argv) > 1:
        output = sys.argv[1]
    main(output=output)
