"""Build the open-source distribution into a clean staging directory."""
from html import escape
from pathlib import Path
from tempfile import TemporaryDirectory
import shutil

from sarit import build_corpus

ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_ORIGIN = 'https://pathtomoksha.org'
# Never copy the assets directory wholesale: source drafts, screenshots, and
# other local-only files must not become public just by being placed there.
PUBLIC_ASSETS = ("_headers", "style.css", "reader.js", "mahabharata.jpg", "vyasa-ganesha.jpg")


def stage_public_assets(source, destination):
    destination.mkdir(parents=True)
    for name in PUBLIC_ASSETS:
        asset = source / name
        if not asset.is_file() or asset.is_symlink():
            raise ValueError(f"Missing or unsupported public asset: {name}")
        shutil.copyfile(asset, destination / name)

def public_url(path):
    return PRODUCTION_ORIGIN + ('/' + path.strip('/') + '/' if path else '/')


def document(path, title, body, *, indexable=True):
    if indexable:
        description = ('An open Hindu scripture library with the original Sanskrit Mahābhārata, a Bhagavad Gītā index, and reading tools.'
                       if not path else f'{title}. Browse the original Sanskrit of the Kumbhakonam edition and use the reader’s study tools on Path to Moksha.')
        discovery = (f'<link rel="canonical" href="{escape(public_url(path), quote=True)}">'
                     f'<meta name="description" content="{escape(description, quote=True)}">')
    else:
        discovery = '<meta name="robots" content="noindex, nofollow, noarchive">'
    library_current = ' aria-current="page"' if path == '' else ''
    source_current = ' aria-current="page"' if path == 'sources' else ''
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)} · Path to Moksha</title>{discovery}<link rel="stylesheet" href="/style.css"><script src="/reader.js" defer></script></head>
<body><a class="skip" href="#reading">Skip to main content</a><header class="site-header"><div class="frame masthead">
<a class="brand" href="/"><span class="brand-mark" aria-hidden="true">✧</span><span>Path to Moksha</span></a>
<nav aria-label="Main navigation"><a href="/#library"{library_current}>Library</a><a href="/sources/"{source_current}>Sources <span class="nav-extra">&amp; method</span></a></nav>
</div></header><main id="reading" class="frame" tabindex="-1">{body}</main>
<footer class="site-footer"><div class="frame"><a href="/">Path to Moksha</a><span>An open Hindu scripture library</span><a href="/sources/">Sources &amp; method</a></div></footer>
</body></html>'''

def build():
    output = ROOT / 'dist'
    with TemporaryDirectory(dir=ROOT) as tmp:
        stage = Path(tmp) / 'site'
        stage_public_assets(ROOT / 'assets', stage)
        pages = []
        def page(path, title, body):
            target = stage / path / 'index.html'
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(document(path, title, body), encoding='utf-8')
            pages.append(path)
        build_corpus(page, study_link=False)
        if len(set(pages)) != len(pages):
            raise ValueError('Two public pages have the same URL')
        sitemap = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                   '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                   + ''.join(f'<url><loc>{escape(public_url(path))}</loc></url>\n' for path in sorted(pages))
                   + '</urlset>\n')
        (stage / 'sitemap.xml').write_text(sitemap, encoding='utf-8')
        (stage / 'robots.txt').write_text(f'User-agent: *\nDisallow: /review/\nSitemap: {PRODUCTION_ORIGIN}/sitemap.xml\n', encoding='utf-8')
        (stage / '404.html').write_text(document('404', 'Page not found',
            '<section class="page-intro"><p class="eyebrow">Error 404</p><h1>Page not found</h1>'
            '<p>This address does not point to a page in the scripture library. You can return to the library or browse the Mahābhārata.</p>'
            '<a class="primary" href="/#library">Go to library</a> <a class="secondary" href="/mahabharata/">Browse parvas</a></section>',
            indexable=False), encoding='utf-8')
        if output.exists():
            output.rename(Path(tmp) / 'previous')
        try:
            stage.rename(output)
        except OSError:
            if (Path(tmp) / 'previous').exists():
                (Path(tmp) / 'previous').rename(output)
            raise

if __name__ == '__main__':
    build()
