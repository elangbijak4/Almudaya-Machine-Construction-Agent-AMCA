# P3 — Implementation Plan and Contracts

**Status:** Prepared; awaiting project-owner approval  
**Design baseline:** P2 approved 2026-10-22

## 1. Implementation boundary

Implement the local Python 3.12+ offline PoC from the approved P1/P2 requirements and contracts. Build a deterministic declarative graph constructor, independent structural/interface verifier, fixed six-component registry, sequential scheduler, bounded runtime, CLI, and machine-readable reports. Do not introduce LLMs, network calls, arbitrary plugin loading, shell execution, telemetry, or runtime dependencies beyond the declared PyYAML requirement without an approved change request.

No implementation begins until P3 is approved. P4 implements the tasks below in order and records deviations through change control.

## 2. Planned repository layout

```text
src/amca/
  __init__.py          public package/version
  cli.py               CLI parsing, command dispatch, exit codes
  errors.py            typed AMCA error categories
  models.py            immutable spec, graph, verification, execution models
  canonical.py         JSON-compatible normalization and SHA-256 helpers
  specification.py     bounded UTF-8/YAML load, duplicate-key rejection
  schema.py            strict field/value validation for spec/report contracts
  registry.py          immutable component and port registry
  constructor.py       deterministic candidate construction/normalization
  verifier.py          independent checks and status derivation
  scheduler.py         deterministic topological order
  runtime.py           admission, component dispatch, state/error handling
  reporting.py         canonical JSON reports and bounded evidence
tests/
  unit/                isolated model, parser, validator, registry, scheduler tests
  integration/         constructor/verifier/runtime/report interaction
  e2e/                 valid reference graph, negative graph, reproducibility
  security/            untrusted-data and no-dynamic-execution checks
schemas/
  task-spec.schema.yaml
  graph.schema.yaml
  verification-report.schema.yaml
  execution-record.schema.yaml
examples/
  valid_parallel_analysis.yaml
  invalid_missing_dependency.yaml
```

`setup.cfg`/`pyproject.toml` packaging is not required for the PoC. From the repository root, set `PYTHONPATH=src` (PowerShell: `$env:PYTHONPATH = "src"`) and invoke `python -m amca.cli`. This avoids adding a build backend dependency. P4 must confirm exact CLI flags before documentation is finalized.

## 3. Module interfaces and invariants

| Module | Public contract | Must not do |
|---|---|---|
| `specification.py` | `load_spec(path_or_bytes) -> MachineSpec`; raises categorized `InputError` | Import task-selected modules or execute YAML values |
| `schema.py` | `validate_spec(value) -> MachineSpec`; exact fields/types/ranges/config | Modify input silently or accept unknown fields |
| `canonical.py` | `canonical_json(value) -> bytes`; `sha256(value) -> str` | Include volatile metadata in content digests |
| `registry.py` | immutable `get_component(component_id)` / registry profile | Accept runtime registration from spec or CLI |
| `constructor.py` | `construct(spec) -> CandidateGraph` | Verify itself or create executable code |
| `verifier.py` | `verify(candidate, registry) -> VerificationReport` | Call component implementations or trust constructor status |
| `scheduler.py` | `topological_order(candidate) -> tuple[node_id, ...]` | Execute nodes or choose nondeterministic tie order |
| `runtime.py` | `run(candidate, report, inputs) -> ExecutionRecord` | Dispatch if admission is not exactly verified/bound |
| `reporting.py` | stable serialization and safe summaries | Emit raw secrets, unbounded payloads, tracebacks |
| `cli.py` | validate/construct/verify/run/report commands with stable exit contract | Bypass public validation or runtime admission |

Use immutable dataclasses or equivalent explicit models. Normalize to JSON-compatible data at boundaries. Catch expected errors into stable categories; unexpected errors fail closed. Validate all external inputs before component execution.

## 4. Registry behavior contracts

| Component | Required config | Input/output behavior to implement |
|---|---|---|
| `input_source` | `{input_key: <identifier>}` | Reads exactly one supplied string value and emits `text`; no incoming edge. |
| `validate_text` | `{}` | Reject blank text; strips outer whitespace; emits `text`. |
| `analysis_a` | `{}` | Emits exactly `finding: {character_count: N}`, where N is Python Unicode code-point length of the validated text. |
| `analysis_b` | `{}` | Emits exactly `finding: {word_count: N}`, where N is the number of nonempty tokens from Unicode-aware `str.split()` on validated text. |
| `aggregate_results` | `{}` | Requires both finding objects with nonnegative integer counts; emits exactly `summary: "characters=N; words=M"` in that key order. |
| `generate_report` | `{}` | Emits exactly `report: {summary: <same string>}`. |

For input text `AMCA builds a graph.`, the output is exactly `{"summary":"characters=20; words=4"}`. This fixes transparent, distinct branch behaviors and the acceptance fixture before implementation. Any semantic change requires change control. All built-ins must be pure, offline, deterministic, and obey P2 size limits.

## 5. Implementation work breakdown

1. Create package, typed errors, immutable models, and canonicalization; add focused unit tests.
2. Implement strict YAML loading, duplicate-key/alias/multi-document rejection, size guards, schemas, and parser tests.
3. Implement the six-item immutable registry and component config/port metadata; test unknown IDs and contract inventory.
4. Implement deterministic constructor and candidate identity; assert exact reference nodes/edges/digests.
5. Implement independent verifier in stable check order; cover every check and each report status.
6. Implement deterministic topological scheduler and ordering/boundary/cycle tests.
7. Implement runtime digest/profile admission, bounded dispatch, upstream failure propagation, and output validation; assert zero invocations for refused candidates.
8. Implement report/evidence serialization and CLI commands/exit codes; add CLI and integration tests.
9. Exercise examples end-to-end, update actual implementation record, requirements-to-code/test traceability, and setup instructions.

## 6. Dependency and environment policy

- Supported baseline: CPython 3.12 or newer; P4/P5 record the exact executable/platform used.
- Runtime/parser dependency: `PyYAML>=6.0,<7.0` in `requirements-dev.txt` is the only declared third-party dependency at this stage.
- Use Python standard library for dataclasses, graph traversal, hashing, JSON, CLI, and unittest.
- No schema validation library, packaging backend, hosted service, API key, or network access at runtime. Implement the approved schema/contract checks directly in `schema.py` and test against the machine-readable schema files and examples.
- Clean environment instructions: create a venv, install `-r requirements-dev.txt`, set `PYTHONPATH=src`, run CLI and unittest discovery. P4/P5 records actual commands and results; do not claim clean-environment reproducibility before the run occurs.

## 7. Release and acceptance procedure

1. Implement only after P3 approval; record code and tests in `docs/08-implementation-record.md`.
2. P4 review requires source, examples, unit/integration tests, and actual test command evidence; no P5 acceptance claim is made.
3. After P4 owner approval, run the P5 full suite: structural/static, unit, negative/adversarial, integration, end-to-end, and clean-environment reproduction as defined in `docs/07-test-and-validation-plan.md`.
4. Update the traceability matrix with source paths and actual test evidence, summarize failures and fixes, and run the phase gate.
5. Submit P5 for explicit approval. After approval only, prepare P6 handover, release limitations, evidence, and final acceptance request.
6. No commit, push, publication, or external disclosure is implied by phase approval.

## 8. P3 approval package

**Objective:** Make implementation executable as a planned task sequence with explicit module/API boundaries, schemas/examples, tests, setup, and release steps.

| Criterion | Evidence | Prepared status |
|---|---|---|
| P3-EC1 — Module/file plan and implementation order are explicit. | Sections 2–6 | Complete for owner review |
| P3-EC2 — Positive, negative, boundary, integration, and end-to-end cases are defined. | `docs/07-test-and-validation-plan.md` | Complete for owner review |
| P3-EC3 — Requirements map to design, planned code modules, and tests. | `docs/traceability-matrix.md` | Complete for owner review |

**Recommendation:** APPROVE P3. This authorizes moving to P4 implementation only after explicit owner approval.

**Approval record:** Decision [Pending]; reviewer [Pending]; date [Pending].
