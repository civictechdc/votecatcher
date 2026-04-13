"""Feature flag registry — one sub-model per domain.

Usage:
    from app.settings.providers.features import AllFeatures

    features = AllFeatures()
    features.runtime.simulation.enabled   # True/False
    features.fieldspec.matching.enabled   # True/False

Adding a new flag domain:
1. Create a new file in this directory (e.g., newfeature.py)
2. Define a FooFlags(BaseModel) with FeatureFlag fields
3. Add it as a field on AllFeatures below
4. Update test_feature_flag_hygiene.py domain_files expected set

Removing a transitional domain (G10 cleanup pattern):
1. Delete the domain file
2. Remove from AllFeatures
3. Delete all if/else branches that reference it
4. Hygiene test confirms nothing stale remains
"""

from pydantic import BaseModel, Field

from app.settings.providers.features._base import FeatureFlag, FlagLifecycle
from app.settings.providers.features.fieldspec import FieldSpecFlags
from app.settings.providers.features.runtime import RuntimeFlags


class AllFeatures(BaseModel):
    runtime: RuntimeFlags = Field(default_factory=RuntimeFlags)
    fieldspec: FieldSpecFlags = Field(default_factory=FieldSpecFlags)

    def all_transitional(self) -> list[tuple[str, str, FeatureFlag]]:
        """Collect all transitional flags with (domain, name, flag) for hygiene checks."""
        flags: list[tuple[str, str, FeatureFlag]] = []
        for domain_name in self.model_fields:
            domain = getattr(self, domain_name)
            for flag_name in domain.model_fields:
                flag = getattr(domain, flag_name)
                if (
                    isinstance(flag, FeatureFlag)
                    and flag.meta.lifecycle == FlagLifecycle.transitional
                ):
                    flags.append((domain_name, flag_name, flag))
        return flags


__all__ = [
    "AllFeatures",
    "RuntimeFlags",
    "FieldSpecFlags",
    "FeatureFlag",
    "FlagLifecycle",
]
