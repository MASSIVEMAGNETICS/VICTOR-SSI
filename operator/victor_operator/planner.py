from __future__ import annotations

from .config import Settings
from .models import Action, TaskRecord


class PlannerError(RuntimeError):
    pass


class Planner:
    """Sovereign execution-plan resolver.

    Victor Operator deliberately contains no hosted-model client and no silent model
    fallback. Until a Victor-owned local cognition adapter is explicitly integrated
    and provenance-verified, this planner executes only user/authority-supplied
    explicit actions. A natural-language-only task fails closed.
    """

    def __init__(self, settings: Settings):
        self.settings = settings

    def _explicit_next(self, task: TaskRecord) -> Action:
        assert task.explicit_steps is not None
        executed = sum(1 for event in task.history if event.kind == "tool_result")
        if executed >= len(task.explicit_steps):
            failures = [event for event in task.history if event.result and not event.result.ok]
            if failures:
                return Action(
                    tool="finish",
                    arguments={"summary": "Explicit plan finished with failed steps."},
                    rationale="The explicit plan has no remaining actions.",
                )
            return Action(
                tool="finish",
                arguments={
                    "summary": "All explicit plan steps completed successfully.",
                    "evidence": [
                        evidence
                        for event in task.history
                        if event.result
                        for evidence in event.result.evidence
                    ],
                },
            )
        return task.explicit_steps[executed]

    def next_action(self, task: TaskRecord) -> Action:
        if task.explicit_steps is not None:
            return self._explicit_next(task)
        raise PlannerError(
            "Victor-native cognition is unavailable. Submit an explicit `steps` plan; "
            "hosted-model fallback is forbidden by VICTOR_MODEL_SOVEREIGNTY."
        )
