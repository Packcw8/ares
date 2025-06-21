from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
from db import get_db
from models.evidence import Evidence
from schemas.evidence import EvidenceOut
from utils.blob_utils import upload_file_to_azure

router = APIRouter()

@router.post("/vault/upload", response_model=EvidenceOut)
async def upload_evidence(
    file: UploadFile = File(...),
    description: str = Form(...),
    tags: str = Form(""),
    location: str = Form(""),
    is_public: bool = Form(True),
    is_anonymous: bool = Form(False),
    db: Session = Depends(get_db),
):
    blob_url = await upload_file_to_azure(file)

    evidence = Evidence(
        blob_url=blob_url,
        description=description,
        tags=tags,
        location=location,
        is_public=is_public,
        is_anonymous=is_anonymous
    )

    db.add(evidence)
    db.commit()
    db.refresh(evidence)

    return evidence
