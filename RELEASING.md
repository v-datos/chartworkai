# Releasing

How a ChartworkAI release is cut. Versioning follows
[`DEC-008`](docs/decisions/20260805_DEC008_versioning_scheme.md): the framework and the
Python package version independently, and package tags are prefixed
`chartworkai-vX.Y.Z`.

**Publishing is done by a human.** No token is stored in this repository and no workflow
uploads on your behalf.

## 1. Pre-flight

Everything here must pass before you tag.

```bash
python -m pytest                       # full suite
ruff check src tests                   # lint
chartworkai check . --strict           # the project governs itself
sh scripts/check_framework_compliance.sh .   # shell checker agrees
```

Then confirm the two implementations still agree, because the scaffold is a published
contract:

```bash
rm -rf /tmp/sh_p /tmp/py_p
sh scripts/init_project_from_framework.sh /tmp/sh_p "Parity" parity software-app >/dev/null
chartworkai init /tmp/py_p --name "Parity" --slug parity --profile software-app >/dev/null
diff -r /tmp/sh_p /tmp/py_p && echo "scaffolds identical"
```

## 2. Bump and record

1. Set `version` in `pyproject.toml` (package) and/or `framework.json` (framework).
2. Move `## [Unreleased]` in `CHANGELOG.md` to the new version with today's date, and add
   the compare link at the bottom.
3. While the package is 0.x, say plainly in the entry if the CLI surface, the `--json`
   schema or the MCP tool names changed — those are not yet stable (DEC-008).

## 3. Build and verify the artifacts

```bash
rm -rf dist
python -m build                        # sdist + wheel
twine check dist/*
```

Check the sdist did not pick up local clutter — it should be a few hundred KB, not
megabytes:

```bash
ls -lh dist
tar -tzf dist/*.tar.gz | grep -E "outputs/|\.venv|\.claude" && echo "LEAK — fix excludes" || echo "clean"
```

**Install from the sdist, not just the wheel**, in a throwaway environment, and scaffold
from outside this repository. This is what proves the packaged assets resolve for a real
user rather than falling back to the source checkout:

```bash
python -m venv /tmp/relcheck
/tmp/relcheck/bin/pip install dist/chartworkai-*.tar.gz
cd /tmp && /tmp/relcheck/bin/chartworkai init /tmp/relproj --name "Release Check" \
    --profile software-app
```

Expect the scaffold to **fail** `check` on unresolved placeholders and the leftover
`_framework_*` folders — that is the graduation gate. Delete those folders, fill the
placeholders, and confirm it turns green.

## 4. Tag

```bash
git tag -a chartworkai-v0.1.0 -m "ChartworkAI 0.1.0 — the governance layer for agentic work"
git push origin main
git push origin chartworkai-v0.1.0
```

## 5. Publish

Publishing runs from `.github/workflows/release.yml` using **Trusted Publishing**
(OIDC). No API token is stored anywhere: PyPI verifies the workflow's identity —
repository, workflow filename, and environment — and mints a credential good for that
one upload. A token that does not exist cannot leak.

### One-time setup

On **test.pypi.org** and again on **pypi.org**, under *Publishing → Add a pending
publisher*, register:

| Field | Value |
|---|---|
| PyPI project name | `chartworkai` |
| Owner | `v-datos` |
| Repository name | `chartworkai` |
| Workflow name | `release.yml` |
| Environment | `testpypi` on TestPyPI, `pypi` on PyPI |

"Pending publisher" is the right form before the project exists; it converts to a
normal publisher on first upload. Create the two matching GitHub environments under
*Settings → Environments* — that is what makes the environment name in the claim
meaningful, and it is where you can add a manual approval gate.

### TestPyPI first

Run the **Release** workflow manually from the Actions tab, then install what it
published before touching the real index:

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple chartworkai
```

### Then PyPI

Pushing the tag is the whole release.

```bash
git push origin chartworkai-v0.1.0
```

**Tag a commit that is already on `main`.** A tag is not a review: it can be pushed
to any commit, including one that never passed CI or was never on a protected
branch. The workflow refuses to publish unless the tagged commit is contained in
`origin/main`, and refuses if the tag and the packaged version disagree.

Before uploading anything the workflow re-runs, against the exact commit being
published: the test suite, `ruff check` and `ruff format --check`, both compliance
engines, and `sh -n` over every shell script — on Linux, macOS, and Windows. It then
scans both the sdist and the wheel for local clutter, credential-shaped files, and
personal identifiers (a home directory or a non-`noreply` email reaching PyPI cannot
be recalled), and installs the sdist into a clean venv to scaffold a project from
outside the repo.

Never reuse a tag created in the pre-publication private repository. Those tags point
into history that was deliberately left behind; create the release tag from a commit
in this repository.

## 6. After the first release

- **Do not upload a placeholder to reserve `chartwork`.** The near-miss name is worth
  watching (DEC-007), but PyPI's name-retention policy (PEP 541) treats a project
  uploaded only to hold a name as abandoned and reclaimable, so the placeholder buys
  nothing and can itself be transferred away. The supported route is the PEP 541
  dispute process, opened against a name once someone actually misuses it — plus
  naming `chartworkai` clearly in the README so a typosquat is obvious to users.
- Create the GitHub release from the tag, pasting the changelog section.
- Set the repository's social preview image to `assets/chartworkai_banner.png`.
