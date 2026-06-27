"""Stable source variables for provenance polynomials.

A source variable is the indeterminate of a Green-style provenance polynomial:
one stable, content-addressed identifier per source artifact that can witness a
derivation. The role is an arbitrary caller-supplied tag (the upstream
reference deployment used roles like ``claim`` or ``rule``; this package keeps
the role generic so consumers pick their own vocabulary).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import NewType


SourceVariableId = NewType("SourceVariableId", str)


@dataclass(frozen=True)
class SourceVariable:
    """A content-addressed source variable.

    ``role`` is a free-form string tag chosen by the consumer. ``id`` must be
    the value derived from ``role``, ``artifact_id``, ``canonical_body_hash``,
    and ``prefix`` so that identity stays a pure function of content.
    """

    id: SourceVariableId
    role: str
    artifact_id: str
    canonical_body_hash: str
    prefix: str = "var"

    def __post_init__(self) -> None:
        object.__setattr__(self, "role", str(self.role))
        object.__setattr__(self, "artifact_id", str(self.artifact_id))
        object.__setattr__(self, "canonical_body_hash", str(self.canonical_body_hash))
        object.__setattr__(self, "prefix", str(self.prefix))
        expected = derive_source_variable_id(
            self.role,
            self.artifact_id,
            self.canonical_body_hash,
            prefix=self.prefix,
        )
        if self.id != expected:
            raise ValueError(
                "SourceVariable id must be derived from role, artifact_id, "
                "canonical_body_hash, and prefix"
            )


def derive_source_variable_id(
    role: str,
    artifact_id: str,
    canonical_body_hash: str,
    *,
    prefix: str = "var",
) -> SourceVariableId:
    """Derive a stable source-variable id from content.

    The id is ``<prefix>:source:<role>:<sha256>`` where the digest is taken over
    the role, artifact id, and canonical body hash. ``prefix`` only shapes the
    id string; it does not enter the digest.
    """

    body = "\0".join((str(role), str(artifact_id), str(canonical_body_hash)))
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    return SourceVariableId(f"{prefix}:source:{role}:{digest}")
