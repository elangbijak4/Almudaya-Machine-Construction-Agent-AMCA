# CR-001 / P4 Extension — Agent Authoring UI Implementation Review

**Status:** `AWAITING_APPROVAL` for the implementation extension review. The previously accepted P0–P6 baseline remains recorded separately; this extension has not yet completed its post-change P5/P6 review.

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

## Implementation and files

- `app.py` — Streamlit interface and local verification/run flow.
- `src/amca_agent/provider.py` — Gemini, xAI/Grok, and OpenAI API calls with a system prompt constraining output to the AMCA schema and allowlist.
- `src/amca_agent/graph.py` — Graphviz DOT rendering from verified candidate IDs and edges.
- `src/amca_agent/artifacts.py` — local chat/version and per-run evidence persistence.
- `requirements-app.txt` — optional app dependencies.
- `README.md`, `CHANGELOG.md`, and `docs/change-control.md` — usage, limitations, and CR-001 record.

The configured model names can be edited in the UI. Provider endpoints follow their documented REST interfaces: [Gemini `generateContent`](https://ai.google.dev/api/generate-content), [xAI chat completions](https://docs.x.ai/developers/rest-api-reference/inference/chat-completions), and [OpenAI chat completions](https://platform.openai.com/docs/api-reference/chat/create). Model availability depends on the account and can change.

## Evidence collected

Environment: Windows, CPython 3.12.14, PyYAML 6.0.3, Streamlit 1.66.1 in `.venv-app`.

- `python -m compileall -q app.py src/amca_agent` — passed.
- `python -m pip check` — passed, no broken requirements.
- Streamlit server started at `http://localhost:8501`; `GET /_stcore/health` returned HTTP 200 `ok`.
- Manually exercised the real UI using `examples/valid_parallel_analysis.yaml`: AMCA validation showed `VERIFIED`, the six-node/six-edge DAG rendered, explicit run approval was required, and the actual runtime succeeded with `characters=20; words=4`.
- Run artifacts are in `artifacts/runs/20261022T134141293951Z/`: `machine.yaml`, `candidate-graph.json`, `machine-dag.dot`, `verification-report.json`, `execution-record.json`, and `manifest.json`.
- Existing unit/integration/security/E2E suite was not rerun after the extension. The previously accepted baseline recorded 69 passing tests; that result is not evidence for this new UI.
- Live model generation/revision was not exercised because no provider API key was supplied. The provider adapters still require a P5 verification pass, including provider error handling and validation of generated output.

## Risks and limitations

- Generation and revision send the problem statement, bounded recent chat, and current YAML to the selected external provider. Use only data appropriate to transmit there.
- Chat messages and YAML versions persist locally under `artifacts/agent_sessions/`; API keys are not persisted.
- The agent can only describe arrangements of the six built-in components. It cannot implement new component code or create a persistent general-purpose agent.
- Model-generated YAML is nondeterministic and may be invalid or fail to express the user's intent. The UI does not automatically repair after validation failure; the user can revise via chat.
- The UI has been smoke-checked with the built-in reference YAML, but no browser automation or full extension regression suite has been run yet.
- Localhost UI is intended for a single local user; authentication, multi-user storage, and remote deployment are not included.

## P4 extension review decision

**Recommendation:** APPROVE the implementation extension for progression to P5 extension verification, with the risks and evidence limits above.

**Approval question:** Do you approve the CR-001 P4 implementation extension as documented here, including the local agent UI, AI-provider boundary, YAML revision workflow, explicit runtime gate, DAG display, and the stated limitations? Reply **APPROVE P4-EXT** or **REVISE P4-EXT**.
