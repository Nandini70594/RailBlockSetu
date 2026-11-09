import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.config import settings
from app.models.resource import Resource, ResourceType
from app.models.request import MaintenanceRequest
from app.optimization.train_windows import (
    TrainInterval,
    build_train_intervals,
    has_train_free_gap,
)
from app.models.train import TrainSchedule


IST = ZoneInfo("Asia/Kolkata")
PILLAR_NAMES = (
    "staff",
    "machinery",
    "materials",
    "traffic_window",
    "safety_isolation",
)


def _parse_requirement_list(raw_value: Optional[str], field_name: str) -> List[str]:
    if not raw_value:
        return []
    try:
        value = json.loads(raw_value)
    except json.JSONDecodeError as exc:
        if raw_value.lstrip().startswith(("[", "{", '"')):
            raise ValueError(f"{field_name} must be a JSON list: {exc.msg}") from exc
        value = raw_value
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{field_name} must be a string or JSON list of strings")
    return [item.strip() for item in value if item.strip()]


def _score(passed: int, total: int) -> Optional[float]:
    if total == 0:
        return None
    return round(passed / total * 100, 1)


class ReadinessValidator:
    def validate_request_readiness(
        self,
        req: MaintenanceRequest,
        db: Session,
        base_time: Optional[datetime] = None,
        horizon_minutes: Optional[int] = None,
        train_intervals: Optional[List[TrainInterval]] = None,
    ) -> Dict[str, Any]:
        pillars: Dict[str, Dict[str, Any]] = {}

        # Crew availability is measured only from recorded department crew resources.
        crew_records = db.query(Resource).filter(
            Resource.resource_type == ResourceType.STAFF,
            Resource.department == req.department,
        ).all()
        required_staff = req.required_staff
        if not crew_records:
            crew_reason = (
                f"No crew record found for department {req.department} in division "
                f"{req.railway_division}; no depot is specified on the request."
            )
            pillars["staff"] = {
                "score": None,
                "status": "FAILED",
                "required": required_staff,
                "available": None,
                "department": req.department,
                "reasons": [crew_reason],
                "notes": crew_reason,
            }
        else:
            available_staff = sum(
                record.available_quantity
                for record in crew_records
                if record.operational_status != "UNDER_MAINTENANCE"
            )
            crew_passed = available_staff >= required_staff
            crew_reason = (
                []
                if crew_passed
                else [
                    f"Available crew ({available_staff:g}) is below the "
                    f"required {required_staff:g} for department {req.department}."
                ]
            )
            pillars["staff"] = {
                "score": round(min(100.0, available_staff / required_staff * 100), 1)
                if required_staff > 0 else None,
                "status": "PASS" if crew_passed else "FAILED",
                "required": required_staff,
                "available": available_staff,
                "department": req.department,
                "depots": sorted({record.base_station for record in crew_records}),
                "reasons": crew_reason,
                "notes": (
                    f"{available_staff:g} personnel available vs "
                    f"{required_staff:g} required."
                ),
            }

        # Machine identifiers are matched by exact resource code or exact resource name.
        try:
            required_machines = _parse_requirement_list(
                req.required_machinery, "required_machinery"
            )
            machine_parse_error = None
        except ValueError as exc:
            required_machines = []
            machine_parse_error = str(exc)
        machine_checks = []
        machine_passed = 0
        if machine_parse_error:
            machine_checks.append({
                "id": None,
                "status": "INVALID_REQUIREMENT",
                "reason": machine_parse_error,
            })
        for machine_id in required_machines:
            machine = db.query(Resource).filter(
                Resource.resource_type == ResourceType.MACHINERY,
                Resource.department == req.department,
                (Resource.code == machine_id) | (Resource.name == machine_id),
            ).first()
            if machine is None:
                machine_checks.append({
                    "id": machine_id,
                    "status": "NOT_FOUND",
                    "reason": (
                        f"No exact machine record found for {machine_id} "
                        f"in department {req.department}."
                    ),
                })
            elif (
                machine.operational_status == "UNDER_MAINTENANCE"
                or machine.available_quantity <= 0
            ):
                machine_checks.append({
                    "id": machine_id,
                    "status": "UNAVAILABLE",
                    "code": machine.code,
                    "reason": (
                        f"Machine {machine.code} is {machine.operational_status} "
                        f"or has no available quantity."
                    ),
                })
            else:
                machine_passed += 1
                machine_checks.append({
                    "id": machine_id,
                    "status": "AVAILABLE",
                    "code": machine.code,
                    "available_quantity": machine.available_quantity,
                })
        machine_reasons = [
            item["reason"] for item in machine_checks if "reason" in item
        ]
        pillars["machinery"] = {
            "score": _score(machine_passed, len(required_machines)),
            "status": "FAILED" if machine_reasons else "PASS",
            "items": machine_checks,
            "reasons": machine_reasons,
            "notes": machine_parse_error or (
                f"{machine_passed} of {len(required_machines)} exact machine "
                "requirements are available."
                if required_machines else "No machinery is required."
            ),
        }

        try:
            required_materials = _parse_requirement_list(
                req.required_materials, "required_materials"
            )
            material_parse_error = None
        except ValueError as exc:
            required_materials = []
            material_parse_error = str(exc)
        material_checks = []
        materials_passed = 0
        if material_parse_error:
            material_checks.append({
                "item": None,
                "status": "INVALID_REQUIREMENT",
                "reason": material_parse_error,
            })
        for material_id in required_materials:
            material = db.query(Resource).filter(
                Resource.resource_type == ResourceType.MATERIAL,
                Resource.department == req.department,
                (Resource.code == material_id) | (Resource.name == material_id),
            ).first()
            if material is None or material.available_quantity <= 0:
                reason = (
                    f"No available exact material record found for {material_id} "
                    f"in department {req.department}."
                )
                material_checks.append({
                    "item": material_id,
                    "status": "UNAVAILABLE",
                    "reason": reason,
                })
            else:
                materials_passed += 1
                material_checks.append({
                    "item": material_id,
                    "status": "AVAILABLE",
                    "code": material.code,
                    "available_quantity": material.available_quantity,
                    "unit": material.unit,
                })
        material_reasons = [
            item["reason"] for item in material_checks if "reason" in item
        ]
        pillars["materials"] = {
            "score": _score(materials_passed, len(required_materials)),
            "status": "FAILED" if material_reasons else "PASS",
            "items": material_checks,
            "reasons": material_reasons,
            "notes": material_parse_error or (
                f"{materials_passed} of {len(required_materials)} exact material "
                "requirements are available."
                if required_materials else "No materials are required."
            ),
        }

        if base_time is None:
            base_time = datetime.now(IST).replace(
                tzinfo=None, minute=0, second=0, microsecond=0
            )
        if horizon_minutes is None:
            horizon_minutes = max(
                0,
                int((req.deadline - base_time).total_seconds() // 60),
            )
        if train_intervals is None:
            trains = db.query(TrainSchedule).all()
            train_intervals = build_train_intervals(
                trains,
                base_time,
                horizon_minutes,
                settings.TRAIN_BUFFER_MINUTES,
            )

        section_id = req.section_id
        start_minute = max(
            0, int((req.required_start_date - base_time).total_seconds() // 60)
        )
        deadline_minute = min(
            horizon_minutes,
            int((req.deadline - base_time).total_seconds() // 60),
        )
        duration_minutes = int(req.estimated_duration * 60)
        section_train_intervals = [
            interval for interval in train_intervals
            if interval.section_id == section_id and interval.is_hard
        ]
        gap_exists = (
            section_id is not None
            and duration_minutes > 0
            and has_train_free_gap(
                start_minute,
                deadline_minute,
                duration_minutes,
                section_train_intervals,
            )
        )
        traffic_reason = [] if gap_exists else [
            f"No train-free gap of {duration_minutes} minutes on section "
            f"{req.railway_section or section_id} before the deadline."
        ]
        pillars["traffic_window"] = {
            "score": 100.0 if gap_exists else 0.0,
            "status": "PASS" if gap_exists else "FAILED",
            "estimated_duration_minutes": duration_minutes,
            "section_id": section_id,
            "reasons": traffic_reason,
            "notes": (
                "A train-free gap exists before the request deadline."
                if gap_exists else traffic_reason[0]
            ),
        }

        try:
            safety_requirements = _parse_requirement_list(
                req.safety_requirements, "safety_requirements"
            )
            obtained_requirements = set(
                _parse_requirement_list(
                    req.obtained_safety_requirements,
                    "obtained_safety_requirements",
                )
            )
            missing_clearances = [
                requirement for requirement in safety_requirements
                if requirement not in obtained_requirements
            ]
            safety_status = "PENDING" if missing_clearances else "PASS"
            safety_reasons = [
                f"Required clearance not recorded as obtained: {item}."
                for item in missing_clearances
            ]
            safety_score = _score(
                len(safety_requirements) - len(missing_clearances),
                len(safety_requirements),
            )
        except ValueError as exc:
            safety_requirements = []
            missing_clearances = []
            safety_status = "FAILED"
            safety_reasons = [str(exc)]
            safety_score = None
        pillars["safety_isolation"] = {
            "score": safety_score,
            "status": safety_status,
            "protocol_checks": safety_requirements,
            "obtained": [
                item for item in safety_requirements
                if item not in missing_clearances
            ],
            "reasons": safety_reasons,
            "notes": (
                "No safety clearance requirements were specified."
                if not safety_requirements and safety_status == "PASS"
                else (
                    "All required safety clearances are recorded as obtained."
                    if safety_status == "PASS" else safety_reasons[0]
                )
            ),
        }

        mandatory_pillars = [
            pillar.strip()
            for pillar in settings.READINESS_MANDATORY_PILLARS
            if pillar.strip()
        ]
        unknown_pillars = set(mandatory_pillars) - set(PILLAR_NAMES)
        if unknown_pillars:
            raise ValueError(
                "Unknown READINESS_MANDATORY_PILLARS: "
                + ", ".join(sorted(unknown_pillars))
            )

        mandatory_statuses = [
            pillars[name]["status"] for name in mandatory_pillars
        ]
        if all(status == "PASS" for status in mandatory_statuses):
            verdict = "READY"
        elif any(status == "FAILED" for status in mandatory_statuses):
            verdict = "NOT_READY"
        else:
            verdict = "PARTIALLY_READY"

        corrective_actions = {
            "staff": "Assign sufficient qualified crew and record the roster.",
            "machinery": "Repair/release the listed machine or assign an available exact machine ID.",
            "materials": "Restock the listed materials or update the request requirements.",
            "traffic_window": "Adjust the requested window/deadline to include a train-free gap.",
            "safety_isolation": "Obtain the listed permits and record them in obtained safety clearances.",
        }
        actions = [
            f"{name}: {corrective_actions[name]} "
            f"Details: {'; '.join(pillars[name]['reasons'])}"
            for name in PILLAR_NAMES
            if pillars[name]["status"] != "PASS" and pillars[name]["reasons"]
        ]
        recommendation = (
            "All mandatory readiness pillars passed."
            if verdict == "READY"
            else "Resolve the following readiness items: " + " ".join(actions)
        )
        grade_by_verdict = {
            "READY": "READY_FOR_EXECUTION",
            "PARTIALLY_READY": "CONDITIONAL_APPROVAL",
            "NOT_READY": "CRITICAL_DEFICIT",
        }
        return {
            "request_id": req.request_id,
            "overall_readiness_score": None,
            "readiness_grade": grade_by_verdict[verdict],
            "verdict": verdict,
            "mandatory_pillars": mandatory_pillars,
            "failing_pillars": [
                name for name in mandatory_pillars
                if pillars[name]["status"] != "PASS"
            ],
            "pillars": pillars,
            "recommendation": recommendation,
            "recommended_action": recommendation,
        }


readiness_validator = ReadinessValidator()
