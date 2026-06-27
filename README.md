# provenance-semiring

A pure-Python, stdlib-only implementation of the **provenance semiring** of
Green, Karvounarakis, and Tannen (2007), with the why-provenance characterization
of Buneman, Khanna, and Tan (2001).

Provenance is tracked as a polynomial over *source variables* — one stable,
content-addressed indeterminate per source artifact that can witness a
derivation. The two semiring operations have direct meanings:

- `+` collects **alternative** derivations (coefficients count them).
- `*` combines **joint** dependencies within one derivation (exponents count
  repeated use of a source).

Because it is the *universal* commutative semiring, every other provenance model
(boolean trust, derivation counting, why-provenance, tropical cost) is a
homomorphic image. This package gives you the polynomial and those projections.

Zero dependencies, pure stdlib (`hashlib`, `dataclasses`, `enum`, `math`,
`collections`, `typing`). Requires Python 3.11+ (`StrEnum`).

## Install

```powershell
uv add provenance-semiring
```

## Core algebra

```python
from provenance_semiring import (
    ProvenancePolynomial,
    SourceVariableId,
    derive_source_variable_id,
)

a = ProvenancePolynomial.variable(derive_source_variable_id("claim", "doc-1", "h1"))
b = ProvenancePolynomial.variable(derive_source_variable_id("claim", "doc-2", "h2"))

# Two alternative derivations of the same fact, one of which needs both sources.
support = a + a * b
```

- `ProvenancePolynomial`: a canonical sum of `PolynomialTerm`s. Construct with
  `.zero()`, `.one()`, `.variable(id)`, or `.from_terms(...)`. `+` and `*` are
  the semiring operations; terms are collected and sorted canonically, so equal
  polynomials compare and hash equal.
- `PolynomialTerm(coefficient, powers)`: a monomial with a positive integer
  coefficient and a tuple of `VariablePower`s.
- `VariablePower(variable, exponent)`: a source variable raised to a positive
  integer exponent.
- `SourceVariableId`: a `NewType(str)` indeterminate.
- `derive_source_variable_id(role, artifact_id, canonical_body_hash, *, prefix="var")`:
  derive a stable id of the form `<prefix>:source:<role>:<sha256>`. `role` is a
  free-form caller-chosen tag.
- `SourceVariable`: a content-addressed source variable bundling
  `id / role / artifact_id / canonical_body_hash / prefix`, validating that the
  id is the derived value.

## Homomorphic evaluation

```python
from provenance_semiring import Homomorphism, evaluate
```

`evaluate(poly, hom)` applies the semiring's universal property: any object
implementing the `Homomorphism` protocol (`zero`, `one`, `add`, `mul`,
`variable`) defines a target semiring, and `evaluate` folds the polynomial into
it. The projections below are built this way.

## Projections

- `boolean_presence(poly, trusted)`: is there at least one derivation using only
  trusted source variables?
- `derivation_count(poly)`: the N-semiring image — total number of derivations
  (sum of coefficients).
- `why_provenance(poly, kind_of=None)`: the minimal squarefree supports
  (Buneman et al. 2001), i.e. the irredundant sets of sources that justify the
  result. `kind_of` is an optional classifier (a callable or a mapping) that
  buckets each source variable under a string *kind tag*; the returned
  `WhySupport`s group their variables by that tag. With no classifier every
  variable is tagged `"other"`.
- `normalize_why_supports(supports)`: deduplicate and keep only subset-minimal
  supports.
- `tropical_cost(poly, costs)`: the min-plus (tropical) projection — the cost of
  the cheapest derivation, given per-source costs. These floats are costs, not
  confidences.

```python
from provenance_semiring import why_provenance

def kind_of(variable):
    return "assumption" if variable.endswith("asm") else "other"

for support in why_provenance(a * b, kind_of):
    print(support.variables_for("other"))
```

## Derivatives

`partial_derivative(poly, variable)` is the formal derivative with respect to a
source variable: it isolates, with multiplicity, the derivations that use that
source. It obeys the sum and product rules.

## Nogood filtering

```python
from provenance_semiring import NogoodWitness, ProvenanceNogood, live

nogood = ProvenanceNogood(frozenset({var_x, var_y}), NogoodWitness("checker", "x and y conflict"))
surviving = live(poly, [nogood])
```

A `ProvenanceNogood` names a set of source variables that cannot jointly hold.
`live` removes every monomial whose support is a superset of some nogood,
leaving the still-consistent derivations with their coefficients intact. An
empty-set nogood kills every monomial (the environment is inconsistent).

## Provenance carriers

The algebra deliberately carries **no** provenance metadata. Source variables
are bare content-addressed ids; nogoods carry only a lightweight witness. If you
need to attach a richer provenance record (named graphs, git notes, status
discriminators, opinion algebra), key your own carrier by `SourceVariableId`
outside this package.

## Papers

See `papers/` for extraction notes:

- `Green_2007_ProvenanceSemirings` — Green, Karvounarakis, Tannen, *Provenance
  Semirings*, PODS 2007. The universal positive provenance semiring N[X].
- `Buneman_2001_CharacterizationDataProvenance` — Buneman, Khanna, Tan, *Why and
  Where: A Characterization of Data Provenance*, ICDT 2001. The why/where split
  and minimal-witness (why-provenance) semantics.

## License

MIT
