# Changelog

## 0.1.0

Initial extraction from the propstore reference implementation.

- Provenance polynomial algebra: `ProvenancePolynomial`, `PolynomialTerm`,
  `VariablePower` over `SourceVariableId` source variables, with the `+` and `*`
  semiring operations and canonical term collection.
- Content-addressed source variables: `SourceVariable` and
  `derive_source_variable_id(role, artifact_id, canonical_body_hash, *, prefix)`.
  The propstore-specific `SourceRole` enum is dropped; `role` is a free-form
  string tag and the id prefix is a caller parameter (default `"var"`).
- Universal homomorphic evaluation: `Homomorphism` protocol and `evaluate`.
- Formal `partial_derivative` (sum and product rules).
- Projections: `boolean_presence`, `derivation_count`, `why_provenance`,
  `normalize_why_supports`, `tropical_cost`. `WhySupport` is generic over
  caller-supplied string kind tags; `why_provenance` takes a `kind_of`
  classifier instead of propstore assumption/context id types.
- Nogood filtering: `NogoodWitness`, `ProvenanceNogood`, `live`.
- Support evidence: `SupportEvidence`, `SupportQuality`.
- No propstore dependency and no provenance carrier: the propstore `Provenance`
  field was removed from `SourceVariable` and `ProvenanceNogood`. Consumers
  attach their own provenance carrier externally, keyed by source variable id.
- Pure stdlib, zero runtime dependencies.
