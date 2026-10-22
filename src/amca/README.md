# AMCA source package

The package is organized around the approved P2 boundaries:

- specification.py safely loads and validates declarative YAML;
- constructor.py normalizes a candidate graph;
- verifier.py independently checks graph structure and contracts;
- registry.py contains the fixed six-component allowlist;
- scheduler.py computes stable topological order;
- runtime.py binds current verification to execution and records outcomes;
- reporting.py and cli.py serialize user-facing results.

From the repository root, set PYTHONPATH to src and run python -m amca.cli --help. See docs/06-implementation-plan.md for module contracts and docs/08-implementation-record.md for the implementation record.
