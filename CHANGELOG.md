# Changelog

## 0.2.0 — 2026-10-22

- Added executable workflow consistency and phase-gate validator.
- Added per-phase exit-criterion evidence and owner-approval register.
- Added Definition of Done and explicit final release acceptance gate.
- Required a human owner approval before each phase transition.
- Synchronized initial phase statuses across `orchestration.yaml` and `docs/phase-status.md`.
- Kept all phase approvals pending; this scaffold update does not approve P0 or claim implementation/test completion.

## 0.1.0 — Initial scaffold

- Established the AMCA Waterfall document structure, orchestration plan, and initial PoC scope.
# Unreleased

- Added an optional Streamlit web UI for AI-assisted YAML authoring and revision chat, reusing AMCA's verifier and allowlisted runtime.
- Added verified DAG visualization and locally persisted/downloadable YAML, graph, verification, and execution artifacts.
- Added optional Gemini, xAI/Grok, and OpenAI API adapters; API keys are not persisted.

