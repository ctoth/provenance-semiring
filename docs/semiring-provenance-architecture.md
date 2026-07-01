# Semiring Provenance Architecture

Status: design artifact for WS-A1.

Date: 2026-04-17

## Decision

Propstore claims remain typed semantic content. Their support becomes algebraic:

```text
AnnotatedClaim(
    content: ClaimContent,
    support: SupportEvidence,
)

SupportEvidence(
    polynomial: ProvenancePolynomial,
    quality: SupportQuality,
)
```

The polynomial is positive support provenance in the sense of Green, Karvounarakis, and Tannen 2007. Alternative derivations add. Joint derivations multiply. Projections are explicit homomorphisms.

The polynomial is not the claim. It is the support annotation for the claim.

## Why This Fits Propstore

Current ATMS labels are already a why-provenance projection:

- an `EnvironmentKey` is a support monomial;
- `merge_labels` is projected addition;
- `combine_labels` is projected multiplication;
- `NogoodSet` is support-set pruning;
- `Label.environments` is an antichain projection that loses multiplicity.

The semiring substrate preserves the richer support object first, then derives the current ATMS view from it. Once equivalence tests prove the projection matches the current label behavior, label storage can be collapsed into a view instead of remaining a parallel truth.

## Source Variables

Every support-bearing primitive receives a stable source variable:

```text
SourceVariable(
    id,
    role,
    artifact_id,
    canonical_body_hash,
    provenance,
)
```

Roles include claim, rule, measurement, calibration, lifting rule, solver witness, assumption, and context.

Assumptions and contexts are separate roles. Current labels distinguish `assumption_ids` from `context_ids`, and the semiring projection must preserve that split.

Variable ids must be content-addressed and stable. They must not depend on load order or mutable finalization state.

## Polynomials

A polynomial is a canonical sparse sum of terms:

```text
ProvenancePolynomial(
    terms: tuple[PolynomialTerm, ...]
)

PolynomialTerm(
    coefficient,
    powers,
)
```

`N[X]` keeps multiplicity. Why-provenance projects monomials to squarefree support sets and intentionally forgets multiplicity. Both facts matter:

- `2*x*y` and `x*y` differ for derivation count;
- both project to the same ATMS support environment `{x, y}`.

## Nogoods

Solvers do not run inside the semiring. They inspect claim content and emit nogoods:

```text
ProvenanceNogood(
    variables,
    witness,
    provenance,
)
```

`live(polynomial, nogoods)` removes monomials whose squarefree support contains a nogood.

Live filtering is not a generic homomorphism. Homomorphism laws apply to polynomial evaluation before live filtering. Current-world projections should evaluate the live polynomial, but code must not claim that live filtering commutes with every projection.

## Argumentation

Semiring provenance does not replace directional argumentation.

Nogoods express symmetric joint inconsistency. ASPIC+ and Dung still express directed attack, undercut, rebut, and preference-sensitive defeat. The correct architecture is:

```text
polynomials + nogoods + directional rules
    -> derived attack/defeat graph
    -> Dung/ASPIC+ semantics
```

Arguments and defeats gain support annotations. Directionality remains in the argumentation layer.

## Fragility

Derivative-style fragility is real, but it is not the whole fragility subsystem.

```text
fragility(source) = derivative(live(polynomial, nogoods), source)
```

This measures support sensitivity for support-bearing intervention kinds. It does not by itself model missing measurements, conflict interventions, or bridge undercuts. Those intervention families remain explicit unless and until they have tested polynomial equivalents.

## WS-C Contract

Justifiable exceptions and CKR-derived defeats carry support evidence:

```text
JustifiableException(
    target_claim,
    exception_pattern,
    justification_claims,
    context,
    support: SupportEvidence,
    decidability_status,
)

ExceptionDefeat(
    defeated_use,
    exception,
    support: SupportEvidence,
    solver_witness,
)
```

An unsupported exception has zero live support and is not applied. A solver nogood can kill an exception support monomial without deleting the exception object.

## Limits

This design implements positive provenance. It does not claim Green 2007 solves negation-as-failure, nonmonotonic recursion, subjective-logic discount, or probability under dependent sources.

Probability-like projections must carry their assumptions or bounds in the result type. A naked confidence float is not allowed.
