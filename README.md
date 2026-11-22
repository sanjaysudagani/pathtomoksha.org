# Path to Moksha

An open-source Sanskrit reader for all eighteen parvas of the SARIT Kumbhakonam Mahābhārata. Chapters are static HTML with source identifiers and automatic Roman transliteration. Reading requires no account, JavaScript, or database.

## Build and verify

Run from the repository root using Python 3.10 or later.

```sh
python3 scripts/build.py
python3 -m unittest discover -s tests -v
python3 -m http.server 8000 --bind 127.0.0.1 --directory dist
```

Open http://127.0.0.1:8000/. The build checks the decompressed XML against a pinned SHA-256 and stages a fresh distribution. Tests compare each rendered Sanskrit line group, including nested groups, against the frozen XML in source order. They check internal page links, asset presence, and selected transliterations. The per-parva counts are in docs/sarit-inventory.json. Independent textual collation and translation review remain pending.

## GitHub and Cloudflare

Push the source tree and compressed source snapshot to your public GitHub repository. Generated assets and local study examples are ignored by Git. The Verify reader workflow builds and tests pushes and pull requests with read-only access. In GitHub, require the verify check on main before merging.

In Cloudflare Workers & Pages, connect the GitHub repository to the Worker named path-to-moksha. Choose main as the production branch, the repository root as the working directory, and these commands:

| Setting | Value |
| --- | --- |
| Build command | `python3 scripts/build.py && python3 -m unittest discover -s tests -v` |
| Deploy command | `npx wrangler deploy` |
| Static assets | `./dist`, configured in wrangler.toml |

Run a first deployment on the workers.dev address. Check the homepage, a chapter from the first and last parvas, a missing URL, and the response headers. Then attach pathtomoksha.org as the Worker custom domain. For rollback, redeploy the previous known-good version in the Worker deployment history and revert the release commit on main before the next deployment.

[Cloudflare build configuration](https://developers.cloudflare.com/workers/ci-cd/builds/configuration/)

## Contributing and licensing

Include the affected edition and XML locator with any source or transliteration issue. Keep editorial corrections separate from the frozen XML. Run the full tests before opening a pull request.

Project software uses MIT. The SARIT corpus and derived transliteration use CC BY-SA 3.0. See LICENSE and NOTICE.md.
