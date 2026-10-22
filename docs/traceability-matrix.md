# Requirements Traceability Matrix

**Status:** P5 verification mapping and evidence completed; owner approval pending.  
**Requirement baseline:** [docs/01-requirements-specification.md](01-requirements-specification.md)

| Requirement | Design | Implemented source | Current test/evidence | Status |
|---|---|---|---|---|
| FR-01 | `docs/03-data-model-and-yaml-schemas.md` | `src/amca/specification.py`, `src/amca/models.py` | `tests/unit/test_specification.py`; `tests/unit/test_schema.py` | Implemented; P5 full suite passed (68/68; see docs/evidence/p5-unittest-rerun.txt) |
| FR-02 | `docs/03-data-model-and-yaml-schemas.md` | `src/amca/schema.py` | `tests/unit/test_schema.py`; `tests/unit/test_limits.py` | Implemented; P5 full suite passed (68/68; see docs/evidence/p5-unittest-rerun.txt) |
| FR-03 | `docs/02-system-architecture.md` | `src/amca/constructor.py` | `tests/unit/test_constructor.py`; `tests/e2e/test_cli_reference.py` | Implemented; P5 full suite passed (68/68; see docs/evidence/p5-unittest-rerun.txt) |
| FR-04 | `docs/03-data-model-and-yaml-schemas.md` | `src/amca/constructor.py`, `src/amca/models.py` | `tests/unit/test_constructor.py`; `tests/unit/test_verifier.py` | Implemented; P5 full suite passed (68/68; see docs/evidence/p5-unittest-rerun.txt) |
| FR-05 | `docs/04-verification-design.md` | `src/amca/verifier.py`, `src/amca/scheduler.py` | `tests/unit/test_verifier.py`; `tests/unit/test_scheduler.py` | Implemented; P5 full suite passed (68/68; see docs/evidence/p5-unittest-rerun.txt) |
| FR-06 | `docs/03-data-model-and-yaml-schemas.md`, `docs/04-verification-design.md` | `src/amca/registry.py`, `src/amca/verifier.py` | `tests/unit/test_registry.py`; `tests/unit/test_verifier.py` | Implemented; P5 full suite passed (68/68; see docs/evidence/p5-unittest-rerun.txt) |
| FR-07 | `docs/05-runtime-and-execution-design.md` | `src/amca/runtime.py`, `src/amca/registry.py`, `src/amca/scheduler.py` | `tests/integration/test_runtime_admission.py`; `tests/unit/test_scheduler.py` | Implemented; P5 full suite passed (68/68; see docs/evidence/p5-unittest-rerun.txt) |
| FR-08 | `docs/03-data-model-and-yaml-schemas.md`, `docs/04-verification-design.md` | `src/amca/models.py`, `src/amca/reporting.py` | `tests/unit/test_reporting.py`; `tests/integration/test_runtime_admission.py` | Implemented; P5 full suite passed (68/68; see docs/evidence/p5-unittest-rerun.txt) |
| FR-09 | `docs/03-data-model-and-yaml-schemas.md`, `docs/05-runtime-and-execution-design.md` | `src/amca/reporting.py`, `src/amca/canonical.py` | `tests/integration/test_evidence.py` | Implemented; P5 full suite passed (68/68; see docs/evidence/p5-unittest-rerun.txt) |
| FR-10 | `docs/04-verification-design.md`, `docs/05-runtime-and-execution-design.md` | `src/amca/runtime.py`, `src/amca/verifier.py` | `tests/integration/test_runtime_admission.py`; `tests/e2e/test_cli_reference.py` | Implemented; P5 full suite passed (68/68; see docs/evidence/p5-unittest-rerun.txt) |
| NFR-01 | `docs/02-system-architecture.md` | `src/amca/canonical.py`, `src/amca/scheduler.py`, `src/amca/reporting.py` | `tests/integration/test_evidence.py`; `tests/unit/test_canonical.py` | Implemented; P5 full suite passed (68/68; see docs/evidence/p5-unittest-rerun.txt) |
| NFR-02 | `docs/05-runtime-and-execution-design.md` | `src/amca/registry.py`, `src/amca/runtime.py`, `src/amca/specification.py` | `tests/security/test_untrusted_spec.py`; source review | P5 source scan/security tests passed; not a security certification |
| NFR-03 | `docs/04-verification-design.md` | `src/amca/models.py`, `src/amca/reporting.py` | `tests/unit/test_reporting.py`; `tests/unit/test_verifier.py` | Implemented; P5 full suite passed (68/68; see docs/evidence/p5-unittest-rerun.txt) |
| NFR-04 | `docs/06-implementation-plan.md`, `docs/07-test-and-validation-plan.md` | `requirements-dev.txt`, `src/amca/cli.py`, `README.md` | `docs/evidence/p5-static-and-reproducibility.txt`; `docs/evidence/p5-unittest-rerun.txt` | Clean venv reproduction passed with bundled CPython fallback |
| NFR-05 | `docs/02-system-architecture.md`, `docs/06-implementation-plan.md` | `src/amca/*.py` | `compileall`; test suite; code review | P5 compile and full suite passed |
| NFR-06 | `docs/03-data-model-and-yaml-schemas.md`, `docs/05-runtime-and-execution-design.md` | `src/amca/specification.py`, `src/amca/schema.py`, `src/amca/runtime.py` | `tests/unit/test_limits.py`; `tests/integration/test_runtime_admission.py` | Implemented; tested boundaries passed |
| NFR-07 | `docs/02-system-architecture.md`, `docs/06-implementation-plan.md` | `requirements-dev.txt`; `src/amca/*.py` | dependency/source review; `docs/evidence/p5-static-and-reproducibility.txt` | Clean-environment dependency and full-suite checks passed; no external services used |
| NFR-08 | `docs/04-verification-design.md`, `docs/05-runtime-and-execution-design.md` | `src/amca/errors.py`, `src/amca/cli.py`, `src/amca/reporting.py` | `tests/e2e/test_cli_reference.py`; `tests/unit/test_reporting.py` | Implemented; P5 full suite passed (68/68; see docs/evidence/p5-unittest-rerun.txt) |

P5 verification evidence is in `docs/09-verification-report.md` and `docs/evidence/`. The final acceptance and release handover review remains P6 work.

