# P1 — Requirements Specification

**Status:** Prepared; awaiting project-owner approval  
**Baseline:** P0 charter approved 2026-10-22  
**Scope:** AMCA PoC v0.1 as defined in [the project charter](00-project-charter.md)

## 1. Purpose and terminology

This document converts the approved charter into requirements that can be verified against the implementation. The baseline is a local, deterministic, rule-based constructor for declarative machine specifications. It is not an unrestricted autonomous coding system and does not depend on an LLM.

- A **specification** is untrusted declarative input describing a finite graph and its registered components.
- A **candidate graph** is constructor output not yet trusted for execution.
- A **verification decision** describes only the defined checks: `verified` means every applicable check passed; `rejected` means one or more checks failed; `inconclusive` means a required check could not be completed. Only `verified` permits execution.
- An **execution result** is separate from verification and reports the outcome of running a verified graph. Verification success does not guarantee runtime success or semantic correctness of component implementations.

## 2. Functional requirements

| ID | Requirement | Acceptance criteria | Planned verification |
|---|---|---|---|
| FR-01 | Load a machine specification from YAML. | A UTF-8 YAML document with a mapping root and valid specification shape loads into the defined internal model. Malformed YAML, non-mapping roots, and invalid encodings return a controlled diagnostic and do not construct or execute a graph. | Parser unit tests: valid fixture and each invalid input class. |
| FR-02 | Validate specification fields and values. | Required fields, types, allowed fields, identifier syntax, and component names are checked. Missing required fields, wrong types, unknown fields, malformed identifiers, and unregistered component names produce a rejection with a field/path diagnostic. | Schema and negative tests for each listed class. |
| FR-03 | Construct the reference graph deterministically. | The approved reference specification produces exactly six nodes (`Input`, `Validate`, `Analysis A`, `Analysis B`, `Aggregate`, `Report`) and six directed edges: Input→Validate, Validate→each analysis, each analysis→Aggregate, Aggregate→Report. No extra nodes or edges appear. | Constructor integration test asserting exact node and edge sets. |
| FR-04 | Preserve both analysis branches and their join. | Analysis A and Analysis B are distinct nodes, each depends on Validate, and Aggregate depends on both analyses. Removing either required dependency is rejected by verification. | Graph assertions and missing-edge negative tests, one per branch. |
| FR-05 | Independently verify graph structure. | Before execution, verification checks unique node IDs, valid edge endpoints, registered component IDs, required dependencies, and acyclicity. A duplicate ID, unknown endpoint/component, missing required dependency, self-loop, or cycle is rejected with at least one identifying reason. | Unit and adversarial tests for every listed condition. |
| FR-06 | Verify component interfaces and inputs. | Every edge connects compatible declared output/input types; every required component input is supplied exactly once; absent, duplicate, or incompatible required inputs are rejected before execution. Optional ports may be omitted only when explicitly declared optional. | Contract unit tests covering compatible, missing, duplicate, and incompatible ports. |
| FR-07 | Execute verified graphs through the allowlist. | The runtime accepts only a graph with a `verified` decision and dispatches only component IDs in the project-owned registry. Any unregistered component or non-verified decision is refused before the first component invocation. For the baseline sequential scheduler, ready nodes are selected in stable ascending node-ID order while respecting dependencies. | Runtime tests with invocation counters, unknown component, non-verified candidate, and deterministic ordering. |
| FR-08 | Produce a structured verification report. | Each report contains a status from `verified`, `rejected`, `inconclusive`, the specification/candidate identifier, the checks performed with outcomes, and reasons for failed or inconclusive checks. An unsupported check cannot result in `verified`. | Report serialization tests for all three statuses and check/reason completeness. |
| FR-09 | Preserve reproducible run evidence. | The run record identifies the canonical specification/input by cryptographic digest, records the verification decision, deterministic execution order, each invoked component's status, and output or a documented output summary. The record contains no credentials and is serializable as machine-readable data. A repeated run with the same inputs and configuration has the same canonical graph, component order, and outputs; volatile run metadata is excluded from the deterministic comparison. | Integration test comparing repeated outputs and evidence fields; secret-pattern scan of fixtures/reports. |
| FR-10 | Prevent execution of invalid candidates. | Rejected or inconclusive candidates invoke zero runtime components. A failure in an upstream component prevents all dependent components, including Aggregate and Report, from running; the report records failure and skipped states. | Negative integration tests with component invocation counters and upstream failure fixture. |

## 3. Non-functional requirements

| ID | Requirement | Acceptance criteria | Planned verification |
|---|---|---|---|
| NFR-01 | Determinism | For identical canonical specification, input, and configuration, the canonical graph, verification checks/reasons, dependency-respecting execution order, and component outputs are byte-for-byte stable after canonical serialization. Timestamps or other volatile metadata are excluded. | Repeated-run integration test. |
| NFR-02 | Restrict executable behavior | No task-provided source code is evaluated, executed, imported, or used to invoke an OS command. Specifications cannot select arbitrary Python modules or network services. All dispatch resolves through a fixed, project-owned component registry. | Source review and adversarial fixtures attempting arbitrary import/command selection; verify no component invocation. |
| NFR-03 | Explain verification decisions | Every `verified`, `rejected`, or `inconclusive` report identifies all applicable checks and gives a stable reason code/message for each failed or inconclusive check. | Report contract tests. |
| NFR-04 | Reproducible local setup | The documented setup and test commands succeed in a clean supported Python 3.12 environment with dependencies declared in the repository, without a hosted service or API key. | Clean environment setup and test run in P5. |
| NFR-05 | Maintainability | Runtime modules have separated responsibilities; public runtime interfaces and data models have type annotations; validation errors use documented categories rather than unstructured tracebacks. | Code review, import check, and error-contract tests in P4/P5. |
| NFR-06 | Bound graph work and fail safely | The accepted graph limit is at most 64 nodes and 128 edges. Inputs above either limit are rejected before graph execution. Component implementations are project-owned and must have documented finite input/output constraints before implementation approval; unexpected component exceptions fail the run and stop dependent work. | Boundary tests at limits and one above each limit; component failure integration test. |
| NFR-07 | Minimize dependencies and external trust | The baseline uses Python standard library plus PyYAML (`>=6.0,<7.0`) for YAML parsing. It makes no network calls and requires no external API key or service during normal validation, construction, execution, or tests. | Dependency/config review and run with network/API credentials absent. |
| NFR-08 | Handle errors predictably | Invalid input and runtime failure are surfaced as structured category, message, and relevant node/field context; command-line use returns nonzero for invalid input, rejected candidates, or failed execution. No raw traceback is required for expected user errors. | CLI tests for parse, validation, and component failures. |

## 4. Specification classes

### Valid baseline

A valid machine specification declares the six reference nodes, only registered component identifiers, explicit typed input/output interfaces, and dependencies matching the six reference edges. The YAML root is a mapping, all required fields are present with their declared types, IDs are unique and well-formed, and graph bounds are respected.

### Invalid inputs and candidates

The implementation must reject malformed YAML; a non-mapping root; missing or unknown fields; wrong field types; duplicate/malformed identifiers; unknown nodes or components; absent, duplicate, or incompatible required ports; missing dependencies; self-loops or cycles; and graphs above 64 nodes or 128 edges. It must also refuse direct runtime submission of any candidate that lacks a current `verified` decision. Rejection must occur before component invocation.

## 5. Error and execution semantics

Verification statuses are defined in section 1. Execution has separate node/run states: `succeeded`, `failed`, `skipped`, and `refused`. `refused` means verification did not permit execution; `failed` means an invoked registered component raised or returned a defined failure; `skipped` means a dependent node was not invoked because an upstream dependency failed. A successful verification can therefore be followed by a failed execution.

Expected user-input errors are structured diagnostics. Unexpected internal errors are recorded without secrets; dependent work stops on execution failure. There is no automatic repair requirement. If a candidate is unsupported or a check cannot finish, verification is `inconclusive` and runtime dispatch is refused.

## 6. Trust boundaries and exclusions

- YAML specifications, external inputs, and constructor output are untrusted.
- Verification is logically and modularly separate from construction. It checks declared graph and interface properties; it does not prove semantic correctness of trusted component implementations.
- The registry and component code are trusted project-owned code. Machine data cannot add registry entries.
- Runtime has no arbitrary Python execution, dynamic imports, shell/OS command interface, network access, telemetry, LLM dependency, or secret retrieval.
- Physical parallel execution, cycles, recursive/meta-machine construction, probabilistic synthesis, general automatic repair, multi-tenant service, and formal proofs are outside the baseline.
- The 64-node/128-edge limits constrain graph size only. They do not constitute a general CPU or memory isolation guarantee; P2/P3 must define component-specific finite input/output bounds appropriate to the built-ins.

## 7. Assumptions and decisions for later phases

- Python 3.12 is the initial supported baseline, matching the inspected environment; P3 may specify a wider supported range if clean-environment evidence supports it.
- YAML parsing uses safe data loading; PyYAML is the only declared third-party dependency.
- Branch semantics are mandatory; the scheduler may execute sequentially with stable ordering. Physical parallelism is optional and excluded from acceptance.
- Graph bounds are fixed here before implementation or test results: 64 nodes and 128 edges.
- P2 will define exact schema fields, identifier grammar, port type compatibility, canonical serialization/hash, and output redaction/size limits. These details may refine contracts but must not weaken the requirements here without change control and owner approval.
- P3 will define the exact component input/output limits and clean-install command based on P2 contracts.

## 8. P1 approval package

**Objective:** Establish unique, testable functional and non-functional requirements for the approved P0 scope, including valid/invalid inputs and trust boundaries.

**Deliverables:** This requirements specification and the updated [traceability matrix](traceability-matrix.md).

**Acceptance evidence:**

| Criterion | Evidence | Prepared status |
|---|---|---|
| P1-EC1 — Functional and non-functional requirements have unique IDs and acceptance criteria. | Sections 2–3 | Complete for owner review |
| P1-EC2 — Out-of-scope behavior and trust boundaries are explicit. | Sections 4–6 | Complete for owner review |
| P1-EC3 — Every requirement maps to a planned verification method. | `docs/traceability-matrix.md` | Complete for owner review |

**Checks:** Scaffold consistency and workflow-validator tests are rerun for this package; results are recorded in `docs/phase-status.md`.

**Open design work:** P2/P3 must define schema and canonicalization details, output redaction/size limits, and per-component finite input/output limits within these requirements. These are design contracts, not requests to expand scope.

**Recommendation:** APPROVE P1, subject to owner review of requirement IDs, measurable criteria, graph caps, and trust boundaries. P1 approval remains pending until the owner explicitly decides.

**Approval record:** Decision [Pending]; reviewer [Pending]; date [Pending].
