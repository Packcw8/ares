from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from db import get_db
from models.rating import RatedEntity

router = APIRouter(
    prefix="/entities",
    tags=["entities"],
)

@router.get("/search", response_model=List[dict])
def search_entities(
    q: str = Query(..., min_length=2),
    db: Session = Depends(get_db),
):
    results = (
        db.query(RatedEntity)
        .filter(
            RatedEntity.approval_status == "approved",
            RatedEntity.name.ilike(f"%{q}%"),
        )
        .order_by(RatedEntity.name.asc())
        .limit(10)
        .all()
    )

    return [
        {
            "id": e.id,
            "name": e.name,
            "state": e.state,
            "county": e.county,
            "type": e.type,
        }
        for e in results
    ]
