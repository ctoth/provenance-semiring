"""provenance-semiring: Green et al. (2007) provenance polynomials.

A pure, stdlib-only implementation of the positive provenance semiring N[X]:
provenance polynomials over content-addressed source variables, the semiring
operations, universal homomorphic evaluation, formal derivatives, why-provenance
minimal supports (Buneman et al. 2001), nogood filtering, and a tropical
min-plus cost projection.

The algebra carries no provenance metadata of its own. Consumers attach their
own provenance carrier externally and keep it keyed by source variable id.
"""

from __future__ import annotations

from provenance_semiring.derivative import partial_derivative
from provenance_semiring.homomorphism import Homomorphism, evaluate
from provenance_semiring.nogoods import NogoodWitness, ProvenanceNogood, live
from provenance_semiring.polynomial import (
    PolynomialTerm,
    ProvenancePolynomial,
    VariablePower,
)
from provenance_semiring.projections import (
    WhySupport,
    boolean_presence,
    derivation_count,
    normalize_why_supports,
    tropical_cost,
    why_provenance,
)
from provenance_semiring.support import SupportEvidence, SupportQuality
from provenance_semiring.variables import (
    SourceVariable,
    SourceVariableId,
    derive_source_variable_id,
)

__version__ = "0.1.0"

__all__ = [
    "Homomorphism",
    "NogoodWitness",
    "PolynomialTerm",
    "ProvenanceNogood",
    "ProvenancePolynomial",
    "SourceVariable",
    "SourceVariableId",
    "SupportEvidence",
    "SupportQuality",
    "VariablePower",
    "WhySupport",
    "boolean_presence",
    "derivation_count",
    "derive_source_variable_id",
    "evaluate",
    "live",
    "normalize_why_supports",
    "partial_derivative",
    "tropical_cost",
    "why_provenance",
    "__version__",
]
