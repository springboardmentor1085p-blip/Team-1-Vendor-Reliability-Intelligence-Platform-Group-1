from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import VendorPerformance, User, Vendor
from ..schemas import VendorPerformanceOut, VendorPerformanceCreate
from ..utils.dependencies import get_current_user, RoleChecker
from ..utils.helpers import log_audit, create_notification
from .reliability import calculate_vendor_score_logic

router = APIRouter(prefix="/performance", tags=["Vendor Performance"])

allowed_to_log = RoleChecker(["Administrator", "Supply Chain Manager", "Procurement Manager"])

@router.get("/", response_model=List[VendorPerformanceOut])
def list_performances(
    vendor_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(VendorPerformance)
    
    # Vendor restriction
    if current_user.role == "Vendor":
        if not current_user.vendor_id:
            return []
        query = query.filter(VendorPerformance.vendor_id == current_user.vendor_id)
    elif vendor_id:
        query = query.filter(VendorPerformance.vendor_id == vendor_id)
        
    return query.all()

@router.get("/vendor/{vendor_id}", response_model=List[VendorPerformanceOut])
def get_vendor_performances(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Vendor restriction
    if current_user.role == "Vendor" and current_user.vendor_id != vendor_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return db.query(VendorPerformance).filter(VendorPerformance.vendor_id == vendor_id).all()

@router.post("/", response_model=VendorPerformanceOut, status_code=status.HTTP_201_CREATED)
def create_performance_log(
    perf_in: VendorPerformanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(allowed_to_log)
):
    vendor = db.query(Vendor).filter(Vendor.id == perf_in.vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    perf = VendorPerformance(
        vendor_id=perf_in.vendor_id,
        purchase_order_id=perf_in.purchase_order_id,
        delivery_on_time=perf_in.delivery_on_time,
        delivery_delay_days=perf_in.delivery_delay_days,
        quality_rating=perf_in.quality_rating,
        communication_rating=perf_in.communication_rating,
        compliance_rating=perf_in.compliance_rating,
        issue_resolution_rating=perf_in.issue_resolution_rating,
        comments=perf_in.comments,
        logged_by_id=current_user.id
    )
    db.add(perf)
    db.commit()
    db.refresh(perf)

    # Recalculate Vendor's reliability score immediately
    calculate_vendor_score_logic(vendor.id, db)

    log_audit(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="Log Vendor Performance",
        module="Performance",
        details=f"Logged performance record for Vendor '{vendor.name}'. Score recalculation triggered."
    )

    return perf

@router.put("/{perf_id}", response_model=VendorPerformanceOut)
def update_performance_log(
    perf_id: int,
    perf_in: VendorPerformanceCreate,  # Reuse create schema for full override/update
    db: Session = Depends(get_db),
    current_user: User = Depends(allowed_to_log)
):
    perf = db.query(VendorPerformance).filter(VendorPerformance.id == perf_id).first()
    if not perf:
        raise HTTPException(status_code=404, detail="Performance record not found")

    perf.delivery_on_time = perf_in.delivery_on_time
    perf.delivery_delay_days = perf_in.delivery_delay_days
    perf.quality_rating = perf_in.quality_rating
    perf.communication_rating = perf_in.communication_rating
    perf.compliance_rating = perf_in.compliance_rating
    perf.issue_resolution_rating = perf_in.issue_resolution_rating
    perf.comments = perf_in.comments
    
    db.commit()
    db.refresh(perf)

    # Recalculate Vendor's reliability score immediately
    calculate_vendor_score_logic(perf.vendor_id, db)

    log_audit(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="Update Vendor Performance",
        module="Performance",
        details=f"Updated performance record ID {perf.id} for Vendor ID {perf.vendor_id}."
    )

    return perf
