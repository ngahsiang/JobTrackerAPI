from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import JobApplication, User
from app.services.auth_service import get_current_user
from app.services.csv_import_service import parse_csv_import

router = APIRouter(prefix="/api/import", tags=["CSV Import"])


@router.post("/csv")
async def import_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Import job applications from a LinkedIn or JobStreet CSV export.

    - **LinkedIn:** Go to Jobs → My Jobs → Saved/Applied → More (⋯) → Export
    - **JobStreet:** Go to Profile → Application History → Export CSV
    """
    # Validate file type
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted.")

    MAX_SIZE = 5 * 1024 * 1024  # 5 MB
    file_bytes = await file.read()
    if len(file_bytes) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 5MB.")

    # Parse the CSV
    try:
        platform, parsed_rows, errors = parse_csv_import(file_bytes)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    if not parsed_rows and errors:
        raise HTTPException(status_code=422, detail={"message": "No valid rows found.", "errors": errors})

    # Check for duplicates (same company + position for this user)
    existing = db.query(JobApplication).filter(JobApplication.user_id == current_user.id).all()
    existing_keys = {(a.company.lower(), a.position.lower()) for a in existing}

    imported = []
    skipped_duplicates = []

    for row in parsed_rows:
        key = (row["company"].lower(), row["position"].lower())
        if key in existing_keys:
            skipped_duplicates.append(f"{row['company']} — {row['position']}")
            continue

        application = JobApplication(
            user_id=current_user.id,
            company=row["company"],
            position=row["position"],
            location=row.get("location"),
            job_url=row.get("job_url"),
            status=row["status"],
            notes=row.get("notes"),
            applied_date=row.get("applied_date"),
        )
        db.add(application)
        imported.append(f"{row['company']} — {row['position']}")
        existing_keys.add(key)  # prevent dupes within the same upload

    db.commit()

    return {
        "platform_detected": platform,
        "total_rows_in_file": len(parsed_rows) + len(skipped_duplicates),
        "imported": len(imported),
        "skipped_duplicates": len(skipped_duplicates),
        "parse_errors": len(errors),
        "imported_jobs": imported,
        "skipped_jobs": skipped_duplicates,
        "errors": errors,
    }


@router.get("/csv/sample/{platform}")
def download_sample_csv(platform: str):
    """
    Returns the expected CSV column format for each platform.
    Use this to understand what columns are required.
    """
    samples = {
        "linkedin": {
            "platform": "LinkedIn",
            "export_instructions": "Jobs → My Jobs → Applied Jobs → Export (top right)",
            "expected_columns": [
                "Company Name", "Job Title", "Job URL",
                "Applied On", "Status", "Notes", "Location"
            ],
            "status_values": [
                "Applied", "Interviewing", "Offer",
                "Rejected", "Withdrawn", "Saved"
            ],
            "date_format_example": "2024-01-15 or 01/15/2024",
        },
        "jobstreet": {
            "platform": "JobStreet",
            "export_instructions": "Profile → Application History → Export CSV",
            "expected_columns": [
                "Company", "Position", "Location",
                "Job URL", "Date Applied", "Application Status", "Notes"
            ],
            "status_values": [
                "New", "Application Received", "Under Review",
                "Shortlisted", "Interview", "Unsuccessful", "Hired"
            ],
            "date_format_example": "15/01/2024 or 15 Jan 2024",
        },
    }

    if platform.lower() not in samples:
        raise HTTPException(status_code=404, detail="Platform must be 'linkedin' or 'jobstreet'.")

    return samples[platform.lower()]
