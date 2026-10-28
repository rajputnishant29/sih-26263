from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.validation import VersionedRule
from backend.app.core.rbac import get_current_user

router = APIRouter(prefix="/api/rules", tags=["Rules & Integration Architecture"])


@router.get("")
def list_versioned_rules(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    rules = db.query(VersionedRule).filter(VersionedRule.is_active == True).all()
    return [
        {
            "id": r.id,
            "rule_code": r.rule_code,
            "rule_version": r.rule_version,
            "rule_name": r.rule_name,
            "description": r.description,
            "severity": r.severity,
            "config_payload": r.config_payload,
            "is_active": r.is_active,
        }
        for r in rules
    ]


@router.get("/integrations/status")
def get_integration_status(current_user=Depends(get_current_user)):
    """
    Documents integration health, simulated vs production status, and the 3-phase pilot roadmap:
    CSV/Excel -> Documented REST APIs -> Authorized APAAR/ABC integration.
    """
    return {
        "architecture_progression": [
            {
                "phase": "Phase 1: CSV / Excel Staging & Validation",
                "status": "OPERATIONAL_PROTOTYPE",
                "description": "Deterministic parsing, column mapping, dry-run schema validation, and atomic commit.",
                "readiness": "100%",
                "official_dependency": "None (Fully active)",
            },
            {
                "phase": "Phase 2: Documented Institution REST APIs",
                "status": "OPERATIONAL_PROTOTYPE",
                "description": "Standardized JSON endpoints with bearer token auth, institution isolation, and batch staging.",
                "readiness": "100%",
                "official_dependency": "Institution API credentials",
            },
            {
                "phase": "Phase 3: Authorized APAAR / ABC / DigiLocker Adapter",
                "status": "SIMULATED_ADAPTER",
                "description": "Simulated local verification gateway clearly labeled. Awaits MeitY/AICTE authorized production credentials.",
                "readiness": "Adapter Implemented (Simulated Engine)",
                "official_dependency": "Government APAAR production gateway access & DPDP consent framework compliance",
            },
        ],
        "pilot_roadmap": {
            "phase_1": "3–5 institutions: Approval-source onboarding & CSV validation",
            "phase_2": "Regional pilot: Reviewer queue workflow & audit trails",
            "phase_3": "National scale: Authorized external integrations & load scaling",
        },
        "adapters_health": {
            "database_postgresql": "HEALTHY",
            "hmac_identity_engine": "ACTIVE (Keyed HMAC-SHA256)",
            "eoa_pdf_parser": "READY (Human-in-the-loop confirmation)",
            "simulated_apaar_gateway": "ONLINE (Demo Provider)",
            "sse_realtime_broker": "ACTIVE",
        },
        "disclaimer": (
            "Live APAAR verification and institutional API integration require authorized government access. "
            "All identity matches in this demonstration are evaluated against the synthetic local prototype repository."
        ),
    }
