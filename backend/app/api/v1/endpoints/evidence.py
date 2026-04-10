import hashlib
import logging
import uuid

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_active_user
from app.config import settings
from app.database import get_db
from app.models.evidence import EvidenceAttachment
from app.models.user import User
from app.schemas.evidence import EvidenceCreate, EvidenceRead

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_s3_client():
    kwargs = {
        "aws_access_key_id": settings.AWS_ACCESS_KEY_ID or None,
        "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY or None,
    }
    if settings.AWS_S3_ENDPOINT_URL:
        kwargs["endpoint_url"] = settings.AWS_S3_ENDPOINT_URL
    return boto3.client("s3", **kwargs)


def _upload_to_s3(file_bytes: bytes, s3_key: str, content_type: str) -> bool:
    if not settings.AWS_ACCESS_KEY_ID and settings.ENVIRONMENT == "development":
        logger.warning("S3 not configured — skipping upload in development mode")
        return False
    try:
        client = _get_s3_client()
        client.put_object(
            Bucket=settings.AWS_S3_BUCKET,
            Key=s3_key,
            Body=file_bytes,
            ContentType=content_type,
        )
        return True
    except (BotoCoreError, ClientError) as exc:
        logger.warning("S3 upload failed: %s", exc)
        return False


def _generate_presigned_url(s3_key: str, expiry: int = 3600) -> str | None:
    if not settings.AWS_ACCESS_KEY_ID and settings.ENVIRONMENT == "development":
        return None
    try:
        client = _get_s3_client()
        return client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.AWS_S3_BUCKET, "Key": s3_key},
            ExpiresIn=expiry,
        )
    except (BotoCoreError, ClientError) as exc:
        logger.warning("Failed to generate presigned URL: %s", exc)
        return None


@router.post("/upload", response_model=EvidenceRead, status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    file: UploadFile = File(...),
    revision_id: uuid.UUID | None = Query(None),
    section_id: uuid.UUID | None = Query(None),
    field_key: str | None = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    file_bytes = await file.read()
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    s3_key = f"evidence/{uuid.uuid4()}/{file.filename}"

    _upload_to_s3(file_bytes, s3_key, file.content_type or "application/octet-stream")

    evidence = EvidenceAttachment(
        id=uuid.uuid4(),
        revision_id=revision_id,
        section_id=section_id,
        field_key=field_key,
        type="file",
        filename=file.filename,
        s3_key=s3_key,
        file_hash=file_hash,
        mime_type=file.content_type,
        size_bytes=len(file_bytes),
        uploaded_by=current_user.id,
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return EvidenceRead.model_validate(evidence)


@router.post("/url", response_model=EvidenceRead, status_code=status.HTTP_201_CREATED)
def attach_url_evidence(
    evidence_in: EvidenceCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if not evidence_in.url:
        raise HTTPException(status_code=400, detail="URL is required")

    evidence = EvidenceAttachment(
        id=uuid.uuid4(),
        revision_id=evidence_in.revision_id,
        section_id=evidence_in.section_id,
        field_key=evidence_in.field_key,
        type="url",
        url=evidence_in.url,
        source=evidence_in.source,
        version=evidence_in.version,
        uploaded_by=current_user.id,
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return EvidenceRead.model_validate(evidence)


@router.get("/", response_model=list[EvidenceRead])
def list_evidence(
    section_id: uuid.UUID | None = Query(None),
    revision_id: uuid.UUID | None = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    query = db.query(EvidenceAttachment)
    if section_id:
        query = query.filter(EvidenceAttachment.section_id == section_id)
    elif revision_id:
        query = query.filter(EvidenceAttachment.revision_id == revision_id)
    else:
        raise HTTPException(status_code=400, detail="Either section_id or revision_id is required")
    return [EvidenceRead.model_validate(e) for e in query.all()]


@router.delete("/{evidence_id}")
def delete_evidence(
    evidence_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    evidence = db.query(EvidenceAttachment).filter(EvidenceAttachment.id == evidence_id).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    db.delete(evidence)
    db.commit()
    return {"message": "Evidence deleted"}


@router.get("/{evidence_id}/download-url")
def get_download_url(
    evidence_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    evidence = db.query(EvidenceAttachment).filter(EvidenceAttachment.id == evidence_id).first()
    if not evidence or not evidence.s3_key:
        raise HTTPException(status_code=404, detail="Evidence file not found")

    url = _generate_presigned_url(evidence.s3_key)
    if not url:
        raise HTTPException(status_code=503, detail="Could not generate download URL")
    return {"download_url": url, "expires_in": 3600}
