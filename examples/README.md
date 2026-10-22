# Examples

valid_parallel_analysis.yaml and invalid_missing_dependency.yaml use the approved P2 task contract. reference-input.json supplies the end-to-end input. These declarative examples are data, not executable source code.

From the repository root, set PYTHONPATH to src. The valid example runs with python -m amca.cli run examples/valid_parallel_analysis.yaml --inputs examples/reference-input.json. The invalid example is rejected before component dispatch.
