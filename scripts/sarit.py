"""Build local reading pages from the frozen Kumbhakonam TEI edition."""
from collections import Counter
from hashlib import sha256
from html import escape
from pathlib import Path
import gzip
import json
import re
import xml.etree.ElementTree as ET

SOURCE = Path('sources/mahabharata-devanagari.xml.gz')
HASH = '35f6808ac45c6ee7386db70afea1f79f4b83a60760904c308fcea0bff2272100'
ID = '{http://www.w3.org/XML/1998/namespace}id'
CREDIT = '''<footer><p>Southern recension, Kumbhakonam edition. Digital transcription by the Sansknet team led by Shrinivasa Varakhedi. TEI preparation by Patrick McAllister and Dominik Wujastyk. Chapter layout and automatic transliteration by Path to Moksha.</p><a href="https://github.com/sarit/SARIT-corpus/blob/master/mahabharata-devanagari.xml">SARIT source</a> · <a rel="license" href="https://creativecommons.org/licenses/by-sa/3.0/">CC BY-SA 3.0</a></footer>'''
CONSONANTS = dict(zip('कखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसहळ',
    'k kh g gh ṅ c ch j jh ñ ṭ ṭh ḍ ḍh ṇ t th d dh n p ph b bh m y r l v ś ṣ s h ḷ'.split()))
SIGNS = dict(zip('ािीुूृॄॢॣेैोौ', 'ā i ī u ū ṛ ṝ ḷ ḹ e ai o au'.split()))
OTHER = dict(zip('अआइईउऊऋॠऌॡएऐओऔंःँऽॐ।॥', 'a ā i ī u ū ṛ ṝ ḷ ḹ e ai o au ṃ ḥ m̐ ’ oṃ | ||'.split()))
OTHER.update(zip('०१२३४५६७८९', '0123456789'))

def transliterate(value):
    out = []
    pending = False
    for char in value:
        if pending and char not in SIGNS and char != '्':
            out.append('a')
        pending = char in CONSONANTS
        out.append(CONSONANTS.get(char, SIGNS.get(char, OTHER.get(char, '' if char == '्' else char))))
    return ''.join(out) + ('a' if pending else '')

def render(node, counts):
    tag = node.tag.split('}')[-1]
    counts[tag] += 1
    children = ''.join(render(child, counts) + escape(child.tail or '') for child in node)
    content = escape(node.text or '') + children
    locator = node.get(ID, '')
    anchor = f' id="{escape(locator, quote=True)}"' if locator else ''
    if tag == 'lg':
        lines = [' '.join(''.join(line.itertext()).split()) for line in node.findall('{*}l')]
        latin = '<br>'.join(escape(transliterate(line)) for line in lines)
        study = ''
        if locator == 'adi-1-1-1':
            study = ('<h2>Synonyms · draft</h2><p><i>namaskṛtya</i> — having bowed to; '
                     '<i>tataḥ</i> — then.</p><h2>Translation · draft</h2>'
                     '<p><strong>Having bowed to Nārāyaṇa, to Nara, best among men, and to the goddess Sarasvatī, '
                     'one should then recite the Jaya.</strong></p><p>The parenthetical reading “Vyāsa” awaits review.</p>')
        return f'<article class="verse"{anchor}><small>{escape(locator)}</small><div class="sanskrit" lang="sa">{content}</div><p class="iast" lang="sa-Latn"><i>{latin}</i></p>{study}</article>'
    element = {'head':'h2', 'p':'p', 'l':'div', 'div':'section','note':'small'}.get(tag,'span')
    return f'<{element}{anchor} lang="sa">{content}</{element}>'

def build_corpus(page, study_link=True):
    with gzip.open(SOURCE, 'rb') as stream:
        raw = stream.read()
    if sha256(raw).hexdigest() != HASH:
        raise ValueError('SARIT snapshot checksum mismatch')
    body = ET.fromstring(raw).find('.//{*}body')
    books, records, counts = [], [], Counter()
    for book in body:
        number = int(book.get('n'))
        path = f'mahabharata/sarit/{number}'
        label = book.get(ID)
        books.append(f'<li><a href="/{path}/">{escape(label)}</a></li>')
        entries = []
        chapters = closing = 0
        before = counts['lg']
        for seq, node in enumerate(book):
            if not node.tag.endswith('}div'):
                entries.append(render(node, counts))
                continue
            locator = node.get(ID)
            if locator:
                chapters += 1
            else:
                assert node.get('type') == 'closing'
                closing += 1
            title = locator or 'Closing material'
            route = f'section-{seq+1}'
            entries.append(f'<p><a href="{route}/">{escape(title)}</a></p>')
            page(f'{path}/{route}', title,
                 f'<nav><a href="../">{escape(label)}</a></nav><h1>{escape(title)}</h1><p>Automatic transliteration. English translation and word meanings await editorial review.</p>'
                 + render(node, counts) + CREDIT)
        page(path,label,'<nav><a href="../../">Mahābhārata</a></nav><h1>'+escape(label)+'</h1>'+''.join(entries)+CREDIT)
        records.append(dict(parva=number, source_id=label, chapter_divisions=chapters,
                            separate_closings=closing, line_groups=counts['lg']-before))
    expected = Counter(n.tag.split('}')[-1] for n in body.iter())
    assert expected == counts + Counter(body=1,div=len(books))
    page('mahabharata','Mahābhārata','<h1>Mahābhārata</h1><p>Read the eighteen parvas of the Kumbhakonam edition in source order.</p><ol>'+''.join(books)+'</ol>'+('<a href="adi/1/">Opening invocation with English draft and glosses</a>' if study_link else '')+CREDIT)
    report = dict(edition='Kumbhakonam SARIT',sha256=HASH,raw_bytes=len(raw),
                  parvas=records, rendered_elements=counts, independent_collation=False)
    Path('docs/sarit-inventory.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
