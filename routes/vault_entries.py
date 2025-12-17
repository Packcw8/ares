from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timezone

from db import get_db
from models.vault_entry import VaultEntry
from models.user import User
from utils.auth import get_current_user

router = APIRouter(
    prefix="/vault-entries",
    tags=["vault-entries"],
)

# ======================================================
# 1️⃣ CREATE VAULT ENTRY (PRIVATE OR PUBLIC)
# ======================================================
@router.post("", response_model=dict)
def create_vault_entry(
    testimony: str,
    entity_id: Optional[int] = None,
    incident_date: Optional[datetime] = None,
    location: Optional[str] = None,
    category: Optional[str] = None,
    is_anonymous: bool = False,
    is_public: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not testimony or not testimony.strip():
        raise HTTPException(status_code=400, detail="Testimony is required")

    entry = VaultEntry(
        user_id=current_user.id,
        entity_id=entity_id,
        testimony=testimony.strip(),
        incident_date=incident_date,
        location=location,
        category=category,
        is_anonymous=is_anonymous,
        is_public=is_public,
        published_at=datetime.now(timezone.utc) if is_public else None,
    )

    db.add(entry)
    db.commit()
    db.refresh(entry)

    return {
        "id": entry.id,
        "created_at": entry.created_at,
        "is_public": entry.is_public,
    }


# ======================================================
# 2️⃣ USER PROFILE – VIEW OWN ENTRIES (PRIVATE + PUBLIC)
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

    return [
        {
            "id": e.id,
            "testimony": e.testimony,
            "entity_id": e.entity_id,
            "location": e.location,
            "category": e.category,
            "is_public": e.is_public,
            "created_at": e.created_at,
            "published_at": e.published_at,
        }
        for e in entries
    ]


# ======================================================
# 3️⃣ TOGGLE VISIBILITY (OWNER ONLY)
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
    entry.published_at = (
        datetime.now(timezone.utc) if make_public else None
    )

    db.commit()

    return {
        "id": entry.id,
        "is_public": entry.is_public,
        "published_at": entry.published_at,
    }


# ======================================================
# 4️⃣ PUBLIC VAULT FEED (DOCUMENTATION-FIRST)
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
