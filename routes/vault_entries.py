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
