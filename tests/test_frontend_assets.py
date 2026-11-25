"""Regression tests for the public frontend staging boundary."""

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build import PUBLIC_ASSETS, stage_public_assets


class FrontendAssetTests(unittest.TestCase):
    def fixture(self, folder):
        source = Path(folder) / "source"
        source.mkdir()
        for filename in PUBLIC_ASSETS:
            (source / filename).write_text(filename, encoding="utf-8")
        return source

    def test_only_public_manifest_is_staged(self):
        with TemporaryDirectory(dir=Path.cwd()) as folder:
            source = self.fixture(folder)
            (source / "draft-private.md").write_text("unpublished text", encoding="utf-8")
            (source / "private").mkdir()
            (source / "private" / "unreleased-cover.jpg").write_bytes(b"reference")
            dist = Path(folder) / "site"
            stage_public_assets(source, dist)
            self.assertEqual(sorted(path.name for path in dist.iterdir()), sorted(PUBLIC_ASSETS))

    def test_listed_asset_missing_or_symlinked_is_rejected(self):
        for symlink in (False, True):
            with self.subTest(symlink=symlink), TemporaryDirectory(dir=Path.cwd()) as folder:
                source = self.fixture(folder)
                asset = source / "reader.js"
                asset.unlink()
                if symlink:
                    private = Path(folder) / "unpublished.js"
                    private.write_text("private", encoding="utf-8")
                    asset.symlink_to(private)
                with self.assertRaisesRegex(ValueError, "public asset: reader.js"):
                    stage_public_assets(source, Path(folder) / "site")
