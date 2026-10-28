import re
from typing import Dict, Any, List, Optional
from datetime import datetime
import pypdf
import io


class EoAParserService:
    """
    AICTE Extension of Approval (EoA) document ingestion and extraction service.
    Extracts institution identifiers, academic year, letter reference, programme names,
    and approved intake.
    Extracted values are NEVER silently treated as authoritative; they are flagged
    as 'PENDING_CONFIRMATION' with extraction confidence until human confirmation.
    """

    @classmethod
    def parse_eoa_text(cls, text_content: str, filename: str = "EoA_Document.pdf") -> Dict[str, Any]:
        """
        Parses raw text extracted from an AICTE EoA letter.
        """
        # 1. Extract Letter Reference Number e.g. "F.No. Western/1-3689201923/2026/EOA"
        ref_match = re.search(r"F\.No\.\s*([A-Za-z0-9\-\_\/]+(?:\/EOA|\/20\d\d))", text_content, re.IGNORECASE)
        ref_number = ref_match.group(0).strip() if ref_match else f"AICTE-EOA-EXTRACTED-{datetime.utcnow().strftime('%Y%m%d%H%M')}"

        # 2. Extract Academic Year e.g. "2026-27" or "2026-2027"
        ay_match = re.search(r"for\s+(?:the\s+)?academic\s+year\s+(20\d{2}[\-\/]\d{2,4})", text_content, re.IGNORECASE)
        ay_code = ay_match.group(1).strip() if ay_match else "2026-27"
        if len(ay_code) == 9 and ay_code[4] == "-":  # 2026-2027 -> 2026-27
            ay_code = f"{ay_code[:5]}{ay_code[7:]}"

        # 3. Extract Permanent Institute ID e.g. "1-10023456"
        pid_match = re.search(r"Permanent\s+Id\s*[:\-]?\s*([0-9\-]+)", text_content, re.IGNORECASE)
        institution_code = pid_match.group(1).strip() if pid_match else ""

        # 4. Extract Institution Name
        name_match = re.search(r"Name\s+of\s+the\s+Institution\s*[:\-]?\s*([^\n\r]+)", text_content, re.IGNORECASE)
        institution_name = name_match.group(1).strip() if name_match else ""

        # 5. Extract Programme / Course Intakes
        # Official AICTE tables list: Program, Course, Level, Intake Approved for Year
        programmes_extracted = []
        # Pattern matching table entries: e.g. "ENGINEERING AND TECHNOLOGY | COMPUTER SCIENCE & ENGINEERING | 120"
        course_patterns = [
            r"(COMPUTER SCIENCE|MECHANICAL|ELECTRICAL|ELECTRONICS|CIVIL|INFORMATION TECHNOLOGY|ARTIFICIAL INTELLIGENCE)[^\n\d]*\b(UG|PG|DIPLOMA)?\b[^\n\d]*(\d{2,3})\b",
            r"(CSE|ECE|MECH|CIVIL|IT|EE|AI&DS)[^\n\d]*(\d{2,3})",
        ]

        lines = text_content.splitlines()
        confidence = 0.85 if ref_match and ay_match else 0.65

        for line in lines:
            for pat in course_patterns:
                m = re.search(pat, line, re.IGNORECASE)
                if m:
                    course_name = m.group(1).strip().upper()
                    intake_val = int(m.group(len(m.groups())))
                    if intake_val in [30, 60, 90, 120, 180, 240, 300, 360]:
                        programmes_extracted.append({
                            "programme_name": course_name,
                            "degree_level": "UG",
                            "base_approved_intake": intake_val,
                            "supernumerary_seats": int(intake_val * 0.15),  # Standard 15% supernumerary ceiling
                            "effective_limit": int(intake_val * 1.15),
                            "confidence": 0.95,
                        })
                    break

        if not programmes_extracted:
            # Fallback sample parsing from structured lines if format varies
            confidence = 0.50

        return {
            "source_filename": filename,
            "reference_number": ref_number,
            "academic_year": ay_code,
            "institution_code": institution_code,
            "institution_name": institution_name,
            "extraction_status": "PENDING_CONFIRMATION",
            "extraction_confidence": confidence,
            "extracted_at": datetime.utcnow().isoformat(),
            "programmes": programmes_extracted,
            "notes": "Extracted values require human confirmation before being marked authoritative in reconciliation.",
        }

    @classmethod
    def parse_pdf_bytes(cls, pdf_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Parses a PDF file buffer using pypdf.
        """
        try:
            reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
            full_text = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    full_text.append(text)
            extracted_text = "\n".join(full_text)
            return cls.parse_eoa_text(extracted_text, filename)
        except Exception as e:
            return {
                "source_filename": filename,
                "reference_number": "EXTRACTION_FAILED",
                "academic_year": "2026-27",
                "institution_code": "",
                "institution_name": "",
                "extraction_status": "FAILED",
                "extraction_confidence": 0.0,
                "error": str(e),
                "programmes": [],
            }
