import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.notification import Notification
from app.schemas.base import GenericResponse
from app.services.notification_service import mark_read

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=GenericResponse[list[dict]])
async def list_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve all notifications for the current user."""
    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )
    
    data = []
    for n in notifications:
        data.append({
            "id": str(n.id),
            "user_id": str(n.user_id),
            "type": n.type,
            "title": n.title,
            "body": n.body,
            "extra_data": n.extra_data if hasattr(n, "extra_data") else {},
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat(),
        })
        
    return {
        "success": True,
        "message": "Notifications retrieved",
        "data": data,
    }


@router.patch("/{notification_id}/read", response_model=GenericResponse[bool])
async def read_notification(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a single notification as read."""
    success = mark_read(db, notification_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {
        "success": True,
        "message": "Notification marked as read",
        "data": True,
    }


@router.post("/read-all", response_model=GenericResponse[bool])
async def read_all_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark all notifications as read for the current user."""
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).update({Notification.is_read: True}, synchronize_session=False)
    db.commit()
    return {
        "success": True,
        "message": "All notifications marked as read",
        "data": True,
    }
