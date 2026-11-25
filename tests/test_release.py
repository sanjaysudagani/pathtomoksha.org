import gzip
import re
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit
import sys

sys.path.insert(0, str(Path('scripts').resolve()))
from sarit import ID, SOURCE, transliterate

class SanskritReader(HTMLParser):
    def __init__(self):
        super().__init__()
        self.groups = []
        self.active = []
        self.stack = []
        self.excluded = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ('br', 'meta', 'link', 'input', 'img'):
            return
        starts = tag == 'div' and attrs.get('class') == 'sanskrit'
        exclude = attrs.get('class') == 'iast' or (tag == 'small' and self.stack and self.stack[-1][0] == 'article')
        if tag == 'article' and attrs.get('class') == 'verse':
            self.groups.append((attrs.get('id'), []))
        if starts:
            self.active.append(self.groups[-1][1])
        self.excluded += int(exclude)
        self.stack.append((tag, starts, exclude))

    def handle_endtag(self, tag):
        name, starts, excluded = self.stack.pop()
        if name != tag:
            raise ValueError((name, tag))
        if starts:
            self.active.pop()
        self.excluded -= int(excluded)

    def handle_data(self, data):
        if not self.excluded:
            for parts in self.active:
                parts.append(data)


class ReleaseTests(unittest.TestCase):
    def test_opening_study_and_navigation(self):
        from study import NOTES
        home = Path('dist/index.html').read_text()
        start = re.search(r'class="primary" href="([^"]+)"', home).group(1)
        route, anchor = start.split('#')
        chapter = (Path('dist') / route.strip('/') / 'index.html').read_text()
        self.assertIn(f'id="{anchor}"', chapter)
        expected = sum(chapter.count(f'id="{locator}"') for locator in NOTES)
        self.assertEqual(chapter.count('<h3>Translation</h3>'), expected)
        self.assertEqual(chapter.count('<h3>Synonyms</h3>'), expected)
        following = re.search(r'rel="next" href="([^"]+)"', chapter).group(1)
        next_path = urljoin(route, following)
        next_chapter = (Path('dist') / next_path.strip('/') / 'index.html').read_text()
        previous = re.search(r'rel="prev" href="([^"]+)"', next_chapter).group(1)
        self.assertEqual(urljoin(next_path, previous), route)

    def test_study_notes_have_unique_source_anchors(self):
        from study import NOTES
        with gzip.open(SOURCE) as stream:
            body = ET.parse(stream).find('.//{*}body')
        matches = {}
        for node in body.iterfind('.//{*}lg'):
            locator = node.get(ID)
            if locator in NOTES:
                matches[locator] = matches.get(locator, 0) + 1
        self.assertEqual(matches, dict.fromkeys(NOTES, 1))
        for locator, (glosses, translation) in NOTES.items():
            self.assertTrue(translation.strip(), locator)
            self.assertTrue(glosses, locator)
            for word, meaning in glosses:
                self.assertTrue(word.strip() and meaning.strip(), locator)

    def test_reading_options_and_cover(self):
        root = Path('dist')
        home = (root / 'index.html').read_text()
        self.assertIn('class="book" href="/mahabharata/"', home)
        self.assertIn('class="book" href="/bhagavad-gita/"', home)
        self.assertIn('id="planned-title">Planned collections', home)
        self.assertEqual(home.count('class="status">Planned</span>'), 4)
        self.assertTrue((root / 'vyasa-ganesha.jpg').stat().st_size > 0)
        chapters = list(root.glob('mahabharata/sarit/*/section-*/index.html'))
        self.assertEqual(len(chapters), 2320)
        for chapter in chapters:
            html = chapter.read_text()
            self.assertIn('id="show-iast"', html, chapter)
            if '<section class="study">' not in html:
                self.assertIn('id="show-sa" checked', html, chapter)
                self.assertIn('English translation is pending', html, chapter)
                self.assertNotIn('id="show-words"', html, chapter)
            else:
                self.assertIn('id="show-sa">', html, chapter)
                self.assertIn('id="show-words"', html, chapter)

    def test_gita_uses_attested_chapters_in_the_same_edition(self):
        root = Path('dist')
        index = (root / 'bhagavad-gita/index.html').read_text()
        links = re.findall(r'href="(/mahabharata/sarit/6/section-[0-9]+/)"><span>Chapter ([0-9]+)</span>', index)
        self.assertEqual([int(number) for _, number in links], list(range(1, 19)))
        for route, number in links:
            chapter = (root / route.strip('/') / 'index.html').read_text()
            self.assertRegex(chapter, rf'भगवद्गीता(?:ध्या|द्या)यः[\s ]+॥[\s ]+{number}[\s ]+॥')
        self.assertIn('धर्मक्षेत्रे कुरुक्षेत्रे', (root / links[0][0].strip('/') / 'index.html').read_text())

    def test_transliteration(self):
        for source, expected in [('धर्मक्षेत्रे', 'dharmakṣetre'), ('अध्यायः', 'adhyāyaḥ'), ('जयम्', 'jayam')]:
            self.assertEqual(transliterate(source), expected)

    def test_all_chapters_against_source(self):
        with gzip.open(SOURCE) as stream:
            body = ET.parse(stream).find('.//{*}body')
        total = 0
        self.assertEqual(len(body), 18)
        for book in body:
            for index, chapter in enumerate(book, 1):
                if not chapter.tag.endswith('}div'):
                    continue
                target = Path(f'dist/mahabharata/sarit/{int(book.get("n"))}/section-{index}/index.html')
                html = target.read_text()
                reader = SanskritReader()
                reader.feed(html)
                groups = chapter.findall('.//{*}lg')
                self.assertEqual(len(groups), len(reader.groups), target)
                for node, (locator, parts) in zip(groups, reader.groups):
                    self.assertEqual(locator, node.get(ID))
                    self.assertEqual(''.join(parts), ''.join(node.itertext()), locator)
                total += len(groups)
        self.assertEqual(total, 98575)

    def test_internal_links_and_release_assets(self):
        root = Path('dist')
        pages = list(root.rglob('*.html'))
        self.assertEqual(len(pages), 2343)
        for file in pages:
            url = '/' + file.relative_to(root).as_posix()
            for href in re.findall('href="([^"]+)"', file.read_text()):
                resolved = urlsplit(urljoin(url, href))
                if resolved.netloc:
                    continue
                target = root / resolved.path.lstrip('/')
                if target.is_dir():
                    target /= 'index.html'
                self.assertTrue(target.is_file(), (file, href))
        self.assertTrue((root / '_headers').is_file())
