# CR-001 / P4 Extension — Agent Authoring UI Implementation Review

**Status:** `AWAITING_APPROVAL` for the implementation extension review. At the owner's request, a local regression and reproducibility pass has since been run and recorded in `docs/evidence/cr-001-retest-2026-10-22.md`; this does not record formal P4-EXT approval or close the later P5/P6 approval gates. The previously accepted P0–P6 baseline remains recorded separately.

## Objective and change

Add an optional local web application that lets a user describe a machine in natural language, request YAML from a selectable model provider, revise the YAML through the same chat session, choose existing YAML examples, inspect validation results and a DAG visualization, and explicitly approve execution through the existing AMCA runtime.

The owner explicitly requested this extension on 2026-10-22. The runtime component registry, YAML schema, verifier, scheduler, and execution semantics remain the authority for what can run.

## Extension requirements and implementation mapping

| ID | Acceptance criterion | Implementation |
|---|---|---|
| CR-UI-01 | User can choose an example YAML or enter a problem statement and ask an AI provider for a candidate | `app.py`, `src/amca_agent/provider.py` |
| CR-UI-02 | User can request revisions in the same chat; each returned YAML is a separately numbered version, stored locally and recoverable | `app.py`, `src/amca_agent/artifacts.py` |
| CR-UI-03 | Every candidate goes through the existing YAML loader, constructor, and verifier; invalid candidates cannot be run | `app.py` calls `load_spec`, `construct`, `verify_candidate`, `run` |
| CR-UI-04 | User sees a DAG visualization and can download its source | `src/amca_agent/graph.py`, `st.graphviz_chart` in `app.py` |
| CR-UI-05 | Execution requires a verified candidate and an explicit user confirmation control | `app.py` gates runtime on verification status and checkbox |
| CR-UI-06 | A local run folder persists YAML, graph, verification, and (after run) execution evidence, all viewable/downloadable in the UI | `src/amca_agent/artifacts.py`, artifact browser in `app.py` |
| CR-UI-07 | API credentials are never written to persisted artifacts | `src/amca_agent/provider.py` and `artifacts.py`; key is passed in memory only |
| CR-UI-08 | Base CLI setup stays independent of Streamlit | `requirements-app.txt` adds the optional GUI dependency without changing `requirements-dev.txt` |
| CR-UI-09 | CLI offers a scriptable and interactive counterpart for examples, AI YAML authoring/revisions, version restore, validation, DAG export, execution, sessions, and artifacts | `src/amca_agent/cli.py`; integration tests in `tests/integration/test_agent_cli.py` |

## Implementation and files

- `app.py` — Streamlit interface and local verification/run flow.
- `src/amca_agent/provider.py` — Gemini, xAI/Grok, and OpenAI API calls with a system prompt constraining output to the AMCA schema and allowlist.
- `src/amca_agent/graph.py` — Graphviz DOT rendering from verified candidate IDs and edges.
- `src/amca_agent/artifacts.py` — local chat/version and per-run evidence persistence.
- `requirements-app.txt` — optional app dependencies, including Streamlit chart support for the DAG view.
- `src/amca_agent/cli.py` — feature-complete command interface and approval-gated interactive run flow.
- `README.md`, `CHANGELOG.md`, and `docs/change-control.md` — usage, limitations, and CR-001 record.

The configured model names can be edited in the UI. Provider endpoints follow their documented REST interfaces: [Gemini `generateContent`](https://ai.google.dev/api/generate-content), [xAI chat completions](https://docs.x.ai/developers/rest-api-reference/inference/chat-completions), and [OpenAI chat completions](https://platform.openai.com/docs/api-reference/chat/create). Model availability depends on the account and can change.

## Evidence collected

Environment: Windows, CPython 3.12.10, PyYAML 6.0.3, Streamlit 1.66.1, Graphviz Python package 0.21 in a clean `.venv-retest` environment.

- `python -m compileall -q app.py src/amca src/amca_agent` — passed.
- `python -m pip check` — passed, no broken requirements.
- Streamlit server health check: `GET http://localhost:8501/_stcore/health` returned HTTP 200 `ok`.
- Streamlit `AppTest` exercised example loading, YAML validation, DAG display, approval checkbox, and real local runtime execution; output included `characters=20; words=4`.
- New agent CLI integration tests exercise examples, validation/rejection, Graphviz export, execution evidence, chat revision, version listing/restore, manual YAML load, session reload, and explicit run approval.
- Provider adapter tests mock Gemini, xAI, and OpenAI-compatible responses, check request construction/fence stripping, and ensure surfaced HTTP errors do not expose credentials. No live provider request was made.
- Complete suite after this extension: 77 tests passed, 0 failed, 0 errors, 0 skipped (including optional Streamlit AppTest). Detailed commands and output summary: `docs/evidence/cr-001-retest-2026-10-22.md`.
- `requirements-app.txt` includes `streamlit[charts]` because the installed Streamlit API documents the `graphviz` package as a requirement for `st.graphviz_chart`.
- Run artifacts are in `artifacts/runs/20261022T134141293951Z/`: `machine.yaml`, `candidate-graph.json`, `machine-dag.dot`, `verification-report.json`, `execution-record.json`, and `manifest.json`.
- The first AppTest run exposed an unsupported `alt` keyword on `st.graphviz_chart`; it was removed, and the GUI path now passes AppTest.
- Live model generation/revision was not exercised because no provider API key was supplied. Mocked adapter checks do not establish current provider model availability or live account access.

## Risks and limitations

- Generation and revision send the problem statement, bounded recent chat, and current YAML to the selected external provider. Use only data appropriate to transmit there.
- Chat messages and YAML versions persist locally under `artifacts/agent_sessions/`; API keys are not persisted.
- The agent can only describe arrangements of the six built-in components. It cannot implement new component code or create a persistent general-purpose agent.
- Model-generated YAML is nondeterministic and may be invalid or fail to express the user's intent. The UI does not automatically repair after validation failure; the user can revise via chat.
- The UI test uses Streamlit's in-process AppTest; it does not replace a cross-browser deployment test.
- Localhost UI is intended for a single local user; authentication, multi-user storage, and remote deployment are not included.

## P4 extension review decision

**Recommendation:** APPROVE the implementation extension for progression to P5 extension verification, with the risks and evidence limits above.

**Approval question:** Do you approve the CR-001 P4 implementation extension as documented here, including the local agent UI, AI-provider boundary, YAML revision workflow, explicit runtime gate, DAG display, and the stated limitations? Reply **APPROVE P4-EXT** or **REVISE P4-EXT**.
