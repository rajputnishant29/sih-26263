import hmac
import hashlib
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt, JWTError
import bcrypt
from backend.app.config import settings

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


# JWT Tokens
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


# Identity Protection & Cryptographic Fingerprinting
def normalize_apaar_id(raw_apaar: str) -> str:
    """
    Cleanses and standardizes APAAR identity input.
    Removes hyphens, spaces, and non-alphanumeric noise.
    """
    if not raw_apaar:
        return ""
    # Strip any prefix like "APAAR-" or spaces/dashes
    cleaned = re.sub(r"[^0-9A-Za-z]", "", str(raw_apaar).strip()).upper()
    return cleaned


def compute_identity_fingerprint(raw_apaar: str) -> str:
    """
    Computes a keyed HMAC-SHA256 deterministic fingerprint over the normalized identity.
    Never uses an ordinary unsalted hash.
    Secret key is injected via secure configuration.
    """
    canonical = normalize_apaar_id(raw_apaar)
    if not canonical:
        return ""
    key = settings.HMAC_SECRET_KEY.encode("utf-8")
    message = canonical.encode("utf-8")
    return hmac.new(key, message, hashlib.sha256).hexdigest()


def mask_apaar_id(raw_apaar: str) -> str:
    """
    Masks APAAR identifier for routine displays, tables, and dashboards.
    Keeps full identity references out of routine UI, logs, and aggregate views.
    Example: 123456789012 -> APAAR-****-****-9012
    """
    clean = normalize_apaar_id(raw_apaar)
    if not clean:
        return "APAAR-MISSING"
    if len(clean) >= 4:
        last4 = clean[-4:]
        return f"APAAR-****-****-{last4}"
    return f"APAAR-****-{clean}"


def check_apaar_format_readiness(raw_apaar: str) -> Dict[str, Any]:
    """
    Configured identity-readiness rule.
    Separates:
    1. Field present or missing.
    2. Format readiness (12-digit numeric structure).
    3. External verification status.
    """
    if not raw_apaar or str(raw_apaar).strip() == "":
        return {
            "is_present": False,
            "is_format_ready": False,
            "message": "APAAR reference is missing",
            "rule_code": "APAAR_PRESENCE_CHECK",
        }

    clean = normalize_apaar_id(raw_apaar)

    # APAAR standard format in educational governance is 12 digits numeric
    is_twelve_digits = bool(re.match(r"^\d{12}$", clean))
    if not is_twelve_digits:
        return {
            "is_present": True,
            "is_format_ready": False,
            "message": f"APAAR format readiness check failed (expected 12 digits, got {len(clean)})",
            "rule_code": "APAAR_FORMAT_READINESS",
        }

    # Format readiness passed
    return {
        "is_present": True,
        "is_format_ready": True,
        "message": "Format readiness verified (12-digit structural check passed)",
        "rule_code": "APAAR_FORMAT_READINESS",
    }
