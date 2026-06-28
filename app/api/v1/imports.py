import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user, require_roles
from app.core.errors import BakerProfitError
from app.db.session import get_db
from app.models.user import User
from app.schemas.imports import (
    ConfirmImportResponse,
    ImportJobResponse,
    ReviewMappingRequest,
    RollbackResponse,
)
from app.services import import_service

router = APIRouter(prefix="/imports", tags=["imports"])

_ALLOWED_TYPES = {"xlsx", "csv", "pdf"}
_MAX_BYTES = getattr(settings, "max_upload_size_bytes", 10 * 1024 * 1024)  # 10 MB default


def _err(exc: Exception) -> HTTPException:
    code = getattr(exc, "status_code", 400)
    return HTTPException(status_code=code, detail=exc.to_dict() if hasattr(exc, "to_dict") else str(exc))


def _job_to_response(job) -> ImportJobResponse:
    import json
    sections = None
    if job.detected_sections_json:
        from app.schemas.imports import DetectedSection
        raw = json.loads(job.detected_sections_json)
        sections = [DetectedSection(**s) for s in raw]
    return ImportJobResponse(
        id=job.id,
        status=job.status,
        source_file_type=job.source_file_type,
        source_file_url=job.source_file_url,
        mapping_confidence_score=float(job.mapping_confidence_score) if job.mapping_confidence_score else None,
        error_message=job.error_message,
        detected_sections=sections,
        created_at=job.created_at,
        completed_at=job.completed_at,
    )


@router.get("", response_model=list[ImportJobResponse])
def list_jobs(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from app.models.import_job import ImportJob
    jobs = (
        db.query(ImportJob)
        .filter(ImportJob.tenant_id == user.tenant_id)
        .order_by(ImportJob.created_at.desc())
        .limit(50)
        .all()
    )
    return [_job_to_response(j) for j in jobs]


@router.post("/upload", response_model=ImportJobResponse, status_code=201)
async def upload(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("owner", "manager")),
):
    file_type = import_service._detect_file_type(file.filename or "")
    if file_type not in _ALLOWED_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type. Allowed: {', '.join(_ALLOWED_TYPES)}",
        )

    content = await file.read()
    if len(content) > _MAX_BYTES:
        raise HTTPException(status_code=413, detail="File too large")

    try:
        job = import_service.upload_and_parse(db, user.tenant_id, user.id, file.filename or "upload", content)
        db.commit()
        db.refresh(job)
        return _job_to_response(job)
    except BakerProfitError as exc:
        raise _err(exc)


@router.get("/{job_id}", response_model=ImportJobResponse)
def get_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        job = import_service.get_job(db, user.tenant_id, job_id)
        return _job_to_response(job)
    except BakerProfitError as exc:
        raise _err(exc)


@router.post("/{job_id}/review-mapping", response_model=ImportJobResponse)
def review_mapping(
    job_id: uuid.UUID,
    payload: ReviewMappingRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("owner", "manager")),
):
    try:
        job = import_service.review_mapping(db, user.tenant_id, job_id, payload)
        db.commit()
        db.refresh(job)
        return _job_to_response(job)
    except BakerProfitError as exc:
        raise _err(exc)


@router.post("/{job_id}/confirm", response_model=ConfirmImportResponse)
def confirm(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("owner", "manager")),
):
    try:
        _job, response = import_service.confirm_import(db, user.tenant_id, job_id)
        db.commit()
        return response
    except BakerProfitError as exc:
        raise _err(exc)


@router.post("/{job_id}/rollback", response_model=RollbackResponse)
def rollback(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("owner", "manager")),
):
    try:
        _job, response = import_service.rollback_import(db, user.tenant_id, job_id)
        db.commit()
        return response
    except BakerProfitError as exc:
        raise _err(exc)
