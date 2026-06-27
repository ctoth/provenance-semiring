"""Semiring coefficients survive the SupportEvidence carrier.

Adapted from the upstream test of the same name. The original threaded a
``ProvenancePolynomial`` through the upstream ``core.labels.combine_labels`` and
asserted the coefficient survived. ``Label``/``combine_labels`` are upstream
types outside this package, so this version exercises the package-level
invariant the original guarded: a ``SupportEvidence`` wrapping a coefficient-``k``
monomial reports ``derivation_count == k``.
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from provenance_semiring import (
    PolynomialTerm,
    ProvenancePolynomial,
    SourceVariableId,
    SupportEvidence,
    SupportQuality,
    VariablePower,
    derivation_count,
)


@given(st.integers(min_value=2, max_value=8))
@pytest.mark.property
def test_support_evidence_preserves_semiring_coefficients(coefficient: int) -> None:
    variable = SourceVariableId("var:source:semiring")
    evidence = SupportEvidence(
        ProvenancePolynomial.from_terms(
            (
                PolynomialTerm(
                    coefficient,
                    (VariablePower(variable, 1),),
                ),
            )
        ),
        SupportQuality.EXACT,
    )

    assert derivation_count(evidence.polynomial) == coefficient
