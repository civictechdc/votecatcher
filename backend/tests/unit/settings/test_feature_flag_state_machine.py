"""Tests for feature flag lifecycle state machine integration.

Validates the flag lifecycle transitions driven by the generic state machine:
    DEFINED → ACTIVATED → COMPLETED → REMOVED

And guard enforcement:
- ACTIVATE requires code reference
- COMPLETE requires else branch
- REMOVE is always allowed from COMPLETED
"""

import pytest

from app.domain.state_machine import InvalidTransition
from app.settings.providers.features._base import (
    FlagActivateEvent,
    FlagContext,
    FlagPhase,
    flag_lifecycle_machine,
)


class TestFlagLifecycleTransitions:
    def test_defined_to_activated_with_code_ref(self):
        ctx = FlagContext(has_code_reference=True)
        result = flag_lifecycle_machine.handle(
            ctx, FlagPhase.DEFINED, FlagActivateEvent.ACTIVATE
        )
        assert result == FlagPhase.ACTIVATED
        assert ctx.has_code_reference is True

    def test_defined_to_activated_blocked_without_code_ref(self):
        ctx = FlagContext(has_code_reference=False)
        with pytest.raises(InvalidTransition, match="Guard blocked"):
            flag_lifecycle_machine.handle(
                ctx, FlagPhase.DEFINED, FlagActivateEvent.ACTIVATE
            )

    def test_activated_to_completed_with_else_branch(self):
        ctx = FlagContext(has_code_reference=True, has_else_branch=True)
        result = flag_lifecycle_machine.handle(
            ctx, FlagPhase.ACTIVATED, FlagActivateEvent.COMPLETE
        )
        assert result == FlagPhase.COMPLETED
        assert ctx.enabled is True

    def test_activated_to_completed_blocked_without_else_branch(self):
        ctx = FlagContext(has_code_reference=True, has_else_branch=False)
        with pytest.raises(InvalidTransition, match="Guard blocked"):
            flag_lifecycle_machine.handle(
                ctx, FlagPhase.ACTIVATED, FlagActivateEvent.COMPLETE
            )

    def test_completed_to_removed(self):
        ctx = FlagContext(enabled=True)
        result = flag_lifecycle_machine.handle(
            ctx, FlagPhase.COMPLETED, FlagActivateEvent.REMOVE
        )
        assert result == FlagPhase.REMOVED
        assert ctx.has_code_reference is False
        assert ctx.has_else_branch is False


class TestFlagLifecycleInvalidTransitions:
    def test_cannot_skip_to_completed(self):
        ctx = FlagContext()
        with pytest.raises(InvalidTransition):
            flag_lifecycle_machine.handle(
                ctx, FlagPhase.DEFINED, FlagActivateEvent.COMPLETE
            )

    def test_cannot_remove_from_defined(self):
        ctx = FlagContext()
        with pytest.raises(InvalidTransition):
            flag_lifecycle_machine.handle(
                ctx, FlagPhase.DEFINED, FlagActivateEvent.REMOVE
            )

    def test_cannot_remove_from_activated(self):
        ctx = FlagContext(has_code_reference=True)
        with pytest.raises(InvalidTransition):
            flag_lifecycle_machine.handle(
                ctx, FlagPhase.ACTIVATED, FlagActivateEvent.REMOVE
            )

    def test_cannot_reactivate_from_completed(self):
        ctx = FlagContext(enabled=True)
        with pytest.raises(InvalidTransition):
            flag_lifecycle_machine.handle(
                ctx, FlagPhase.COMPLETED, FlagActivateEvent.ACTIVATE
            )

    def test_cannot_transition_from_removed(self):
        ctx = FlagContext()
        with pytest.raises(InvalidTransition):
            flag_lifecycle_machine.handle(
                ctx, FlagPhase.REMOVED, FlagActivateEvent.ACTIVATE
            )
        with pytest.raises(InvalidTransition):
            flag_lifecycle_machine.handle(
                ctx, FlagPhase.REMOVED, FlagActivateEvent.COMPLETE
            )
        with pytest.raises(InvalidTransition):
            flag_lifecycle_machine.handle(
                ctx, FlagPhase.REMOVED, FlagActivateEvent.REMOVE
            )


class TestFlagLifecycleIntrospection:
    def test_available_events_defined(self):
        events = flag_lifecycle_machine.available_events(FlagPhase.DEFINED)
        assert FlagActivateEvent.ACTIVATE in events
        assert FlagActivateEvent.COMPLETE not in events

    def test_available_events_activated(self):
        events = flag_lifecycle_machine.available_events(FlagPhase.ACTIVATED)
        assert FlagActivateEvent.COMPLETE in events
        assert FlagActivateEvent.ACTIVATE not in events

    def test_available_events_completed(self):
        events = flag_lifecycle_machine.available_events(FlagPhase.COMPLETED)
        assert FlagActivateEvent.REMOVE in events

    def test_available_events_removed(self):
        events = flag_lifecycle_machine.available_events(FlagPhase.REMOVED)
        assert events == []


class TestFlagLifecycleFullCycle:
    def test_happy_path_full_cycle(self):
        ctx = FlagContext(has_code_reference=True, has_else_branch=True)
        state = flag_lifecycle_machine.handle(
            ctx, FlagPhase.DEFINED, FlagActivateEvent.ACTIVATE
        )
        assert state == FlagPhase.ACTIVATED

        state = flag_lifecycle_machine.handle(ctx, state, FlagActivateEvent.COMPLETE)
        assert state == FlagPhase.COMPLETED
        assert ctx.enabled is True

        state = flag_lifecycle_machine.handle(ctx, state, FlagActivateEvent.REMOVE)
        assert state == FlagPhase.REMOVED

    def test_gate_scenario_persistence_flag(self):
        """Simulates the G4 persistence flag lifecycle."""
        ctx = FlagContext()
        assert ctx.enabled is False
        assert ctx.has_code_reference is False

        ctx.has_code_reference = True
        ctx.has_else_branch = True

        state = flag_lifecycle_machine.handle(
            ctx, FlagPhase.DEFINED, FlagActivateEvent.ACTIVATE
        )
        assert state == FlagPhase.ACTIVATED

        state = flag_lifecycle_machine.handle(ctx, state, FlagActivateEvent.COMPLETE)
        assert state == FlagPhase.COMPLETED
        assert ctx.enabled is True

        state = flag_lifecycle_machine.handle(ctx, state, FlagActivateEvent.REMOVE)
        assert state == FlagPhase.REMOVED


class TestFlagContext:
    def test_default_values(self):
        ctx = FlagContext()
        assert ctx.has_code_reference is False
        assert ctx.has_else_branch is False
        assert ctx.enabled is False

    def test_pydantic_model_serialization(self):
        ctx = FlagContext(has_code_reference=True, has_else_branch=True, enabled=True)
        data = ctx.model_dump()
        restored = FlagContext.model_validate(data)
        assert restored == ctx
