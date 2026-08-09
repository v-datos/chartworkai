# Documentation site

The public site is generated from ChartworkAI's canonical repository documentation. Do not copy-edit files under `website/.generated/`; that directory is rebuilt and ignored by Git.

## Local build

```bash
python -m venv .venv-docs
.venv-docs/bin/python -m pip install -r website/requirements.txt
.venv-docs/bin/python website/build_site.py
.venv-docs/bin/mkdocs build --strict
.venv-docs/bin/python website/check_site.py site
```

Preview it with:

```bash
.venv-docs/bin/mkdocs serve
```

`website/build_site.py` projects the implementation guide, public reference documents, profiles, CrewAI guide, and brand assets into the MkDocs source tree. Relative links to curated pages stay inside the site; links to non-site repository artifacts point to their canonical GitHub location.

`website/check_site.py` validates the built HTML without network access. It rejects broken internal links and assets, missing image alternatives, unexpected H1 counts, leaked local filesystem paths, a missing search index, or a homepage that no longer contains the canonical front-door content.

The protected CI gate runs the same sequence. `.github/workflows/pages.yml` repeats it before deploying the immutable output to GitHub Pages.
