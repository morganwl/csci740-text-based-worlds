#!/usr/bin/env python3

"""Creates a BibTeX document from a Zotero library."""

import os

from pyzotero import zotero
import bibtexparser

COLLECTION_KEY = 'S2FDBR52'


def read_secret(filename=os.path.expanduser(
        '~/.config/sync-bibtex/sync-bibtex_secret.txt')):
    """Returns the API key and user_id from the secrets file."""
    key, user_id = '', ''
    with open(filename) as fh:
        for line in fh:
            if line.startswith('KEY='):
                key = line[len('KEY='):].strip()
            elif line.startswith('USER_ID='):
                user_id = line[len('USER_ID='):].strip()
    return key, user_id


def get_bibtex(zot, collection_key):
    """Returns a collection's items as a BibTeX string."""
    items = zot.collection_items(collection_key, format='bibtex')
    return bibtexparser.dumps(items)


def main():
    """Main function."""
    key, user_id = read_secret()
    zot = zotero.Zotero(user_id, 'user', key)
    print(get_bibtex(zot, COLLECTION_KEY))


if __name__ == '__main__':
    main()
