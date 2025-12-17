from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from db import get_db
from models.vault_entry import VaultEntry
from models.user import User
from utils.auth import get_current_user

router = APIRouter(
    prefix="/vault-entries",
    tags=["vault-entries"],
)
@router.post("", response_model=dict)
def create_vault_entry(
    testimony: str,
    entity_id: Optional[int] = None,
    incident_date: Optional[datetime] = None,
    location: Optional[str] = None,
    category: Optional[str] = None,
    is_anonymous: bool = False,
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
        is_public=False,   # 🔒 ALWAYS private at creation
    )

    db.add(entry)
    db.commit()
    db.refresh(entry)

    return {
        "id": entry.id,
        "created_at": entry.created_at,
        "is_public": entry.is_public,
    }
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
