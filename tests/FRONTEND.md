# Run the browser release checks

Build the site locally, then run this from the project folder:

```sh
python3 scripts/build.py
python3 -m unittest discover -s tests -v
node tests/frontend_browser.mjs
```

The browser suite needs Node 22 or later and Chrome or Chromium. Set
`CHROME_BIN` if the executable is installed in a nonstandard location.
Optionally pass a staging output path after the script name to leave the
primary `dist` untouched. The test launches an isolated browser and a loopback
server, applies the shipped `_headers`, and deletes the test browser profile.
It does not publish or contact the production site.

The seven scenarios cover layout at 320, 375, 390, 768, 1024, and 1440 px in light
and dark themes; 200% reader text, control contrast, links and source provenance; keyboard navigation, exact and
Devanagari chapter search; text size, saved bookmarks and reading-link copy;
failure modes with the enhancement script blocked or browser storage denied;
and direct verse links and frontend asset size budgets. These checks are not a
substitute for Safari, Firefox, hardware, screen-reader, or reader review.

To check the local-only translation review after building it:

```sh
node tests/frontend_browser.mjs --review
```

This covers the private index and representative first and last review
chapters for each imported parva at four widths in both themes.
