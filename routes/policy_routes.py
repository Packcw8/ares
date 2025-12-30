from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime

from db import get_db
from routes.auth_routes import get_current_user

from models.policy import (
    Policy,
    PolicyStatus,
    PolicyStatusHistory,
    PolicyStatusChangeRequest,
    ApprovalStatus,
)

from schemas.policy_schemas import (
    PolicyCreate,
    PolicyOut,
    PolicyStatusChangeRequestCreate,
    PolicyStatusChangeRequestOut,
)

router = APIRouter(prefix="/policies", tags=["Policies"])

# ======================================================
# PUBLIC — READ ONLY
# ======================================================

@router.get("/", response_model=list[PolicyOut])
def list_policies(db: Session = Depends(get_db)):
    return (
        db.query(Policy)
        .filter(Policy.is_active == True)
        .order_by(Policy.created_at.desc())
        .all()
    )


@router.get("/{policy_id}", response_model=PolicyOut)
def get_policy(policy_id: int, db: Session = Depends(get_db)):
    policy = db.query(Policy).get(policy_id)
    if not policy or not policy.is_active:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy

# ======================================================
# ADMIN — CREATE POLICY
# ======================================================

@router.post("/", response_model=PolicyOut)
def create_policy(
    data: PolicyCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    if data.jurisdiction_level == "state" and not data.state_code:
        raise HTTPException(
            status_code=400,
            detail="state_code is required for state-level policies",
        )

    policy = Policy(
        title=data.title,
        summary=data.summary,
        jurisdiction_level=data.jurisdiction_level,
        state_code=data.state_code,
        governing_body=data.governing_body,
        introduced_date=data.introduced_date,
        created_by=current_user.id,
    )

    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy

# ======================================================
# USER — SUBMIT STATUS CHANGE REQUEST
# ======================================================

@router.post(
    "/status-request",
    response_model=PolicyStatusChangeRequestOut
)
def submit_status_change_request(
    data: PolicyStatusChangeRequestCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    policy = db.query(Policy).get(data.policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    status = db.query(PolicyStatus).get(data.requested_status_id)
    if not status:
        raise HTTPException(status_code=400, detail="Invalid status")

    request = PolicyStatusChangeRequest(
        policy_id=data.policy_id,
        requested_status_id=data.requested_status_id,
        requested_by=current_user.id,
        source_link=data.source_link,
        note=data.note,
    )

    db.add(request)
    db.commit()
    db.refresh(request)
    return request

# ======================================================
# ADMIN — REVIEW STATUS CHANGE REQUEST
# ======================================================

@router.post("/status-request/{request_id}/review")
def review_status_change_request(
    request_id: int,
    approve: bool = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    req = (
        db.query(PolicyStatusChangeRequest)
        .filter(PolicyStatusChangeRequest.id == request_id)
        .first()
    )

    if not req or req.approval_status != ApprovalStatus.pending:
        raise HTTPException(status_code=404, detail="Request not found")

    policy = db.query(Policy).get(req.policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy missing")

    if approve:
        policy.current_status_id = req.requested_status_id
        policy.last_verified_at = datetime.utcnow()

        history = PolicyStatusHistory(
            policy_id=policy.id,
            status_id=req.requested_status_id,
            changed_by=current_user.id,
            change_source=req.source_link,
            note=req.note,
        )
        db.add(history)

        req.approval_status = ApprovalStatus.approved
    else:
        req.approval_status = ApprovalStatus.rejected

    req.reviewed_by = current_user.id
    req.reviewed_at = datetime.utcnow()

    db.commit()
    return {"status": req.approval_status.value}

# ======================================================
# ADMIN — PENDING REQUEST QUEUE
# ======================================================

@router.get("/status-requests/pending")
def list_pending_status_requests(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    return (
        db.query(PolicyStatusChangeRequest)
        .filter(PolicyStatusChangeRequest.approval_status == ApprovalStatus.pending)
        .order_by(PolicyStatusChangeRequest.created_at.asc())
        .all()
    )
