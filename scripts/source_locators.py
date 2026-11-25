"""Stable locators shared by the reading and editorial pipelines."""
from dataclasses import dataclass

XML_ID = '{http://www.w3.org/XML/1998/namespace}id'
UNIT_TAGS = frozenset(('lg', 'p', 'head', 'note'))


def unit_locator(node, book, path):
    return node.get(XML_ID) or f'tei-{book:02d}-' + '.'.join(map(str, path))


def tag(node):
    return node.tag.rsplit('}', 1)[-1]


def owned_text(node):
    """Nested notes and quoted groups have their own records; inline markup is transparent."""
    pieces = [node.text or '']
    for child in node:
        if tag(child) in UNIT_TAGS:
            pieces.append(' ')
        else:
            if tag(child) in {'l', 'lb'}:
                pieces.append('\n')
            pieces.append(owned_text(child))
        pieces.append(child.tail or '')
    return ''.join(pieces)


@dataclass
class Unit:
    locator: str
    book: int
    section: int
    tag: str
    kind: str
    source: str
    source_lines: tuple = ()


def source_units(body):
    def walk(node, path, book, section, apparatus=False, owned=False):
        name = tag(node)
        is_unit = name in UNIT_TAGS
        apparatus = apparatus or name == 'note' or node.get('rend') == 'footnotes'
        if is_unit:
            locator = unit_locator(node, book, path)
            kind = node.get('rend') or {'lg': 'verse group', 'p': 'prose', 'head': 'heading',
                                        'note': 'note'}[name]
            if apparatus:
                kind = 'edition note / ' + kind
            owned = owned_text(node)
            source = ' '.join(owned.split())
            lines = tuple(line for raw in owned.splitlines() if (line := ' '.join(raw.split())))
            yield Unit(locator, book, section, name, kind, source, lines)
        owned = owned or is_unit
        if not owned and (node.text or '').strip():
            raise ValueError(f'Unassigned text at book {book}, element {path}')
        for i, child in enumerate(node, 1):
            child_section = i if not path and tag(child) == 'div' else section
            yield from walk(child, path + (i,), book, child_section, apparatus, owned)
            if not owned and (child.tail or '').strip():
                raise ValueError(f'Unassigned text after book {book}, element {path + (i,)}')

    for book in body:
        yield from walk(book, (), int(book.get('n')), 0)
