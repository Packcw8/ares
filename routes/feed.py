from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from db import get_db

from models.vault_entry import VaultEntry
from models.rating import RatingCategoryScore
from models.official_post import OfficialPost
from models.evidence import Evidence
from schemas.feed import FeedItemOut

router = APIRouter(prefix="/feed", tags=["feed"])


@router.get("", response_model=list[FeedItemOut])
def unified_feed(
    db: Session = Depends(get_db),
    state: str | None = Query(None),
    county: str | None = Query(None),
    q: str | None = Query(None),
    limit: int = 50,
):
    items: list[dict] = []

    # =====================================================
    # Public Vault Records
    # =====================================================
    vault_q = db.query(VaultEntry).filter(VaultEntry.is_public == True)

    if state:
        vault_q = vault_q.filter(VaultEntry.entity.has(state=state))
    if county:
        vault_q = vault_q.filter(VaultEntry.entity.has(county=county))

    vault_entries = vault_q.limit(limit).all()

    for v in vault_entries:
        evidence_items = (
            db.query(Evidence)
            .filter(
                Evidence.vault_entry_id == v.id,
                Evidence.is_public == True,
            )
            .order_by(Evidence.timestamp.desc())
            .all()
        )

        items.append({
            "type": "vault_record",
            "created_at": v.published_at or v.created_at,
            "entity": v.entity,
            "description": v.testimony,
            "user": v.user,
            "evidence": [
                {
                    "id": ev.id,
                    "blob_url": ev.blob_url,
                    "description": ev.description,
                }
                for ev in evidence_items
            ],
        })

    # =====================================================
    # Ratings (ENTITY SURFACES HERE)
    # =====================================================
    ratings_q = db.query(RatingCategoryScore)

    if state:
        ratings_q = ratings_q.filter(
            RatingCategoryScore.entity.has(state=state)
        )
    if county:
        ratings_q = ratings_q.filter(
            RatingCategoryScore.entity.has(county=county)
        )

    ratings = (
        ratings_q
        .order_by(RatingCategoryScore.created_at.desc())
        .limit(limit)
        .all()
    )

    for r in ratings:
        items.append({
            "type": "rating",
            "created_at": r.created_at,
            "entity": r.entity,
            "rating": r,
            "user": r.user,
        })

    # =====================================================
    # Forum / Official Posts
    # =====================================================
    posts_q = db.query(OfficialPost)

    if state:
        posts_q = posts_q.filter(
            OfficialPost.entity.has(state=state)
        )
    if county:
        posts_q = posts_q.filter(
            OfficialPost.entity.has(county=county)
        )

    posts = (
        posts_q
        .order_by(
            OfficialPost.is_pinned.desc(),
            OfficialPost.created_at.desc()
        )
        .limit(limit)
        .all()
    )

    for p in posts:
        items.append({
            "type": "forum_post",
            "created_at": p.created_at,
            "entity": p.entity,
            "title": p.title,
            "body": p.body,
            "user": p.author,
            "is_pinned": p.is_pinned,
            "is_ama": p.is_ama,
        })

    # =====================================================
    # Final sort & trim
    # =====================================================
    items.sort(key=lambda x: x["created_at"], reverse=True)
    return items[:limit]
