from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import Contract, User, Vendor
from ..schemas import ContractOut, ContractCreate, ContractUpdate
from ..utils.dependencies import get_current_user, RoleChecker
from ..utils.helpers import log_audit, create_notification

router = APIRouter(prefix="/contracts", tags=["Contracts & Compliance"])

allowed_to_modify = RoleChecker(["Administrator", "Supply Chain Manager", "Procurement Manager"])

def verify_and_update_contract_statuses(db: Session):
    """
    Scans active/expiring contracts and updates their status dynamically.
    Sends notification warnings to alert stakeholders of contract expirations.
    """
    today = date.today()
    contracts = db.query(Contract).filter(Contract.status.in_(["Active", "Expiring Soon"])).all()
    
    status_updated = False
    for c in contracts:
        days_left = (c.expiry_date - today).days
        new_status = c.status
        
        if days_left < 0:
            new_status = "Expired"
        elif days_left <= 30:
            new_status = "Expiring Soon"
            
        if new_status != c.status:
            c.status = new_status
            status_updated = True
            
            # Send warning notification
            scms = db.query(User).filter(User.role.in_(["Supply Chain Manager", "Administrator"])).all()
            for scm in scms:
                create_notification(
                    db=db,
                    user_id=scm.id,
                    title=f"Contract Status Alert: {c.contract_number}",
                    message=f"Contract '{c.title}' for Vendor ID {c.vendor_id} is now '{new_status}'. Expiry Date: {c.expiry_date}",
                    notification_type="Contract Expiry"
                )
                # Trigger email alert
                from ..services.email_service import send_contract_expiry_alert
                send_contract_expiry_alert(scm.email, c.contract_number, c.title, days_left)

                # Trigger SMS alert
                from ..services.sms_service import send_sms_notification
                if scm.phone:
                    send_sms_notification(scm.phone, f"VendorIQ Alert: Contract {c.contract_number} is {new_status} ({days_left} days left).")
    
    if status_updated:
        db.commit()

@router.get("/", response_model=List[ContractOut])
def list_contracts(
    status: Optional[str] = None,
    vendor_id: Optional[int] = None,
    compliance_status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Perform status maintenance scan
    verify_and_update_contract_statuses(db)
    
    query = db.query(Contract)
    
    # Vendor restriction
    if current_user.role == "Vendor":
        if not current_user.vendor_id:
            return []
        query = query.filter(Contract.vendor_id == current_user.vendor_id)
        
    if status:
        query = query.filter(Contract.status == status)
    if vendor_id:
        query = query.filter(Contract.vendor_id == vendor_id)
    if compliance_status:
        query = query.filter(Contract.compliance_status == compliance_status)
        
    return query.all()

@router.get("/{contract_id}", response_model=ContractOut)
def get_contract(contract_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
        
    if current_user.role == "Vendor" and contract.vendor_id != current_user.vendor_id:
        raise HTTPException(status_code=403, detail="Access denied")
        
    return contract

@router.post("/", response_model=ContractOut, status_code=status.HTTP_201_CREATED)
def create_contract(
    contract_in: ContractCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(allowed_to_modify)
):
    # Verify vendor
    vendor = db.query(Vendor).filter(Vendor.id == contract_in.vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    # Check duplicate contract number
    if db.query(Contract).filter(Contract.contract_number == contract_in.contract_number).first():
        raise HTTPException(status_code=400, detail="Contract number already exists")

    # Determine status
    today = date.today()
    days_left = (contract_in.expiry_date - today).days
    status_str = "Active"
    if days_left < 0:
        status_str = "Expired"
    elif days_left <= 30:
        status_str = "Expiring Soon"

    contract = Contract(
        contract_number=contract_in.contract_number,
        vendor_id=contract_in.vendor_id,
        title=contract_in.title,
        value=contract_in.value,
        start_date=contract_in.start_date,
        expiry_date=contract_in.expiry_date,
        status=status_str,
        compliance_status=contract_in.compliance_status,
        certification_details=contract_in.certification_details
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)

    log_audit(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="Create Contract",
        module="Contracts",
        details=f"Contract '{contract.contract_number}' created for Vendor '{vendor.name}' (Value: ${contract.value})."
    )

    return contract

@router.put("/{contract_id}", response_model=ContractOut)
def update_contract(
    contract_id: int,
    contract_in: ContractUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(allowed_to_modify)
):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    if contract_in.title is not None:
        contract.title = contract_in.title
    if contract_in.value is not None:
        contract.value = contract_in.value
    if contract_in.start_date is not None:
        contract.start_date = contract_in.start_date
    if contract_in.expiry_date is not None:
        contract.expiry_date = contract_in.expiry_date
    if contract_in.status is not None:
        contract.status = contract_in.status
    if contract_in.compliance_status is not None:
        contract.compliance_status = contract_in.compliance_status
    if contract_in.certification_details is not None:
        contract.certification_details = contract_in.certification_details

    # Recalculate status dynamically based on dates if updated
    if contract_in.expiry_date or contract_in.start_date:
        today = date.today()
        days_left = (contract.expiry_date - today).days
        if days_left < 0:
            contract.status = "Expired"
        elif days_left <= 30:
            contract.status = "Expiring Soon"
        else:
            contract.status = "Active"

    db.commit()
    db.refresh(contract)

    log_audit(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="Update Contract",
        module="Contracts",
        details=f"Updated details for Contract '{contract.contract_number}'."
    )

    return contract
