"""Original library presentation; published cards link only to attested content."""
from html import escape

OPENING = '/mahabharata/sarit/1/section-4/#adi-1-1-0'
GITA = '/bhagavad-gita/'
GITA_BOOK = '/mahabharata/sarit/6/'
WORKS = (
    ('mahabharata', 'Mahābhārata', 'महाभारतम्', 'Epics · Kumbhakonam edition', '18 parvas', '/mahabharata/'),
    ('gita', 'Bhagavad Gītā', 'भगवद्गीता', 'A passage within the Mahābhārata', '18 chapters', GITA),
)
ROADMAP = (
    ('ramayana', 'Rāmāyaṇa', 'रामायणम्', 'Epic · Kāṇḍas to be indexed'),
    ('puranas', 'Mahāpurāṇas', 'महापुराणानि', 'Collection · 18 major Purāṇas'),
    ('upapuranas', 'Upapurāṇas', 'उपपुराणानि', 'Collection · 18 minor Purāṇas'),
    ('vedas', 'Vedas & Upaniṣads', 'वेदाः · उपनिषदः', 'Vedic texts and philosophical works'),
)

def cover(theme, title, script, caption):
    art = ('<img src="/mahabharata.jpg" width="520" height="780" loading="lazy" decoding="async" alt="">' if theme == 'mahabharata'
           else f'<span class="cover-script" lang="sa">{escape(script)}</span>')
    return (f'<span class="cover cover--{theme}" aria-hidden="true">{art}'
            f'<span class="cover-title">{escape(title)}</span><span class="cover-caption">{escape(caption)}</span></span>')

def shelves():
    published = ''.join(
        f'<li><a class="book" href="{url}">{cover(theme, title, script, "Path to Moksha")}'
        f'<span class="book-title">{escape(title)}</span><span class="book-meta">{escape(meta)}</span>'
        f'<span class="status status--readable">{count} <span aria-hidden="true">↗</span></span></a></li>'
        for theme, title, script, meta, count, url in WORKS
    )
    planned = ''.join(
        f'<li><article class="book">{cover(theme, title, script, "Collection roadmap")}'
        f'<h3 class="book-title">{escape(title)}</h3><span class="book-meta">{escape(meta)}</span>'
        '<span class="status">Planned</span></article></li>'
        for theme, title, script, meta in ROADMAP
    )
    return f'''<section class="shelf-section" aria-labelledby="catalog-title" id="library">
      <div class="section-title"><div><p class="eyebrow">The collection</p><h2 id="catalog-title">Browse the library</h2></div>
      <p>Open a text to read, or see what’s planned for the collection.</p></div>
      <div class="books"><section class="books-available" aria-labelledby="available-title"><h3 class="shelf-label" id="available-title">Available to read</h3>
      <ul class="book-grid">{published}</ul></section><section class="books-planned" aria-labelledby="planned-title"><h3 class="shelf-label" id="planned-title">Planned collections</h3>
      <ul class="book-grid">{planned}</ul></section></div></section>'''

def home(book_count, chapter_count, line_count):
    return f'''<section class="library-intro">
      <div><p class="eyebrow">An open Hindu scripture library</p>
      <h1>Read the Hindu<br class="desktop-break"> scriptures<span class="title-period">.</span></h1>
      <p class="intro-copy">Explore original Sanskrit, Roman transliteration, and English study notes where available. The library starts with the Mahābhārata and grows as new editions are prepared.</p>
      <div class="actions"><a class="primary" href="{OPENING}">Start reading <span aria-hidden="true">→</span></a>
      <a class="secondary" href="#library">Browse library <span aria-hidden="true">↓</span></a></div></div>
      <figure class="hero-art"><img src="/vyasa-ganesha.jpg" width="533" height="800" fetchpriority="high" decoding="async" alt="Vyāsa dictating the Mahābhārata to Gaṇeśa"><figcaption>Vyāsa and Gaṇeśa <span>·</span> The Mahābhārata</figcaption></figure>
      </section>{shelves()}
      <section class="edition-panel" aria-labelledby="edition-title"><div><p class="eyebrow">Text &amp; provenance</p><h2 id="edition-title">Read the source, not just the story.</h2>
      <p>The Sanskrit is reproduced from the pinned SARIT Kumbhakonam edition. Roman transliteration is automatic; available English notes are marked as drafts.</p>
      <a href="/sources/">See the edition &amp; verification notes <span aria-hidden="true">→</span></a></div>
      <dl><div><dt>Parvas</dt><dd>{book_count}</dd></div><div><dt>Chapter divisions</dt><dd>{chapter_count:,}</dd></div>
      <div><dt>Sanskrit line groups</dt><dd>{line_count:,}</dd></div></dl></section>'''

def gita_page(chapters):
    rows = ''.join(f'<li><a href="{href}"><span>Chapter {number}</span><span aria-hidden="true">→</span></a></li>'
                   for number, href in chapters)
    return f'''<nav class="crumbs" aria-label="Breadcrumb"><a href="/#library">Library</a><span aria-hidden="true">/</span>
      <span aria-current="page">Bhagavad Gītā</span></nav><div class="page-intro"><p class="eyebrow">Mahābhārata · Bhīṣma Parva</p>
      <h1>Bhagavad Gītā</h1><p class="native-title" lang="sa">भगवद्गीता</p>
      <p>A dialogue between Kṛṣṇa and Arjuna on the battlefield of Kurukṣetra. These 18 links open the corresponding Sanskrit chapters in the <a href="{GITA_BOOK}">Bhīṣma Parva</a>; they are not a separate edition.</p>
      <a class="primary" href="{chapters[0][1]}">Read Chapter 1 <span aria-hidden="true">→</span></a>
      </div><section class="section-block" aria-labelledby="chapter-index"><h2 id="chapter-index">All 18 chapters</h2>
      <ol class="chapter-grid">{rows}</ol></section>'''

def source_page(book_count, chapter_count, line_count, draft_count, sha):
    return f'''<nav class="crumbs" aria-label="Breadcrumb"><a href="/#library">Library</a><span aria-hidden="true">/</span>
      <span aria-current="page">Sources &amp; method</span></nav><div class="page-intro"><p class="eyebrow">Text &amp; provenance</p>
      <h1>Sources &amp; method</h1><p>The reader keeps the Sanskrit transcription, Roman transliteration and English drafts distinct.</p></div>
      <div class="method-grid">
      <section><h2>The edition</h2><p>The Southern recension’s Kumbhakonam edition is reproduced from the <a href="https://github.com/sarit/SARIT-corpus/blob/master/mahabharata-devanagari.xml">SARIT TEI transcription</a>, licensed <a href="https://creativecommons.org/licenses/by-sa/3.0/">CC BY-SA 3.0</a>.</p></section>
      <section><h2>What the build checks</h2><p>The build checks the decompressed source against a pinned hash. The release tests compare the Sanskrit line groups to that source in order. Independent collation with a separate witness is still pending.</p><details><summary>Source SHA-256</summary><code>{escape(sha)}</code></details></section>
      <section><h2>What’s in the library</h2><p>{book_count} parvas, {chapter_count:,} direct chapter divisions and {line_count:,} Sanskrit line groups. The Gītā index links to chapters already included in those counts.</p></section>
      <section><h2>English and transliteration</h2><p>There are {draft_count:,} English study drafts in this build. No independent editorial approval is recorded. Roman transliteration is generated automatically.</p></section></div>'''
