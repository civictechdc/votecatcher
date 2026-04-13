"""Generic decorator-driven state machine engine.

Reusable FSM parameterized over state, event, and context types.
States and events are Enum members for type safety and hashability.
Actions are plain callables that receive a context object.

Usage:
    class JobState(Enum):
        PENDING = auto()
        RUNNING = auto()
        DONE = auto()

    class JobEvent(Enum):
        START = auto()
        FINISH = auto()

    machine = StateMachine[JobState, JobEvent, dict]()

    @machine.transition(JobState.PENDING, JobEvent.START, JobState.RUNNING)
    def start_job(ctx: dict) -> None:
        ctx["started_at"] = time.time()

    @machine.transition(JobState.RUNNING, JobEvent.FINISH, JobState.DONE)
    def finish_job(ctx: dict) -> None:
        ctx["finished_at"] = time.time()

    state = machine.handle({}, JobState.PENDING, JobEvent.START)
    assert state == JobState.RUNNING

Based on the ArjanCodes refactoring walkthrough pattern.
See ~/03 - Resources/python-state-machine/ for the reference implementation.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Generic, TypeVar

S = TypeVar("S", bound=Enum)
E = TypeVar("E", bound=Enum)
C = TypeVar("C")

Action = Callable[[C], None]
Guard = Callable[[C], bool]


class InvalidTransition(Exception):
    """Raised when no transition exists for the given state/event pair."""


@dataclass
class StateMachine(Generic[S, E, C]):
    """Generic state machine with decorator-based transition registration.

    Transitions are stored as a dict keyed by (state, event) tuples,
    modeling the mathematical δ: S × Σ → S transition function.
    O(1) lookup for any state/event combination.

    The machine holds no entity state — state lives on the entity itself.
    A single machine instance can serve many entities.
    """

    transitions: dict[tuple[S, E], tuple[S, Action[C]]] = field(default_factory=dict)
    guards: dict[tuple[S, E], Guard[C]] = field(default_factory=dict)

    def add_transition(
        self,
        from_state: S,
        event: E,
        to_state: S,
        action: Action[C],
        guard: Guard[C] | None = None,
    ) -> None:
        self.transitions[(from_state, event)] = (to_state, action)
        if guard is not None:
            self.guards[(from_state, event)] = guard

    def next_transition(self, state: S, event: E) -> tuple[S, Action[C]]:
        if (transition := self.transitions.get((state, event))) is None:
            raise InvalidTransition(
                f"Invalid transition from {state!r} on event {event!r}"
            )
        return transition

    def handle(self, context: C, state: S, event: E) -> S:
        next_state, action = self.next_transition(state, event)
        guard = self.guards.get((state, event))
        if guard is not None and not guard(context):
            raise InvalidTransition(
                f"Guard blocked transition from {state!r} on event {event!r}"
            )
        action(context)
        return next_state

    def can_handle(self, state: S, event: E) -> bool:
        return (state, event) in self.transitions

    def available_events(self, state: S) -> list[E]:
        return [e for s, e in self.transitions if s == state]

    def transition(
        self,
        from_state: S | tuple[S, ...],
        event: E,
        to_state: S,
        guard: Guard[C] | None = None,
    ) -> Callable[[Action[C]], Action[C]]:
        states = from_state if isinstance(from_state, tuple) else (from_state,)

        def decorator(action: Action[C]) -> Action[C]:
            for s in states:
                self.add_transition(s, event, to_state, action, guard)
            return action

        return decorator
