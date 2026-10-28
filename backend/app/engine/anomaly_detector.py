from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.ensemble import IsolationForest
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.models.institution import ApprovalIntake, Programme, Institution, AcademicYear
from backend.app.models.student import StudentEnrolment, EnrolmentStatus


class AnomalyDetector:
    """
    Historical anomaly detection engine using scikit-learn and statistical baselines.
    AI is used strictly as a secondary signal to highlight unusual patterns for human review.
    Never automatically makes consequential decisions or rejects records.
    """

    @classmethod
    def evaluate_programme_historical_anomaly(
        cls,
        db: Session,
        institution_id: int,
        programme_id: int,
        current_year_id: int,
    ) -> Dict[str, Any]:
        """
        Compares current intake utilization and enrolment with prior academic years.
        """
        # Fetch current programme enrolment
        current_enrolment = (
            db.query(func.count(StudentEnrolment.id))
            .filter(
                StudentEnrolment.institution_id == institution_id,
                StudentEnrolment.programme_id == programme_id,
                StudentEnrolment.academic_year_id == current_year_id,
                StudentEnrolment.enrolment_status == EnrolmentStatus.ACTIVE,
            )
            .scalar()
            or 0
        )

        current_approval = (
            db.query(ApprovalIntake)
            .filter(
                ApprovalIntake.institution_id == institution_id,
                ApprovalIntake.programme_id == programme_id,
                ApprovalIntake.academic_year_id == current_year_id,
            )
            .first()
        )
        current_limit = current_approval.effective_intake_limit if current_approval else 1
        current_utilization = (current_enrolment / current_limit) * 100 if current_limit > 0 else 0.0

        # Fetch prior academic years data
        prior_approvals = (
            db.query(ApprovalIntake)
            .filter(
                ApprovalIntake.institution_id == institution_id,
                ApprovalIntake.programme_id == programme_id,
                ApprovalIntake.academic_year_id != current_year_id,
            )
            .all()
        )

        if not prior_approvals or len(prior_approvals) < 2:
            return {
                "has_anomaly": False,
                "status": "INSUFFICIENT_HISTORICAL_DATA",
                "message": "Baseline requires at least 2 historical academic years for statistical comparison.",
                "current_utilization": round(current_utilization, 2),
                "historical_baseline_utilization": None,
                "anomaly_score": 0.0,
            }

        # Build historical baseline
        historical_utilizations = []
        for pa in prior_approvals:
            count = (
                db.query(func.count(StudentEnrolment.id))
                .filter(
                    StudentEnrolment.institution_id == institution_id,
                    StudentEnrolment.programme_id == programme_id,
                    StudentEnrolment.academic_year_id == pa.academic_year_id,
                    StudentEnrolment.enrolment_status == EnrolmentStatus.ACTIVE,
                )
                .scalar()
                or 0
            )
            limit = pa.effective_intake_limit if pa.effective_intake_limit > 0 else 1
            historical_utilizations.append((count / limit) * 100)

        mean_utilization = float(np.mean(historical_utilizations))
        std_utilization = float(np.std(historical_utilizations)) if len(historical_utilizations) > 1 else 10.0
        delta = current_utilization - mean_utilization

        # Train a micro IsolationForest on utilization delta
        X = np.array(historical_utilizations).reshape(-1, 1)
        iso = IsolationForest(contamination=0.1, random_state=42)
        iso.fit(X)
        pred = iso.predict(np.array([[current_utilization]]))
        anomaly_score = float(-iso.score_samples(np.array([[current_utilization]]))[0])

        is_anomaly = bool(pred[0] == -1 and abs(delta) > 25.0)

        signals = []
        if is_anomaly:
            direction = "increase" if delta > 0 else "decline"
            signals.append({
                "type": "UTILIZATION_SHIFT",
                "reason": (
                    f"Intake utilization ({round(current_utilization, 1)}%) deviated by {round(delta, 1)}% "
                    f"from historical 3-year baseline ({round(mean_utilization, 1)}%). Sharp {direction} requires regulatory review."
                ),
                "baseline_mean": round(mean_utilization, 1),
                "current_val": round(current_utilization, 1),
                "delta": round(delta, 1),
                "anomaly_score": round(anomaly_score, 3),
            })

        return {
            "has_anomaly": is_anomaly,
            "status": "ANOMALY_DETECTED" if is_anomaly else "NORMAL",
            "message": "AI secondary indicator detected statistical outlier" if is_anomaly else "Within normal historical variance",
            "current_utilization": round(current_utilization, 2),
            "historical_baseline_utilization": round(mean_utilization, 2),
            "anomaly_score": round(anomaly_score, 3),
            "signals": signals,
        }
