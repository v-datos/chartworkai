# Command-line reference

The `chartworkai` command installs and checks the governance layer, reads project state, regenerates the phase plan, and exposes the same controls to AI assistants over MCP.

```bash
pip install chartworkai
chartworkai --version
```

## `chartworkai init`

Create the project-agnostic governance core:

```bash
chartworkai init ./my-project --name "My Project"
```

Apply one of the six optional presets:

```bash
chartworkai init ./my-app --name "My App" --profile software-app
```

Apply a project-owned custom profile:

```bash
chartworkai init ./case-review --name "Case Review" \
  --profile-file ./case-review.profile.json
```

| Option | Meaning |
|---|---|
| `target` | Directory in which to create the governance layer. |
| `--name NAME` | Required human-readable project name. |
| `--slug SLUG` | Optional machine-friendly slug; derived when omitted. |
| `--profile PROFILE` | A built-in preset. Omit it for the generic core. |
| `--profile-file FILE` | A custom JSON profile extending generic or a preset. |
| `--force` | Replace an existing governance layer. This discards those documents. |
| `--json` | Emit a machine-readable result. |

## `chartworkai check`

```bash
chartworkai check .
chartworkai check . --strict --json
```

| Option | Meaning |
|---|---|
| `path` | Project root; defaults to the current directory. |
| `--json` | Emit machine-readable findings for CI and agents. |
| `--strict` | Treat warnings as failures. |
| `--quiet` | Show only warnings and failures. |
| `--self-audit` | Audit ChartworkAI itself. Do not use this for consumer projects. |

The checker is the definition of a healthy installation. It never executes validation commands declared by a custom profile.

## `chartworkai plan`

Regenerate `docs/phase_plan.md` from current repository state:

```bash
chartworkai plan .
chartworkai plan . --json
```

## `chartworkai state`

Read the current phase, task queue, blockers, and recent governance records as JSON:

```bash
chartworkai state .
```

## `chartworkai mcp`

Run a local Model Context Protocol server over standard input and output:

```bash
chartworkai mcp
```

Configure an MCP-compatible assistant to launch that command. It exposes health, project state, explicit decision filing, and handoff filing without moving project memory into a hosted service.

```json
{
  "mcpServers": {
    "chartworkai": {
      "command": "chartworkai",
      "args": ["mcp"]
    }
  }
}
```

## Exit behavior

Commands return a non-zero status when an operation fails. `check --strict` also returns non-zero when the project has warnings, making it suitable for a protected CI gate.
