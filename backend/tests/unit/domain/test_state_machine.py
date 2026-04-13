"""Tests for the generic state machine engine.

Validates all engine capabilities:
- Basic transition registration and execution
- Decorator-based registration
- Multi-source transitions
- Invalid transition rejection
- Guard conditions (allow and block)
- Introspection (can_handle, available_events)
- Generic type parameterization
"""

import pytest

from app.domain.state_machine import InvalidTransition, StateMachine


class TrafficState:
    RED = "RED"
    YELLOW = "YELLOW"
    GREEN = "GREEN"


class TrafficEvent:
    TIMER = "TIMER"
    EMERGENCY = "EMERGENCY"


class TestBasicTransitions:
    def test_simple_transition(self):
        sm: StateMachine[str, str, dict] = StateMachine()
        sm.add_transition(
            "A", "go", "B", lambda ctx: ctx.setdefault("log", []).append("A→B")
        )
        ctx: dict = {}
        result = sm.handle(ctx, "A", "go")
        assert result == "B"
        assert ctx["log"] == ["A→B"]

    def test_chain_transitions(self):
        sm: StateMachine[str, str, dict] = StateMachine()
        sm.add_transition(
            "A", "go", "B", lambda ctx: ctx.setdefault("path", []).append("B")
        )
        sm.add_transition(
            "B", "go", "C", lambda ctx: ctx.setdefault("path", []).append("C")
        )
        ctx: dict = {}
        state = sm.handle(ctx, "A", "go")
        assert state == "B"
        state = sm.handle(ctx, state, "go")
        assert state == "C"
        assert ctx["path"] == ["B", "C"]

    def test_invalid_transition_raises(self):
        sm: StateMachine[str, str, dict] = StateMachine()
        sm.add_transition("A", "go", "B", lambda ctx: None)
        with pytest.raises(InvalidTransition, match="Invalid transition"):
            sm.handle({}, "B", "go")

    def test_invalid_event_raises(self):
        sm: StateMachine[str, str, dict] = StateMachine()
        sm.add_transition("A", "go", "B", lambda ctx: None)
        with pytest.raises(InvalidTransition, match="Invalid transition"):
            sm.handle({}, "A", "stop")


class TestDecoratorRegistration:
    def test_decorator_registers_transition(self):
        sm: StateMachine[str, str, list] = StateMachine()

        @sm.transition("A", "go", "B")
        def go_a_to_b(ctx: list) -> None:
            ctx.append("went")

        assert sm.can_handle("A", "go")
        ctx: list = []
        result = sm.handle(ctx, "A", "go")
        assert result == "B"
        assert ctx == ["went"]

    def test_decorator_returns_original_function(self):
        sm: StateMachine[str, str, dict] = StateMachine()

        @sm.transition("A", "go", "B")
        def my_action(ctx: dict) -> None:
            pass

        assert callable(my_action)
        assert my_action.__name__ == "my_action"


class TestMultiSourceTransitions:
    def test_single_source_as_non_iterable(self):
        sm: StateMachine[str, str, list] = StateMachine()

        @sm.transition("X", "reset", "A")
        def reset(ctx: list) -> None:
            ctx.append("reset")

        assert sm.can_handle("X", "reset")
        ctx: list = []
        assert sm.handle(ctx, "X", "reset") == "A"

    def test_multiple_source_states(self):
        sm: StateMachine[str, str, list] = StateMachine()

        @sm.transition(("B", "C"), "reset", "A")
        def reset(ctx: list) -> None:
            ctx.append("reset")

        ctx: list = []
        assert sm.handle(ctx, "B", "reset") == "A"
        ctx2: list = []
        assert sm.handle(ctx2, "C", "reset") == "A"


class TestGuardConditions:
    def test_guard_allows_transition(self):
        sm: StateMachine[str, str, dict] = StateMachine()
        sm.add_transition(
            "A",
            "go",
            "B",
            lambda ctx: ctx.setdefault("log", []).append("go"),
            guard=lambda ctx: ctx.get("allowed", False),
        )
        ctx: dict = {"allowed": True}
        result = sm.handle(ctx, "A", "go")
        assert result == "B"
        assert ctx["log"] == ["go"]

    def test_guard_blocks_transition(self):
        sm: StateMachine[str, str, dict] = StateMachine()
        sm.add_transition(
            "A",
            "go",
            "B",
            lambda ctx: None,
            guard=lambda ctx: ctx.get("allowed", False),
        )
        with pytest.raises(InvalidTransition, match="Guard blocked"):
            sm.handle({"allowed": False}, "A", "go")

    def test_guard_with_decorator(self):
        sm: StateMachine[str, str, dict] = StateMachine()

        @sm.transition("A", "go", "B", guard=lambda ctx: ctx.get("ok", False))
        def guarded(ctx: dict) -> None:
            ctx["went"] = True

        assert sm.handle({"ok": True}, "A", "go") == "B"
        with pytest.raises(InvalidTransition):
            sm.handle({"ok": False}, "A", "go")


class TestIntrospection:
    def test_can_handle_existing(self):
        sm: StateMachine[str, str, dict] = StateMachine()
        sm.add_transition("A", "go", "B", lambda ctx: None)
        assert sm.can_handle("A", "go") is True

    def test_can_handle_missing(self):
        sm: StateMachine[str, str, dict] = StateMachine()
        sm.add_transition("A", "go", "B", lambda ctx: None)
        assert sm.can_handle("B", "go") is False

    def test_available_events(self):
        sm: StateMachine[str, str, dict] = StateMachine()
        sm.add_transition("A", "go", "B", lambda ctx: None)
        sm.add_transition("A", "stop", "C", lambda ctx: None)
        events = sm.available_events("A")
        assert sorted(events) == ["go", "stop"]

    def test_available_events_empty(self):
        sm: StateMachine[str, str, dict] = StateMachine()
        assert sm.available_events("Z") == []


class TestWithEnums:
    def test_enum_state_and_event(self):
        from enum import Enum, auto

        class St(Enum):
            IDLE = auto()
            RUNNING = auto()

        class Ev(Enum):
            START = auto()
            STOP = auto()

        sm: StateMachine[St, Ev, dict] = StateMachine()

        @sm.transition(St.IDLE, Ev.START, St.RUNNING)
        def start(ctx: dict) -> None:
            ctx["started"] = True

        @sm.transition(St.RUNNING, Ev.STOP, St.IDLE)
        def stop(ctx: dict) -> None:
            ctx["stopped"] = True

        ctx: dict = {}
        state = sm.handle(ctx, St.IDLE, Ev.START)
        assert state == St.RUNNING
        assert ctx["started"] is True

        state = sm.handle(ctx, state, Ev.STOP)
        assert state == St.IDLE
        assert ctx["stopped"] is True

    def test_invalid_transition_with_enums(self):
        from enum import Enum, auto

        class St(Enum):
            IDLE = auto()
            DONE = auto()

        class Ev(Enum):
            START = auto()

        sm: StateMachine[St, Ev, dict] = StateMachine()
        sm.add_transition(St.IDLE, Ev.START, St.DONE, lambda ctx: None)

        with pytest.raises(InvalidTransition):
            sm.handle({}, St.DONE, Ev.START)
