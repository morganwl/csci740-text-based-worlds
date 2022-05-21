"""Receives debug messages from the AI driver and display them."""

from multiprocessing.connection import Listener


def print_predicates(predicates):
    """Pretty prints predicates."""
    print('predicates:')
    for pred, literals in predicates.items():
        print(' ', pred)
        for literal in literals:
            print(f'    {literal}: {literals[literal]}')


address = ('localhost', 6000)
listener = Listener(address, authkey=b'textbased-agent')
close = False
while not close:
    conn = listener.accept()
    msg = conn.recv()
    if msg == -1:
        close = True
    else:
        for key, val in msg.items():
            if key == 'predicates':
                print_predicates(val)
            else:
                print(key, val, sep=': ')
    conn.close()
listener.close()
