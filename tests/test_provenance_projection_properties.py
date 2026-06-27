"""Property tests for provenance polynomial projections."""

from __future__ import annotations

import pytest
from dataclasses import dataclass

from hypothesis import given, settings
from hypothesis import strategies as st

from provenance_semiring import (
    PolynomialTerm,
    ProvenancePolynomial,
    SourceVariableId,
    VariablePower,
    boolean_presence,
    derivation_count,
    evaluate,
    tropical_cost,
    why_provenance,
)


_PROP_SETTINGS = settings(deadline=None)
_VARIABLES = tuple(SourceVariableId(f"var:source:test:{name}") for name in ("a", "b", "c"))


@st.composite
def polynomials(draw):
    terms = []
    for _ in range(draw(st.integers(min_value=0, max_value=5))):
        coefficient = draw(st.integers(min_value=1, max_value=3))
        variables = draw(st.lists(st.sampled_from(_VARIABLES), min_size=0, max_size=3))
        terms.append(
            PolynomialTerm(
                coefficient,
                tuple(VariablePower(variable, 1) for variable in variables),
            )
        )
    return ProvenancePolynomial(tuple(terms))


@dataclass(frozen=True)
class CountHomomorphism:
    @property
    def zero(self) -> int:
        return 0

    @property
    def one(self) -> int:
        return 1

    def add(self, left: int, right: int) -> int:
        return left + right

    def mul(self, left: int, right: int) -> int:
        return left * right

    def variable(self, variable: SourceVariableId) -> int:
        return 1


class TestProjectionHomomorphisms:
    @pytest.mark.property
    @given(polynomials(), polynomials())
    @_PROP_SETTINGS
    def test_count_projection_preserves_addition(self, left, right):
        hom = CountHomomorphism()
        assert evaluate(left + right, hom) == hom.add(evaluate(left, hom), evaluate(right, hom))

    @pytest.mark.property
    @given(polynomials(), polynomials())
    @_PROP_SETTINGS
    def test_count_projection_preserves_multiplication(self, left, right):
        hom = CountHomomorphism()
        assert evaluate(left * right, hom) == hom.mul(evaluate(left, hom), evaluate(right, hom))

    @pytest.mark.property
    @given(polynomials())
    @_PROP_SETTINGS
    def test_derivation_count_matches_count_homomorphism(self, poly):
        assert derivation_count(poly) == evaluate(poly, CountHomomorphism())

    def test_boolean_presence_requires_trusted_variables_for_one_monomial(self):
        a = SourceVariableId("var:source:test:a")
        b = SourceVariableId("var:source:test:b")
        poly = ProvenancePolynomial.variable(a) * ProvenancePolynomial.variable(b)

        assert boolean_presence(poly, {a, b})
        assert not boolean_presence(poly, {a})

    def test_why_projection_preserves_kind_split(self):
        # Adapted from the upstream assumption/context split test: the seam
        # change replaces AssumptionId/ContextId buckets with caller-supplied
        # string kind tags, so we classify variables into "assumption",
        # "context", and "other" and read them back per tag.
        assumption_var = SourceVariableId("var:source:test:assumption")
        context_var = SourceVariableId("var:source:test:context")
        other_var = SourceVariableId("var:source:test:other")
        poly = (
            ProvenancePolynomial.variable(assumption_var)
            * ProvenancePolynomial.variable(context_var)
            * ProvenancePolynomial.variable(other_var)
        )

        kinds = {assumption_var: "assumption", context_var: "context"}

        result = why_provenance(poly, lambda variable: kinds.get(variable, "other"))

        assert len(result) == 1
        assert result[0].variables_for("assumption") == (assumption_var,)
        assert result[0].variables_for("context") == (context_var,)
        assert result[0].variables_for("other") == (other_var,)

    def test_why_projection_accepts_mapping_classifier(self):
        # The kind_of argument also accepts a Mapping, defaulting absent
        # variables to the "other" tag.
        assumption_var = SourceVariableId("var:source:test:assumption")
        other_var = SourceVariableId("var:source:test:other")
        poly = (
            ProvenancePolynomial.variable(assumption_var)
            * ProvenancePolynomial.variable(other_var)
        )

        result = why_provenance(poly, {assumption_var: "assumption"})

        assert len(result) == 1
        assert result[0].variables_for("assumption") == (assumption_var,)
        assert result[0].variables_for("other") == (other_var,)

    def test_tropical_cost_uses_min_plus_projection(self):
        a = SourceVariableId("var:source:test:a")
        b = SourceVariableId("var:source:test:b")
        c = SourceVariableId("var:source:test:c")
        poly = (
            ProvenancePolynomial.variable(a) * ProvenancePolynomial.variable(b)
            + ProvenancePolynomial.variable(c)
        )

        assert tropical_cost(poly, {a: 3.0, b: 4.0, c: 10.0}) == 7.0
