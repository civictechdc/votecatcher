"""Unit tests for the feature flag framework types.

Validates the base primitives: FeatureFlag, FlagMeta, FlagLifecycle,
AllFeatures registry, and domain models.
"""

from app.settings.providers.features import AllFeatures
from app.settings.providers.features._base import FeatureFlag, FlagLifecycle, FlagMeta
from app.settings.providers.features.fieldspec import FieldSpecFlags
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


class TestFieldSpecFlags:
    def test_all_transitional(self):
        flags = FieldSpecFlags()
        for name in FieldSpecFlags.model_fields:
            flag = getattr(flags, name)
            assert isinstance(flag, FeatureFlag)
            assert flag.meta.lifecycle == FlagLifecycle.transitional

    def test_all_have_issue(self):
        flags = FieldSpecFlags()
        for name in FieldSpecFlags.model_fields:
            flag = getattr(flags, name)
            assert flag.meta.issue is not None, f"{name} missing issue"

    def test_all_start_disabled(self):
        flags = FieldSpecFlags()
        for name in FieldSpecFlags.model_fields:
            flag = getattr(flags, name)
            assert flag.enabled is False

    def test_fully_complete_false_initially(self):
        flags = FieldSpecFlags()
        assert flags.fully_complete is False

    def test_fully_complete_true_when_all_enabled(self):
        flags = FieldSpecFlags()
        defaults = FieldSpecFlags()
        for name in FieldSpecFlags.model_fields:
            default_meta = getattr(defaults, name).meta
            setattr(
                flags,
                name,
                FeatureFlag(enabled=True, meta=default_meta),
            )
        assert flags.fully_complete is True

    def test_fully_complete_false_if_one_missing(self):
        flags = FieldSpecFlags()
        defaults = FieldSpecFlags()
        names = list(FieldSpecFlags.model_fields.keys())
        for name in names[:-1]:
            default_meta = getattr(defaults, name).meta
            setattr(
                flags,
                name,
                FeatureFlag(enabled=True, meta=default_meta),
            )
        assert flags.fully_complete is False


class TestAllFeatures:
    def test_has_runtime_and_fieldspec(self):
        features = AllFeatures()
        assert hasattr(features, "runtime")
        assert hasattr(features, "fieldspec")
        assert isinstance(features.runtime, RuntimeFlags)
        assert isinstance(features.fieldspec, FieldSpecFlags)

    def test_all_transitional_collects_only_transitional(self):
        features = AllFeatures()
        transitional = features.all_transitional()
        domain_names = {domain for domain, _, _ in transitional}
        assert domain_names == {"fieldspec"}
        assert len(transitional) == 5

    def test_all_transitional_format(self):
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
        expected = {"runtime", "fieldspec"}
        actual = set(AllFeatures.model_fields.keys())
        assert actual == expected
