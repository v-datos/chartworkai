# Integration: {{TRACKER_NAME}} sync

**Direction:** repo → {{TRACKER_NAME}} (one-way mirror). `TASKS.md` / `STATUS.md` are canonical.
**Synced:** {{what is mirrored — e.g. each TASKS item to a tracker task; the latest STATUS entry to a tracker doc/comment}}.
**Trigger:** {{manual `scripts/sync_tracker.sh`, or a hook on edits to TASKS.md / STATUS.md}}.
**Auth:** token from `{{ENV_VAR_NAME}}` (never committed).
**ID mapping:** {{how repo IDs map to tracker IDs — e.g. T-### to a tracker custom field}}.

## Notes

- The tracker is a **read-only mirror**. Make changes in the repo and sync them out; never edit the tracker expecting it to flow back.
- Do **not** place these instructions in `AGENTS.md` or `PROJECT_CHARTER.md` — they live here, in `docs/integrations/`.
