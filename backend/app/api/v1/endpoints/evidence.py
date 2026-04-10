import re
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.v1.deps import OrgContext, get_org_context
from app.database import get_db
from app.models.evidence import Evidence
from app.models.system import AISystem

router = APIRouter(tags=["evidence"])

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "text/plain",
    "text/csv",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


def _sanitize_filename(filename: str) -> str:
    filename = re.sub(r"[^\w\s\-.]", "", filename)
    filename = re.sub(r"\s+", "_", filename)
    return filename[:255]


def _upload_to_s3(key: str, content: bytes, content_type: str) -> bool:
    try:
        import boto3
        from app.config import settings
        s3 = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )
        s3.put_object(Bucket=settings.AWS_S3_BUCKET, Key=key, Body=content, ContentType=content_type)
        return True
    except Exception:
        return False


@router.post(
    "/organizations/{org_id}/systems/{system_id}/evidence",
    status_code=status.HTTP_201_CREATED,
)
async def upload_evidence(
    system_id: str,
    file: UploadFile = File(...),
    ctx: OrgContext = Depends(get_org_context),
    db: Session = Depends(get_db),
):
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail=f"File type '{file.content_type}' not allowed")

    system = db.query(AISystem).filter(AISystem.id == system_id, AISystem.org_id == ctx.org.id).first()
    if not system:
        raise HTTPException(status_code=404, detail="System not found")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File exceeds 50MB limit")

    safe_filename = _sanitize_filename(file.filename or "upload")
    s3_key = f"evidence/{uuid.uuid4()}/{safe_filename}"
    _upload_to_s3(s3_key, content, file.content_type)

    evidence = Evidence(
        system_id=system_id,
        org_id=ctx.org.id,
        filename=safe_filename,
        s3_key=s3_key,
        content_type=file.content_type,
        size=len(content),
        uploaded_by=ctx.user.id,
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return {"id": evidence.id, "filename": evidence.filename, "s3_key": evidence.s3_key}


@router.get("/organizations/{org_id}/systems/{system_id}/evidence")
def list_evidence(system_id: str, ctx: OrgContext = Depends(get_org_context), db: Session = Depends(get_db)):
    return db.query(Evidence).filter(Evidence.system_id == system_id, Evidence.org_id == ctx.org.id).all()
