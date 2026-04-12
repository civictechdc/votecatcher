"""Feature flag configuration provider."""

from pydantic import BaseModel, Field


class FeatureConfig(BaseModel):
    """Feature flag configuration provider."""

    simulation: bool = Field(default=False)
    beta_features: bool = Field(default=False)
    debug_mode: bool = Field(default=False)
    demo_mode: bool = Field(default=False)
