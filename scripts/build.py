"""Build the open-source distribution into a clean staging directory."""
from html import escape
from pathlib import Path
from tempfile import TemporaryDirectory
import shutil
from sarit import build_corpus

ROOT = Path(__file__).resolve().parents[1]

def build():
    output = ROOT / 'dist'
    with TemporaryDirectory(dir=ROOT) as tmp:
        stage = Path(tmp) / 'site'
        shutil.copytree(ROOT / 'assets', stage)
        def page(path, title, body):
            target = stage / path / 'index.html'
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)} · Path to Moksha</title><link rel="stylesheet" href="/style.css"></head><body><a class="skip" href="#reading">Skip to reading</a><header><a class="brand" href="/">Path to Moksha</a><a href="/mahabharata/">Browse parvas</a></header><main id="reading">{body}</main></body></html>''', encoding='utf-8')
        page('', 'Scripture library', '<section class="shelf"><a class="book-cover" href="/mahabharata/" aria-label="Open the Mahābhārata"><img src="/vyasa-ganesha.jpg" alt="Vyāsa dictating the Mahābhārata to Gaṇeśa"></a><div><p class="edition">Kumbhakonam edition</p><h1>Mahābhārata</h1><p>Explore the eighteen books of the epic. Read the opening passages in English, or turn on Sanskrit to study the source.</p><a class="primary" href="/mahabharata/sarit/1/section-4/#adi-1-1-0">Read the opening invocation</a> <a href="/mahabharata/">Explore all 18 parvas</a></div></section>')
        build_corpus(page, study_link=False)
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
