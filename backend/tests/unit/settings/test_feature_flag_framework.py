"""Unit tests for the feature flag framework types.

Validates the base primitives: FeatureFlag, FlagMeta, FlagLifecycle,
AllFeatures registry, and domain models.
"""

from app.settings.providers.features import AllFeatures
from app.settings.providers.features._base import FeatureFlag, FlagLifecycle, FlagMeta
from app.settings.providers.features.runtime import RuntimeFlags


class TestFeatureFlag:
    def test_default_disabled(self):
        flag = FeatureFlag(meta=FlagMeta(lifecycle=FlagLifecycle.permanent))
        assert flag.enabled is False

    def test_enabled_explicitly(self):
        flag = FeatureFlag(
            enabled=True,
            meta=FlagMeta(lifecycle=FlagLifecycle.permanent),
        )
        assert flag.enabled is True

    def test_meta_description(self):
        flag = FeatureFlag(
            meta=FlagMeta(
                lifecycle=FlagLifecycle.transitional,
                description="Test flag",
                issue=42,
            ),
        )
        assert flag.meta.description == "Test flag"
        assert flag.meta.issue == 42


class TestFlagLifecycle:
    def test_permanent_values(self):
        assert FlagLifecycle.permanent == "permanent"

    def test_transitional_values(self):
        assert FlagLifecycle.transitional == "transitional"


class TestFlagMeta:
    def test_permanent_no_issue_required(self):
        meta = FlagMeta(lifecycle=FlagLifecycle.permanent, description="ok")
        assert meta.issue is None

    def test_transitional_with_issue(self):
        meta = FlagMeta(
            lifecycle=FlagLifecycle.transitional,
            issue=99,
            description="transitional flag",
        )
        assert meta.issue == 99


class TestRuntimeFlags:
    def test_all_permanent(self):
        flags = RuntimeFlags()
        for name in RuntimeFlags.model_fields:
            flag = getattr(flags, name)
            assert isinstance(flag, FeatureFlag)
            assert flag.meta.lifecycle == FlagLifecycle.permanent

    def test_defaults(self):
        flags = RuntimeFlags()
        assert flags.simulation.enabled is False
        assert flags.always_batch_ocr.enabled is True

    def test_override_via_construction(self):
        defaults = RuntimeFlags()
        flags = RuntimeFlags(
            simulation=FeatureFlag(
                enabled=True,
                meta=defaults.simulation.meta,
            ),
        )
        assert flags.simulation.enabled is True


class TestAllFeatures:
    def test_has_runtime(self):
        features = AllFeatures()
        assert hasattr(features, "runtime")
        assert isinstance(features.runtime, RuntimeFlags)

    def test_all_transitional_collects_only_transitional(self):
        features = AllFeatures()
        transitional = features.all_transitional()
        for domain, name, flag in transitional:
            assert isinstance(domain, str)
            assert isinstance(name, str)
            assert isinstance(flag, FeatureFlag)
            assert flag.meta.lifecycle == FlagLifecycle.transitional

    def test_no_permanent_in_transitional(self):
        features = AllFeatures()
        transitional = features.all_transitional()
        for domain, name, flag in transitional:
            assert flag.meta.lifecycle != FlagLifecycle.permanent

    def test_domain_registry_matches_model_fields(self):
        expected = {"runtime"}
        actual = set(AllFeatures.model_fields.keys())
        assert actual == expected
