## Machine-readable schemas

The four YAML-formatted JSON Schema artifacts were prepared during P3 and are documented in `docs/03-data-model-and-yaml-schemas.md`. They express specification, graph, verification report, and execution record shapes.

The runtime uses its own strict parser and validator in `src/amca/specification.py` and `src/amca/schema.py`; it does not load schemas dynamically. P4 implemented and tested those runtime checks. The JSON Schema files and examples have been parsed as YAML, but P5 has not run a JSON Schema meta-validator against them.
