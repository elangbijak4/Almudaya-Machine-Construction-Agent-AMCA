# P2 — Independent Verification Design

**Status:** Prepared; awaiting P2 owner approval

## 1. Purpose and scope

The verifier is a separate module and authority from specification parsing, graph construction, and execution. It recomputes graph properties from immutable candidate data and trusted registry metadata. It checks declared structure, interface compatibility, dependency completeness, bounds, and DAG constraints. It does not establish that built-in algorithms are semantically correct or prove arbitrary program behavior.

## 2. Verification inputs and binding

Inputs are the normalized `CandidateGraph`, the immutable registry profile, and the verifier profile/version. The verifier computes candidate canonical bytes and SHA-256 itself; it does not trust a digest or pass/fail value supplied by the constructor. Its result includes the recomputed digest and exact profile ID. The runtime admission layer requires that digest/profile binding to match the candidate and currently loaded registry. A mutation or profile mismatch after verification means refusal and zero invocation.

## 3. Ordered mandatory checks

Checks run in stable order and each produces `passed`, `failed`, or `inconclusive` with a stable check ID and details.

1. `candidate_shape`: required graph fields and normalized value types are present.
2. `graph_bounds`: node/edge and canonical data limits are within 64/128 limits and per-object size limits.
3. `unique_node_ids`: IDs match grammar and are unique.
4. `known_components`: each component ID resolves in the immutable registry profile.
5. `edge_endpoints`: all producer/consumer nodes exist and self-edges are absent.
6. `unique_connections`: each edge has known ports, each required input has exactly one source, and no input is multiply connected.
7. `interface_compatibility`: each producer output type exactly matches consumer input type.
8. `required_inputs`: all required component ports are supplied by a graph edge or (only for source components) an explicitly declared external input mapping.
9. `acyclic`: deterministic topological analysis visits every node; otherwise cycle is reported.
10. `registry_profile_binding`: candidate contracts and digest correspond to the current registry profile used for verification.

Unknown fields, malformed IDs, duplicate edges, undeclared ports, missing Aggregate inputs, and unsupported data values are rejected by the loader/model checks before or at the corresponding verifier check. The verifier still fails closed if a malformed candidate is submitted directly.

## 4. Status derivation

- `verified`: all mandatory checks have status `passed`.
- `rejected`: one or more mandatory checks have status `failed`. Other unevaluable checks are still reported.
- `inconclusive`: no known mandatory failure exists, but one or more mandatory checks could not be completed.

No constructor-provided status is used. Inconclusive is not permission to run. A verifier exception is converted to an `inconclusive` result if the result can be safely serialized; otherwise verification fails closed and runtime receives no admissible record.

## 5. Independence and runtime gate

- Constructor produces data only; it cannot mint a runtime authorization token.
- Verifier traverses nodes and edges and recomputes reachability/ordering and contracts independently of constructor success flags.
- Verifier dependencies are limited to normalized data models and registry metadata; it does not call component implementations.
- Runtime admission compares the candidate digest, profile ID, and status to the actual current candidate/registry. Any absent, rejected, inconclusive, malformed, stale, or mismatched record returns `refused` before the first function call.
- Verification result stays a distinct field in the execution record; runtime failure never rewrites verification status.

## 6. Diagnostics

Each check has a stable identifier and status. Failure/inconclusive details use stable reason codes, a concise message, and optional node/edge context. Ordering is by check order, then stable node ID and edge tuple. Do not include credentials, full user inputs, host paths, raw tracebacks, or unbounded payloads. Output is bounded by the P2 contract.

## 7. Test design obligations

P3/P4 tests must cover each mandatory check, status derivation, direct invalid-runtime submission, a candidate changed after verification, registry profile mismatch, and proof by invocation counter that invalid candidates call no component. End-to-end tests use the real verifier and runtime. Mutation tests alter a valid reference candidate (delete a branch edge, introduce a cycle, change a component ID, corrupt a port) and assert rejection before execution.

## 8. Limitations

Verification checks declared graph/configuration structure. It does not sandbox Python process memory or trusted component code, prove the meaning of analysis outputs, assess arbitrary side-channel behavior, or establish mathematical correctness. The local offline trust assumption is that registry functions and the installed application code are trusted.
