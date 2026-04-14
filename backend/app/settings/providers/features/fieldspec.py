"""Transitional feature flags for configurable field specs plan.

Each flag maps to a gate in plans/configurable-field-specs-plan.md.
Gate implementation flips the flag to True. G10 cleanup removes this entire file
and all if/else branches that gate on these flags.

Usage in code:
    if settings.features.fieldspec.persistence.enabled:
        self._spec_loader()       # G6: load specs into DB
    else:
        pass                      # pre-G6: skip spec loading

Hygiene test (test_feature_flag_hygiene.py) enforces:
- Flag must be referenced in at least one .py file outside this directory
- Flag reference must have a corresponding else/fallback branch
- Flag must have an issue number
"""

from pydantic import BaseModel, Field

from app.settings.providers.features._base import (
    FeatureFlag,
    FlagLifecycle,
    FlagMeta,
    FlagPhase,
)


class FieldSpecFlags(BaseModel):
    persistence: FeatureFlag = Field(
        default_factory=lambda: FeatureFlag(
            meta=FlagMeta(
                lifecycle=FlagLifecycle.transitional,
                issue=12,
                description="G4: region_field_specs table + repo implemented",
            ),
        ),
    )
    service: FeatureFlag = Field(
        default_factory=lambda: FeatureFlag(
            meta=FlagMeta(
                lifecycle=FlagLifecycle.transitional,
                issue=12,
                description="G5-G6: FieldSpecService wired, specs load at startup",
            ),
        ),
    )
    matching: FeatureFlag = Field(
        default_factory=lambda: FeatureFlag(
            meta=FlagMeta(
                lifecycle=FlagLifecycle.transitional,
                issue=12,
                description="G7: MatchingService uses spec-driven weights and templates",
                phase=FlagPhase.ACTIVATED,
            ),
        ),
    )
    voter_list: FeatureFlag = Field(
        default_factory=lambda: FeatureFlag(
            meta=FlagMeta(
                lifecycle=FlagLifecycle.transitional,
                issue=12,
                description="G8: VoterListService uses spec for CSV parsing and hashing",
                phase=FlagPhase.ACTIVATED,
            ),
        ),
    )
    api: FeatureFlag = Field(
        default_factory=lambda: FeatureFlag(
            meta=FlagMeta(
                lifecycle=FlagLifecycle.transitional,
                issue=12,
                description="G9: region selector API + campaign region param",
            ),
        ),
    )

    @property
    def fully_complete(self) -> bool:
        return all(
            [
                self.persistence.enabled,
                self.service.enabled,
                self.matching.enabled,
                self.voter_list.enabled,
                self.api.enabled,
            ]
        )
