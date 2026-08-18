import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets
import hashlib
from ..database import get_db
from ..models import User, Vendor
from ..schemas import UserCreate, UserLogin, Token, UserOut, ForgotPasswordRequest, ResetPasswordConfirm
from ..utils.security import get_password_hash, verify_password, create_access_token
from ..utils.dependencies import get_current_user
from ..utils.helpers import log_audit
from ..config import settings
import logging

logger = logging.getLogger("auth")

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    # Check if username exists
    existing_username = db.query(User).filter(User.username == user_in.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email exists
    existing_email = db.query(User).filter(User.email == user_in.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Validate or create vendor association
    vendor_id = user_in.vendor_id
    if user_in.role == "Vendor" and user_in.vendor_name:
        # Check if vendor already exists
        existing_vendor = db.query(Vendor).filter(Vendor.name == user_in.vendor_name).first()
        if existing_vendor:
            vendor_id = existing_vendor.id
        else:
            # Create new Vendor profile as Pending Approval
            new_vendor = Vendor(
                name=user_in.vendor_name,
                category="Raw Material Supplier",  # Default category
                status="Pending Approval",
                reliability_score=100.0,
                risk_level="LOW"
            )
            db.add(new_vendor)
            db.commit()
            db.refresh(new_vendor)
            vendor_id = new_vendor.id

            # Notify Supply Chain Managers & Administrators
            scms = db.query(User).filter(User.role.in_(["Supply Chain Manager", "Administrator"])).all()
            for scm in scms:
                create_notification(
                    db=db,
                    user_id=scm.id,
                    title="New Vendor Registration Request",
                    message=f"Vendor '{new_vendor.name}' has registered and requires approval.",
                    notification_type="Vendor Approval"
                )
    elif vendor_id:
        vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Associated Vendor not found"
            )

    # Password hashing
    hashed = get_password_hash(user_in.password)
    new_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed,
        role=user_in.role,
        full_name=user_in.full_name,
        vendor_id=vendor_id,
        phone=user_in.phone,
        avatar_url=user_in.avatar_url,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Audit log
    log_audit(
        db=db,
        user_id=new_user.id,
        username=new_user.username,
        action="User Registered",
        module="Auth",
        details=f"User {new_user.username} registered with role {new_user.role}."
    )

    return new_user

@router.post("/login", response_model=Token)
def login(login_in: UserLogin, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == login_in.username).first()
    if not user or not verify_password(login_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is deactivated"
        )

    # Create access token
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    
    # Audit log
    log_audit(
        db=db,
        user_id=user.id,
        username=user.username,
        action="User Login",
        module="Auth",
        details=f"User logged in successfully.",
        ip_address=request.client.host if request.client else None
    )

    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/forgot-password")
def forgot_password(req_in: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req_in.email).first()
    if user:
        # Generate time-limited secure token
        plain_token = secrets.token_urlsafe(32)
        hashed_token = hashlib.sha256(plain_token.encode()).hexdigest()
        
        user.reset_token = hashed_token
        user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        db.commit()
        
        frontend_url = settings.FRONTEND_URL.rstrip('/')
        reset_url = f"{frontend_url}/reset-password?token={plain_token}"
        # Log to terminal for demo purposes
        logger.info(f"[DEMO] PASSWORD RESET URL: {reset_url}")
        print(f"\n[DEMO] PASSWORD RESET URL: {reset_url}\n", flush=True)
        
        # Trigger real SMTP email notification
        from ..services.email_service import send_password_reset_email
        send_password_reset_email(user.email, user.username, reset_url)
        
    # Return generic message to prevent email enumeration
    return {"message": "If this email is registered, a password reset link has been generated."}

@router.post("/reset-password")
def reset_password(confirm_in: ResetPasswordConfirm, db: Session = Depends(get_db)):
    hashed_token = hashlib.sha256(confirm_in.token.encode()).hexdigest()
    user = db.query(User).filter(
        User.reset_token == hashed_token,
        User.reset_token_expiry > datetime.utcnow()
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
        
    if len(confirm_in.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long"
        )
        
    # Hash new password using native bcrypt logic
    user.hashed_password = get_password_hash(confirm_in.new_password)
    user.reset_token = None
    user.reset_token_expiry = None
    db.commit()
    
    log_audit(
        db=db,
        user_id=user.id,
        username=user.username,
        action="Password Reset Self-Service",
        module="Auth",
        details="User successfully reset password using token verification."
    )
    
    return {"message": "Password has been reset successfully."}


ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
ALLOWED_MIMETYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB

@router.post("/me/avatar", response_model=UserOut)
def upload_my_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Validate extension
    ext = file.filename.split(".")[-1].lower() if file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Only PNG, JPG, JPEG, and WebP are allowed."
        )
    
    # Validate MIME type
    if file.content_type not in ALLOWED_MIMETYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image format content."
        )
    
    # Validate size limit
    content = file.file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds the 2MB limit."
        )
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty or corrupted."
        )
    
    # Delete old avatar file to avoid orphaned files
    if current_user.avatar_url:
        old_path = current_user.avatar_url.lstrip("/")
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except Exception as e:
                print(f"Error removing old avatar: {e}")
                
    # Generate unique filename
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    avatar_dir = os.path.join("uploads", "avatars")
    os.makedirs(avatar_dir, exist_ok=True)
    
    # Save file
    target_path = os.path.join(avatar_dir, unique_filename)
    with open(target_path, "wb") as f:
        f.write(content)
        
    # Update user record
    current_user.avatar_url = f"/uploads/avatars/{unique_filename}"
    db.commit()
    db.refresh(current_user)
    
    log_audit(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="Upload Own Avatar",
        module="Auth",
        details="User updated their own avatar profile picture."
    )
    
    return current_user


@router.delete("/me/avatar", response_model=UserOut)
def delete_my_avatar(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.avatar_url:
        # Delete old avatar file to avoid orphaned files
        old_path = current_user.avatar_url.lstrip("/")
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except Exception as e:
                print(f"Error removing avatar file: {e}")
        current_user.avatar_url = None
        db.commit()
        db.refresh(current_user)
        
        log_audit(
            db=db,
            user_id=current_user.id,
            username=current_user.username,
            action="Delete Own Avatar",
            module="Auth",
            details="User cleared/reset their own avatar to default."
        )
        
    return current_user

