import json
from typing import Any, Dict, Iterable, List, Tuple

from app.config import settings
from app.models.request import MaintenanceRequest


def _requirements(value: Any) -> Any:
    if not value:
        return []
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def _flatten(value: Any) -> List[str]:
    if isinstance(value, dict):
        values = []
        for key, item in value.items():
            values.append(str(key))
            values.extend(_flatten(item))
        return values
    if isinstance(value, (list, tuple, set)):
        return [text for item in value for text in _flatten(item)]
    if value is None:
        return []
    return [str(value)]


def _normalized_machines(task: MaintenanceRequest) -> set[str]:
    return {
        machine.strip().casefold()
        for machine in _flatten(_requirements(task.required_machinery))
        if machine.strip()
    }


def _has_exclusive_flag(task: MaintenanceRequest, rules: Dict[str, Any]) -> bool:
    safety = _requirements(task.safety_requirements)
    obtained = _requirements(task.obtained_safety_requirements)
    configured_flags = {
        str(flag).casefold() for flag in rules.get("exclusive_flags", [])
    }
    if isinstance(safety, dict) and any(
        str(key).casefold() in configured_flags and value is True
        for key, value in safety.items()
    ):
        return True
    if any(
        value.strip().casefold() in configured_flags
        for value in _flatten(safety)
    ):
        return True
    search_text = " ".join(
        [*_flatten(safety), *_flatten(obtained), task.task_title or "", task.description or ""]
    ).casefold()
    return any(
        str(term).casefold() in search_text
        for term in rules.get("exclusive_terms", [])
    )


def _is_live_ohe_task(task: MaintenanceRequest, rules: Dict[str, Any]) -> bool:
    if task.department.casefold() != str(
        rules.get("trd_department", "TRD")
    ).casefold():
        return False
    text = " ".join(
        [
            task.task_title or "",
            task.description or "",
            *_flatten(_requirements(task.safety_requirements)),
        ]
    ).casefold()
    return any(
        str(token).casefold() in text
        for token in rules.get("live_ohe_tokens", [])
    )


def _states_power_isolation(task: MaintenanceRequest, rules: Dict[str, Any]) -> bool:
    text = " ".join(
        [
            task.task_title or "",
            task.description or "",
            *_flatten(_requirements(task.safety_requirements)),
        ]
    ).casefold()
    return any(
        str(token).casefold() in text
        for token in rules.get("power_isolation_tokens", [])
    )


def are_compatible(
    task_a: MaintenanceRequest,
    task_b: MaintenanceRequest,
) -> Tuple[bool, str]:
    """Return whether two maintenance requests may share a section window."""
    rules = settings.COMPATIBILITY_RULES
    reasons: List[str] = []
    if (
        rules.get("require_same_section", True)
        and task_a.section_id != task_b.section_id
    ):
        reasons.append("Tasks are on different sections.")
    if (
        rules.get("require_different_departments", True)
        and task_a.department.casefold() == task_b.department.casefold()
    ):
        reasons.append("Tasks must belong to different departments.")

    if _has_exclusive_flag(task_a, rules) or _has_exclusive_flag(task_b, rules):
        reasons.append("An exclusive task cannot share a section window.")

    shared_machines = _normalized_machines(task_a) & _normalized_machines(task_b)
    if shared_machines:
        reasons.append(
            "Tasks require the same machine(s): "
            + ", ".join(sorted(shared_machines))
            + "."
        )

    heavy_tokens = [
        str(token).casefold()
        for token in rules.get("heavy_machine_tokens", [])
    ]
    heavy_machine_involved = any(
        token in machine
        for machine in _normalized_machines(task_a) | _normalized_machines(task_b)
        for token in heavy_tokens
    )
    trd_task = task_a if _is_live_ohe_task(task_a, rules) else (
        task_b if _is_live_ohe_task(task_b, rules) else None
    )
    if (
        heavy_machine_involved
        and trd_task is not None
        and not _states_power_isolation(trd_task, rules)
    ):
        reasons.append(
            "Heavy track machinery cannot share with live-OHE TRD work "
            "without stated power isolation."
        )

    if reasons:
        return False, " ".join(reasons)
    return True, "Different-department tasks share the section window safely."
