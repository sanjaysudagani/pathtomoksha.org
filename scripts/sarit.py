"""Build local reading pages from the frozen Kumbhakonam TEI edition."""
from collections import Counter
from hashlib import sha256
from html import escape
from pathlib import Path
import gzip
import json
from study import NOTES, study_html
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
        study = study_html(locator)
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
        label = ('Ādi', 'Sabhā', 'Araṇya', 'Virāṭa', 'Udyoga', 'Bhīṣma', 'Droṇa', 'Karṇa', 'Śalya', 'Sauptika', 'Strī', 'Śānti', 'Anuśāsana', 'Āśvamedhika', 'Mausala', 'Āśramavāsika', 'Mahāprasthānika', 'Svargārohaṇa')[number-1] + ' Parva'
        sections = [i for i, child in enumerate(book) if child.tag.endswith('}div')]
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
            heading = node.find('{*}head')
            title = ' '.join(''.join(heading.itertext()).split()) if heading is not None else locator or 'Closing material'
            if title.startswith('अध्यायः '):
                title = 'Chapter ' + title.split(' ', 1)[1].lstrip('0')
            position = sections.index(seq)
            links = []
            if position:
                links.append(f'<a rel="prev" href="../section-{sections[position-1]+1}/">← Previous</a>')
            links.append('<a href="../">All chapters</a>')
            if position + 1 < len(sections):
                links.append(f'<a rel="next" href="../section-{sections[position+1]+1}/">Next →</a>')
            pager = '<nav class="pager" aria-label="Chapter navigation">' + ' '.join(links) + '</nav>'
            route = f'section-{seq+1}'
            entries.append(f'<p><a href="{route}/">{escape(title)}</a></p>')
            translated = sum(group.get(ID) in NOTES for group in node.iterfind('.//{*}lg'))
            message = (f'{translated} passages have draft English translations in this chapter.'
                       if translated else 'English translation is pending for this section. Select Sanskrit or transliteration to read the source.')
            controls = '<fieldset class="layers"><legend>Reading options</legend>' + ''.join(
                f'<label><input type="checkbox" id="show-{key}"> {name}</label>'
                for key, name in [('sa','Sanskrit'), ('iast','Roman transliteration'), ('words','Word meanings')]
            ) + '</fieldset>'
            page(f'{path}/{route}', title,
                 f'<nav><a href="../../../">Mahābhārata</a> / <a href="../">{escape(label)}</a></nav><h1>{escape(title)}</h1>{pager}{controls}<p class="muted">{message}</p><div class="reading-text">'
                 + render(node, counts) + '</div>' + pager + CREDIT)
        page(path,label,'<nav><a href="../../">Mahābhārata</a></nav><h1>'+escape(label)+'</h1>'+''.join(entries)+CREDIT)
        records.append(dict(parva=number, source_id=book.get(ID), chapter_divisions=chapters,
                            separate_closings=closing, line_groups=counts['lg']-before))
    expected = Counter(n.tag.split('}')[-1] for n in body.iter())
    assert expected == counts + Counter(body=1,div=len(books))
    page('mahabharata','Mahābhārata','<h1>Mahābhārata</h1><p>Read the eighteen parvas of the Kumbhakonam edition in source order.</p><ol class="catalog">'+''.join(books)+'</ol>'+('<a href="adi/1/">Opening invocation with English draft and glosses</a>' if study_link else '')+CREDIT)
    report = dict(edition='Kumbhakonam SARIT',sha256=HASH,raw_bytes=len(raw),
                  parvas=records, rendered_elements=counts, independent_collation=False)
    Path('docs/sarit-inventory.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
