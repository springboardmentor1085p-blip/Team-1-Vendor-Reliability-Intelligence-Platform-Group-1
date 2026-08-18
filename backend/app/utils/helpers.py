from sqlalchemy.orm import Session
from ..models import AuditLog, Notification

def log_audit(db: Session, user_id: int, username: str, action: str, module: str, details: str = None, ip_address: str = None):
    """
    Standard helper to insert an audit log record.
    """
    audit = AuditLog(
        user_id=user_id,
        username=username,
        action=action,
        module=module,
        details=details,
        ip_address=ip_address
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    return audit

def create_notification(db: Session, user_id: int, title: str, message: str, notification_type: str):
    """
    Standard helper to send an in-app notification.
    """
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=notification_type,
        is_read=False
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification
