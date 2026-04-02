# PRD: Cursor 2.6.22 Reverse Engineering

## Objective

Replicate the proven `2.3.41` workflow on `2.6.22` so protocol, auth headers,
stream framing, and tool-call behaviors can be mapped with the same rigor and
artifact quality.

## Scope

- Bootstrap a dedicated reverse-engineering track at `reveng_2.6.22/`.
- Preserve `2.3.41` artifacts unchanged as a comparison baseline.
- Re-run the same discovery sequence used in prior commits and backlog work.
- Keep findings and implementation tasks linked to backlog task IDs.

## Out of Scope

- Rewriting historical `2.3.41` analyses.
- Deleting legacy tools or old scripts before parity is confirmed.

## Inputs

- Git history in this repo (workflow progression from prototype to agent tools).
- Existing backlog framework and task templates.
- Existing analysis corpus in `reveng_2.3.41/analysis/`.
- AppImage binary: `Cursor-2.6.22-x86_64.AppImage`.

## Playbook (Same As 2.3.41)

1. **Bootstrap artifacts**
   - Copy AppImage into workspace.
   - Extract filesystem.
   - Capture core JS bundles and `product.json`.
2. **Baseline protocol parity**
   - Confirm version/commit metadata.
   - Validate core endpoints and required headers.
   - Reproduce minimal models/chat calls.
3. **Streaming and framing**
   - Validate envelope framing and compression behavior.
   - Confirm decoder compatibility or isolate deltas.
4. **Agent/tool path**
   - Re-verify bidi flow and tool-call schemas.
   - Track enum/schema drift from `2.3.41`.
5. **Deep dives via backlog**
   - Create targeted tasks for each discovered delta.
   - Keep references in `reveng_2.6.22/analysis/TASK-*.md`.

## Deliverables

- `reveng_2.6.22/original/*` core artifacts.
- `reveng_2.6.22/FINDINGS.md` with version-specific deltas.
- New backlog kickoff tasks (`TASK-302+`) for the 2.6 track.

## Success Criteria

- `2.6.22` core artifacts are extracted and versioned in workspace.
- Backlog has explicit tasks for kickoff, diffing, and protocol verification.
- Findings can be compared side-by-side with `2.3.41` analyses.
