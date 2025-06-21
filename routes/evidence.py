from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from db import get_db
from models.evidence import Evidence
from schemas.evidence import EvidenceOut
from utils.blob_utils import upload_file_to_azure
from utils.auth import get_current_user
from models.user import User
import traceback

router = APIRouter(prefix="/vault", tags=["evidence"])

@router.post("/upload", response_model=EvidenceOut)
async def upload_evidence(
    file: UploadFile = File(...),
    description: str = Form(...),
    tags: str = Form(""),
    location: str = Form(""),
    is_public: bool = Form(True),
    is_anonymous: bool = Form(False),
    entity_id: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        blob_url = await upload_file_to_azure(file)

        evidence = Evidence(
            blob_url=blob_url,
            description=description,
            tags=tags,
            location=location,
            is_public=is_public,
            is_anonymous=is_anonymous,
            entity_id=entity_id,
            user_id=None if is_anonymous else current_user.id
        )

        db.add(evidence)
        db.commit()
        db.refresh(evidence)

        return evidence

    except Exception as e:
        print("[ERROR] Upload route failed")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Evidence upload failed.")

@router.get("/public", response_model=list[EvidenceOut])
def list_public_evidence(db: Session = Depends(get_db)):
    return db.query(Evidence).filter(Evidence.is_public == True).order_by(Evidence.timestamp.desc()).all()
