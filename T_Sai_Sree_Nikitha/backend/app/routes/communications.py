from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
import os
import uuid
from typing import List, Optional
from ..database import get_db
from ..models import Communication, User, Vendor
from ..schemas import CommunicationOut, CommunicationCreate
from ..utils.dependencies import get_current_user
from ..utils.helpers import log_audit, create_notification
from ..config import settings

router = APIRouter(prefix="/communications", tags=["Communications"])

@router.get("/", response_model=List[CommunicationOut])
def list_communications(
    vendor_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Communication)
    
    # Restrict messages depending on role
    if current_user.role == "Vendor":
        if not current_user.vendor_id:
            return []
        # Vendor sees messages sent by or received by them, or involving their vendor profile
        query = query.filter(
            or_(
                Communication.sender_id == current_user.id,
                Communication.recipient_id == current_user.id,
                Communication.vendor_id == current_user.vendor_id
            )
        )
    else:
        # Internal roles can view messages they sent/received, or filter by specific vendor profile
        if vendor_id:
            query = query.filter(Communication.vendor_id == vendor_id)
        else:
            query = query.filter(
                or_(
                    Communication.sender_id == current_user.id,
                    Communication.recipient_id == current_user.id
                )
            )
            
    return query.order_by(Communication.created_at.desc()).all()

@router.post("/", response_model=CommunicationOut, status_code=status.HTTP_201_CREATED)
def send_communication(
    msg_in: CommunicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Recipient validation
    recipient = None
    if msg_in.recipient_id:
        recipient = db.query(User).filter(User.id == msg_in.recipient_id).first()
        if not recipient:
            raise HTTPException(status_code=404, detail="Recipient user not found")

    # Vendor validation
    if msg_in.vendor_id:
        vendor = db.query(Vendor).filter(Vendor.id == msg_in.vendor_id).first()
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")

    msg = Communication(
        sender_id=current_user.id,
        recipient_id=msg_in.recipient_id,
        vendor_id=msg_in.vendor_id,
        subject=msg_in.subject,
        message=msg_in.message,
        is_read=False,
        attachment_name=msg_in.attachment_name,
        attachment_path=msg_in.attachment_path,
        attachment_size=msg_in.attachment_size,
        attachment_type=msg_in.attachment_type
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    # Log action
    log_audit(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="Send Message",
        module="Communication",
        details=f"Sent message to User ID {msg_in.recipient_id} regarding Vendor ID {msg_in.vendor_id}."
    )

    # Notify recipient
    if msg_in.recipient_id:
        create_notification(
            db=db,
            user_id=msg_in.recipient_id,
            title=f"New Message from {current_user.full_name}",
            message=f"Subject: {msg_in.subject}. Read details in the communications portal.",
            notification_type="Communication"
        )

    return msg

@router.put("/{msg_id}/read", response_model=CommunicationOut)
def mark_message_as_read(
    msg_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    msg = db.query(Communication).filter(Communication.id == msg_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
        
    if msg.recipient_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the recipient can mark this message as read")
        
    msg.is_read = True
    db.commit()
    db.refresh(msg)
    return msg

@router.post("/upload-file")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    ext = os.path.splitext(file.filename)[1].lower().replace(".", "")
    allowed = ["pdf", "doc", "docx", "xls", "xlsx", "csv", "png", "jpg", "jpeg", "txt"]
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"File extension .{ext} is not allowed.")
        
    contents = await file.read()
    file_size = len(contents)
    max_size_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file_size > max_size_bytes:
        raise HTTPException(status_code=400, detail=f"File size exceeds maximum limit of {settings.MAX_UPLOAD_SIZE_MB} MB.")
        
    upload_dir = settings.UPLOAD_DIR
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
        
    safe_filename = f"{uuid.uuid4().hex}.{ext}"
    target_path = os.path.join(upload_dir, safe_filename)
    
    with open(target_path, "wb") as f:
        f.write(contents)
        
    return {
        "attachment_name": file.filename,
        "attachment_path": safe_filename,
        "attachment_size": file_size,
        "attachment_type": file.content_type
    }

@router.get("/{msg_id}/download")
def download_attachment(
    msg_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    msg = db.query(Communication).filter(Communication.id == msg_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
        
    is_authorized = (
        current_user.role in ["Administrator", "Auditor"]
        or msg.sender_id == current_user.id
        or msg.recipient_id == current_user.id
    )
    if not is_authorized:
        raise HTTPException(status_code=403, detail="Access denied. You are not authorized to download this file.")
        
    if not msg.attachment_path:
        raise HTTPException(status_code=404, detail="This message has no file attachment.")
        
    target_path = os.path.join(settings.UPLOAD_DIR, msg.attachment_path)
    if not os.path.exists(target_path):
        raise HTTPException(status_code=404, detail="Attachment file not found on server storage.")
        
    return FileResponse(
        path=target_path,
        filename=msg.attachment_name,
        media_type=msg.attachment_type
    )
