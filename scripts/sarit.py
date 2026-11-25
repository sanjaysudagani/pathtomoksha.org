"""Build local reading pages from the frozen Kumbhakonam TEI edition."""
from collections import Counter
from hashlib import sha256
from html import escape
from pathlib import Path
import gzip
import json
from study import NOTES, study_html
import xml.etree.ElementTree as ET
from library_pages import gita_page, home, source_page
from source_locators import UNIT_TAGS, XML_ID as ID, unit_locator

SOURCE = Path('sources/mahabharata-devanagari.xml.gz')
HASH = '35f6808ac45c6ee7386db70afea1f79f4b83a60760904c308fcea0bff2272100'
PARVAS = ('Ādi', 'Sabhā', 'Araṇya', 'Virāṭa', 'Udyoga', 'Bhīṣma', 'Droṇa', 'Karṇa', 'Śalya',
          'Sauptika', 'Strī', 'Śānti', 'Anuśāsana', 'Āśvamedhika', 'Mausala', 'Āśramavāsika',
          'Mahāprasthānika', 'Svargārohaṇa')
CREDIT = '''<footer><p>Southern recension, Kumbhakonam edition. Digital transcription by the Sansknet team led by Shrinivasa Varakhedi. TEI preparation by Patrick McAllister and Dominik Wujastyk. Chapter layout and automatic transliteration by Path to Moksha.</p><a href="https://github.com/sarit/SARIT-corpus/blob/master/mahabharata-devanagari.xml">SARIT source</a> · <a rel="license" href="https://creativecommons.org/licenses/by-sa/3.0/">CC BY-SA 3.0</a></footer>'''
CONSONANTS = dict(zip('कखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसहळ',
    'k kh g gh ṅ c ch j jh ñ ṭ ṭh ḍ ḍh ṇ t th d dh n p ph b bh m y r l v ś ṣ s h ḷ'.split()))
SIGNS = dict(zip('ािीुूृॄॢॣेैोौ', 'ā i ī u ū ṛ ṝ ḷ ḹ e ai o au'.split()))
OTHER = dict(zip('अआइईउऊऋॠऌॡएऐओऔंःँऽॐ।॥', 'a ā i ī u ū ṛ ṝ ḷ ḹ e ai o au ṃ ḥ m̐ ’ oṃ | ||'.split()))
OTHER.update(zip('०१२३४५६७८९', '0123456789'))
CONSONANTS['ऱ'] = 'ṟ'

def transliterate(value):
    out = []
    pending = False
    for char in value:
        if char == '़':
            out.append('\u0323')
            continue
        if pending and char not in SIGNS and char != '्':
            out.append('a')
        pending = char in CONSONANTS
        out.append(CONSONANTS.get(char, SIGNS.get(char, OTHER.get(char, '' if char == '्' else char))))
    return ''.join(out) + ('a' if pending else '')

def render(node, counts, book, path):
    tag = node.tag.split('}')[-1]
    counts[tag] += 1
    if tag == 'lb':
        if node.attrib or len(node) or node.text:
            raise ValueError('Unexpected content in a TEI line break')
        return '<br>'
    children = ''.join(render(child, counts, book, path + (i,)) + escape(child.tail or '')
                       for i, child in enumerate(node, 1))
    content = escape(node.text or '') + children
    locator = unit_locator(node, book, path) if tag in UNIT_TAGS else node.get(ID, '')
    anchor = f' id="{escape(locator, quote=True)}"' if locator else ''
    unit = f' data-source-unit="{tag}"' if tag in UNIT_TAGS else ''
    if tag == 'lg':
        lines = [' '.join(''.join(line.itertext()).split()) for line in node.findall('{*}l')]
        latin = '<br>'.join(escape(transliterate(line)) for line in lines)
        study = study_html(locator)
        reference = f'<a href="#{escape(locator, quote=True)}">{escape(locator)}</a>' if locator else ""
        return f'<article class="verse"{anchor}{unit}><small>{reference}</small><div class="sanskrit" lang="sa">{content}</div><p class="iast" lang="sa-Latn"><i>{latin}</i></p>{study}</article>'
    element = {'head':'h2', 'p':'p', 'l':'div', 'div':'section','note':'aside'}.get(tag,'span')
    if tag == 'p' and any(child.tag.endswith('}note') for child in node):
        element = 'div'
        unit += ' class="source-prose"'
    return f'<{element}{anchor}{unit} lang="sa">{content}</{element}>'

def build_corpus(page, study_link=True):
    with gzip.open(SOURCE, 'rb') as stream:
        raw = stream.read()
    if sha256(raw).hexdigest() != HASH:
        raise ValueError('SARIT snapshot checksum mismatch')
    body = ET.fromstring(raw).find('.//{*}body')
    books, records, counts = [], [], Counter()
    gita_chapters = []
    for book in body:
        number = int(book.get('n'))
        path = f'mahabharata/sarit/{number}'
        label = PARVAS[number - 1] + ' Parva'
        sections = [i for i, child in enumerate(book) if child.tag.endswith('}div')]
        assert number == len(records) + 1
        entries = []
        chapters = closing = 0
        before = counts['lg']
        for seq, node in enumerate(book):
            if not node.tag.endswith('}div'):
                entries.append(f'<li class="chapter-frontmatter">{render(node, counts, number, (seq+1,))}</li>')
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
            entries.append(f'<li><a href="{route}/"><span>{escape(title)}</span><span aria-hidden="true">→</span></a></li>')
            if number == 6:
                topics = [' '.join(''.join(p.itertext()).split()) for p in node.findall('{*}p') if p.get('rend') == 'topic']
                for topic in topics:
                    # The pinned source spells chapter 11's heading without the ध.
                    marker = next((item for item in ('भगवद्गीताध्यायः ॥ ', 'भगवद्गीताद्यायः ॥ ') if item in topic), None)
                    if marker:
                        gita_number = int(topic.split(marker, 1)[1].split()[0])
                        if gita_number == 1:
                            assert 'धर्मक्षेत्रे कुरुक्षेत्रे' in ''.join(node.itertext())
                        gita_chapters.append((gita_number, f'/{path}/{route}/'))
                        break
            translated = sum(group.get(ID) in NOTES for group in node.iterfind('.//{*}lg'))
            message = (f'{translated} passages have draft English translations in this chapter.'
                       if translated else 'English translation is pending for this section. Sanskrit is shown by default.')
            options = [('sa', 'Sanskrit'), ('iast', 'Roman transliteration')]
            if translated:
                options.append(('words', 'Word meanings'))
            controls = '<fieldset class="layers"><legend>Reading options</legend>' + ''.join(
                f'<label><input type="checkbox" id="show-{key}"'
                + (' checked' if key == 'sa' and not translated else '')
                + f'> <span>{name}</span></label>' for key, name in options
            ) + '</fieldset>'
            page(f'{path}/{route}', f'{label}: {title}',
                 f'<div class="chapter-reader"><nav class="crumbs" aria-label="Breadcrumb"><a href="/#library">Library</a>'
                 f'<span aria-hidden="true">/</span><a href="../../../">Mahābhārata</a><span aria-hidden="true">/</span><a href="../">{escape(label)}</a></nav>'
                 f'<div class="reader-title"><p class="eyebrow">{escape(label)} · Kumbhakonam edition</p><h1>{escape(title)}</h1></div>'
                 f'{pager}{controls}<p class="reader-note">{message}</p><div class="reading-text">'
                 + render(node, counts, number, (seq+1,)) + '</div>' + pager + CREDIT + '</div>')
        intro = (f'<nav class="crumbs" aria-label="Breadcrumb"><a href="/#library">Library</a><span aria-hidden="true">/</span>'
                 f'<a href="../../">Mahābhārata</a><span aria-hidden="true">/</span><span aria-current="page">{escape(label)}</span></nav>'
                 f'<div class="page-intro"><p class="eyebrow">Mahābhārata · Parva {number:02}</p><h1>{escape(label)}</h1>'
                 f'<p>{chapters} chapters in the Kumbhakonam edition, presented in source order.</p>'
                 + ('<a href="/bhagavad-gita/">Explore the Bhagavad Gītā index →</a>' if number == 6 else '') + '</div>')
        page(path, label, intro + '<section class="section-block"><h2>Chapters &amp; source material</h2><ol class="chapter-grid">' + ''.join(entries) + '</ol></section>' + CREDIT)
        books.append(f'<li><a href="/{path}/"><span class="parva-number">{number:02}</span><span><strong>{escape(label)}</strong>'
                     f'<small>{chapters} chapters</small></span><span class="item-arrow" aria-hidden="true">→</span></a></li>')
        records.append(dict(parva=number, source_id=book.get(ID), chapter_divisions=chapters,
                            separate_closings=closing, line_groups=counts['lg']-before))
    expected = Counter(n.tag.split('}')[-1] for n in body.iter())
    assert expected == counts + Counter(body=1,div=len(books))
    assert [n for n, _ in gita_chapters] == list(range(1, 19)), gita_chapters
    chapter_count = sum(record['chapter_divisions'] for record in records)
    if not study_link:
        page('', 'Hindu scripture library', home(len(books), chapter_count, counts['lg']))
        page('bhagavad-gita', 'Bhagavad Gītā', gita_page(gita_chapters))
        page('sources', 'Sources & method', source_page(len(books), chapter_count, counts['lg'], len(NOTES), HASH))
        page('mahabharata', 'Mahābhārata',
             '<nav class="crumbs" aria-label="Breadcrumb"><a href="/#library">Library</a><span aria-hidden="true">/</span><span aria-current="page">Mahābhārata</span></nav>'
             '<div class="page-intro"><p class="eyebrow">Itihāsa · Kumbhakonam edition</p><h1>Mahābhārata</h1><p class="native-title" lang="sa">महाभारतम्</p>'
             '<p>Read the eighteen parvas of the Kumbhakonam edition in Sanskrit. Roman transliteration and available draft English and word meanings can be shown in the chapter reader.</p>'
             '<a class="secondary" href="/bhagavad-gita/">Explore the Bhagavad Gītā <span aria-hidden="true">→</span></a></div>'
             '<section class="section-block"><h2>The eighteen parvas</h2><ol class="parva-grid">' + ''.join(books) + '</ol></section>' + CREDIT)
    else:
        page('mahabharata', 'Mahābhārata', '<h1>Mahābhārata</h1><ol class="parva-grid">' + ''.join(books)
             + '</ol><a href="adi/1/">Opening invocation with English draft and glosses</a>' + CREDIT)
    report = dict(edition='Kumbhakonam SARIT',sha256=HASH,raw_bytes=len(raw),
                  parvas=records, rendered_elements=counts, independent_collation=False)
    Path('docs/sarit-inventory.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
