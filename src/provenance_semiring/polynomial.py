"""Canonical provenance polynomials over source variables.

Implements the positive-coefficient polynomial semiring N[X] of Green, Karvounarakis,
and Tannen (2007): elements are finite sums of monomials over source variables,
addition is term collection, and multiplication is the usual polynomial product.
Coefficients count alternative derivations; exponents count joint use of a source
within one derivation.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import DefaultDict, Iterable

from provenance_semiring.variables import SourceVariableId


@dataclass(frozen=True, order=True)
class VariablePower:
    variable: SourceVariableId
    exponent: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "variable", SourceVariableId(str(self.variable)))
        object.__setattr__(self, "exponent", int(self.exponent))
        if self.exponent <= 0:
            raise ValueError("VariablePower exponent must be positive")


@dataclass(frozen=True)
class PolynomialTerm:
    coefficient: int
    powers: tuple[VariablePower, ...] = ()

    def __post_init__(self) -> None:
        coefficient = int(self.coefficient)
        if coefficient <= 0:
            raise ValueError("PolynomialTerm coefficient must be positive")
        object.__setattr__(self, "coefficient", coefficient)
        combined: DefaultDict[SourceVariableId, int] = defaultdict(int)
        for power in self.powers:
            combined[power.variable] += power.exponent
        object.__setattr__(
            self,
            "powers",
            tuple(
                VariablePower(variable, exponent)
                for variable, exponent in sorted(combined.items(), key=lambda item: str(item[0]))
            ),
        )

    @property
    def key(self) -> tuple[VariablePower, ...]:
        return self.powers

    def squarefree_support(self) -> frozenset[SourceVariableId]:
        return frozenset(power.variable for power in self.powers)


@dataclass(frozen=True)
class ProvenancePolynomial:
    terms: tuple[PolynomialTerm, ...] = ()

    def __post_init__(self) -> None:
        coefficients: DefaultDict[tuple[VariablePower, ...], int] = defaultdict(int)
        for term in self.terms:
            coefficients[term.key] += term.coefficient
        object.__setattr__(
            self,
            "terms",
            tuple(
                PolynomialTerm(coefficient, powers)
                for powers, coefficient in sorted(
                    coefficients.items(),
                    key=lambda item: tuple((str(power.variable), power.exponent) for power in item[0]),
                )
                if coefficient > 0
            ),
        )

    @classmethod
    def zero(cls) -> ProvenancePolynomial:
        return cls(())

    @classmethod
    def one(cls) -> ProvenancePolynomial:
        return cls((PolynomialTerm(1, ()),))

    @classmethod
    def variable(cls, variable: SourceVariableId) -> ProvenancePolynomial:
        return cls((PolynomialTerm(1, (VariablePower(variable, 1),)),))

    @classmethod
    def from_terms(cls, terms: Iterable[PolynomialTerm]) -> ProvenancePolynomial:
        return cls(tuple(terms))

    def __add__(self, other: ProvenancePolynomial) -> ProvenancePolynomial:
        if not isinstance(other, ProvenancePolynomial):
            return NotImplemented
        return ProvenancePolynomial(self.terms + other.terms)

    def __mul__(self, other: ProvenancePolynomial) -> ProvenancePolynomial:
        if not isinstance(other, ProvenancePolynomial):
            return NotImplemented
        if not self.terms or not other.terms:
            return ProvenancePolynomial.zero()
        products: list[PolynomialTerm] = []
        for left in self.terms:
            for right in other.terms:
                products.append(
                    PolynomialTerm(
                        left.coefficient * right.coefficient,
                        left.powers + right.powers,
                    )
                )
        return ProvenancePolynomial(tuple(products))

    def squarefree_supports(self) -> tuple[frozenset[SourceVariableId], ...]:
        return tuple(term.squarefree_support() for term in self.terms)

    def is_zero(self) -> bool:
        return not self.terms
