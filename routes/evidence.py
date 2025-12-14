from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session, joinedload
from typing import Optional, List

from db import get_db
from models.evidence import Evidence
from models.rating import RatedEntity
from models.user import User
from utils.auth import get_current_user
from utils.blob_utils import upload_file_to_b2
from schemas.evidence import EvidenceOut

router = APIRouter(prefix="/vault", tags=["evidence"])


# ======================================================
# 1️⃣ Upload Evidence (LOGIN REQUIRED)
# 🔒 Only allowed for APPROVED entities
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
    if not file:
        raise HTTPException(status_code=400, detail="File required")

    # 🔒 Entity must be approved
    entity = (
        db.query(RatedEntity)
        .filter(
            RatedEntity.id == entity_id,
            RatedEntity.approval_status == "approved",
        )
        .first()
    )

    if not entity:
        raise HTTPException(
            status_code=400,
            detail="This entity is pending review and cannot receive evidence yet.",
        )

    try:
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
# 2️⃣ Vault Feed (PUBLIC READ)
# 🔒 Only evidence from APPROVED entities
# ======================================================
@router.get("/feed", response_model=List[EvidenceOut])
def vault_feed(
    db: Session = Depends(get_db),
    limit: int = 20,
):
    evidence_items = (
        db.query(Evidence)
        .options(
            joinedload(Evidence.user),
            joinedload(Evidence.entity),
        )
        .filter(
            Evidence.is_public == True,
            Evidence.entity.has(approval_status="approved"),
        )
        .order_by(Evidence.timestamp.desc())
        .limit(limit)
        .all()
    )

    return evidence_items


# ======================================================
# 3️⃣ Single Evidence Detail (PUBLIC READ)
# 🔒 Must belong to approved entity
# ======================================================
@router.get("/{evidence_id}", response_model=EvidenceOut)
def get_evidence_detail(
    evidence_id: int,
    db: Session = Depends(get_db),
):
    evidence = (
        db.query(Evidence)
        .options(
            joinedload(Evidence.user),
            joinedload(Evidence.entity),
        )
        .filter(
            Evidence.id == evidence_id,
            Evidence.is_public == True,
            Evidence.entity.has(approval_status="approved"),
        )
        .first()
    )

    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    return evidence


# ======================================================
# 4️⃣ DELETE EVIDENCE (OWNER ONLY)
# ======================================================
@router.delete("/{evidence_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_evidence(
    evidence_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()

    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    # 🔒 Anonymous uploads cannot be deleted by users
    if evidence.is_anonymous or evidence.user_id is None:
        raise HTTPException(
            status_code=403,
            detail="Anonymous evidence cannot be deleted by users",
        )

    if evidence.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Not authorized to delete this evidence",
        )

    db.delete(evidence)
    db.commit()
    return
