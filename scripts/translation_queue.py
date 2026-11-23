"""Export untranslated line groups as JSON Lines, in source order."""
import argparse
from collections import Counter
import gzip
from hashlib import sha256
import json
import xml.etree.ElementTree as ET

from sarit import HASH, ID, SOURCE
from study import NOTES


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--book', type=int, choices=range(1, 19))
    parser.add_argument('--limit', type=int)
    parser.add_argument('--summary', action='store_true')
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error('--limit must be positive')
    with gzip.open(SOURCE, 'rb') as stream:
        raw = stream.read()
    if sha256(raw).hexdigest() != HASH:
        raise ValueError('Unexpected edition checksum')
    body = ET.fromstring(raw).find('.//{*}body')
    counts = Counter()
    seen = set()
    emitted = 0
    for book in body:
        number = int(book.get('n'))
        for group in book.iterfind('.//{*}lg'):
            locator = group.get(ID)
            if not locator or locator in seen:
                raise ValueError(f'Missing or repeated source locator: {locator}')
            seen.add(locator)
            if args.book is not None and args.book != number:
                continue
            counts['source_groups'] += 1
            if locator in NOTES:
                counts['drafted'] += 1
                continue
            counts['pending'] += 1
            if args.summary or (args.limit is not None and emitted >= args.limit):
                continue
            lines = [' '.join(''.join(line.itertext()).split()) for line in group.findall('{*}l')]
            print(json.dumps(dict(book=number, locator=locator, lines=lines), ensure_ascii=False))
            emitted += 1
    if NOTES.keys() - seen:
        raise ValueError('Study notes reference missing source groups')
    if args.summary:
        print(json.dumps({key: counts[key] for key in ('source_groups', 'drafted', 'pending')}))


if __name__ == '__main__':
    main()
