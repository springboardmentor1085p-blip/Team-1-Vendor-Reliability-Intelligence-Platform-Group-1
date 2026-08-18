from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import Vendor, User
from ..schemas import VendorOut, VendorCreate, VendorUpdate
from ..utils.dependencies import get_current_user, RoleChecker
from ..utils.helpers import log_audit, create_notification

router = APIRouter(prefix="/vendors", tags=["Vendors"])

allowed_to_modify = RoleChecker(["Administrator", "Supply Chain Manager", "Procurement Manager"])
allowed_to_approve = RoleChecker(["Administrator", "Supply Chain Manager"])

@router.get("/", response_model=List[VendorOut])
def list_vendors(
    category: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Vendor)
    
    if category:
        query = query.filter(Vendor.category == category)
    if status:
        query = query.filter(Vendor.status == status)
    if search:
        query = query.filter(Vendor.name.ilike(f"%{search}%") | Vendor.contact_person.ilike(f"%{search}%"))
        
    return query.all()

@router.get("/{vendor_id}", response_model=VendorOut)
def get_vendor(vendor_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor

@router.post("/", response_model=VendorOut, status_code=status.HTTP_201_CREATED)
def create_vendor(
    vendor_in: VendorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(allowed_to_modify)
):
    # Check duplicate name
    if db.query(Vendor).filter(Vendor.name == vendor_in.name).first():
        raise HTTPException(status_code=400, detail="Vendor name already registered")

    vendor = Vendor(
        name=vendor_in.name,
        category=vendor_in.category,
        address=vendor_in.address,
        contact_person=vendor_in.contact_person,
        email=vendor_in.email,
        phone=vendor_in.phone,
        status="Pending Approval",
        reliability_score=100.0,
        risk_level="LOW"
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)

    log_audit(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="Create Vendor",
        module="Vendors",
        details=f"Vendor {vendor.name} created as Pending Approval."
    )

    # Notify Supply Chain Managers & Administrators
    scms = db.query(User).filter(User.role.in_(["Supply Chain Manager", "Administrator"])).all()
    for scm in scms:
        create_notification(
            db=db,
            user_id=scm.id,
            title="New Vendor Request",
            message=f"Vendor '{vendor.name}' has requested registration approval.",
            notification_type="Vendor Approval"
        )

    return vendor

@router.put("/{vendor_id}", response_model=VendorOut)
def update_vendor(
    vendor_id: int,
    vendor_in: VendorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(allowed_to_modify)
):
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    if vendor_in.name:
        existing = db.query(Vendor).filter(Vendor.name == vendor_in.name, Vendor.id != vendor_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Vendor name already in use")
        vendor.name = vendor_in.name

    if vendor_in.category is not None:
        vendor.category = vendor_in.category
    if vendor_in.address is not None:
        vendor.address = vendor_in.address
    if vendor_in.contact_person is not None:
        vendor.contact_person = vendor_in.contact_person
    if vendor_in.email is not None:
        vendor.email = vendor_in.email
    if vendor_in.phone is not None:
        vendor.phone = vendor_in.phone

    db.commit()
    db.refresh(vendor)

    log_audit(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="Update Vendor",
        module="Vendors",
        details=f"Updated details for vendor {vendor.name}."
    )

    return vendor

@router.put("/{vendor_id}/status", response_model=VendorOut)
def update_vendor_status(
    vendor_id: int,
    status_str: str,  # Active, Inactive, Rejected
    db: Session = Depends(get_db),
    current_user: User = Depends(allowed_to_approve)
):
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    if status_str not in ["Active", "Inactive", "Rejected", "Pending Approval"]:
        raise HTTPException(status_code=400, detail="Invalid status option")

    old_status = vendor.status
    vendor.status = status_str
    db.commit()
    db.refresh(vendor)

    log_audit(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="Update Vendor Status",
        module="Vendors",
        details=f"Vendor '{vendor.name}' status changed from '{old_status}' to '{status_str}'."
    )

    # Notify users associated with this vendor if any
    vendor_users = db.query(User).filter(User.vendor_id == vendor.id).all()
    for vu in vendor_users:
        create_notification(
            db=db,
            user_id=vu.id,
            title="Vendor Status Update",
            message=f"Your vendor account status has been updated to '{status_str}' by {current_user.full_name}.",
            notification_type="Vendor Approval"
        )
        # Attempt external SMTP email alert
        from ..services.email_service import send_vendor_status_email
        send_vendor_status_email(vu.email, vendor.name, status_str, f"Updated by SCM {current_user.full_name}")
        
        # Attempt SMS notification
        from ..services.sms_service import send_sms_notification
        target_phone = vu.phone or vendor.phone
        if target_phone:
            send_sms_notification(target_phone, f"VendorIQ: Registration status for '{vendor.name}' updated to {status_str}.")

    return vendor
