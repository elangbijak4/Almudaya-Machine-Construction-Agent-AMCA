# Definition of Done — AMCA Waterfall Gates

A phase is **not done** merely because its files exist or an agent reports completion. All four layers below must be satisfied.

## 1. Deliverable completeness
- Every deliverable path listed for the phase in `orchestration.yaml` exists.
- Documents contain the required content, decisions, and unresolved issues.
- The traceability matrix is updated where requirements, design, code, or tests change.

## 2. Exit criteria and evidence
- Every exit criterion is recorded as `complete` in `workflow/gate-records.yaml`.
- Every criterion has an evidence path that exists inside the repository and a concise evidence summary.
- Evidence is real and inspectable. Planned tests, generated placeholders, and unsupported claims are not evidence of successful execution.
- `not_applicable` is not an automatic pass; use requires an explicit change request and human review. The validator currently blocks it as a completion state.

## 3. Automated gate validation
- Run `python tools/validate_workflow.py --check-scaffold`.
- Run `python tools/validate_workflow.py --phase Pn` for the phase under review.
- The phase-gate command must return exit code `0` before a transition is considered ready.
- For P4 and later, evidence must include actual test/code artifacts. For P5, record actual test command, environment, output, failures, and known limitations.

## 4. Human approval and transition
- The project owner reviews deliverables and evidence.
- The owner records `approval_status: approved`, `approved_by`, `approved_at` (YYYY-MM-DD), and `decision_evidence` in `workflow/gate-records.yaml`.
- The owner updates the phase status in `orchestration.yaml` and `docs/phase-status.md` consistently, and records the transition in the phase transition log.
- The next phase remains blocked until all dependencies are approved.

## Release acceptance gate (P6)
Release is permitted only if all conditions are true:
1. P0–P5 have approved transition records.
2. The baseline graph constructs successfully from a documented YAML specification.
3. An independent verifier accepts a valid graph and rejects malformed, cyclic, unknown-component, and missing-dependency cases.
4. The runtime executes only allowlisted components and refuses unverified graphs.
5. Automated tests have actually run; the report includes command, environment, result, and test output/evidence path.
6. Reproduction instructions work in a clean environment or any deviation is explicitly recorded.
7. Traceability and known limitations are complete.
8. P6 exit criteria have evidence and explicit owner approval.

A validator pass is a workflow-integrity signal only. It is not a formal proof of correctness, a security certification, or evidence that the underlying research theory is established.
