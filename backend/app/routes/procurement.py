from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import ProcurementRequest, User, Vendor
from ..schemas import ProcurementRequestOut, ProcurementRequestCreate, ProcurementRequestUpdate
from ..utils.dependencies import get_current_user, RoleChecker
from ..utils.helpers import log_audit, create_notification

router = APIRouter(prefix="/procurement", tags=["Procurement Requests"])

allowed_to_create = RoleChecker(["Administrator", "Procurement Manager", "Supply Chain Manager", "Finance Officer"])
allowed_to_approve = RoleChecker(["Administrator", "Supply Chain Manager", "Finance Officer"])

@router.get("/", response_model=List[ProcurementRequestOut])
def list_procurement_requests(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    vendor_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(ProcurementRequest)
    
    # Vendors can only see procurement requests assigned to them
    if current_user.role == "Vendor":
        if not current_user.vendor_id:
            return []
        query = query.filter(ProcurementRequest.vendor_id == current_user.vendor_id)
    
    if status:
        query = query.filter(ProcurementRequest.status == status)
    if priority:
        query = query.filter(ProcurementRequest.priority == priority)
    if vendor_id:
        query = query.filter(ProcurementRequest.vendor_id == vendor_id)
        
    return query.all()

@router.get("/{request_id}", response_model=ProcurementRequestOut)
def get_procurement_request(request_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    req = db.query(ProcurementRequest).filter(ProcurementRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Procurement request not found")
        
    # Vendor restriction
    if current_user.role == "Vendor" and req.vendor_id != current_user.vendor_id:
        raise HTTPException(status_code=403, detail="Access denied")
        
    return req

@router.post("/", response_model=ProcurementRequestOut, status_code=status.HTTP_201_CREATED)
def create_procurement_request(
    req_in: ProcurementRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(allowed_to_create)
):
    if req_in.vendor_id:
        vendor = db.query(Vendor).filter(Vendor.id == req_in.vendor_id).first()
        if not vendor:
            raise HTTPException(status_code=400, detail="Assigned Vendor not found")

    req = ProcurementRequest(
        title=req_in.title,
        description=req_in.description,
        priority=req_in.priority,
        estimated_cost=req_in.estimated_cost,
        vendor_id=req_in.vendor_id,
        requested_by_id=current_user.id,
        status="Pending"
    )
    db.add(req)
    db.commit()
    db.refresh(req)

    log_audit(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="Create Procurement Request",
        module="Procurement",
        details=f"Procurement request '{req.title}' created (Est Cost: ${req.estimated_cost})."
    )

    # Notify approvers
    approvers = db.query(User).filter(User.role.in_(["Supply Chain Manager", "Finance Officer", "Administrator"])).all()
    for approver in approvers:
        create_notification(
            db=db,
            user_id=approver.id,
            title="Procurement Request Pending Approval",
            message=f"Request '{req.title}' for ${req.estimated_cost} is pending review.",
            notification_type="Procurement"
        )

    return req

@router.put("/{request_id}", response_model=ProcurementRequestOut)
def update_procurement_request(
    request_id: int,
    req_in: ProcurementRequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    req = db.query(ProcurementRequest).filter(ProcurementRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Procurement request not found")

    # Authorizations: Administrator or Creator can update
    if current_user.role != "Administrator" and req.requested_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the requester or Administrator can edit details")

    if req.status not in ["Pending", "Rejected"]:
        raise HTTPException(status_code=400, detail="Cannot edit a request that is already approved or ordered")

    if req_in.title is not None:
        req.title = req_in.title
    if req_in.description is not None:
        req.description = req_in.description
    if req_in.priority is not None:
        req.priority = req_in.priority
    if req_in.estimated_cost is not None:
        req.estimated_cost = req_in.estimated_cost
    if req_in.vendor_id is not None:
        req.vendor_id = req_in.vendor_id

    db.commit()
    db.refresh(req)

    log_audit(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="Update Procurement Request",
        module="Procurement",
        details=f"Updated details for request '{req.title}'."
    )
    return req

@router.put("/{request_id}/status", response_model=ProcurementRequestOut)
def update_procurement_request_status(
    request_id: int,
    status_str: str,  # Approved, Rejected, Cancelled
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    req = db.query(ProcurementRequest).filter(ProcurementRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Procurement request not found")

    old_status = req.status

    if status_str in ["Approved", "Rejected"]:
        # Requires Approver Roles
        if current_user.role not in ["Administrator", "Supply Chain Manager", "Finance Officer"]:
            raise HTTPException(status_code=403, detail="Not authorized to approve/reject requests")
        req.approved_by_id = current_user.id
        req.status = status_str
    elif status_str == "Cancelled":
        # Requires Administrator or the original creator
        if current_user.role != "Administrator" and req.requested_by_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to cancel this request")
        req.status = status_str
    else:
        raise HTTPException(status_code=400, detail="Invalid status change action")

    db.commit()
    db.refresh(req)

    log_audit(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="Update Procurement Status",
        module="Procurement",
        details=f"Procurement request '{req.title}' status changed from '{old_status}' to '{status_str}'."
    )

    # Notify the creator
    create_notification(
        db=db,
        user_id=req.requested_by_id,
        title="Procurement Status Update",
        message=f"Your request '{req.title}' has been '{status_str.lower()}' by {current_user.full_name}.",
        notification_type="Procurement"
    )

    # Attempt external notifications
    creator = db.query(User).filter(User.id == req.requested_by_id).first()
    if creator:
        from ..services.email_service import send_procurement_status_email
        send_procurement_status_email(creator.email, req.title, status_str, f"Status modified by {current_user.full_name}")

        from ..services.sms_service import send_sms_notification
        if creator.phone:
            send_sms_notification(creator.phone, f"VendorIQ: Requisition '{req.title}' status changed to {status_str}.")

    return req
