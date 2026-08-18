from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import PurchaseOrder, ProcurementRequest, Vendor, User, VendorPerformance
from ..schemas import PurchaseOrderOut, PurchaseOrderCreate, PurchaseOrderUpdate
from ..utils.dependencies import get_current_user, RoleChecker
from ..utils.helpers import log_audit, create_notification

router = APIRouter(prefix="/purchase-orders", tags=["Purchase Orders"])

allowed_to_create = RoleChecker(["Administrator", "Procurement Manager", "Supply Chain Manager"])
allowed_to_approve = RoleChecker(["Administrator", "Supply Chain Manager", "Finance Officer"])
allowed_to_update = RoleChecker(["Administrator", "Procurement Manager", "Supply Chain Manager", "Finance Officer", "Vendor"])

@router.get("/", response_model=List[PurchaseOrderOut])
def list_purchase_orders(
    status: Optional[str] = None,
    vendor_id: Optional[int] = None,
    invoice_status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(PurchaseOrder)
    
    # Vendor restriction
    if current_user.role == "Vendor":
        if not current_user.vendor_id:
            return []
        query = query.filter(PurchaseOrder.vendor_id == current_user.vendor_id)
        
    if status:
        query = query.filter(PurchaseOrder.status == status)
    if vendor_id:
        query = query.filter(PurchaseOrder.vendor_id == vendor_id)
    if invoice_status:
        query = query.filter(PurchaseOrder.invoice_status == invoice_status)
        
    return query.all()

@router.get("/{po_id}", response_model=PurchaseOrderOut)
def get_purchase_order(po_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
        
    if current_user.role == "Vendor" and po.vendor_id != current_user.vendor_id:
        raise HTTPException(status_code=403, detail="Access denied")
        
    return po

@router.post("/", response_model=PurchaseOrderOut, status_code=status.HTTP_201_CREATED)
def create_purchase_order(
    po_in: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(allowed_to_create)
):
    # Check parent request
    req = db.query(ProcurementRequest).filter(ProcurementRequest.id == po_in.procurement_request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Parent Procurement Request not found")
    
    if req.status != "Approved":
        raise HTTPException(status_code=400, detail="Procurement request must be 'Approved' before creating a PO")

    # Check vendor
    vendor = db.query(Vendor).filter(Vendor.id == po_in.vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    # Generate unique PO number
    today_str = datetime.utcnow().strftime("%Y%m%d")
    count = db.query(PurchaseOrder).count()
    po_number = f"PO-{today_str}-{count + 1:04d}"

    po = PurchaseOrder(
        po_number=po_number,
        procurement_request_id=po_in.procurement_request_id,
        vendor_id=po_in.vendor_id,
        amount=po_in.amount,
        expected_delivery_date=po_in.expected_delivery_date,
        status="Pending Approval",
        invoice_status="Unpaid"
    )
    db.add(po)
    
    # Update Procurement Request status
    req.status = "Ordered"
    db.commit()
    db.refresh(po)

    log_audit(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="Create Purchase Order",
        module="Purchase Orders",
        details=f"PO '{po.po_number}' created for Vendor '{vendor.name}' (Amount: ${po.amount})."
    )

    # Notify vendor contact if user exists
    vendor_users = db.query(User).filter(User.vendor_id == vendor.id).all()
    for vu in vendor_users:
        create_notification(
            db=db,
            user_id=vu.id,
            title="New Purchase Order Available",
            message=f"A new Purchase Order {po.po_number} has been drafted. Awaiting internal approval.",
            notification_type="Delivery"
        )

    # Notify finance officers
    fos = db.query(User).filter(User.role.in_(["Finance Officer", "Administrator"])).all()
    for fo in fos:
        create_notification(
            db=db,
            user_id=fo.id,
            title="PO Awaiting Approval",
            message=f"Purchase Order {po.po_number} is pending approval.",
            notification_type="Procurement"
        )

    return po

@router.put("/{po_id}", response_model=PurchaseOrderOut)
def update_purchase_order(
    po_id: int,
    po_in: PurchaseOrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(allowed_to_update)
):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    if po_in.amount is not None:
        po.amount = po_in.amount
    if po_in.expected_delivery_date is not None:
        po.expected_delivery_date = po_in.expected_delivery_date
    if po_in.actual_delivery_date is not None:
        po.actual_delivery_date = po_in.actual_delivery_date
    if po_in.invoice_status is not None:
        po.invoice_status = po_in.invoice_status

    db.commit()
    db.refresh(po)

    log_audit(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="Update Purchase Order",
        module="Purchase Orders",
        details=f"Updated details for PO '{po.po_number}'."
    )
    return po

@router.put("/{po_id}/status", response_model=PurchaseOrderOut)
def update_purchase_order_status(
    po_id: int,
    status_str: str,  # Approved, Ordered, Delivered, Completed, Cancelled
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    old_status = po.status
    
    # Verify RBAC rules based on transition
    if status_str in ["Approved", "Cancelled"]:
        if current_user.role not in ["Administrator", "Supply Chain Manager", "Finance Officer"]:
            raise HTTPException(status_code=403, detail="Not authorized to approve/cancel this PO")
    elif status_str == "Ordered":
        if current_user.role not in ["Administrator", "Procurement Manager", "Supply Chain Manager"]:
            raise HTTPException(status_code=403, detail="Not authorized to mark PO as ordered")
    elif status_str == "Delivered":
        # Can be done by Vendor or Supply Chain / Procurement
        if current_user.role == "Vendor" and po.vendor_id != current_user.vendor_id:
            raise HTTPException(status_code=403, detail="Not authorized for this vendor")
    elif status_str == "Completed":
        if current_user.role not in ["Administrator", "Finance Officer", "Procurement Manager"]:
            raise HTTPException(status_code=403, detail="Not authorized to complete PO")

    po.status = status_str
    
    # Business logic for specific states
    if status_str == "Delivered":
        po.actual_delivery_date = datetime.utcnow()
        # Create a default Vendor Performance log to be filled in detail
        existing_perf = db.query(VendorPerformance).filter(VendorPerformance.purchase_order_id == po.id).first()
        if not existing_perf:
            # Check delay
            delay_days = 0
            on_time = True
            if po.expected_delivery_date and po.actual_delivery_date:
                delay = (po.actual_delivery_date.date() - po.expected_delivery_date.date()).days
                if delay > 0:
                    delay_days = delay
                    on_time = False
                    
                    # Trigger delay alerts
                    scms = db.query(User).filter(User.role.in_(["Supply Chain Manager", "Administrator"])).all()
                    for scm in scms:
                        from ..services.email_service import send_delivery_delay_alert
                        send_delivery_delay_alert(scm.email, po.po_number, delay_days)
                        
                        from ..services.sms_service import send_sms_notification
                        if scm.phone:
                            send_sms_notification(scm.phone, f"VendorIQ Alert: PO {po.po_number} is delayed by {delay_days} days.")
            
            perf = VendorPerformance(
                vendor_id=po.vendor_id,
                purchase_order_id=po.id,
                delivery_on_time=on_time,
                delivery_delay_days=delay_days,
                quality_rating=90.0,
                communication_rating=90.0,
                compliance_rating=90.0,
                issue_resolution_rating=90.0,
                comments=f"Auto-generated log upon delivery status check.",
                logged_by_id=current_user.id
            )
            db.add(perf)
            
        # Update parent procurement request if exists
        req = db.query(ProcurementRequest).filter(ProcurementRequest.id == po.procurement_request_id).first()
        if req:
            req.status = "Delivered"

    elif status_str == "Completed":
        # Complete parent procurement request
        req = db.query(ProcurementRequest).filter(ProcurementRequest.id == po.procurement_request_id).first()
        if req:
            req.status = "Completed"

    db.commit()
    db.refresh(po)

    log_audit(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="Update PO Status",
        module="Purchase Orders",
        details=f"PO '{po.po_number}' changed from '{old_status}' to '{status_str}'."
    )

    # Notify appropriate users
    recipients = []
    if status_str == "Approved":
        # Notify vendor
        recipients = db.query(User).filter(User.vendor_id == po.vendor_id).all()
    else:
        # Notify procurement and supply chain
        recipients = db.query(User).filter(User.role.in_(["Procurement Manager", "Supply Chain Manager", "Administrator"])).all()

    for r in recipients:
        create_notification(
            db=db,
            user_id=r.id,
            title=f"PO Status Update: {po.po_number}",
            message=f"Purchase Order '{po.po_number}' has been updated to '{status_str}'.",
            notification_type="Delivery" if status_str in ["Ordered", "Delivered"] else "Procurement"
        )

    return po
