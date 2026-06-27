"""Homomorphic evaluation for provenance polynomials.

The defining property of the provenance semiring (Green et al. 2007) is that any
semiring homomorphism on the source variables extends uniquely to the whole
polynomial. ``evaluate`` applies that universal property: given a target
semiring described by a :class:`Homomorphism`, it folds a polynomial into that
semiring's value.
"""

from __future__ import annotations

from typing import Protocol, TypeVar

from provenance_semiring.polynomial import ProvenancePolynomial
from provenance_semiring.variables import SourceVariableId


K = TypeVar("K")


class Homomorphism(Protocol[K]):
    @property
    def zero(self) -> K: ...

    @property
    def one(self) -> K: ...

    def add(self, left: K, right: K) -> K: ...

    def mul(self, left: K, right: K) -> K: ...

    def variable(self, variable: SourceVariableId) -> K: ...


def evaluate(poly: ProvenancePolynomial, hom: Homomorphism[K]) -> K:
    total = hom.zero
    for term in poly.terms:
        value = hom.one
        for power in term.powers:
            base = hom.variable(power.variable)
            factor = hom.one
            for _ in range(power.exponent):
                factor = hom.mul(factor, base)
            value = hom.mul(value, factor)
        for _ in range(term.coefficient):
            total = hom.add(total, value)
    return total
