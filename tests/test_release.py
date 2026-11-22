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
        if tag in ('br', 'meta', 'link'):
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
        self.assertEqual(chapter.count('<h3>Translation</h3>'), len(NOTES))
        self.assertEqual(chapter.count('<h3>Synonyms</h3>'), len(NOTES))
        following = re.search(r'rel="next" href="([^"]+)"', chapter).group(1)
        next_path = urljoin(route, following)
        next_chapter = (Path('dist') / next_path.strip('/') / 'index.html').read_text()
        previous = re.search(r'rel="prev" href="([^"]+)"', next_chapter).group(1)
        self.assertEqual(urljoin(next_path, previous), route)

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
        self.assertEqual(len(pages), 2340)
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
