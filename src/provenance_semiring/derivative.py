"""Derivative-style source sensitivity for provenance polynomials.

The formal derivative with respect to a source variable isolates the
derivations that actually use that source, with multiplicity. It satisfies the
sum and product rules, so it composes through the polynomial algebra and lets a
consumer ask "how does this result depend on source x?".
"""

from __future__ import annotations

from provenance_semiring.polynomial import (
    PolynomialTerm,
    ProvenancePolynomial,
    VariablePower,
)
from provenance_semiring.variables import SourceVariableId


def partial_derivative(
    poly: ProvenancePolynomial,
    variable: SourceVariableId,
) -> ProvenancePolynomial:
    normalized = SourceVariableId(str(variable))
    terms: list[PolynomialTerm] = []
    for term in poly.terms:
        next_powers: list[VariablePower] = []
        multiplier = 0
        for power in term.powers:
            if power.variable == normalized:
                multiplier = power.exponent
                if power.exponent > 1:
                    next_powers.append(VariablePower(power.variable, power.exponent - 1))
            else:
                next_powers.append(power)
        if multiplier:
            terms.append(PolynomialTerm(term.coefficient * multiplier, tuple(next_powers)))
    return ProvenancePolynomial(tuple(terms))
