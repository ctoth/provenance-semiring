"""Nogood filtering for provenance polynomials.

A nogood names a set of source variables that cannot jointly hold. ``live``
drops every monomial whose squarefree support contains a nogood set, so a
polynomial can be filtered down to its still-consistent derivations without
collapsing coefficients of the survivors.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from provenance_semiring.polynomial import PolynomialTerm, ProvenancePolynomial
from provenance_semiring.variables import SourceVariableId


@dataclass(frozen=True)
class NogoodWitness:
    source: str
    detail: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "source", str(self.source))
        object.__setattr__(self, "detail", str(self.detail))


@dataclass(frozen=True)
class ProvenanceNogood:
    variables: frozenset[SourceVariableId]
    witness: NogoodWitness

    def __post_init__(self) -> None:
        variables = frozenset(SourceVariableId(str(variable)) for variable in self.variables)
        object.__setattr__(self, "variables", variables)


def live(
    poly: ProvenancePolynomial,
    nogoods: Iterable[ProvenanceNogood],
) -> ProvenancePolynomial:
    nogood_sets = tuple(nogood.variables for nogood in nogoods)
    if not nogood_sets:
        return poly
    kept: list[PolynomialTerm] = []
    for term in poly.terms:
        support = term.squarefree_support()
        if any(nogood.issubset(support) for nogood in nogood_sets):
            continue
        kept.append(term)
    return ProvenancePolynomial(tuple(kept))
