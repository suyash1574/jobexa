from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from uuid import UUID
import uuid
from datetime import datetime
from typing import List, Optional

from src.models.base import get_db
from src.models.user import User
from src.models.resume import Resume, Certificate
from src.schemas.resume import ResumeOut, CertificateOut
from src.api.auth import get_current_user
from src.services.storage import StorageService

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/resumes", response_model=ResumeOut, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    role_tag: Optional[str] = Form(None),
    is_default: bool = Form(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported for resumes.")

    try:
        # Read bytes to upload and measure size
        file_bytes = await file.read()
        file_url = StorageService.upload_file(
            file_bytes=file_bytes,
            filename=file.filename,
            folder="resumes"
        )

        # If setting as default, unset other default resumes
        if is_default:
            db.query(Resume).filter(
                Resume.user_id == current_user.id,
                Resume.is_default == True
            ).update({Resume.is_default: False})

        new_resume = Resume(
            id=uuid.uuid4(),
            user_id=current_user.id,
            filename=file.filename,
            file_url=file_url,
            file_size=len(file_bytes),
            role_tag=role_tag,
            is_default=is_default,
            created_at=datetime.utcnow()
        )
        db.add(new_resume)
        db.commit()
        db.refresh(new_resume)
        return new_resume
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload resume: {str(e)}")

@router.get("/resumes", response_model=List[ResumeOut])
def list_resumes(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Resume).filter(Resume.user_id == current_user.id).all()

@router.delete("/resumes/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resume(id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(
        Resume.id == id,
        Resume.user_id == current_user.id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    db.delete(resume)
    db.commit()
    return

@router.post("/certificates", response_model=CertificateOut, status_code=status.HTTP_201_CREATED)
async def upload_certificate(
    file: UploadFile = File(...),
    category: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported for certificates.")

    try:
        file_bytes = await file.read()
        file_url = StorageService.upload_file(
            file_bytes=file_bytes,
            filename=file.filename,
            folder="certificates"
        )

        new_certificate = Certificate(
            id=uuid.uuid4(),
            user_id=current_user.id,
            filename=file.filename,
            file_url=file_url,
            file_size=len(file_bytes),
            category=category,
            created_at=datetime.utcnow()
        )
        db.add(new_certificate)
        db.commit()
        db.refresh(new_certificate)
        return new_certificate
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload certificate: {str(e)}")

@router.get("/certificates", response_model=List[CertificateOut])
def list_certificates(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Certificate).filter(Certificate.user_id == current_user.id).all()

@router.delete("/certificates/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_certificate(id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cert = db.query(Certificate).filter(
        Certificate.id == id,
        Certificate.user_id == current_user.id
    ).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    db.delete(cert)
    db.commit()
    return
