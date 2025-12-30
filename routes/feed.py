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
    # Type-balanced feed ordering
    # =====================================================

    from collections import defaultdict

    grouped = defaultdict(list)

    for item in items:
        grouped[item["type"]].append(item)

    # Sort each group by recency
    for group in grouped.values():
        group.sort(key=lambda x: x["created_at"], reverse=True)

    # Interleave items by type
    ordered = []
    types_cycle = ["vault_record", "rating", "forum_post"]

    while len(ordered) < limit:
        progressed = False

        for t in types_cycle:
            if grouped[t]:
                ordered.append(grouped[t].pop(0))
                progressed = True

            if len(ordered) >= limit:
                break

        if not progressed:
            break  # nothing left to add

    return ordered

