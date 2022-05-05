"""Generate the TextWorld games being used for benchmarking."""

import os
import sys

from driver import get_root

OHOTNIK_ROOT = get_root()
OHOTNIK_GAMES = os.path.join(OHOTNIK_ROOT, 'games')

try:
    from ohotnik.game_templates import maze
except ModuleNotFoundError:
    sys.path.insert(0, OHOTNIK_ROOT)
    from ohotnik.game_templates import maze


def main():
    maze().compile(os.path.join(OHOTNIK_GAMES, 'maze10.z8'))
    maze(20).compile(os.path.join(OHOTNIK_GAMES, 'maze20.z8'))
    maze(50).compile(os.path.join(OHOTNIK_GAMES, 'maze50.z8'))
    maze(100).compile(os.path.join(OHOTNIK_GAMES, 'maze100.z8'))
    maze(250).compile(os.path.join(OHOTNIK_GAMES, 'maze250.z8'))
    maze(500).compile(os.path.join(OHOTNIK_GAMES, 'maze500.z8'))

if __name__ == '__main__':
    main()
