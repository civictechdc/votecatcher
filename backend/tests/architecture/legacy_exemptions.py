"""Explicit, temporary backend violation baseline and validation helpers.

Each exemption names one source-to-target edge with a reason, owner, removal
issue, and removal criteria. Domain-layer and import-cycle violations are not
exemptible. New code must not add exemptions.

Currently empty: all architecture rules pass without baseline edges.
Populate this tuple only when a real pre-existing router-to-data or
router-to-persistence edge is discovered during a failing test run.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class LegacyExemption:
    source: str
    target: str
    reason: str
    owner: str
    removal_issue: str
    removal_criteria: str


ROUTER_TO_DATA_EXEMPTIONS: tuple[LegacyExemption, ...] = ()
ROUTER_TO_PERSISTENCE_EXEMPTIONS: tuple[LegacyExemption, ...] = ()
