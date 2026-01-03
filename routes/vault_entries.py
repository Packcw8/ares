from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from datetime import datetime, timezone

from db import get_db
from models.vault_entry import VaultEntry
from models.evidence import Evidence
from models.user import User
from utils.auth import get_current_user
from schemas.evidence import EvidenceOut
from schemas.vault_entry import VaultEntryCreate, VaultEntryUpdate

router = APIRouter(
    prefix="/vault-entries",
    tags=["vault-entries"],
)

# ======================================================
# 1️⃣ CREATE VAULT ENTRY (JSON BODY)
# ======================================================
@router.post("", response_model=dict)
def create_vault_entry(
    payload: VaultEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not payload.testimony or not payload.testimony.strip():
        raise HTTPException(status_code=400, detail="Testimony is required")

    entry = VaultEntry(
        user_id=current_user.id,
        entity_id=payload.entity_id,
        testimony=payload.testimony.strip(),
        incident_date=payload.incident_date,
        location=payload.location,
        category=payload.category,
        is_anonymous=payload.is_anonymous,
        is_public=payload.is_public,
        published_at=datetime.now(timezone.utc) if payload.is_public else None,
    )

    db.add(entry)
    db.commit()
    db.refresh(entry)

    return {
        "id": entry.id,
        "created_at": entry.created_at,
        "is_public": entry.is_public,
        "entity_id": entry.entity_id,
    }

# ======================================================
# 2️⃣ USER PROFILE – VIEW OWN ENTRIES
# ======================================================
@router.get("/mine", response_model=list[dict])
def get_my_vault_entries(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entries = (
        db.query(VaultEntry)
        .filter(VaultEntry.user_id == current_user.id)
        .order_by(VaultEntry.created_at.desc())
        .all()
    )

    entry_ids = [e.id for e in entries]
    evidence_counts = {}

    if entry_ids:
        rows = (
            db.query(Evidence.vault_entry_id, func.count(Evidence.id))
            .filter(Evidence.vault_entry_id.in_(entry_ids))
            .group_by(Evidence.vault_entry_id)
            .all()
        )
        evidence_counts = {
            vault_entry_id: count for vault_entry_id, count in rows
        }

    return [
        {
            "id": e.id,
            "testimony": e.testimony,
            "entity_id": e.entity_id,
            "location": e.location,
            "category": e.category,
            "is_public": e.is_public,
            "is_anonymous": e.is_anonymous,
            "created_at": e.created_at,
            "published_at": e.published_at,
            "evidence_count": int(evidence_counts.get(e.id, 0)),
        }
        for e in entries
    ]

# ======================================================
# 3️⃣ TOGGLE VISIBILITY
# ======================================================
@router.patch("/{entry_id}/visibility", response_model=dict)
def toggle_vault_entry_visibility(
    entry_id: int,
    make_public: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = db.query(VaultEntry).filter(VaultEntry.id == entry_id).first()

    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    if entry.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    entry.is_public = make_public
    entry.published_at = datetime.now(timezone.utc) if make_public else None

    db.commit()

    return {
        "id": entry.id,
        "is_public": entry.is_public,
        "published_at": entry.published_at,
    }

# ======================================================
# 4️⃣ PUBLIC VAULT FEED
# ======================================================
@router.get("/feed", response_model=list[dict])
def public_vault_feed(
    db: Session = Depends(get_db),
    limit: int = 20,
):
    entries = (
        db.query(VaultEntry)
        .filter(VaultEntry.is_public == True)
        .order_by(VaultEntry.published_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": e.id,
            "testimony": e.testimony,
            "entity_id": e.entity_id,
            "category": e.category,
            "location": e.location,
            "created_at": e.created_at,
            "published_at": e.published_at,
        }
        for e in entries
    ]

# ======================================================
# 5️⃣ GET EVIDENCE FOR A VAULT ENTRY
# ======================================================
@router.get("/{entry_id}/evidence", response_model=List[EvidenceOut])
def get_vault_entry_evidence(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = db.query(VaultEntry).filter(VaultEntry.id == entry_id).first()

    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    if entry.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    evidence_items = (
        db.query(Evidence)
        .filter(Evidence.vault_entry_id == entry_id)
        .order_by(Evidence.timestamp.desc())
        .all()
    )

    return evidence_items

# ======================================================
# 6️⃣ UPDATE VAULT ENTRY (JSON BODY – FIXED)
# ======================================================
@router.patch("/{entry_id}", response_model=dict)
def update_vault_entry(
    entry_id: int,
    payload: VaultEntryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = db.query(VaultEntry).filter(VaultEntry.id == entry_id).first()

    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    if entry.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    entry.testimony = payload.testimony.strip()
    entry.entity_id = payload.entity_id
    entry.is_public = payload.is_public
    entry.published_at = (
        datetime.now(timezone.utc) if payload.is_public else None
    )

    db.commit()

    return {
        "id": entry.id,
        "is_public": entry.is_public,
        "entity_id": entry.entity_id,
        "published_at": entry.published_at,
    }

# ======================================================
# 7️⃣ DELETE VAULT ENTRY (ADMIN)
# ======================================================
@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vault_entry_admin(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    entry = db.query(VaultEntry).filter(VaultEntry.id == entry_id).first()

    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    db.query(Evidence).filter(
        Evidence.vault_entry_id == entry_id
    ).delete()

    db.delete(entry)
    db.commit()
# ======================================================
# 🔐 ADMIN – VIEW ALL VAULT ENTRIES
# ======================================================
@router.get("/admin/all", response_model=list[dict])
def admin_get_all_vault_entries(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    entries = (
        db.query(VaultEntry)
        .order_by(VaultEntry.created_at.desc())
        .all()
    )

    return [
        {
            "id": e.id,
            "testimony": e.testimony,
            "entity": e.entity.name if e.entity else None,
            "entity_id": e.entity_id,
            "user_id": e.user_id,
            "is_public": e.is_public,
            "is_anonymous": e.is_anonymous,
            "created_at": e.created_at,
            "published_at": e.published_at,
        }
        for e in entries
    ]
# ======================================================
# 🔐 ADMIN – VIEW TEXT-ONLY TESTIMONIES
# ======================================================
@router.get("/admin/text-only", response_model=list[dict])
def admin_get_text_only_testimonies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    entries = (
        db.query(VaultEntry)
        .filter(
            VaultEntry.evidence == None  # 🚨 no linked evidence
        )
        .order_by(VaultEntry.created_at.desc())
        .all()
    )

    return [
        {
            "id": e.id,
            "testimony": e.testimony,
            "entity": e.entity.name if e.entity else None,
            "entity_id": e.entity_id,
            "is_public": e.is_public,
            "is_anonymous": e.is_anonymous,
            "created_at": e.created_at,
            "published_at": e.published_at,
        }
        for e in entries
    ]
