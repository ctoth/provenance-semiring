"""Property tests for Green-style provenance polynomial algebra."""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from provenance_semiring import (
    PolynomialTerm,
    ProvenancePolynomial,
    SourceVariableId,
    VariablePower,
)
from provenance_semiring.projections import why_provenance


_PROP_SETTINGS = settings(deadline=None)
_VARIABLES = st.sampled_from(
    tuple(SourceVariableId(f"var:source:test:{name}") for name in ("a", "b", "c", "d"))
)


@st.composite
def terms(draw):
    coefficient = draw(st.integers(min_value=1, max_value=4))
    variables = draw(st.lists(_VARIABLES, min_size=0, max_size=4))
    powers = tuple(VariablePower(variable, 1) for variable in variables)
    return PolynomialTerm(coefficient, powers)


@st.composite
def polynomials(draw):
    return ProvenancePolynomial(tuple(draw(st.lists(terms(), min_size=0, max_size=5))))


class TestProvenancePolynomialAlgebra:
    @pytest.mark.property
    @given(polynomials(), polynomials(), polynomials())
    @_PROP_SETTINGS
    def test_addition_is_associative(self, left, middle, right):
        assert (left + middle) + right == left + (middle + right)

    @pytest.mark.property
    @given(polynomials(), polynomials())
    @_PROP_SETTINGS
    def test_addition_is_commutative(self, left, right):
        assert left + right == right + left

    @pytest.mark.property
    @given(polynomials())
    @_PROP_SETTINGS
    def test_zero_is_additive_identity(self, poly):
        assert poly + ProvenancePolynomial.zero() == poly
        assert ProvenancePolynomial.zero() + poly == poly

    @pytest.mark.property
    @given(polynomials(), polynomials(), polynomials())
    @_PROP_SETTINGS
    def test_multiplication_is_associative(self, left, middle, right):
        assert (left * middle) * right == left * (middle * right)

    @pytest.mark.property
    @given(polynomials(), polynomials())
    @_PROP_SETTINGS
    def test_multiplication_is_commutative(self, left, right):
        assert left * right == right * left

    @pytest.mark.property
    @given(polynomials())
    @_PROP_SETTINGS
    def test_one_and_zero_are_multiplicative_identities(self, poly):
        assert poly * ProvenancePolynomial.one() == poly
        assert ProvenancePolynomial.one() * poly == poly
        assert poly * ProvenancePolynomial.zero() == ProvenancePolynomial.zero()
        assert ProvenancePolynomial.zero() * poly == ProvenancePolynomial.zero()

    @pytest.mark.property
    @given(polynomials(), polynomials(), polynomials())
    @_PROP_SETTINGS
    def test_multiplication_distributes_over_addition(self, left, middle, right):
        assert left * (middle + right) == (left * middle) + (left * right)

    @pytest.mark.property
    @given(polynomials())
    @_PROP_SETTINGS
    def test_canonicalization_is_idempotent(self, poly):
        assert ProvenancePolynomial(poly.terms) == poly

    def test_multiplication_of_sums_preserves_multiplicity(self):
        a = ProvenancePolynomial.variable(SourceVariableId("var:source:test:a"))
        b = ProvenancePolynomial.variable(SourceVariableId("var:source:test:b"))

        result = (a + a) * b

        assert result == ProvenancePolynomial(
            (
                PolynomialTerm(
                    2,
                    (
                        VariablePower(SourceVariableId("var:source:test:a"), 1),
                        VariablePower(SourceVariableId("var:source:test:b"), 1),
                    ),
                ),
            )
        )

    def test_why_projection_is_invariant_under_repeated_variable_power(self):
        x = SourceVariableId("var:source:test:x")
        linear = ProvenancePolynomial.variable(x)
        repeated = ProvenancePolynomial((PolynomialTerm(1, (VariablePower(x, 3),)),))

        assert why_provenance(linear) == why_provenance(repeated)
