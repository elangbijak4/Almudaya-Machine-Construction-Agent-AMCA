# Change Control

## Approved change record

- **Change ID:** CR-001
- **Date:** 2026-10-22
- **Requester:** Project owner (explicit request in project conversation)
- **Affected phase/document:** Post-P6 scope extension; P1–P4 requirements/design/implementation records and P5–P6 evaluation/handover
- **Current approved baseline:** Local CLI PoC accepts user-authored YAML for the fixed allowlisted DAG runtime; no LLM/API or GUI dependency.
- **Proposed change:** Add a separate optional Streamlit agent UI that generates/revises YAML through a configured model API, supports example selection and chat iteration, validates every candidate with the existing verifier, requires explicit user confirmation to execute, and persists/display DAG and run artifacts locally.
- **Reason and evidence:** Project owner requested the conversational machine-authoring workflow and a visible DAG/run artifact experience.
- **Impact:** Adds a GUI dependency and optional external model calls; extends data handling to locally persist user chat/YAML; leaves the AMCA runtime allowlist, graph schema, verifier, and execution semantics unchanged.
- **Earlier phases to reopen:** P1 requirements, P2 architecture, P3 contracts/test plan, P4 implementation; P5 verification and P6 handover need an extension review after implementation.
- **Decision:** Approved by explicit project-owner implementation request; 2026-10-22.
- **Decision maker/date:** Project owner / 2026-10-22.
- **Follow-up actions:** Implemented. Extension requirements, security boundaries, setup, artifacts, evidence and limitations are in `docs/11-agent-web-extension-review.md`; P4 extension review awaits owner approval before formal P5 extension verification.

Use this process when changing scope, requirements, architecture, dependencies, acceptance criteria, or the runtime trust model.

## Change request template

- **Change ID:** CR-XXX
- **Date:** [YYYY-MM-DD]
- **Requester:** [Role]
- **Affected phase/document:** [IDs and paths]
- **Current approved baseline:** [Description]
- **Proposed change:** [Description]
- **Reason and evidence:** [Why it is needed]
- **Impact:** [Requirements, design, code, tests, security, schedule]
- **Earlier phases to reopen:** [P0/P1/P2/P3...]
- **Decision:** [Pending/Approved/Rejected]
- **Decision maker/date:** [Pending]
- **Follow-up actions:** [Pending]

## Rules

1. Do not silently modify approved requirements or architecture.
2. A change affecting an earlier phase reopens that phase and dependent review steps as needed.
3. Update `orchestration.yaml`, `phase-status.md`, and `traceability-matrix.md` after approval.
4. Keep a short rationale and evidence trail.
