# P3 — Test and Validation Plan

**Status:** Approved in P3; implemented test inventory and results are being reviewed in P4. Final acceptance and clean-environment reproduction remain P5 work.

## 1. Verification layers

The P3 plan was implemented during P4. P5 runs the complete suite against the real implementation and performs reproducibility checks. Unit tests may isolate a function; integration and end-to-end acceptance use the actual registry, verifier, scheduler, and runtime (no mocked runtime evidence).

| Layer | Target | Test approach |
|---|---|---|
| Static/structural | Required modules/schema/example files, imports, schema/example parseability, dependency list, unsafe execution patterns | Explicit file/import checks; scan source for eval, exec, dynamic imports, subprocess/OS command use; review findings rather than substring-only automatic claims. |
| Unit | Loader, model, canonicalization, registry, constructor, verifier checks, scheduler, report serialization, error categories | Table-driven positive/negative cases; assert exact error category and relevant path/node. |
| Integration | Loader→construct→verify→runtime→report; registry dispatch; fail-closed admission; dependency propagation | Real components; invocation counters verify dispatch boundaries. |
| End-to-end | Valid reference graph, invalid missing-edge graph, unknown component, cyclic graph, deterministic repeated run | Invoke actual CLI/API and built-ins from repository-root example files. |
| Reproducibility | Clean CPython 3.12+ venv and documented dependencies/commands | Create fresh environment; install requirements-dev.txt; run examples and complete suite; record exact versions/commands/results. |

## 2. Unit test inventory

| Area | Required cases |
|---|---|
| YAML loader | Valid single document; malformed YAML; invalid UTF-8; empty/non-mapping root; multiple documents; duplicate keys; anchor/alias; custom tag; >65,536 bytes. |
| Specification contract | Missing/unknown fields; wrong types; invalid IDs; unknown component; config-specific fields; non-JSON values; nonfinite numbers; config size boundary. |
| Canonicalization | Key-order/comment independence after load; stable node/edge sorting; digest stable across repeats; volatile metadata excluded; unsupported values rejected. |
| Models/registry | Six entries and exact port/config contracts; unknown ID rejected; immutable registry profile; wrong port/type rejected. |
| Constructor | Deterministic candidate digest; edges normalized independent of YAML order; malformed source never yields executable candidate. Exact six-node/six-edge fixture assertion is an integration test. |
| Verifier | Every mandatory check passes valid graph; duplicate ID, unknown component/endpoint, self-edge, duplicate connection, missing input/dependency, incompatible port, cycle, oversize, profile mismatch; all three verification statuses. |
| Scheduler | Dependency order; stable lexical tie-break among ready nodes; disconnected valid nodes; cycles rejected; exact once-per-node behavior. |
| Runtime/report | Refusal for rejected/inconclusive/stale digest/profile; zero invocations; valid outputs; missing/oversize/wrong-type output; component exception; upstream skip; report fields and safe summaries. |

Every check ID in docs/04-verification-design.md has at least one positive and one negative test where applicable.

## 3. Negative and adversarial tests

1. Remove each required edge independently, especially both Aggregate inputs.
2. Submit duplicate node IDs, self-loop, multi-node cycle, nonexistent endpoint, duplicate edge, and >64 nodes/>128 edges/>65,536 YAML bytes.
3. Use unknown component, unexpected config key, wrong port name/type, missing required port, and multiply connected input.
4. Submit YAML custom tags, aliases/anchors, duplicate keys, multiple documents, malformed UTF-8/YAML, arbitrary module/command/source-looking strings.
5. Call runtime directly with rejected, inconclusive, missing, stale, digest-mismatched, or registry-profile-mismatched verification evidence.
6. Force a real upstream component failure and prove its dependent aggregate/report components are skipped; invocation counters assert no invalid or refused execution.
7. Tamper with candidate after verification and prove digest binding refuses it.

Adversarial text in configuration must remain ordinary data and must never cause code import/execution or OS/network activity.

## 4. Integration and end-to-end cases

### E2E-01: valid reference workflow

Input text AMCA builds a graph. should produce:

- input → validate → both analysis nodes → aggregate → report;
- Analysis A character_count: 20;
- Analysis B word_count: 4;
- Aggregate summary exactly characters=20; words=4; the report output summary exposes that safe derived summary without returning the source text;
- verification status verified, execution status succeeded, all six nodes succeeded.

Run twice and compare canonical graph digest, checks, order, node states, output digests, and report content excluding volatile metadata; they must match.

### E2E-02: missing required branch

Use examples/invalid_missing_dependency.yaml, which omits the analysis_b→aggregate edge. Expect verification status rejected; actual runtime component invocation count is zero; aggregate and report are not invoked.

### E2E-03: unknown component and cycle

Substitute an unregistered component and separately add a back edge creating a cycle. Both candidates are rejected before runtime and invoke no component.

### E2E-04: runtime dependency failure

Use a test-only controlled failure from a registered built-in boundary or injected test fixture that does not add a production registry entry. Confirm the failing node is failed, downstream nodes skipped, and the report distinguishes verification verified from execution failed.

## 5. Boundary and output assertions

- Accept exactly 64 nodes and 128 edges when otherwise valid; reject 65 nodes and 129 edges.
- Accept exactly 65,536 spec bytes only if the fixture remains valid; reject one byte over.
- Check config/input/output byte boundaries at limit and one over.
- Confirm no silent truncation and no raw input/traceback/credential in default evidence.
- Confirm CLI uses exit 0 for successful validate/verify/run; nonzero for expected rejection/refusal/failure, with structured diagnostics.

## 6. Clean setup and commands

From repository root, use a clean CPython 3.12+ environment. PowerShell example:

    py -3.12 -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
    $env:PYTHONPATH = "src"
    .\.venv\Scripts\python.exe -m amca.cli validate examples/valid_parallel_analysis.yaml
    .\.venv\Scripts\python.exe -m amca.cli run examples/valid_parallel_analysis.yaml --inputs examples/reference-input.json
    .\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v

If py is unavailable, substitute an installed CPython 3.12+ executable. The current execution host has Python only through a bundled runtime. P4 implemented the CLI and exercised it in the test suite; P5 must verify clean setup and document any host-specific deviation. The repository itself does not need to commit a virtual environment.

## 7. Evidence and acceptance rules

P5 records interpreter/platform, PyYAML version, exact command lines, test counts and pass/fail/error/skip counts, raw output path, defects and correction reruns, and clean-environment deviations. The mandatory acceptance target is 100% pass rate. No skipped mandatory test, mock-only E2E result, or validator pass may be represented as AMCA runtime evidence. Code coverage may be measured if available but is not a correctness threshold.
