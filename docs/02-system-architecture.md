# P2 — System and Software Architecture

**Status:** Prepared; awaiting project-owner approval  
**Requirements baseline:** P1 approved 2026-10-22

## 1. System boundary

AMCA is a local Python library and CLI that loads a declarative machine specification, constructs a normalized graph candidate, independently verifies it, and executes it only when verification returns `verified`. A user supplies a YAML specification and, when running, bounded JSON-compatible external inputs. The program uses a project-owned registry of trusted built-in components. The baseline has no LLM, network service, telemetry, credential store, shell interface, dynamic imports, or task-provided source execution.

The constructor is deterministic assembly/normalization from declarative nodes and edges; it does not synthesize arbitrary programs. The independent verifier recomputes candidate structure and contracts from the candidate and trusted registry metadata. It does not accept a constructor's boolean assertion as proof.

## 2. Components and responsibilities

| Component | Responsibility | Trust role |
|---|---|---|
| CLI | Parse commands and paths, read bounded inputs, invoke public APIs, emit JSON diagnostics/results, choose report destination. | Untrusted boundary adapter; no execution policy of its own. |
| Specification loader | Read one UTF-8 YAML document using safe parsing; reject duplicate keys, unsupported YAML values, malformed shapes, and oversized input; validate the task-spec contract. | Parses untrusted data only. |
| Models / canonicalization | Represent immutable normalized nodes, edges, contracts, and results; produce deterministic canonical JSON and SHA-256 identities. | Data-only; no component dispatch. |
| Component registry | Hold the fixed mapping from six component identifiers to project-owned functions and trusted interface/config metadata. | Trusted code/configuration. Never extendable from machine data. |
| Constructor | Normalize a validated specification into a candidate graph, resolve defaults permitted by the specification, and derive deterministic candidate identity. | Candidate-producing, not an authority to execute. |
| Independent verifier | Check IDs, bounds, edge endpoints, component membership, input/output compatibility, required inputs/dependencies, duplicate connections, and acyclicity. | Gate authority; uses candidate data plus trusted registry metadata, not constructor success claims. |
| Scheduler/runtime | Reverify or validate a verification artifact bound to the candidate digest; schedule dependency-ready nodes in stable node-ID order; invoke registered components; stop dependent work on failure. | Execution boundary; only trusted registry dispatch. |
| Reporting/evidence | Serialize check-level verification result and execution evidence; redact by default, include input/specification hashes, statuses, order, and bounded output summaries. | Data-only reporting. |

Proposed modules are `cli.py`, `specification.py`, `schema.py`, `models.py`, `canonical.py`, `registry.py`, `constructor.py`, `verifier.py`, `scheduler.py`, `runtime.py`, and `reporting.py` under `src/amca/`. P3 will finalize files and test boundaries before implementation.

## 3. Data flow

```text
bounded YAML bytes
  -> safe loader + duplicate-key rejection
  -> strict specification validation
  -> deterministic constructor / normalized CandidateGraph
  -> independent verifier (checks and candidate digest)
      -> rejected or inconclusive: report; runtime not called
      -> verified: verification token/result bound to candidate digest
          -> runtime rechecks binding and registry membership
          -> stable dependency-respecting scheduler
          -> registered functions only
          -> execution report and evidence
```

If loading, construction, or verification fails, execution is not entered. A verification record is scoped to the canonical candidate digest and verifier profile/version. A different candidate digest cannot reuse that record.

## 4. Graph and interface model

The graph is a directed finite DAG, with up to 64 node instances and 128 edges. A node has a unique instance ID, one fixed component ID, and component configuration. An edge names a producer node/output port and consumer node/input port. The registry defines each component's required and optional ports, port types, configuration contract, and trusted function. The specification may not override the registry interface.

The baseline example contains six node instances and six port-level edges. Components are `input_source`, `validate_text`, `analysis_a`, `analysis_b`, `aggregate_results`, and `generate_report`; their exact contracts are specified in `docs/03-data-model-and-yaml-schemas.md`.

## 5. Determinism

Canonicalization operates on the normalized, JSON-compatible data model: UTF-8 JSON, sorted object keys, no insignificant whitespace, stable arrays after defined node/edge sorting, and finite numeric values only. SHA-256 of those bytes identifies a specification, candidate graph, or external input. The scheduler selects from currently ready nodes by ascending node ID and runs sequentially. Timestamps and environment-specific paths are excluded from deterministic digests and comparison fields.

YAML mapping key order and comments do not affect canonical identity. Duplicate mapping keys, non-string keys, YAML tags producing non-JSON values, non-finite numbers, and multiple YAML documents are rejected rather than normalized ambiguously.

## 6. Failure behavior and states

- Parse/schema failure: structured input rejection; no candidate execution.
- Constructor failure: candidate not emitted or marked rejected with a reason.
- Verification failure: `rejected`; no runtime invocation.
- Unsupported/incomplete required check or internal verifier failure: `inconclusive`; fail closed, no runtime invocation.
- Verification success: `verified` only if every mandatory check passes.
- Runtime admission mismatch or absent verification binding: execution `refused`; no function invocation.
- Component exception or output-contract failure: node/run `failed`; dependent nodes `skipped`; independent nodes not yet run are also skipped when fail-fast is triggered.
- Successful component: node `succeeded`.

Verification and execution are separate records. A `verified` graph can still fail during execution, and neither status proves semantic correctness of component code.

## 7. Architecture decisions

| ADR | Decision | Rationale and consequence |
|---|---|---|
| ADR-01 (2026-10-22) | Local, offline baseline; Python plus PyYAML only. | Fits the approved scope and reproducibility goal; no external service trust boundary. |
| ADR-02 (2026-10-22) | Use safe YAML loading with strict normalization into JSON-compatible values. | Prevents YAML data from becoming executable objects and makes canonical digesting well-defined; duplicate keys and unsupported tags must be rejected. |
| ADR-03 (2026-10-22) | Separate constructor, verifier, and runtime modules; bind verification to candidate digest and profile. | Prevents constructor self-certification and stale verification reuse; adds explicit result-binding logic. |
| ADR-04 (2026-10-22) | Fixed registry of six built-ins; no plugin or runtime registration from specification. | Keeps executable authority narrow and auditable; extending components requires code/design review. |
| ADR-05 (2026-10-22) | Sequential deterministic scheduler with stable node-ID tie-break; logical branches, not physical parallelism. | Satisfies dependency semantics and reproducibility without concurrency complexity; parallel speedup is not claimed. |
| ADR-06 (2026-10-22) | Port-level structured edges; contract metadata is registry-owned. | Allows independent type/required-input checks; specifications cannot forge component interfaces. |
| ADR-07 (2026-10-22) | Strict limits: 64 nodes, 128 edges, 64 KiB YAML spec, 16 KiB invocation input, 16 KiB node config, and 64 KiB per component output. | Provides finite data sizes for built-in work; these limits are architecture constraints and will be verified at boundaries. Trusted component code is not an OS sandbox. |

## 8. P2 approval package

**Objective:** Define module responsibilities, data flow, graph semantics, interfaces, verification/execution separation, security boundaries, and failure handling consistent with approved P1 requirements.

| Criterion | Evidence | Prepared status |
|---|---|---|
| P2-EC1 — Module boundaries and data flow are documented. | Sections 1–6 | Complete for owner review |
| P2-EC2 — Machine, graph, contract, and verification result formats are specified. | `docs/03-data-model-and-yaml-schemas.md` | Complete for owner review |
| P2-EC3 — Verifier/runtime trust boundaries and failure modes are designed. | Sections 2, 3, 6; `docs/04-verification-design.md`; `docs/05-runtime-and-execution-design.md` | Complete for owner review |

**Checks:** Scaffold consistency and the workflow validator's own tests are run and recorded in `docs/phase-status.md`. These validate workflow records only, not the proposed AMCA design.

**Recommendation:** APPROVE P2. Machine-readable schema files, source code, and runtime tests remain P3/P4 work and are not claimed as implemented here.

**Approval record:** Decision [Pending]; reviewer [Pending]; date [Pending].
