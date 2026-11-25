"""Immutable source text, site size and public/private boundary checks."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import gzip
import sys
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path('scripts').resolve()))
from source_locators import source_units
from sarit import SOURCE
from build import PRODUCTION_ORIGIN, public_url

DIST = Path('dist')


class UnitReader(HTMLParser):
    void = frozenset('area base br col embed hr img input link meta param source track wbr'.split())

    def __init__(self):
        super().__init__()
        self.stack, self.units, self.ids, self.duplicate_ids = [], {}, set(), set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        key = attrs.get('id')
        if key is not None:
            if key in self.ids:
                self.duplicate_ids.add(key)
            self.ids.add(key)
        unit = attrs.get('data-source-unit')
        parent = self.stack[-1] if self.stack else ('', '', False)
        _, owner, write = parent
        if unit:
            if owner and write:
                self.units[owner].append(' ')
            if key in self.units or not key:
                raise ValueError(f'Duplicate or missing source unit: {key}')
            self.units[key] = []
            owner, write = key, unit != 'lg'
        elif attrs.get('class') == 'sanskrit':
            write = bool(owner)
        elif owner and write and (tag == 'br' or tag == 'div'):
            self.units[owner].append(' ')
        if tag not in self.void:
            self.stack.append((tag, owner, write))

    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1][0] != tag:
            raise ValueError(f'Unbalanced markup at {tag}, expected {self.stack[-1] if self.stack else None}')
        self.stack.pop()

    def handle_data(self, value):
        if self.stack:
            _, owner, write = self.stack[-1]
            if owner and write:
                self.units[owner].append(value)


class ReleaseIsolationTests(unittest.TestCase):
    def test_every_owned_source_unit_verbatim_and_in_order(self):
        expected = {}
        with gzip.open(SOURCE, 'rb') as stream:
            body = ET.parse(stream).find('.//{*}body')
        for item in source_units(body):
            expected.setdefault((item.book, item.section), {})[item.locator] = item.source
        observed_count = 0
        for (book, section), target in expected.items():
            folder = DIST / 'mahabharata/sarit' / str(book)
            if section:
                folder /= f'section-{section}'
            file = folder / 'index.html'
            reader = UnitReader()
            reader.feed(file.read_text(encoding='utf-8'))
            reader.close()
            self.assertEqual(reader.stack, [], file)
            self.assertEqual(reader.duplicate_ids, set(), file)
            actual = {key: ' '.join(''.join(values).split()) for key, values in reader.units.items()}
            self.assertEqual(list(actual), list(target), file)
            for key, original in target.items():
                self.assertEqual(actual[key], original, (file, key))
            observed_count += len(actual)
        self.assertEqual(observed_count, 109277)

    def test_public_output_contains_only_allowed_data_and_bundled_assets(self):
        html_files = sorted(DIST.rglob('*.html'))
        allowed = {'_headers', 'style.css', 'reader.js', 'mahabharata.jpg', 'vyasa-ganesha.jpg', 'robots.txt', 'sitemap.xml'}
        self.assertEqual({x.relative_to(DIST).as_posix() for x in DIST.rglob('*') if x.is_file() and x.suffix != '.html'},
                         allowed)
        for path in html_files:
            file = path.relative_to(DIST)
            text = path.read_text(encoding='utf-8')
            self.assertNotIn('local-translation', file.parts, file)
            self.assertNotIn('review', file.parts, file)
            self.assertNotIn('Private review copy', text, file)
            self.assertNotIn('Awaiting independent review</p></section>', text, file)
            self.assertNotIn('imported_translation_drafts', text, file)
        headers = (DIST / '_headers').read_text(encoding='utf-8')
        self.assertIn("default-src 'none'", headers)
        self.assertIn("script-src 'self'", headers)
        self.assertNotIn('unsafe-inline', headers)
        self.assertNotIn('unsafe-eval', headers)
        self.assertIn('X-Content-Type-Options: nosniff', headers)

    def test_public_reader_payload_budget(self):
        budgets = {'style.css': 24_000, 'reader.js': 24_000, 'index.html': 18_000,
                   'mahabharata/sarit/6/section-26/index.html': 125_000}
        for name, ceiling in budgets.items():
            count = (DIST / name).stat().st_size
            self.assertLessEqual(count, ceiling, f'{name}: {count} exceeds {ceiling} bytes')

    def test_sitemap_and_canonicals_only_cover_live_pages(self):
        robots = (DIST / 'robots.txt').read_text()
        self.assertIn(f'Sitemap: {PRODUCTION_ORIGIN}/sitemap.xml', robots)
        urls = [row.text for row in ET.parse(DIST / 'sitemap.xml').findall('.//{*}loc')]
        self.assertEqual(len(urls), len(set(urls)))
        paths = set()
        for link in urls:
            parsed_url = urlsplit(link)
            self.assertEqual(f'{parsed_url.scheme}://{parsed_url.netloc}', PRODUCTION_ORIGIN)
            self.assertFalse(parsed_url.fragment or parsed_url.query)
            relative = parsed_url.path.strip('/')
            self.assertNotIn('review', relative.split('/'))
            page = DIST / relative / 'index.html'
            body = page.read_text()
            self.assertIn(f'rel="canonical" href="{public_url(relative)}"', body)
            self.assertIn('name="description"', body)
            paths.add(page)
        self.assertEqual(paths, set(DIST.rglob('index.html')))
        not_found = (DIST / '404.html').read_text()
        self.assertIn('<h1>Page not found</h1>', not_found)
        self.assertIn('noindex', not_found)
        self.assertNotIn('rel="canonical"', not_found)
