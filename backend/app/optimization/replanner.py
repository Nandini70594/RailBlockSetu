from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.models.schedule import MaintenanceBlock, BlockStatus
from app.models.disruption import Disruption
from app.models.audit import AuditLog
from app.optimization.scheduler import optimizer_scheduler
from app.optimization.validator import refresh_schedule_validation

class DisruptionReplanner:
    def __init__(self):
        pass

    def execute_disruption_replan(self, disruption_id: int, db: Session) -> Dict[str, Any]:
        """
        Intelligent disruption-aware replanning:
        1. Identifies directly colliding blocks in the disruption corridor & window.
        2. Pins all non-colliding and already approved blocks so their timings are preserved.
        3. Re-runs Google OR-Tools CP-SAT to smoothly reschedule only the affected tasks.
        """
        disruption = db.query(Disruption).filter(Disruption.id == disruption_id).first()
        if not disruption:
            return {"error": f"Disruption with ID {disruption_id} not found."}

        # Find all blocks in the system
        all_blocks = db.query(MaintenanceBlock).filter(
            MaintenanceBlock.status.in_([BlockStatus.APPROVED, BlockStatus.PROPOSED])
        ).all()

        unaffected_block_ids = []
        affected_blocks = []

        for b in all_blocks:
            # Check if block overlaps spatially and temporally with disruption
            is_same_section = (b.section_id == disruption.section_id)
            is_time_conflict = not (
                b.scheduled_end <= disruption.affected_from or
                b.scheduled_start >= disruption.affected_until
            )

            if is_same_section and is_time_conflict:
                # Affected! Must be shifted by replanner
                b.is_pinned = False
                affected_blocks.append(b)
            else:
                # Unaffected! Pin it to preserve railway operations stability!
                if b.status == BlockStatus.APPROVED:
                    b.is_pinned = True
                    unaffected_block_ids.append(b.id)

        db.commit()

        # Run CP-SAT with pinned blocks and disruption exclusion window
        opt_result = optimizer_scheduler.run_optimization(
            db=db,
            horizon_hours=96,
            pinned_block_ids=unaffected_block_ids,
            disruption=disruption
        )

        # Update disruption record
        disruption.replan_triggered = True
        disruption.replanned_at = datetime.utcnow()
        disruption.affected_blocks_count = len(affected_blocks)
        disruption.preserved_blocks_count = len(unaffected_block_ids)
        
        # Log to audit feed
        audit = AuditLog(
            user_name="Replanning Engine",
            role="OPERATIONS",
            action="TRIGGER_REPLAN",
            department="Operations",
            badge_type="warning",
            details=f"Replanned {len(affected_blocks)} affected blocks due to {disruption.disruption_type.value} on section {disruption.section.section_code if disruption.section else 'corridor'}. {len(unaffected_block_ids)} unaffected blocks preserved intact."
        )
        db.add(audit)
        db.commit()
        refresh_schedule_validation(db)

        return {
            "disruption_code": disruption.disruption_code,
            "disruption_type": disruption.disruption_type.value,
            "severity": disruption.severity.value,
            "affected_blocks_count": len(affected_blocks),
            "preserved_blocks_count": len(unaffected_block_ids),
            "optimization_result": opt_result,
            "message": f"Successfully replanned! {len(unaffected_block_ids)} approved blocks were preserved untouched, and {len(affected_blocks)} affected activities were rescheduled safely."
        }

disruption_replanner = DisruptionReplanner()
