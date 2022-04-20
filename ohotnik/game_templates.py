"""Templates for TextWorld GameMaker."""

import random

from textworld import GameMaker
from textworld.generator.maker import WorldRoomExit


DIRECTIONS = {
    'north': 'south',
    'south': 'north',
    'east': 'west',
    'west': 'east',
}


def sym_passage_available(room, other, direction):
    """Checks if an exit and its symmetrical return is available between
    two rooms."""
    return (getattr(room, direction).dest is None and
            getattr(other, DIRECTIONS[direction]).dest is None)


def is_connected(room, other):
    """Returns True if a direct passage leads between two rooms."""
    for d in DIRECTIONS:
        exit = getattr(room, d)
        if exit.dest and exit.dest.src == other:
            return True
    return False


def find_path(start, dest):
    """Given a starting and ending point, return a path as a list of
    text commands."""
    reached = set()
    frontier = [(start, [])]
    while frontier:
        room, path = frontier.pop()
        print(room, path)
        reached.add(room)
        if room == dest:
            return path
        for direction, exit in room.exits.items():
            if (exit.dest and exit.dest.src not in reached):
                child_path = path[:]
                child_path.append(direction)
                frontier.append((exit.dest.src, child_path))
    return ['help']


def maze(nb_rooms=10, min_paths=2, max_paths=4):
    """Create a small "maze", i.e. a series of interconnected rooms with
    no obstacles."""
    game = GameMaker()
    rooms = []
    print('Generating rooms.')
    for i in range(nb_rooms):
        rooms.append(game.new_room())
    paths = []
    print('Generating paths.')
    while len(paths) != 1 or len(paths[0]) != nb_rooms:
        unvisited = rooms[:]
        random.shuffle(unvisited)
        room = unvisited.pop()
        path = {room}
        while unvisited:
            next_room = unvisited.pop()
            if is_connected(room, next_room):
                continue
            directions = list(DIRECTIONS.keys())
            random.shuffle(directions)
            passage = None
            while directions:
                d = directions.pop()
                if sym_passage_available(room, next_room, d):
                    passage = game.connect(getattr(room, d),
                                           getattr(next_room,
                                                   DIRECTIONS[d]))
                    break
            if passage is not None:
                path.add(next_room)
                room = next_room
                if random.randint(0, len(unvisited)) < min_paths:
                    break
        new_paths = []
        while paths:
            p = paths.pop()
            if p.isdisjoint(path):
                new_paths.append(p)
            else:
                path = path.union(p)
        new_paths.append(path)
        paths = new_paths
    print('Placing player.')
    game.set_player(rooms[0])
    print('Generating quest.')
    # game.record_quest()
    quest = find_path(rooms[0], rooms[-1])
    print(quest)
    game.set_quest_from_commands(quest)
    return game

