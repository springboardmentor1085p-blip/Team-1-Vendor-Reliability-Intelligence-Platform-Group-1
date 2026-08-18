import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import User
from ..schemas import UserOut, UserUpdate, UserCreate
from ..utils.dependencies import RoleChecker, get_current_user
from ..utils.security import get_password_hash
from ..utils.helpers import log_audit

router = APIRouter(prefix="/users", tags=["Users"])
admin_required = RoleChecker(["Administrator"])
internal_staff_required = RoleChecker(["Administrator", "Procurement Manager", "Supply Chain Manager", "Finance Officer", "Auditor"])

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
ALLOWED_MIMETYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB

@router.post("/upload-avatar")
def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(admin_required)
):
    # Validate extension
    ext = file.filename.split(".")[-1].lower() if file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Only PNG, JPG, JPEG, and WebP are allowed."
        )
    
    # Validate MIME content type
    if file.content_type not in ALLOWED_MIMETYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image format content."
        )
    
    # Read file content to check size and verify it is not empty
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
    
    # Generate unique filename
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    
    # Ensure folder path exists
    avatar_dir = os.path.join("uploads", "avatars")
    os.makedirs(avatar_dir, exist_ok=True)
    
    # Save the file
    target_path = os.path.join(avatar_dir, unique_filename)
    with open(target_path, "wb") as f:
        f.write(content)
        
    # Return relative URL
    return {"avatar_url": f"/uploads/avatars/{unique_filename}"}

@router.get("/", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db), current_user: User = Depends(internal_staff_required)):
    return db.query(User).all()

@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(admin_required)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(user_in: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(admin_required)):
    # Check username and email uniqueness
    if db.query(User).filter(User.username == user_in.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")

    hashed = get_password_hash(user_in.password)
    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed,
        role=user_in.role,
        full_name=user_in.full_name,
        vendor_id=user_in.vendor_id,
        phone=user_in.phone,
        avatar_url=user_in.avatar_url,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_audit(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="Create User",
        module="Users",
        details=f"Admin created user {user.username} with role {user.role}."
    )
    return user

@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: int, user_in: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(admin_required)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_in.email:
        existing = db.query(User).filter(User.email == user_in.email, User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        user.email = user_in.email

    if user_in.full_name is not None:
        user.full_name = user_in.full_name
    if user_in.role is not None:
        user.role = user_in.role
    if user_in.is_active is not None:
        user.is_active = user_in.is_active
    if user_in.vendor_id is not None:
        user.vendor_id = user_in.vendor_id
    if user_in.phone is not None:
        user.phone = user_in.phone
    if user_in.password:
        user.hashed_password = get_password_hash(user_in.password)
    if user_in.avatar_url is not None:
        # Delete old avatar file to avoid orphaned files
        if user.avatar_url and user.avatar_url != user_in.avatar_url:
            old_path = user.avatar_url.lstrip("/")
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except Exception as e:
                    print(f"Error removing old avatar: {e}")
        user.avatar_url = user_in.avatar_url

    db.commit()
    db.refresh(user)

    log_audit(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="Update User",
        module="Users",
        details=f"Admin updated user details for {user.username}."
    )
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(admin_required)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own admin account")

    # Delete old avatar file to avoid orphaned files
    if user.avatar_url:
        old_path = user.avatar_url.lstrip("/")
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except Exception as e:
                print(f"Error removing avatar file on delete: {e}")

    db.delete(user)
    db.commit()

    log_audit(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="Delete User",
        module="Users",
        details=f"Admin deleted user {user.username}."
    )
    return
