# P2 — Data Model and YAML Contract Design

**Status:** Contract design prepared; awaiting P2 owner approval. Machine-readable schema files are scheduled for P3.  
**Requirements baseline:** `docs/01-requirements-specification.md`

## 1. Serialization and strictness

The external format is exactly one UTF-8 YAML document, parsed only as safe data. The normalized model consists only of mappings with string keys, arrays, strings, booleans, null, integers, and finite floats. Reject duplicate mapping keys, non-string keys, anchors/aliases, multiple documents, custom YAML tags, unsupported scalar types, invalid UTF-8, non-finite numbers, and YAML source larger than 65,536 bytes. Unknown fields are rejected at every contract object. P3 will encode these rules in machine-readable schemas plus parser-specific checks for rules that the schema language cannot express.

## 2. Machine specification

The specification is declarative and describes nodes and port-level edges. It contains no Python names, module paths, source text, shell commands, URLs, or verification claims.

```yaml
schema_version: "1.0"
machine_id: "reference-analysis"
nodes:
  - id: "input"
    component: "input_source"
    config:
      input_key: "text"
  - id: "validate"
    component: "validate_text"
    config: {}
  - id: "analysis_a"
    component: "analysis_a"
    config: {}
  - id: "analysis_b"
    component: "analysis_b"
    config: {}
  - id: "aggregate"
    component: "aggregate_results"
    config: {}
  - id: "report"
    component: "generate_report"
    config: {}
edges:
  - {from: "input", out: "text", to: "validate", in: "text"}
  - {from: "validate", out: "text", to: "analysis_a", in: "text"}
  - {from: "validate", out: "text", to: "analysis_b", in: "text"}
  - {from: "analysis_a", out: "finding", to: "aggregate", in: "finding_a"}
  - {from: "analysis_b", out: "finding", to: "aggregate", in: "finding_b"}
  - {from: "aggregate", out: "summary", to: "report", in: "summary"}
```

The baseline external invocation supplies `{"text": "..."}` as JSON-compatible input, separate from the machine file. `input_source.config.input_key` selects the external key. Specification/config values cannot contain code or registry overrides.

## 3. Field contracts

### Root specification

| Field | Type | Rule |
|---|---|---|
| `schema_version` | string | Required; exactly `"1.0"` for this contract. |
| `machine_id` | string | Required; matches `^[a-z][a-z0-9_-]{0,63}$`. |
| `nodes` | array of node | Required; 1–64 entries; IDs unique. |
| `edges` | array of edge | Required; 0–128 entries; each `(from,out,to,in)` tuple unique. |

### Node

| Field | Type | Rule |
|---|---|---|
| `id` | string | Required; matches `^[a-z][a-z0-9_-]{0,63}$`; unique per machine. |
| `component` | string | Required; exactly one of the six registry IDs in section 5. |
| `config` | object | Required, default is not implicit; at most 16,384 canonical JSON bytes; exact keys depend on component. |

### Edge

| Field | Type | Rule |
|---|---|---|
| `from` | string | Required; existing producer node ID. |
| `out` | string | Required; registered output port on producer component. |
| `to` | string | Required; existing consumer node ID. |
| `in` | string | Required; registered input port on consumer component. |

Self-edges, edges to nonexistent nodes, undeclared ports, duplicate target-port connections, and cycles are rejected. The edge order in YAML does not control construction or scheduling.

## 4. Runtime inputs, graph, and identity

Runtime inputs are a JSON-compatible string-keyed object with at most 16,384 canonical bytes. A node's `input_source` reads the key named by its config. The referenced value must be a string of 1–16,384 UTF-8 bytes for this baseline. Missing keys and wrong types are structured input errors before component execution.

The internal candidate graph contains:

- `graph_version`: `"1.0"`;
- `machine_id`;
- sorted normalized node records (`id`, `component`, canonical `config`);
- sorted normalized edges (`from`, `out`, `to`, `in`);
- `specification_sha256` and `candidate_sha256`;
- `registry_profile`: immutable registry version identifier.

Canonical bytes are UTF-8 JSON using sorted keys, compact separators, stable arrays sorted by node ID / edge tuple, and no NaN/Infinity. SHA-256 is lowercase hexadecimal over canonical bytes. Volatile timestamps and filesystem paths are not included. Python/PyYAML versions are metadata, not content identity.

## 5. Component contract registry

All ports below are required unless identified optional. Port types are nominal JSON value classes; compatibility requires exact type equality. Component IDs and contracts live in project code, not the machine specification.

| Component ID | Config | Inputs | Outputs | Bounded behavior |
|---|---|---|---|---|
| `input_source` | Required `input_key` string matching identifier grammar. | None | `text: string` | Read one supplied UTF-8 string, max 16 KiB. |
| `validate_text` | Empty object only. | `text: string` | `text: string` | Reject empty/whitespace-only text; normalize outer whitespace; max 16 KiB. |
| `analysis_a` | Empty object only. | `text: string` | `finding: object` | Deterministic built-in analysis; output JSON object max 64 KiB. |
| `analysis_b` | Empty object only. | `text: string` | `finding: object` | Deterministic built-in analysis; output JSON object max 64 KiB. |
| `aggregate_results` | Empty object only. | `finding_a: object`, `finding_b: object` | `summary: string` | Requires both findings; deterministic summary max 64 KiB. |
| `generate_report` | Empty object only. | `summary: string` | `report: object` | Deterministic structured report max 64 KiB. |

Every component receives at most 16 KiB of canonical input data, excluding its separately bounded config object. Output values are JSON-compatible and at most 65,536 canonical bytes per component. Component implementation algorithms and expected content semantics are detailed in P3 contracts/test plan; their trustworthiness is not established by these interface types.

## 6. Verification result contract

Machine-readable report contract (required fields):

| Field | Type | Meaning |
|---|---|---|
| `report_version` | string | Verification report format, initially `"1.0"`. |
| `status` | enum | `verified`, `rejected`, or `inconclusive`, with semantics fixed by P1. |
| `candidate_sha256` | string | Lowercase SHA-256 of canonical candidate. |
| `profile_id` | string | Exact verifier/check profile and version. |
| `checks` | array | Stable-ordered `{id, status, details}` entries; check status is `passed`, `failed`, or `inconclusive`. |
| `reasons` | array | Stable-ordered `{code, message, node_id?, edge?}` explanations; required when a check fails/is inconclusive. |
| `assumptions` | array of strings | Relevant explicit assumptions, including trusted registry profile. |

`verified` requires every mandatory check to be `passed` and no failed/inconclusive checks. Any mandatory failure yields `rejected`; inability to evaluate a mandatory check without a known violation yields `inconclusive`. If a known mandatory violation exists alongside an unevaluable check, the overall status is `rejected` and both findings remain listed. No timestamp is needed for deterministic identity; optional run metadata belongs in an outer execution record.

## 7. Execution evidence contract

The outer execution record contains `record_version`, `machine_id`, `specification_sha256`, `candidate_sha256`, `inputs_sha256`, `verification` (the complete verification result), `run_status`, `execution_order`, and node records `{node_id, component, status, output_summary?, error?}`. Run/node status is `succeeded`, `failed`, `skipped`, or `refused`. A refused run may include a bounded `refusal_reason` so mismatched or stale verification evidence is diagnosable even when the fresh verification result itself is `verified`. Outputs are included only when non-sensitive and within limits; default output summaries contain output digest, byte size, and type. A component may add a small `safe_summary` containing only derived non-sensitive counts or the generated report summary; raw source text is never included. Error records contain stable category and sanitized message, not traceback, credentials, or full raw inputs. Run timestamps and host paths are optional and excluded from canonical deterministic comparison.

## 8. Limits and rejected values

- YAML bytes: 65,536 maximum.
- Node count: 64 maximum; edge count: 128 maximum.
- Per-node canonical config: 16,384 bytes maximum.
- Invocation input object: 16,384 canonical bytes maximum; a selected `input_source` text: 16,384 UTF-8 bytes maximum.
- Total canonical data consumed by any component: 16,384 bytes maximum; each output: 65,536 canonical bytes maximum.
- Only JSON-compatible values are allowed; no bytes, dates, sets, custom objects, NaN, or Infinity.
- File size and all data limits are checked before component invocation. Over-limit input is rejected, never silently truncated.

## 9. P3 schema deliverables

P3 will translate these contracts into versioned YAML-formatted JSON Schema documents for the task specification, normalized graph, verification report, and execution record. Parser/runtime checks remain necessary for unique YAML keys, graph topology, registry-port compatibility, byte limits, and digest binding. Examples will be checked against those schemas in P3. Schema files do not replace independent graph verification.
