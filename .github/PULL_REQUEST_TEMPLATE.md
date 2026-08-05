## Summary

- 

## Framework Impact

- [ ] Updates templates, prompts, agents, scripts, or docs intentionally.
- [ ] Keeps `framework.json` current if files/version changed.
- [ ] Generated scaffold passes `scripts/check_framework_compliance.sh`.

## Verification

```bash
sh -n scripts/check_framework_compliance.sh
sh -n scripts/init_project_from_framework.sh
scripts/init_project_from_framework.sh /tmp/awf-example "Example Project" example_project
scripts/check_framework_compliance.sh /tmp/awf-example
```
