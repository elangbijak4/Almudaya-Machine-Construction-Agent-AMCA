# Tests

Run the complete suite from the repository root after installing requirements-dev.txt and setting PYTHONPATH to src:

    python -m unittest discover -s tests -p "test_*.py" -v

The suite includes unit tests for parsing, models, construction, verification, scheduling, registry, limits, and reporting; integration tests for real component execution, admission refusal, failure propagation, and repeatability; adversarial untrusted-input checks; CLI end-to-end examples; and separate workflow-validator smoke tests. The workflow-validator tests do not count as AMCA runtime tests.

P4/P5/P6 test output and environment evidence are recorded under docs/evidence and summarized in docs/08-implementation-record.md, docs/09-verification-report.md, and docs/10-release-and-evaluation.md.
