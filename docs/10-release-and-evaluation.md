# P6 — Release, Evaluation, and Handover

**Status:** Final project acceptance approved by the project owner on 2026-10-22. No external release or publication has been made.  
**Prepared:** 2026-10-22

## 1. Release summary

- Project: AMCA PoC, runtime package version `0.1.0`; Waterfall scaffold `0.2.0`.
- Source revision: unavailable; this directory has no Git metadata or release tag.
- Maintainer: AMCA project owner (name not provided in the project record).
- Environment used for final clean setup: Windows PowerShell, bundled CPython 3.12.14, PyYAML 6.0.3.
- Final P6 acceptance rerun: 69 tests passed, 0 failures, 0 errors, 0 skips; `pip check` and `compileall` passed.
- This is a local PoC handover package. Formal release/acceptance remains subject to this final owner approval.

## 2. Reproducible setup and use

From the repository root in PowerShell, with CPython 3.12+ and network or a local PyYAML package cache available:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m amca.cli validate examples/valid_parallel_analysis.yaml
.\.venv\Scripts\python.exe -m amca.cli verify examples/valid_parallel_analysis.yaml
.\.venv\Scripts\python.exe -m amca.cli run examples/valid_parallel_analysis.yaml --inputs examples/reference-input.json --output run.json
.\.venv\Scripts\python.exe -m amca.cli report run.json
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

If the `py` launcher is unavailable, replace `py -3.12` with the full path to an installed CPython 3.12+ executable. This host used the bundled interpreter to create a fresh `.venv-p6`; the exact setup and dependency checks are recorded in `docs/evidence/p6-clean-setup.txt`. `PYTHONPATH=src` is required because the PoC intentionally has no packaging/build dependency.

The valid example should verify as `verified`, execute six nodes successfully in deterministic dependency order, and report `characters=20; words=4`. `examples/invalid_missing_dependency.yaml` should be rejected before any node executes. Additional saved run evidence is in `docs/evidence/p6-reference-run.json` and `docs/evidence/p6-invalid-run.json`.

### Troubleshooting

- **`py` or `python` is not found:** use the full path to CPython 3.12+ for the `-m venv` command, then use the environment's `.venv\Scripts\python.exe` for subsequent commands.
- **`No module named amca`:** run commands from the repository root and set `$env:PYTHONPATH = "src"` in the active PowerShell session.
- **PyYAML installation fails:** check access to the configured package index or use an approved local package cache for the already-declared `PyYAML>=6.0,<7.0` dependency; no other project dependency is required.
- **A phase gate is blocked:** run `python tools/validate_workflow.py --phase Pn`; the validator reports missing evidence or owner-approval fields. Tests cannot substitute for explicit approval.

## 3. Evaluation results

- Automated test set: P5 ran 68 tests with unit/integration/security/E2E/workflow breakdown in `docs/evidence/p5-category-runs.txt`. P6 added the phase-transition workflow assertion and reran the full suite: 69/69 passed. This is a bounded regression set, not a statistical sample of arbitrary machines.
- Valid construction/execution: the one approved six-node reference graph verified and executed successfully, with all six node records succeeded and the expected safe report summary.
- Negative acceptance: the missing dependency graph was rejected with verification `rejected`, runtime `refused`, and an empty node-record list. The automated suite covers additional cyclic, unknown-component, malformed, interface, boundary, and forged-evidence cases.
- Reproducibility: clean virtual-environment setup, dependency check, compile, complete suite, CLI commands, and saved JSON reports were rerun during P6. See `docs/evidence/p6-clean-setup.txt`, `docs/evidence/p6-final-acceptance.txt`, and `docs/evidence/p6-example-execution.txt`.
- Performance/resource measurements: not performed. No speed, scale, or resource claim is made.

## 4. Demonstrated claims and research status

| Claim or research area | Status | Evidence or limit |
|---|---|---|
| Declarative six-node DAG construction | Demonstrated for the reference specification | Exact graph assertions and saved CLI report |
| Structural, dependency, interface, and cycle verification | Demonstrated for the defined checks and test cases | Verifier tests and P5/P6 acceptance logs; not a formal proof |
| Allowlisted execution and refusal of invalid graphs | Demonstrated for the fixed built-in registry | Runtime integration tests and saved valid/invalid reports |
| Deterministic evidence for repeated reference runs | Demonstrated for checked report fields | P5 deterministic comparison and P6 saved report |
| Physical parallel execution | Not demonstrated; branches run sequentially | Implementation limitation |
| General-purpose machine synthesis, open-ended graph generation, or success on arbitrary tasks | Not evaluated | Scope is the single bounded PoC graph class |
| Meta-machine/recursive construction, probabilistic candidate search, invariant preservation | Future research hypotheses | No implementation or evaluation evidence |

## 5. Known limitations

- Only the six project-owned components and documented graph contracts are supported; arbitrary code, module imports, operating-system commands, external LLM APIs, network services, and telemetry are outside the runtime.
- Component implementations are trusted in-process Python functions. This is not an OS sandbox or security certification.
- The verifier checks declared structures and interfaces and does not establish component semantic correctness or universal runtime safety.
- JSON Schema artifacts are YAML-parseable but were not meta-validated with a separate JSON Schema implementation.
- Execution is sequential even where the DAG has independent branches. No performance or resource benchmark was conducted.
- No commit hash or release tag exists because the workspace is not a Git checkout.

## 6. Handover checklist

- [x] Setup and dependency instructions were reproduced in a fresh CPython virtual environment.
- [x] Valid and invalid examples were executed from the repository root; reports are saved under `docs/evidence/`.
- [x] Full test suite was rerun: 69 passed, 0 failed, 0 errors, 0 skipped.
- [x] Traceability matrix checked against the actual requirement IDs, source paths, and test paths.
- [x] Known limitations and unsupported research claims are disclosed above and in the README.
- [x] Phase status and evidence registers are synchronized; all approvals including final P6 approval are recorded.
- [x] Final owner approval recorded (`APPROVE P6`, 2026-10-22).

## 7. P6 final acceptance decision

Final decision: **P6 approved by the project owner** (`APPROVE P6`, 2026-10-22). The project is formally accepted as a local PoC handover; no external release or publication was made.
