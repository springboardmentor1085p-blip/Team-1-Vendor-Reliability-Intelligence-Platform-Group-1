from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import AuditLog, User
from ..schemas import AuditLogOut
from ..utils.dependencies import RoleChecker

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])
allowed_roles = RoleChecker(["Administrator", "Auditor"])

@router.get("/", response_model=List[AuditLogOut])
def list_audit_logs(
    module: Optional[str] = None,
    action: Optional[str] = None,
    username: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(allowed_roles)
):
    query = db.query(AuditLog)
    
    if module:
        query = query.filter(AuditLog.module == module)
    if action:
        query = query.filter(AuditLog.action == action)
    if username:
        query = query.filter(AuditLog.username.ilike(f"%{username}%"))
        
    return query.order_by(AuditLog.created_at.desc()).all()
