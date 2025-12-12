from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional

from db import get_db
from models.evidence import Evidence
from models.user import User
from utils.auth import get_current_user
from utils.blob_utils import upload_file_to_b2

router = APIRouter(prefix="/vault", tags=["evidence"])


# ======================================================
# 1️⃣ Upload Evidence (FILE + METADATA)
# ======================================================

@router.post("", response_model=dict)
async def upload_evidence(
    file: UploadFile = File(...),

    entity_id: int = Form(...),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    is_public: bool = Form(True),
    is_anonymous: bool = Form(False),

    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Fully backend-handled evidence upload.
    """

    if not file:
        raise HTTPException(status_code=400, detail="File required")

    try:
        # ✅ FIXED: correct argument name
        blob_url = upload_file_to_b2(
            file_obj=file.file,
            original_filename=file.filename,
            content_type=file.content_type or "application/octet-stream",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    evidence = Evidence(
        blob_url=blob_url,
        description=description,
        tags=tags,
        location=location,
        is_public=is_public,
        is_anonymous=is_anonymous,
        entity_id=entity_id,
        user_id=None if is_anonymous else current_user.id,
    )

    db.add(evidence)
    db.commit()
    db.refresh(evidence)

    return {
        "id": evidence.id,
        "blob_url": evidence.blob_url,
        "created_at": evidence.timestamp,
    }


# ======================================================
# 2️⃣ Vault Feed (Public)
# ======================================================

@router.get("/feed")
def vault_feed(db: Session = Depends(get_db), limit: int = 20):
    evidence_items = (
        db.query(Evidence)
        .filter(Evidence.is_public == True)
        .order_by(Evidence.timestamp.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": e.id,
            "media_url": e.blob_url,
            "description": e.description,
            "tags": e.tags,
            "location": e.location,
            "created_at": e.timestamp,
            "is_anonymous": e.is_anonymous,
            "entity": {
                "id": e.entity.id,
                "name": e.entity.name,
                "type": e.entity.type,
                "state": e.entity.state,
                "county": e.entity.county,
            },
        }
        for e in evidence_items
    ]


# ======================================================
# 3️⃣ Single Evidence Detail
# ======================================================

@router.get("/{evidence_id}")
def get_evidence_detail(evidence_id: int, db: Session = Depends(get_db)):
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()

    if not evidence or not evidence.is_public:
        raise HTTPException(status_code=404, detail="Evidence not found")

    return {
        "id": evidence.id,
        "media_url": evidence.blob_url,
        "description": evidence.description,
        "tags": evidence.tags,
        "location": evidence.location,
        "created_at": evidence.timestamp,
        "is_anonymous": evidence.is_anonymous,
        "entity": {
            "id": evidence.entity.id,
            "name": evidence.entity.name,
            "type": evidence.entity.type,
            "state": evidence.entity.state,
            "county": evidence.entity.county,
        },
    }
