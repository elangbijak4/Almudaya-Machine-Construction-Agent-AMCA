# P2 — Runtime and Execution Design

**Status:** Prepared; awaiting P2 owner approval

## 1. Admission policy

The only execution entry point accepts a normalized candidate, JSON-compatible invocation inputs, and a verification result. Before dispatch, runtime admission:

1. enforces input size and value bounds;
2. recomputes the candidate digest;
3. checks verification status is exactly \`verified\`;
4. checks the verification candidate digest, profile ID, and registry version match the current candidate and immutable registry;
5. rejects malformed, stale, mismatched, rejected, or inconclusive results as \`refused\`.

All admission checks complete before the first registered function is invoked. The public runtime must not accept a free-form callable, module name, source string, command, or dynamically supplied registry.

## 2. Registry and component call contract

The registry is initialized in code and contains the six P2 components, their exact input/output port names and types, configuration validator, deterministic behavior, and callable. Each callable receives only its validated JSON-compatible config and named input values and returns one bounded JSON-compatible output mapping. Exceptions are caught at the component boundary and converted to sanitized \`failed\` diagnostics. A function returning an output with wrong keys, type, or size is treated as a component failure; output is not passed downstream.

Component implementations are trusted local code. The design does not claim an OS process sandbox. The baseline components must be deterministic, side-effect-free, offline, and bounded for their defined inputs. P3 records each implementation contract and expected behavior before code is written.

## 3. Scheduler

Build predecessor counts and ready sets from the verified DAG. Select the lexicographically smallest ready node ID at each step. A node can be invoked only when all predecessors completed successfully and all required input ports have values. This produces deterministic sequential execution while preserving parallel-branch dependency semantics; no physical concurrency is performed.

On the first invocation or output-contract failure, mark that node \`failed\`, mark not-yet-run downstream nodes \`skipped\`, and stop the run. Remaining independent nodes not yet invoked are also \`skipped\` under this explicit fail-fast policy. Previously successful independent nodes remain \`succeeded\`. This policy is deterministic and avoids partial continuation after a failed run.

Before successful execution, all graph-level checks and all external source inputs needed by the candidate are validated. Thus malformed/missing source input does not cause a partial run.

## 4. State model

Run-level states:

- \`refused\`: no component was invoked because admission or verification did not permit execution.
- \`succeeded\`: every scheduled node completed and output checks passed.
- \`failed\`: at least one component invocation or output contract failed.

Node-level states are \`succeeded\`, \`failed\`, and \`skipped\`. Refused executions have no invoked node records; an optional plan may be recorded as not-run. Verification remains a separate report with \`verified\`, \`rejected\`, or \`inconclusive\` status.

## 5. Failure and exception policy

- Input validation errors return structured errors before dispatch.
- Internal scheduler errors fail closed; no further node is invoked.
- Component exceptions become a bounded error record with stable category, node ID, and sanitized message. Tracebacks are excluded from ordinary reports.
- Output schema/type/size mismatch is a component failure.
- A dependency only receives successful, validated outputs.
- Runtime never retries a component, repairs the graph, or executes a substitute implementation.
- Rejected/inconclusive candidate or any binding mismatch is refused before execution.

## 6. Data and resource limits

The loader rejects specification input above 65,536 bytes. Graph maximum is 64 nodes/128 edges. Per-node config and invocation input object are each limited separately to 16,384 canonical JSON bytes. The selected source text is limited to 16,384 UTF-8 bytes. Each component receives at most 16,384 bytes of canonical data input, excluding its separately bounded config, and may return at most 65,536 canonical output bytes. Limits are checked before/after calls and over-limit values are rejected, never truncated.

The built-ins use bounded string/JSON operations over these inputs. There is no user-supplied code and no OS/network access. These limits do not protect against defects or malicious behavior in trusted in-process component code; adding untrusted plugins or hard CPU/memory isolation would require a new trust-model design and approval.

## 7. Evidence and reporting

Every execution report carries the complete verification result, machine/specification/candidate/input digests, registry and runtime versions, stable execution order, node statuses, output digests/types/byte sizes, and sanitized error details. Full inputs and outputs are omitted by default. Optional explicit output capture remains bounded and must be documented for the invoking user; no secrets or credentials are logged.

Canonical deterministic comparison excludes timestamps, machine-specific filesystem paths, and environment diagnostics. Given equal canonical spec, inputs, and registry profile, graph digest, verifier checks, execution order, statuses, and output digests must match.

## 8. CLI contract

P3 will define exact CLI commands and flags. Required logical operations are validate, construct/verify, run, and report. The CLI returns exit 0 for successful validation/verification/execution, nonzero for parse/schema rejection, rejected/inconclusive verification, refusal, or failed execution. Expected errors are emitted as structured JSON to stderr or the selected report path; normal output is deterministic apart from explicitly volatile metadata.

## 9. Runtime verification evidence

P4/P5 tests exercise real registry functions and runtime admission, including a non-verified graph, stale digest, profile mismatch, invalid component, malformed external input, upstream component failure, output-size violation, and the end-to-end reference graph. Invocation counters confirm refused graphs execute zero functions. The baseline claims deterministic sequential scheduling only, not parallel runtime performance.
