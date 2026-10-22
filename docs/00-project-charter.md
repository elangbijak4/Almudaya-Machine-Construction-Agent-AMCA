# P0 — Project Charter and Scope

**Status:** Prepared; awaiting project-owner approval  
**Project:** Almudaya Machine Construction Agent (AMCA) PoC v0.1

## 1. Problem statement

Agentic software systems can generate code or workflows, but the resulting architecture may be difficult to inspect, constrain, independently verify, and reproduce. AMCA explores a construction-oriented workflow in which machine descriptions and computational graphs are explicit artifacts that are constructed under rules, checked by a separate verifier, and executed only when accepted.

## 2. Objective

Build a minimal, reproducible PoC that constructs and executes a non-linear computational graph from a declarative task specification while enforcing structural and interface constraints.

## 3. Demonstration scenario

Construct this graph:

`Input -> Validate -> {Analysis A, Analysis B} -> Aggregate -> Report`

The graph must have two branches. Aggregation requires both branch outputs. A deliberately invalid graph that omits a required dependency must be rejected.

## 4. In-scope

- YAML task specification and graph representation.
- Allowlisted component catalogue.
- Deterministic graph construction.
- Independent graph structure and contract verification.
- Controlled runtime for registered components.
- Structured verification and execution reports.
- Unit and integration tests.
- Documentation, traceability, and reproducible commands.

## 5. Out of scope for v0.1

- A complete mathematical theory of machine construction.
- Claims of universal correctness or unrestricted self-construction.
- Arbitrary code generation and execution.
- Mandatory LLM integration or external API keys.
- Production multi-tenant deployment.
- General proof of concurrent-system correctness.
- Automatic repair guarantees.
- Probabilistic synthesis and dynamic graph transformation as required baseline features.
- Claims that a YAML file itself constitutes formal semantics.

## 6. Stakeholders and roles

- Research owner: Almudaya Research Institute / Almudaya Quantum Labs.
- Development agent: Codex, Antigravity, OpenCode, or compatible coding agent.
- Reviewer: project owner or designated technical reviewer.
- Runtime user: researcher running the PoC and reviewing evidence.

## 7. Initial acceptance goals

The P0 scope is considered successful when the later approved requirements and tests demonstrate all of the following:

1. One documented valid YAML specification constructs the six-stage reference DAG: `Input`, `Validate`, `Analysis A`, `Analysis B`, `Aggregate`, and `Report`, with both analysis branches and both branch outputs required by `Aggregate`.
2. A verifier independent of graph construction accepts that valid graph and rejects at least a cyclic graph, an unknown component, and a graph missing a required dependency.
3. Every rejected or inconclusive graph is prevented from entering component execution; the valid graph executes only registered allowlisted components.
4. The reference run produces a machine-readable verification decision, execution result, and diagnostic/evidence record sufficient to identify the specification and outcome.
5. The mandatory local setup, example, and test commands run without an external service or API key. The final mandatory acceptance suite targets 100% pass rate; any exception must be reported and approved rather than hidden.

These are charter-level goals. P1 will turn them into stable requirement IDs and precise testable acceptance criteria before design or implementation begins.

## 8. Constraints and safety boundaries

- The baseline runs locally in Python and uses YAML as declarative input; it has no external API or credential requirement.
- Specifications and task inputs are untrusted data. Only project-owned, explicitly registered components may execute.
- The runtime must fail closed: malformed, unsupported, cyclic, or unverified candidates do not execute.
- Task-provided source code, arbitrary imports, operating-system commands, network access, telemetry, and secret-bearing logs are outside the approved baseline.
- A `verified` result means only that the defined checks passed. It is not a proof of all possible behavior, security certification, or production-readiness claim.

## 9. Assumptions

- Python is acceptable for the first implementation.
- YAML is acceptable as an initial interchange format.
- The first graph class is a finite directed acyclic graph (DAG).
- All executable components are implemented and registered by the project.
- The runtime is local and bounded.

## 10. Risks

- The prototype may be mistaken for a general formal theory.
- The verifier may validate structure but not the semantic correctness of component implementations.
- YAML schema validity may be confused with behavioral correctness.
- A generated graph may be valid structurally but fail at runtime.
- Scope may expand prematurely into LLM agents, recursion, or dynamic reconfiguration.

## 11. P0 approval package

**Phase:** P0 — Project Charter and Scope  
**Objective:** Agree the PoC boundary, baseline DAG scenario, high-level acceptance goals, and safety constraints before requirements analysis.

**Deliverable:** This charter, including explicit scope/exclusions, intended users and roles, measurable charter goals, constraints, assumptions, and risks.

**Exit criteria and evidence:**

| Criterion | Evidence in this package | Current assessment |
|---|---|---|
| P0-EC1 — Problem, objectives, scope, exclusions, and stakeholders are explicit. | Sections 1–6 | Prepared for owner review |
| P0-EC2 — Baseline scenario and high-level acceptance goals are agreed. | Sections 3 and 7 | Owner agreement pending |
| P0-EC3 — Initial risks and assumptions are recorded. | Sections 9 and 10 | Prepared for owner review |

**Checks run:** See `docs/phase-status.md` for baseline environment, commands, actual results, and the initial missing-dependency failure and correction.

**Outstanding issues and risks:** No runtime implementation exists at this scaffold stage. The documented setup initially lacked installed PyYAML; the validator and its tests passed after installing the already-declared dependency locally. This environment is not a Git checkout, so no branch or worktree change evidence is available.

**Recommendation:** APPROVE P0, subject to owner agreement with the scope and acceptance goals above. No P0 approval is recorded by this package.

**Approval record:** APPROVED by the project owner on 2026-10-22 via the explicit chat message `APPROVE P0`. The decision is recorded in `workflow/gate-records.yaml`; P1 may proceed.


## Workflow governance added in scaffold v0.2.0

The project uses an executable workflow validator, per-criterion evidence records, Definition of Done rules, and explicit project-owner approval at every phase transition. These controls govern the development process; they do not imply the PoC has been implemented or validated.
