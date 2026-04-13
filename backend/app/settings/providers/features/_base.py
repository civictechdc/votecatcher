"""Feature flag base types with state machine lifecycle enforcement.

Provides structured feature flags with lifecycle transitions:
- FlagLifecycle: permanent (always exists) vs transitional (remove after rollout)
- FlagPhase: tracks a flag's progression through its lifecycle
- FlagMeta: metadata describing why a flag exists and what introduced it
- FeatureFlag: a single boolean flag with metadata and phase tracking

Lifecycle for transitional flags:
    DEFINED → ACTIVATED → COMPLETED → REMOVED

    DEFINED:    Flag exists in code but no code references .enabled yet.
                (newly added, waiting for gate implementation)
    ACTIVATED:  Code references the flag with if/else branching.
                (gate in progress, flag guards old vs new code path)
    COMPLETED:  Flag flipped to enabled=True. New code path is active.
                (gate done, old code path still exists as fallback)
    REMOVED:    Flag and its if/else branches deleted. Feature is just code.
                (G10 cleanup — flag and all branching removed)

Transitions are enforced:
- Cannot skip ACTIVATED (must have code refs before flipping enabled)
- Cannot go backwards (once activated, must complete then remove)
- Guard conditions check hygiene (else branch exists for ACTIVATED)

The generic StateMachine engine from app.domain.state_machine drives transitions.
Hygiene tests in test_feature_flag_hygiene.py validate the lifecycle at CI time.
"""

from enum import Enum

from pydantic import BaseModel, Field

from app.domain.state_machine import StateMachine


class FlagLifecycle(str, Enum):
    permanent = "permanent"
    transitional = "transitional"


class FlagPhase(str, Enum):
    DEFINED = "defined"
    ACTIVATED = "activated"
    COMPLETED = "completed"
    REMOVED = "removed"


class FlagActivateEvent(str, Enum):
    ACTIVATE = "activate"
    COMPLETE = "complete"
    REMOVE = "remove"


class FlagContext(BaseModel):
    has_code_reference: bool = False
    has_else_branch: bool = False
    enabled: bool = False


def _activate_action(ctx: FlagContext) -> None:
    ctx.has_code_reference = True


def _complete_action(ctx: FlagContext) -> None:
    ctx.enabled = True


def _remove_action(ctx: FlagContext) -> None:
    ctx.has_code_reference = False
    ctx.has_else_branch = False


def _has_code_ref_guard(ctx: FlagContext) -> bool:
    return ctx.has_code_reference


def _has_else_branch_guard(ctx: FlagContext) -> bool:
    return ctx.has_else_branch


flag_lifecycle_machine: StateMachine[FlagPhase, FlagActivateEvent, FlagContext] = (
    StateMachine()
)


@flag_lifecycle_machine.transition(
    FlagPhase.DEFINED,
    FlagActivateEvent.ACTIVATE,
    FlagPhase.ACTIVATED,
    guard=_has_code_ref_guard,
)
def activate_flag(ctx: FlagContext) -> None:
    _activate_action(ctx)


@flag_lifecycle_machine.transition(
    FlagPhase.ACTIVATED,
    FlagActivateEvent.COMPLETE,
    FlagPhase.COMPLETED,
    guard=_has_else_branch_guard,
)
def complete_flag(ctx: FlagContext) -> None:
    _complete_action(ctx)


@flag_lifecycle_machine.transition(
    FlagPhase.COMPLETED,
    FlagActivateEvent.REMOVE,
    FlagPhase.REMOVED,
)
def remove_flag(ctx: FlagContext) -> None:
    _remove_action(ctx)


class FlagMeta(BaseModel):
    lifecycle: FlagLifecycle
    description: str = ""
    issue: int | None = None
    phase: FlagPhase = FlagPhase.DEFINED


class FeatureFlag(BaseModel):
    enabled: bool = Field(default=False)
    meta: FlagMeta
