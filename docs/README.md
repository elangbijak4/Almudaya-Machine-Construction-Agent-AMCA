# AMCA Technical Document Tree

This document tree is the Waterfall deliverable chain. Documents are not merely reference notes: each one is a phase artifact and must be reviewed before the next phase begins.

## Document dependency sequence

```text
00-project-charter.md
  └── 01-requirements-specification.md
        └── 02-system-architecture.md
              ├── 03-data-model-and-yaml-schemas.md
              ├── 04-verification-design.md
              └── 05-runtime-and-execution-design.md
                    └── 06-implementation-plan.md
                          └── 07-test-and-validation-plan.md
                                └── 08-implementation-record.md
                                      └── 09-verification-report.md
                                            └── 10-release-and-evaluation.md
```

Cross-cutting control documents:
- `phase-status.md`: current phase, decisions, exit-criteria evidence, and blockers.
- `traceability-matrix.md`: requirement-to-design-to-code-to-test mapping.
- `change-control.md`: controlled changes and phase reopening.

## Waterfall rule

Do not fill every document speculatively and then implement. Start at P0, approve the charter, then produce and review P1, and continue in order. Later documents contain initial prompts and templates, not pre-approved design decisions.


## Workflow governance

- `definition-of-done.md` — mandatory completion and release criteria.
- `../workflow/gate-records.yaml` — criterion evidence and human approval records.
- `../tools/validate_workflow.py` — executable consistency and transition-gate validator.

Run `python tools/validate_workflow.py --check-scaffold` for consistency checks. A phase transition check intentionally fails until criteria evidence and human approval are recorded.
