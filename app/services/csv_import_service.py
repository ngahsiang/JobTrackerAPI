import csv
import io
from datetime import datetime
from typing import Optional
from app.models.models import ApplicationStatus


# ── LinkedIn CSV columns (from LinkedIn's "My Jobs" export) ───────────────────
# Company Name, Job Title, Job URL, Applied On, Status, Notes
LINKEDIN_COLUMNS = {"company name", "job title", "job url", "applied on", "status", "notes"}

# ── JobStreet CSV columns (from JobStreet's application history export) ────────
# Company, Position, Location, Job URL, Date Applied, Application Status, Notes
JOBSTREET_COLUMNS = {"company", "position", "location", "job url", "date applied", "application status", "notes"}


def detect_platform(headers: list[str]) -> Optional[str]:
    """Detect whether the CSV is from LinkedIn or JobStreet based on headers."""
    lowered = {h.strip().lower() for h in headers}
    if "job title" in lowered and "company name" in lowered:
        return "linkedin"
    if "position" in lowered and "application status" in lowered:
        return "jobstreet"
    return None


def parse_date(date_str: str) -> Optional[datetime]:
    """Try to parse common date formats from both platforms."""
    if not date_str or date_str.strip() == "":
        return None
    formats = [
        "%Y-%m-%d",         # 2024-01-15
        "%m/%d/%Y",         # 01/15/2024
        "%d/%m/%Y",         # 15/01/2024
        "%d %b %Y",         # 15 Jan 2024
        "%B %d, %Y",        # January 15, 2024
        "%d-%m-%Y",         # 15-01-2024
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None


def normalize_status(raw_status: str) -> ApplicationStatus:
    """Map platform-specific status strings to our ApplicationStatus enum."""
    mapping = {
        # LinkedIn statuses
        "applied": ApplicationStatus.APPLIED,
        "interviewing": ApplicationStatus.INTERVIEW,
        "offer": ApplicationStatus.OFFER,
        "rejected": ApplicationStatus.REJECTED,
        "withdrawn": ApplicationStatus.WITHDRAWN,
        "saved": ApplicationStatus.WISHLIST,
        "in progress": ApplicationStatus.APPLIED,
        # JobStreet statuses
        "new": ApplicationStatus.APPLIED,
        "application received": ApplicationStatus.APPLIED,
        "under review": ApplicationStatus.APPLIED,
        "shortlisted": ApplicationStatus.INTERVIEW,
        "interview": ApplicationStatus.INTERVIEW,
        "unsuccessful": ApplicationStatus.REJECTED,
        "hired": ApplicationStatus.OFFER,
    }
    return mapping.get(raw_status.strip().lower(), ApplicationStatus.APPLIED)


def parse_linkedin_row(row: dict) -> dict:
    """Parse a single LinkedIn CSV row into our application schema."""
    def g(key): return row.get(key, "").strip()

    return {
        "company":      g("Company Name") or g("company name"),
        "position":     g("Job Title") or g("job title"),
        "location":     g("Location") or g("location") or None,
        "job_url":      g("Job URL") or g("job url") or None,
        "status":       normalize_status(g("Status") or g("status")),
        "notes":        g("Notes") or g("notes") or None,
        "applied_date": parse_date(g("Applied On") or g("applied on")),
    }


def parse_jobstreet_row(row: dict) -> dict:
    """Parse a single JobStreet CSV row into our application schema."""
    def g(key): return row.get(key, "").strip()

    return {
        "company":      g("Company") or g("company"),
        "position":     g("Position") or g("position"),
        "location":     g("Location") or g("location") or None,
        "job_url":      g("Job URL") or g("job url") or None,
        "status":       normalize_status(g("Application Status") or g("application status")),
        "notes":        g("Notes") or g("notes") or None,
        "applied_date": parse_date(g("Date Applied") or g("date applied")),
    }


def parse_csv_import(file_bytes: bytes) -> tuple[str, list[dict], list[str]]:
    """
    Main entry point. Accepts raw CSV bytes, detects platform,
    and returns (platform, parsed_rows, errors).
    """
    try:
        content = file_bytes.decode("utf-8-sig")  # handle BOM from Excel exports
    except UnicodeDecodeError:
        content = file_bytes.decode("latin-1")

    reader = csv.DictReader(io.StringIO(content))
    headers = reader.fieldnames or []

    platform = detect_platform(headers)
    if not platform:
        raise ValueError(
            "Could not detect CSV format. "
            "Please export from LinkedIn (My Jobs → Export) or JobStreet (Application History → Export)."
        )

    parsed_rows = []
    errors = []

    for i, row in enumerate(reader, start=2):  # start=2 because row 1 is headers
        try:
            if platform == "linkedin":
                data = parse_linkedin_row(row)
            else:
                data = parse_jobstreet_row(row)

            if not data["company"] or not data["position"]:
                errors.append(f"Row {i}: skipped — missing company or position.")
                continue

            parsed_rows.append(data)
        except Exception as e:
            errors.append(f"Row {i}: {str(e)}")

    return platform, parsed_rows, errors
