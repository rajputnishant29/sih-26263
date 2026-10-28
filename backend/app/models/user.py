from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from backend.app.database import Base


class UserRole:
    AICTE_ADMIN = "AICTE_ADMIN"
    INSTITUTION_ADMIN = "INSTITUTION_ADMIN"
    INSTITUTION_DATA_OPERATOR = "INSTITUTION_DATA_OPERATOR"
    AUTHORIZED_REVIEWER = "AUTHORIZED_REVIEWER"
    EXTERNAL_VERIFIER = "EXTERNAL_VERIFIER"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default=UserRole.INSTITUTION_DATA_OPERATOR)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    institution = relationship("Institution", back_populates="users")
