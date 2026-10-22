# P4 — Implementation Record

**Status:** Implemented; submitted for P4 owner review. P5 has not started.  
**Implementation baseline:** approved P1 requirements and P2 architecture, using P3 contracts and plans.

## 1. Environment and setup

- Host: Windows, PowerShell; no Git metadata is present in this directory.
- Interpreter: bundled CPython 3.12.14 at `C:\Users\HP\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`.
- Runtime dependency: PyYAML 6.0.3, matching `requirements-dev.txt` (`PyYAML>=6.0,<7.0`). For this phase it was installed in the temporary workspace-local `.amca-p4-deps` directory; this temporary directory is removed after the checks.
- Test import path: `PYTHONPATH=src;.amca-p4-deps`.
- Documented developer setup remains a CPython 3.12+ venv and `pip install -r requirements-dev.txt`; a fresh clean-venv installation has not been performed and is reserved for P5 reproducibility verification.

## 2. Implemented modules

| Module | Implementation | Main evidence |
|---|---|---|
| `models.py`, `errors.py` | Typed graph, verification, execution, and diagnostic records; stable error categories | `tests/unit/test_schema.py`, `tests/unit/test_reporting.py` |
| `specification.py`, `schema.py` | Bounded strict YAML loading and specification validation; rejects duplicate keys, aliases, custom tags, extra fields, invalid values, and unsupported components | `tests/unit/test_specification.py`, `tests/unit/test_schema.py`, `tests/unit/test_limits.py` |
| `canonical.py`, `constructor.py` | Canonical JSON-compatible encoding, deterministic graph construction, and SHA-256 identity | `tests/unit/test_canonical.py`, `tests/unit/test_constructor.py` |
| `registry.py` | Six project-owned built-in components with explicit contracts and allowlisted dispatch | `tests/unit/test_registry.py` |
| `scheduler.py` | Deterministic topological ordering with cycle rejection | `tests/unit/test_scheduler.py` |
| `verifier.py` | Ordered independent structural, dependency, interface, bounds, registry-profile, and digest checks; derives `verified`, `rejected`, or `inconclusive` | `tests/unit/test_verifier.py` |
| `runtime.py`, `pipeline.py` | Fresh verification admission, verification/candidate binding, bounded execution, fail-fast dependency propagation, and run coordination | `tests/integration/test_runtime_admission.py`, `tests/integration/test_evidence.py` |
| `reporting.py`, `cli.py` | Structured JSON evidence, safe derived summaries, and `validate`, `verify`, `run`, and `report` commands | `tests/unit/test_reporting.py`, `tests/e2e/test_cli_reference.py` |

The reference pipeline is `Input → Validate → Analysis A / Analysis B → Aggregate → Report`. Analysis A counts Unicode code points; Analysis B counts whitespace-separated words. The reference input yields `characters=20; words=4`. Execution is deterministic and sequential; the branches are logically independent but not run concurrently.

## 3. Decisions and deviations

- Added an optional `safe_summary` to execution records and `refusal_reason` for pre-execution refusals. This is additive to the P2 evidence model and supports the P1 observability requirement while retaining the P2 redaction boundary. The execution-record schema and runtime design document describe these fields.
- Kept `requirements-dev.txt` unchanged. PyYAML was already the declared dependency; no new runtime package or network/API service was introduced.
- Used a bundled interpreter because Python was not available on PATH. The documented `py -3.12` setup therefore could not be executed on this host. P5 should reproduce with a clean environment or report the host limitation.
- No P1/P2 requirement or acceptance threshold was intentionally changed.

## 4. Test and check evidence

The latest executed test command and complete verbose output are recorded in `docs/evidence/p4-unittest.txt`.

| Command | Environment/date | Result | Evidence |
|---|---|---|---|
| `python -m unittest discover -s tests -p 'test_*.py' -v` (bundled interpreter; see `docs/phase-status.md` for exact executable) | CPython 3.12.14, PyYAML 6.0.3; 2026-10-22 | 67 tests, 67 passed, 0 failures, 0 errors, 0 skipped; exit 0 | `docs/evidence/p4-unittest.txt` |
| `python -m compileall -q src tests` | Same interpreter; 2026-10-22 | Passed; exit 0 | `docs/evidence/p4-workflow-checks.txt` |
| `python tools/validate_workflow.py --check-scaffold` | Same interpreter; 2026-10-22 | Passed; exit 0 | `docs/evidence/p4-workflow-checks.txt` |
| `python tools/validate_workflow.py --phase P3` | Same interpreter; 2026-10-22 | Passed; exit 0 | `docs/evidence/p4-workflow-checks.txt` |
| `python tools/validate_workflow.py --phase P4` | Same interpreter; 2026-10-22 | Blocked only because P4 lacks explicit owner approval fields; all criterion evidence is complete | `docs/evidence/p4-workflow-checks.txt` |

P4 tests include unit, integration, security-boundary, workflow, and CLI end-to-end coverage against the actual built-in registry/runtime. The P4 test run is not the P5 final acceptance report. The verified live CLI reference run and its generated temporary outputs were exercised during implementation; P5 will rerun and capture reproducibility evidence.

## 5. Security review and limitations

- Machine specifications are parsed as data; component resolution uses the fixed registry. Source tests check for dynamic execution/process-launch calls and prohibited import modules.
- Unknown components, invalid graphs, stale/forged verification evidence, and input/output limit violations fail closed before or during execution as applicable.
- This is not an OS sandbox. Built-ins are trusted in-process Python functions; there is no formal proof, security certification, or production-readiness claim.
- JSON Schema YAML files and examples are parseable, but were not checked against a JSON Schema meta-validator because no validator dependency is part of the approved dependency set.
- Clean venv installation, broader adversarial review, and final requirement-to-test acceptance review remain P5 work.

## 6. P4 exit review

- In-scope implementation: implemented for the approved bounded PoC; see module mapping above.
- Automated evidence: 67/67 tests passed in the recorded run; compile and scaffold checks passed.
- Security scope: fixed allowlist and strict data validation are implemented; limitations are explicit above.
- Known unresolved issues: clean-install reproduction and P5 acceptance evidence remain outstanding; P4 owner review and approval are pending.
- Recommendation: **APPROVE P4** if the owner accepts the implementation and limitations documented here.
