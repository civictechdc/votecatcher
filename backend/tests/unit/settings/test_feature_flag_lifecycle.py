"""Lifecycle integration test for the feature flag framework.

Simulates the full lifecycle of a transitional flag:
1. DEFINE: add flag to a domain model
2. USE: code references the flag with an else branch
3. COMPLETE: flip flag to enabled
4. CLEANUP: remove flag, remove if/else branch, remove domain file

This test uses a temporary domain to avoid polluting real flags.
Validates that the hygiene checks correctly catch each lifecycle stage.
"""

import re
from textwrap import dedent


from app.settings.providers.features._base import FeatureFlag, FlagLifecycle, FlagMeta


class _FakeDomainFlags:
    def __init__(self, **flags):
        self._flags = flags
        self.model_fields = {k: type(v) for k, v in flags.items()}

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        return self._flags.get(name)


def _make_flag(enabled=False, lifecycle=FlagLifecycle.transitional, issue=99):
    return FeatureFlag(
        enabled=enabled,
        meta=FlagMeta(lifecycle=lifecycle, issue=issue, description="test"),
    )


class TestFlagLifecycleSimulation:
    def test_define_flag_default_disabled(self):
        flag = _make_flag()
        assert flag.enabled is False
        assert flag.meta.lifecycle == FlagLifecycle.transitional

    def test_flip_flag_enabled(self):
        flag = _make_flag()
        assert flag.enabled is False
        flipped = _make_flag(enabled=True)
        assert flipped.enabled is True

    def test_else_branch_detection_with_fallback(self):
        code = dedent("""\
            if settings.features.testdomain.myflag.enabled:
                new_path()
            else:
                old_path()
        """)
        lines = code.splitlines()
        assert self._has_else_after_flag(lines, "testdomain", "myflag") is True

    def test_else_branch_detection_without_fallback(self):
        code = dedent("""\
            if settings.features.testdomain.myflag.enabled:
                new_path()
            other_stuff()
        """)
        lines = code.splitlines()
        assert self._has_else_after_flag(lines, "testdomain", "myflag") is False

    def test_else_branch_detection_with_elif(self):
        code = dedent("""\
            if settings.features.testdomain.myflag.enabled:
                new_path()
            elif something_else:
                alt_path()
            else:
                fallback()
        """)
        lines = code.splitlines()
        assert self._has_else_after_flag(lines, "testdomain", "myflag") is True

    def test_dead_flag_detection(self):
        code = "print('no flag reference here')"
        assert not re.search(r"features\.testdomain\.myflag\.enabled", code)

    def test_live_flag_detection(self):
        code = "if settings.features.testdomain.myflag.enabled:"
        assert re.search(r"features\.testdomain\.myflag\.enabled", code)

    def test_permanent_flag_exempt_from_transitional_checks(self):
        flag = _make_flag(lifecycle=FlagLifecycle.permanent)
        assert flag.meta.lifecycle == FlagLifecycle.permanent
        assert flag.meta.lifecycle != FlagLifecycle.transitional

    def test_cleanup_simulation(self):
        domain_before = _FakeDomainFlags(
            testflag=_make_flag(enabled=True),
        )
        assert len(domain_before.model_fields) == 1

        domain_after = _FakeDomainFlags()
        assert len(domain_after.model_fields) == 0

    @staticmethod
    def _has_else_after_flag(lines, domain, name):
        pattern = rf"features\.{domain}\.{name}\.enabled"
        for i, line in enumerate(lines):
            if not re.search(pattern, line):
                continue
            if_indent = len(line) - len(line.lstrip())
            for j in range(i + 1, min(i + 30, len(lines))):
                stripped = lines[j].strip()
                if not stripped or stripped.startswith("#"):
                    continue
                line_indent = len(lines[j]) - len(lines[j].lstrip())
                if line_indent < if_indent:
                    break
                if line_indent == if_indent and stripped.startswith("else"):
                    return True
        return False


class TestFlagEnforcementPatterns:
    def test_correct_usage_pattern(self):
        """Validates the expected code pattern for transitional flags."""
        code = dedent("""\
            from app.settings import get_settings

            settings = get_settings()

            if settings.features.fieldspec.matching.enabled:
                score = spec_driven_matching(spec, ocr, voter)
            else:
                score = hardcoded_matching(ocr_name, ocr_address, voter_name, voter_address)
        """)
        lines = code.splitlines()
        has_ref = any(
            re.search(r"features\.fieldspec\.matching\.enabled", line) for line in lines
        )
        has_else = TestFlagLifecycleSimulation._has_else_after_flag(
            lines, "fieldspec", "matching"
        )
        assert has_ref, "Flag should be referenced"
        assert has_else, "Flag should have else branch"

    def test_wrong_usage_no_else(self):
        """Code that gates on a flag but has no fallback — ossified."""
        code = dedent("""\
            if settings.features.fieldspec.voter_list.enabled:
                parse_with_spec()
        """)
        lines = code.splitlines()
        has_ref = any(
            re.search(r"features\.fieldspec\.voter_list\.enabled", line)
            for line in lines
        )
        has_else = TestFlagLifecycleSimulation._has_else_after_flag(
            lines, "fieldspec", "voter_list"
        )
        assert has_ref
        assert not has_else, "Should detect missing else branch"
