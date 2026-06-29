"""Polynomial-native ATMS label / environment / nogood antichain algebra.

An *environment* is a conjunction of source variables that jointly support a
datum; it is the squarefree support of a single provenance monomial. A *label*
is a disjunction of environments — the set of alternative supports — carried
directly as a :class:`~provenance_semiring.support.SupportEvidence` over a
:class:`~provenance_semiring.polynomial.ProvenancePolynomial`. Each monomial of
the polynomial is one environment; addition is disjunction of supports and
multiplication is conjunction (the cross-product join the ATMS uses to combine
antecedent labels).

The label *is* the polynomial: there is no ``label_to_polynomial`` /
``polynomial_to_label`` round-trip. ``Label.support.polynomial`` is the
polynomial and :meth:`Label.environments` projects it back to its squarefree
supports; that projection is the canonical reading, not a parallel encoding.

Nogoods are reused from :mod:`provenance_semiring.nogoods`: a
:class:`NogoodSet` carries the minimal inconsistent environments as
:class:`ProvenanceNogood` records, and :func:`live` drops every monomial whose
support contains a nogood. ``normalize_environments`` keeps a label minimal —
deduplicated, with supersets and known-nogood environments pruned — so the
stored support stays an antichain.

The algebra is generic over the polynomial indeterminate
:data:`~provenance_semiring.variables.SourceVariableId`. Consumers that give the
variables domain meaning (an assumption id versus a context id, say) supply that
encoding at the call site; this module never interprets a variable.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from provenance_semiring.nogoods import NogoodWitness, ProvenanceNogood, live
from provenance_semiring.polynomial import ProvenancePolynomial
from provenance_semiring.support import SupportEvidence, SupportQuality
from provenance_semiring.variables import SourceVariableId

__all__ = [
    "EnvironmentKey",
    "NogoodSet",
    "Label",
    "JustificationRecord",
    "normalize_environments",
    "combine_labels",
    "merge_labels",
]


@dataclass(frozen=True, order=True)
class EnvironmentKey:
    """An immutable conjunction of supporting source variables.

    The variables are the squarefree support of one provenance monomial: the set
    of sources that, taken together, support the labelled datum. The empty
    environment denotes unconditional support.
    """

    variables: tuple[SourceVariableId, ...] = ()

    def __post_init__(self) -> None:
        normalized = tuple(
            sorted(dict.fromkeys(SourceVariableId(str(variable)) for variable in self.variables))
        )
        object.__setattr__(self, "variables", normalized)

    def union(self, other: EnvironmentKey) -> EnvironmentKey:
        return EnvironmentKey(self.variables + other.variables)

    def subsumes(self, other: EnvironmentKey) -> bool:
        """True when this environment is a (non-strict) subset of ``other``."""

        return set(self.variables).issubset(other.variables)


@dataclass(frozen=True, init=False)
class NogoodSet:
    """Minimal inconsistent environments held as provenance nogoods."""

    provenance_nogoods: tuple[ProvenanceNogood, ...]

    def __init__(
        self,
        environments: Iterable[EnvironmentKey] = (),
        *,
        provenance_nogoods: Iterable[ProvenanceNogood] | None = None,
    ) -> None:
        if provenance_nogoods is None:
            provenance_nogoods = tuple(
                _environment_to_provenance_nogood(environment)
                for environment in normalize_environments(environments)
            )
        object.__setattr__(self, "provenance_nogoods", tuple(provenance_nogoods))

    @property
    def environments(self) -> tuple[EnvironmentKey, ...]:
        return normalize_environments(
            _provenance_nogood_to_environment(nogood) for nogood in self.provenance_nogoods
        )

    def excludes(self, environment: EnvironmentKey) -> bool:
        """True when ``environment`` is killed by some nogood in the set."""

        support = _environment_to_polynomial(environment)
        return not live(support, self.provenance_nogoods).terms


def normalize_environments(
    environments: Iterable[EnvironmentKey],
    *,
    nogoods: NogoodSet | None = None,
) -> tuple[EnvironmentKey, ...]:
    """Deduplicate, drop known-nogood environments, and prune supersets.

    The result is an antichain: no remaining environment is a superset of
    another, so the support stays minimal.
    """

    unique = {
        env.variables: env
        for env in environments
        if nogoods is None or not nogoods.excludes(env)
    }
    ordered = sorted(unique.values(), key=lambda env: (len(env.variables), env.variables))
    minimal: list[EnvironmentKey] = []
    for candidate in ordered:
        if any(existing.subsumes(candidate) for existing in minimal):
            continue
        minimal.append(candidate)
    return tuple(minimal)


@dataclass(frozen=True, init=False, eq=False)
class Label:
    """A minimal antichain of supporting environments, carried as a polynomial.

    The label is its :class:`SupportEvidence`: each monomial of
    ``support.polynomial`` is one environment, and the empty polynomial denotes
    no support (an *out* datum). The empty environment (:meth:`empty`) denotes
    unconditional support (an *in* datum that needs no assumptions).
    """

    support: SupportEvidence

    def __init__(
        self,
        environments: Iterable[EnvironmentKey] = (),
        *,
        support: SupportEvidence | None = None,
    ) -> None:
        if support is None:
            normalized = normalize_environments(environments)
            support = SupportEvidence(
                _environments_to_polynomial(normalized),
                SupportQuality.EXACT,
            )
        object.__setattr__(self, "support", support)

    @property
    def environments(self) -> tuple[EnvironmentKey, ...]:
        return _polynomial_to_environments(self.support.polynomial)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Label):
            return NotImplemented
        return self.environments == other.environments

    def __hash__(self) -> int:
        return hash(self.environments)

    @classmethod
    def empty(cls) -> Label:
        """Unconditional support: the single empty environment."""

        return cls((EnvironmentKey(()),))

    @classmethod
    def from_environments(cls, environments: Iterable[EnvironmentKey]) -> Label:
        return cls(tuple(environments))

    @classmethod
    def from_variable(cls, variable: SourceVariableId) -> Label:
        """Support conditioned on a single source variable."""

        return cls((EnvironmentKey((SourceVariableId(str(variable)),)),))


@dataclass(frozen=True)
class JustificationRecord:
    """A conclusion's label derived from the conjunction of its antecedents."""

    conclusion: str
    antecedents: tuple[Label, ...]
    label: Label

    @classmethod
    def from_antecedents(
        cls,
        conclusion: str,
        antecedents: Sequence[Label],
        *,
        nogoods: NogoodSet | None = None,
    ) -> JustificationRecord:
        return cls(
            conclusion=conclusion,
            antecedents=tuple(antecedents),
            label=combine_labels(*antecedents, nogoods=nogoods),
        )


def combine_labels(*labels: Label, nogoods: NogoodSet | None = None) -> Label:
    """Conjoin antecedent labels by the polynomial cross-product.

    Each antecedent contributes its alternative environments; the combined label
    is every joint choice, filtered through ``nogoods`` so inconsistent joins are
    dropped as they form.
    """

    if not labels:
        return Label.empty()

    support = ProvenancePolynomial.one()
    for label in labels:
        if label.support.polynomial.is_zero():
            return Label(())
        support = support * label.support.polynomial
        if nogoods is not None:
            support = live(support, nogoods.provenance_nogoods)
        if support.is_zero():
            return Label(())
    return Label(support=SupportEvidence(support, SupportQuality.EXACT))


def merge_labels(labels: Iterable[Label], *, nogoods: NogoodSet | None = None) -> Label:
    """Disjoin alternative supports for one datum into a single normalized label."""

    support = ProvenancePolynomial.zero()
    for label in labels:
        support = support + label.support.polynomial
    environments = normalize_environments(_polynomial_to_environments(support), nogoods=nogoods)
    return Label(
        support=SupportEvidence(_environments_to_polynomial(environments), SupportQuality.EXACT)
    )


def _environment_to_provenance_nogood(environment: EnvironmentKey) -> ProvenanceNogood:
    return ProvenanceNogood(
        variables=frozenset(environment.variables),
        witness=NogoodWitness(
            source="provenance_semiring.labels.NogoodSet",
            detail="inconsistent environment projected to provenance nogood",
        ),
    )


def _provenance_nogood_to_environment(nogood: ProvenanceNogood) -> EnvironmentKey:
    return EnvironmentKey(tuple(sorted(nogood.variables, key=str)))


def _environment_to_polynomial(environment: EnvironmentKey) -> ProvenancePolynomial:
    support = ProvenancePolynomial.one()
    for variable in environment.variables:
        support = support * ProvenancePolynomial.variable(variable)
    return support


def _environments_to_polynomial(environments: Iterable[EnvironmentKey]) -> ProvenancePolynomial:
    support = ProvenancePolynomial.zero()
    for environment in environments:
        support = support + _environment_to_polynomial(environment)
    return support


def _polynomial_to_environments(poly: ProvenancePolynomial) -> tuple[EnvironmentKey, ...]:
    environments = [
        EnvironmentKey(tuple(sorted(term.squarefree_support(), key=str))) for term in poly.terms
    ]
    return normalize_environments(environments)
