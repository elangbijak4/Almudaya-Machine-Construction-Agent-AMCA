"""Stable, user-facing AMCA error categories."""
from __future__ import annotations


class AMCAError(Exception):
    """Base class for expected AMCA errors."""

    category = "amca_error"

    def __init__(self, message: str, *, path: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.path = path

    def to_dict(self) -> dict[str, str]:
        value = {"category": self.category, "message": self.message}
        if self.path is not None:
            value["path"] = self.path
        return value


class InputError(AMCAError):
    category = "input_error"


class SpecificationError(AMCAError):
    category = "specification_rejected"


class ConstructionError(AMCAError):
    category = "construction_failed"


class GraphError(AMCAError):
    category = "graph_invalid"


class RuntimeRefused(AMCAError):
    category = "runtime_refused"


class ComponentFailure(AMCAError):
    category = "component_failed"
