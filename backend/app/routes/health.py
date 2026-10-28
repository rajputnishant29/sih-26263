from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.database import get_db
from backend.app.config import settings

router = APIRouter(tags=["Health & Diagnostics"])


@router.get("/health")
@router.get("/api/health")
def health_check(db: Session = Depends(get_db)):
    db_status = "UNKNOWN"
    try:
        db.execute(text("SELECT 1;"))
        db_status = "CONNECTED"
    except Exception as e:
        db_status = f"ERROR: {str(e)}"

    return {
        "status": "HEALTHY" if db_status == "CONNECTED" else "DEGRADED",
        "service": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "environment": settings.ENVIRONMENT,
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat(),
        "is_synthetic_data": settings.IS_SYNTHETIC_DATA,
    }
