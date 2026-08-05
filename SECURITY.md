# Security Policy

## Supported versions

| Artifact | Version | Supported |
|---|---|---|
| `chartworkai` package | latest 0.x release | Yes — fixes land on the newest release |
| `chartworkai` package | older 0.x releases | No — upgrade to the latest |
| Framework contracts | 1.x | Yes |

The `chartworkai` Python package is on its way to its first published release. Until it reaches
1.0, security fixes land on the latest published version only; there are no backports to earlier
pre-1.0 builds.

## Reporting a vulnerability

**Report privately through GitHub Security Advisories:**
[github.com/v-datos/chartworkai/security/advisories/new](https://github.com/v-datos/chartworkai/security/advisories/new)
(Security tab → "Report a vulnerability").

**Please do not open a public issue, discussion, or pull request for a suspected vulnerability.**
Public reports expose users who have not yet upgraded. Use the private advisory channel and we
will coordinate disclosure with you.

Useful things to include: the version or commit, the platform and shell, a minimal reproduction,
what an attacker gains, and any proposed fix.

**What to expect:**

- **Acknowledgement within 5 business days.** If you have not heard back by then, assume the
  message was missed and ping the advisory thread.
- An assessment of severity and affected versions, and a fix or mitigation plan.
- Credit in the advisory and `CHANGELOG.md` if you want it, or anonymity if you prefer.

This is a small project. We do not run a paid bug bounty.

## Security model

Be clear-eyed about what this tool is. ChartworkAI is a governance layer made of Markdown artifacts
and POSIX shell scripts, plus a Python CLI that lints them.

**What the core does:**

- Reads and writes Markdown and JSON files inside a project repository.
- Runs POSIX `sh` scripts locally, under your own user account, with your own permissions.
- Prints results to your terminal and exits 0 (pass) or 1 (failures).

**What the core does not do:**

- **No network calls.** No core script or CLI path opens a socket, fetches a URL, or phones home.
- **No telemetry.** Nothing about your project, files, or usage is collected or transmitted.
- **No runtime credentials.** The core reads no tokens, keys, or secrets, and has zero runtime
  dependencies — deliberately, so it never drags a dependency tree into the repo it audits.

**Optional extensions are a different story.** Modules under `extensions/` — notably
`external-tracker-sync` — are opt-in and *may* talk to third-party services such as issue
trackers. When you enable one:

- You supply your own API token through an environment variable (for example `TRACKER_TOKEN`).
- **Never commit a token.** Keep it in your environment or a secret store. `.gitignore` already
  excludes `.env` files; that is a backstop, not a substitute for care.
- You own the trust relationship with that third party. Review the extension's script and its
  README before enabling it, and scope the token as narrowly as the vendor allows.

### Running the checker on untrusted repositories

The compliance checker inspects repository files: it walks the tree, reads document contents, and
**prints matched excerpts back to your terminal** (for example, the lines that tripped a
placeholder or tool-leak check). File contents and file names from the repository under inspection
therefore reach your screen, and a repository authored by someone else is untrusted input.

Do not run ChartworkAI — or any of the shell scripts in a cloned repository — against a project you
have not reviewed. Shell scripts in a repo you cloned execute with your permissions, whatever they
happen to contain. Read before you run.

## Scope

**In scope:**

- Arbitrary code or command execution triggered by parsing repository files or CLI arguments.
- Shell injection through file names, paths, or document contents.
- Path traversal — reads or writes outside the target project root by the bootstrap, generator,
  or checker.
- Secret leakage caused by our scripts (a token written into a file, a log, or a committed
  artifact).
- Any unexpected network call or telemetry from the core.
- Supply-chain problems with the published `chartworkai` package on PyPI (typosquatting of our
  name, a compromised release artifact, dependency confusion).

**Not in scope:**

- Vulnerabilities in the AI assistant, editor, or agent runtime you use alongside the framework —
  report those to that vendor.
- Vulnerabilities in third-party trackers or their APIs reached by an optional extension — report
  those to that vendor.
- Consequences of running the tool against a repository you chose not to review (documented
  above).
- Secrets a user commits to their own repository.
- The fact that local shell scripts run locally with your permissions. That is the design, not a
  flaw.
- Social engineering, physical access, or attacks requiring an already-compromised machine.
- Automated scanner output with no demonstrated impact.
