"""Permanent runtime feature toggles.

These flags control operational modes that are always relevant.
They are never removed by hygiene checks.
"""

from pydantic import BaseModel, Field

from app.settings.providers.features._base import FeatureFlag, FlagLifecycle, FlagMeta


class RuntimeFlags(BaseModel):
    simulation: FeatureFlag = Field(
        default_factory=lambda: FeatureFlag(
            meta=FlagMeta(
                lifecycle=FlagLifecycle.permanent,
                description="Simulate OCR without API keys",
            ),
        ),
    )
    beta_features: FeatureFlag = Field(
        default_factory=lambda: FeatureFlag(
            meta=FlagMeta(
                lifecycle=FlagLifecycle.permanent,
                description="Enable beta features",
            ),
        ),
    )
    debug_mode: FeatureFlag = Field(
        default_factory=lambda: FeatureFlag(
            meta=FlagMeta(
                lifecycle=FlagLifecycle.permanent,
                description="Debug and development mode",
            ),
        ),
    )
    demo_mode: FeatureFlag = Field(
        default_factory=lambda: FeatureFlag(
            meta=FlagMeta(
                lifecycle=FlagLifecycle.permanent,
                description="Demo and public mode",
            ),
        ),
    )
    demo_reset: FeatureFlag = Field(
        default_factory=lambda: FeatureFlag(
            meta=FlagMeta(
                lifecycle=FlagLifecycle.permanent,
                description="Allow data reset in demo mode",
            ),
        ),
    )
    always_batch_ocr: FeatureFlag = Field(
        default=FeatureFlag(
            enabled=True,
            meta=FlagMeta(
                lifecycle=FlagLifecycle.permanent,
                description="Always use batch OCR processing",
            ),
        ),
    )
