from pathlib import Path

from amca.constructor import construct
from amca.specification import load_spec

ROOT = Path(__file__).resolve().parents[1]


def reference_spec():
    return load_spec(ROOT / "examples" / "valid_parallel_analysis.yaml")


def reference_graph():
    return construct(reference_spec())
