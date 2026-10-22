# Workflow Governance

- `gate-records.yaml` is the authoritative register for per-criterion evidence and human phase approvals.
- `../tools/validate_workflow.py --check-scaffold` checks required paths, criterion-ID parity, project/version consistency, and phase-status references.
- `../tools/validate_workflow.py --phase Pn` evaluates a phase gate and returns a nonzero exit code until all criteria have evidence and the project owner has explicitly approved the phase.

Never approve a phase automatically merely because validation ran. Approval must be based on a human review of actual evidence.
