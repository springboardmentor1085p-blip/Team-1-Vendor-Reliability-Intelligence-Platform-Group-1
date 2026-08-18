from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import Vendor, VendorPerformance, ReliabilityScore, PurchaseOrder, Contract, User
from ..schemas import ReliabilityScoreOut, VendorOut
from ..utils.dependencies import get_current_user, RoleChecker
from ..utils.helpers import log_audit, create_notification

router = APIRouter(prefix="/reliability", tags=["Vendor Reliability & Risk"])

# Logic for calculating the vendor score. Exported to be triggered on performance log updates.
def calculate_vendor_score_logic(vendor_id: int, db: Session) -> ReliabilityScore:
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise ValueError("Vendor not found")

    performances = db.query(VendorPerformance).filter(VendorPerformance.vendor_id == vendor_id).all()
    completed_pos_count = db.query(PurchaseOrder).filter(
        PurchaseOrder.vendor_id == vendor_id,
        PurchaseOrder.status == "Completed"
    ).count()

    # Default values if no performance logs exist
    delivery_score = 100.0
    quality_score = 100.0
    communication_score = 100.0
    compliance_score = 100.0
    issue_resolution_score = 100.0
    
    total_logs = len(performances)
    on_time_count = 0
    
    if total_logs > 0:
        total_delivery = 0.0
        total_quality = 0.0
        total_communication = 0.0
        total_compliance = 0.0
        total_resolution = 0.0
        
        for p in performances:
            # Delivery scoring: 100 if on time, else deduct 10 points per delay day down to 0
            if p.delivery_on_time:
                on_time_count += 1
                total_delivery += 100.0
            else:
                total_delivery += max(0.0, 100.0 - (p.delivery_delay_days * 10))
            
            total_quality += p.quality_rating
            total_communication += p.communication_rating
            total_compliance += p.compliance_rating
            total_resolution += p.issue_resolution_rating

        delivery_score = total_delivery / total_logs
        quality_score = total_quality / total_logs
        communication_score = total_communication / total_logs
        compliance_score = total_compliance / total_logs
        issue_resolution_score = total_resolution / total_logs

    # Purchase History 10%: Base score on volume of completed POs
    # 0 POs -> 60 points, 1-3 POs -> 80 points, 4+ POs -> 100 points
    if completed_pos_count == 0:
        history_score = 60.0
    elif completed_pos_count <= 3:
        history_score = 80.0
    else:
        history_score = 100.0

    # Weighted calculation
    overall_score = (
        0.25 * delivery_score +
        0.20 * quality_score +
        0.15 * communication_score +
        0.15 * compliance_score +
        0.10 * history_score +
        0.15 * issue_resolution_score
    )

    # Round to 2 decimals
    overall_score = round(overall_score, 2)
    delivery_score = round(delivery_score, 2)
    quality_score = round(quality_score, 2)
    communication_score = round(communication_score, 2)
    compliance_score = round(compliance_score, 2)
    history_score = round(history_score, 2)
    issue_resolution_score = round(issue_resolution_score, 2)

    # Risk level classification
    if overall_score >= 80:
        risk_level = "LOW"
    elif overall_score >= 60:
        risk_level = "MEDIUM"
    elif overall_score >= 40:
        risk_level = "HIGH"
    else:
        risk_level = "CRITICAL"

    # Rule-based recommendations
    recommendations_list = []
    if overall_score >= 80:
        recommendations_list.append("Recommended supplier")
    elif overall_score >= 60:
        recommendations_list.append("Monitor performance closely")
    else:
        recommendations_list.append("Review risk profile before assigning orders")

    # Delivery performance trigger
    on_time_rate = (on_time_count / total_logs) if total_logs > 0 else 1.0
    if on_time_rate < 0.75:
        recommendations_list.append("Review delivery performance - high frequency of delays")

    # Expiring contract check
    today = date.today()
    expiring_contracts = db.query(Contract).filter(
        Contract.vendor_id == vendor_id,
        Contract.status == "Active"
    ).all()
    for c in expiring_contracts:
        days_left = (c.expiry_date - today).days
        if 0 <= days_left <= 30:
            recommendations_list.append(f"Renew expiring contract ({c.contract_number})")
            break

    recommendations = "; ".join(recommendations_list)

    # Create new score entry
    score_record = ReliabilityScore(
        vendor_id=vendor_id,
        overall_score=overall_score,
        delivery_score=delivery_score,
        quality_score=quality_score,
        communication_score=communication_score,
        compliance_score=compliance_score,
        history_score=history_score,
        issue_resolution_score=issue_resolution_score,
        risk_level=risk_level,
        recommendations=recommendations,
        calculated_at=datetime.utcnow()
    )
    db.add(score_record)
    
    # Update vendor model main fields
    vendor.reliability_score = overall_score
    vendor.risk_level = risk_level
    
    db.commit()
    db.refresh(score_record)
    db.refresh(vendor)

    # Trigger compliance notification if risk becomes HIGH or CRITICAL
    if risk_level in ["HIGH", "CRITICAL"]:
        scms = db.query(User).filter(User.role.in_(["Supply Chain Manager", "Administrator"])).all()
        for scm in scms:
            create_notification(
                db=db,
                user_id=scm.id,
                title=f"Critical Risk: {vendor.name}",
                message=f"Vendor '{vendor.name}' reliability dropped to {overall_score} ({risk_level} risk).",
                notification_type="Compliance"
            )
            # Trigger email alert
            from ..services.email_service import send_compliance_alert
            send_compliance_alert(scm.email, vendor.name, overall_score, risk_level)

            # Trigger SMS alert
            from ..services.sms_service import send_sms_notification
            if scm.phone:
                send_sms_notification(scm.phone, f"VendorIQ Alert: Vendor '{vendor.name}' score dropped to {overall_score:.1f}% ({risk_level} risk).")

    return score_record

@router.get("/vendor/{vendor_id}", response_model=List[ReliabilityScoreOut])
def get_vendor_reliability_history(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "Vendor" and current_user.vendor_id != vendor_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return db.query(ReliabilityScore).filter(ReliabilityScore.vendor_id == vendor_id).order_by(ReliabilityScore.calculated_at.desc()).all()

@router.post("/vendor/{vendor_id}/calculate", response_model=ReliabilityScoreOut)
def calculate_vendor_score(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        score = calculate_vendor_score_logic(vendor_id, db)
        log_audit(
            db=db,
            user_id=current_user.id,
            username=current_user.username,
            action="Calculate Reliability Score",
            module="Reliability",
            details=f"Recalculated score for Vendor ID {vendor_id}. New score: {score.overall_score}"
        )
        return score
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/ranking", response_model=List[VendorOut])
def get_vendor_ranking(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Vendor).filter(Vendor.status == "Active").order_by(Vendor.reliability_score.desc()).all()
