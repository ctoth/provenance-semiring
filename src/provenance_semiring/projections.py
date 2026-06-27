"""Projection homomorphisms for provenance polynomials.

These are the standard Green-et-al. specializations of the universal semiring:
boolean presence (does any trusted derivation survive), derivation counting (the
N-semiring image), why-provenance (minimal squarefree supports, after Buneman et
al.), and a tropical min-plus cost projection. Why-provenance buckets the
variables of each minimal support by a caller-supplied string kind tag, so the
algebra stays free of any consumer's identity taxonomy.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Container, Mapping
from dataclasses import dataclass
from math import inf
from typing import DefaultDict

from provenance_semiring.homomorphism import evaluate
from provenance_semiring.polynomial import ProvenancePolynomial
from provenance_semiring.variables import SourceVariableId


@dataclass(frozen=True)
class WhySupport:
    """A minimal set of source variables that jointly justify a result.

    Variables are grouped by a free-form string kind tag supplied by the caller.
    ``by_kind`` is normalized at construction: tags are sorted, the variables
    under each tag are deduplicated and sorted, and empty tags are dropped, so
    two ``WhySupport`` values with the same content compare and hash equal.
    """

    by_kind: tuple[tuple[str, tuple[SourceVariableId, ...]], ...] = ()

    def __post_init__(self) -> None:
        merged: DefaultDict[str, set[SourceVariableId]] = defaultdict(set)
        for tag, variables in self.by_kind:
            for variable in variables:
                merged[str(tag)].add(SourceVariableId(str(variable)))
        normalized = tuple(
            (tag, tuple(sorted(merged[tag])))
            for tag in sorted(merged)
            if merged[tag]
        )
        object.__setattr__(self, "by_kind", normalized)

    @property
    def size(self) -> int:
        return sum(len(variables) for _, variables in self.by_kind)

    def variables_for(self, tag: str) -> tuple[SourceVariableId, ...]:
        for candidate, variables in self.by_kind:
            if candidate == tag:
                return variables
        return ()

    def union(self, other: WhySupport) -> WhySupport:
        return WhySupport(self.by_kind + other.by_kind)

    def is_subsumed_by(self, other: WhySupport) -> bool:
        return all(
            set(variables).issubset(other.variables_for(tag))
            for tag, variables in self.by_kind
        )


def boolean_presence(
    poly: ProvenancePolynomial,
    trusted: Container[SourceVariableId],
) -> bool:
    for term in poly.terms:
        if all(power.variable in trusted for power in term.powers):
            return True
    return False


def derivation_count(poly: ProvenancePolynomial) -> int:
    return sum(term.coefficient for term in poly.terms)


def why_provenance(
    poly: ProvenancePolynomial,
    kind_of: Callable[[SourceVariableId], str] | Mapping[SourceVariableId, str] | None = None,
) -> tuple[WhySupport, ...]:
    """Return the minimal squarefree supports of ``poly``.

    ``kind_of`` classifies each source variable into a string kind tag. It may
    be a callable or a mapping; a mapping returns ``"other"`` for any variable
    it does not contain. When omitted, every variable is tagged ``"other"``.
    """

    classify = _as_classifier(kind_of)
    supports: list[WhySupport] = []
    for term in poly.terms:
        grouped: DefaultDict[str, list[SourceVariableId]] = defaultdict(list)
        for variable in term.squarefree_support():
            grouped[classify(variable)].append(variable)
        supports.append(WhySupport(tuple((tag, tuple(variables)) for tag, variables in grouped.items())))
    return normalize_why_supports(supports)


def _as_classifier(
    kind_of: Callable[[SourceVariableId], str] | Mapping[SourceVariableId, str] | None,
) -> Callable[[SourceVariableId], str]:
    if kind_of is None:
        return lambda _variable: "other"
    if isinstance(kind_of, Mapping):
        mapping = kind_of
        return lambda variable: mapping.get(variable, "other")
    return kind_of


def normalize_why_supports(supports: list[WhySupport]) -> tuple[WhySupport, ...]:
    unique = {support.by_kind: support for support in supports}
    ordered = sorted(unique.values(), key=lambda support: (support.size, support.by_kind))
    minimal: list[WhySupport] = []
    for candidate in ordered:
        if any(existing.is_subsumed_by(candidate) for existing in minimal):
            continue
        minimal.append(candidate)
    return tuple(minimal)


class _TropicalCostHomomorphism:
    """Min-plus cost projection; these floats are costs, not confidence values."""

    def __init__(self, costs: Mapping[SourceVariableId, float]) -> None:
        self._costs = costs

    @property
    def zero(self) -> float:
        return inf

    @property
    def one(self) -> float:
        return 0.0

    def add(self, left: float, right: float) -> float:
        return min(left, right)

    def mul(self, left: float, right: float) -> float:
        return left + right

    def variable(self, variable: SourceVariableId) -> float:
        return float(self._costs.get(variable, inf))


def tropical_cost(
    poly: ProvenancePolynomial,
    costs: Mapping[SourceVariableId, float],
) -> float:
    """Return the preferred derivation cost, not a probability or confidence."""

    return evaluate(poly, _TropicalCostHomomorphism(costs))
