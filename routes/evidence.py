from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from db import get_db
from models.evidence import Evidence
from models.user import User
from utils.auth import get_current_user
from utils.blob_utils import generate_presigned_upload

router = APIRouter(prefix="/vault", tags=["evidence"])

# ======================================================
# Schemas (local to keep this file self-contained)
# ======================================================

class UploadURLRequest(BaseModel):
    filename: str
    content_type: str


class EvidenceCreate(BaseModel):
    blob_url: str
    description: str | None = None
    tags: str | None = None
    location: str | None = None
    is_public: bool = True
    is_anonymous: bool = False
    entity_id: int


# ======================================================
# 1️⃣ Generate Backblaze Upload URL
# ======================================================

@router.post("/upload-url")
def get_upload_url(
    payload: UploadURLRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Returns a presigned Backblaze upload URL.
    Frontend uploads the file directly to B2.
    """
    return generate_presigned_upload(
        filename=payload.filename,
        content_type=payload.content_type,
    )


# ======================================================
# 2️⃣ Save Evidence Metadata (AFTER upload)
# ======================================================

@router.post("", response_model=dict)
def create_evidence(
    payload: EvidenceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Stores metadata ONLY. No file bytes touch the API.
    """

    evidence = Evidence(
        blob_url=payload.blob_url,
        description=payload.description,
        tags=payload.tags,
        location=payload.location,
        is_public=payload.is_public,
        is_anonymous=payload.is_anonymous,
        entity_id=payload.entity_id,
        user_id=None if payload.is_anonymous else current_user.id,
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
# 3️⃣ Vault Feed (PUBLIC LANDING PAGE)
# ======================================================

@router.get("/feed")
def vault_feed(
    db: Session = Depends(get_db),
    limit: int = 20,
):
    """
    Public, scrolling Vault feed.
    Ordered by relevance (v1 = newest first).
    """

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
# 4️⃣ Single Evidence Detail
# ======================================================

@router.get("/{evidence_id}")
def get_evidence_detail(
    evidence_id: int,
    db: Session = Depends(get_db),
):
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
