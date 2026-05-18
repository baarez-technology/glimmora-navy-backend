import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models.documentation import DocumentationTopic
from app.models.user import User
from app.schemas.base import GenericResponse
from app.schemas.documentation import DocumentationCreate, DocumentationOut, DocumentationUpdate

router = APIRouter(prefix="/documentation", tags=["Documentation"])


def _topic_to_dict(t: DocumentationTopic) -> dict:
    return {
        "id": str(t.id),
        "title": t.title,
        "domain": t.domain,
        "description": t.description,
        "content_markdown": t.content_markdown,
        "example_interactive": t.example_interactive,
        "created_by": str(t.created_by) if t.created_by else None,
        "is_active": t.is_active,
        "created_at": t.created_at.isoformat(),
        "updated_at": t.updated_at.isoformat(),
    }


@router.get(
    "",
    response_model=GenericResponse[list[dict]],
    summary="List Documentation Topics",
    description="Retrieve technical manuals and doctrine-grounded study tutorials. Filterable by domain.",
)
async def list_documentation(
    domain: str = None,
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(DocumentationTopic)
    if active_only:
        query = query.filter(DocumentationTopic.is_active)
    if domain:
        query = query.filter(DocumentationTopic.domain == domain)
    topics = query.order_by(DocumentationTopic.created_at.desc()).all()
    return {
        "success": True,
        "message": "Documentation topics retrieved successfully",
        "data": [_topic_to_dict(t) for t in topics],
    }


@router.get(
    "/{topic_id}",
    response_model=GenericResponse[dict],
    summary="Get Documentation Topic Details",
    description="Retrieve a single documentation topic details by its ID.",
)
async def get_documentation_detail(
    topic_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    topic = db.query(DocumentationTopic).filter(DocumentationTopic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Documentation topic not found")
    return {
        "success": True,
        "message": "Documentation topic retrieved successfully",
        "data": _topic_to_dict(topic),
    }


@router.post(
    "",
    response_model=GenericResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Create Documentation Topic",
    description="Upload a new technical documentation topic. Requires Instructor or Admin privileges.",
)
async def create_documentation(
    body: DocumentationCreate,
    current_user: User = Depends(require_roles("instructor", "admin")),
    db: Session = Depends(get_db),
):
    topic = DocumentationTopic(
        id=uuid.uuid4(),
        title=body.title,
        domain=body.domain,
        description=body.description,
        content_markdown=body.content_markdown,
        example_interactive=body.example_interactive,
        created_by=current_user.id,
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db.add(topic)
    db.commit()
    db.refresh(topic)

    return {
        "success": True,
        "message": "Documentation topic created successfully",
        "data": _topic_to_dict(topic),
    }


@router.put(
    "/{topic_id}",
    response_model=GenericResponse[dict],
    summary="Update Documentation Topic",
    description="Modify an existing technical documentation topic. Requires Instructor or Admin privileges.",
)
async def update_documentation(
    topic_id: uuid.UUID,
    body: DocumentationUpdate,
    current_user: User = Depends(require_roles("instructor", "admin")),
    db: Session = Depends(get_db),
):
    topic = db.query(DocumentationTopic).filter(DocumentationTopic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Documentation topic not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(topic, field, value)

    topic.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(topic)

    return {
        "success": True,
        "message": "Documentation topic updated successfully",
        "data": _topic_to_dict(topic),
    }


@router.delete(
    "/{topic_id}",
    response_model=GenericResponse[dict],
    summary="Delete Documentation Topic",
    description="Remove an existing technical documentation topic. Requires Instructor or Admin privileges.",
)
async def delete_documentation(
    topic_id: uuid.UUID,
    current_user: User = Depends(require_roles("instructor", "admin")),
    db: Session = Depends(get_db),
):
    topic = db.query(DocumentationTopic).filter(DocumentationTopic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Documentation topic not found")

    db.delete(topic)
    db.commit()

    return {
        "success": True,
        "message": "Documentation topic deleted successfully",
        "data": {"id": str(topic_id)},
    }
