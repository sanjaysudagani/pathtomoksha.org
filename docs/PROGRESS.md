# Current full-edition status

The SARIT Kumbhakonam XML is archived in sources/mahabharata-devanagari.xml.gz. The build verifies the SHA-256 of its decompressed bytes and renders the entire TEI body. All 18 parvas, 2,315 direct chapter divisions, five separate closing divisions, and 98,575 line groups are present. Four nested divisions are retained inside their parent pages. Source and rendered line-group counts agree. A line group can contain speaker or introductory material. Chapter numbering and edition completeness await independent inventory review. The digital source gives CC BY-SA 3.0 in its own header. Automatic transliteration is unreviewed. The production reader includes original English translations and contextual glosses for the five opening units adi-1-1-0 through adi-1-1-4. Reviewed English coverage is zero. Production is hosted on Cloudflare at https://pathtomoksha.org/.

## Earlier excerpt milestone

# Edition and release record
Selected Kumbhakonam Southern recension, Krishnacharya edition (1906–1914), excluding Harivaṃśa. The initial study excerpt uses the Sanskrit Documents ITRANS rendering credited to Shrinivasa Varakhedi and team. The linked transcription requests personal study and research use. Public release of the excerpt awaits clearance. The mirror and SARIT are related witnesses. No independent comparison or scholar approval has been recorded.

Source: https://sanskritdocuments.org/mirrors/mahabharata/mbhK/txt/mbhK01.itx (1-1-1). Parentheses preserved. The XML fixture is a local encoding of two retrieved lines, not an upstream TEI snapshot. Its hash covers only the fixture. No full chapter or parva acquired. One original English draft and two draft glosses, none reviewed.

Implemented: static navigation, excerpt reader, local inventory and baseline check. Future: full-source resumable ingestion, verified source-specific TEI mapping, independent collation, editorial workflow, search and full coverage reports. Direct raw source download failed at DNS. Browser layout and Cloudflare deployment unverified.

## Open-source distribution

The release is generated in dist/ from the pinned SARIT XML. The previous public/ directory is the local study preview. GitHub CI and the Cloudflare build run the full corpus regression suite. GitHub Actions and Cloudflare builds run the release suite. Production domain routing has been verified. A rollback drill remains pending.
