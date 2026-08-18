from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

# User Schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    role: str
    phone: Optional[str] = None
    avatar_url: Optional[str] = None

class UserCreate(UserBase):
    password: str
    vendor_id: Optional[int] = None
    vendor_name: Optional[str] = None

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None
    vendor_id: Optional[int] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None

class UserOut(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    vendor_id: Optional[int] = None

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str

# Vendor Schemas
class VendorBase(BaseModel):
    name: str
    category: str
    address: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

class VendorCreate(VendorBase):
    pass

class VendorUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    address: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

class VendorOut(VendorBase):
    id: int
    status: str
    reliability_score: float
    risk_level: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Procurement Schemas
class ProcurementRequestBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "Medium"
    estimated_cost: float
    vendor_id: Optional[int] = None

class ProcurementRequestCreate(ProcurementRequestBase):
    pass

class ProcurementRequestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    estimated_cost: Optional[float] = None
    status: Optional[str] = None
    vendor_id: Optional[int] = None
    approved_by_id: Optional[int] = None

class ProcurementRequestOut(ProcurementRequestBase):
    id: int
    status: str
    requested_by_id: int
    approved_by_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    requested_by: UserOut
    approved_by: Optional[UserOut] = None
    vendor: Optional[VendorOut] = None

    class Config:
        from_attributes = True

# Purchase Order Schemas
class PurchaseOrderBase(BaseModel):
    procurement_request_id: int
    vendor_id: int
    amount: float
    expected_delivery_date: datetime

class PurchaseOrderCreate(PurchaseOrderBase):
    pass

class PurchaseOrderUpdate(BaseModel):
    amount: Optional[float] = None
    status: Optional[str] = None
    expected_delivery_date: Optional[datetime] = None
    actual_delivery_date: Optional[datetime] = None
    invoice_status: Optional[str] = None

class PurchaseOrderOut(PurchaseOrderBase):
    id: int
    po_number: str
    status: str
    order_date: datetime
    actual_delivery_date: Optional[datetime] = None
    invoice_status: str
    created_at: datetime
    updated_at: datetime
    vendor: VendorOut

    class Config:
        from_attributes = True

# Vendor Performance Schemas
class VendorPerformanceBase(BaseModel):
    vendor_id: int
    purchase_order_id: Optional[int] = None
    delivery_on_time: bool = True
    delivery_delay_days: int = 0
    quality_rating: float = Field(default=100.0, ge=0, le=100)
    communication_rating: float = Field(default=100.0, ge=0, le=100)
    compliance_rating: float = Field(default=100.0, ge=0, le=100)
    issue_resolution_rating: float = Field(default=100.0, ge=0, le=100)
    comments: Optional[str] = None

class VendorPerformanceCreate(VendorPerformanceBase):
    pass

class VendorPerformanceOut(VendorPerformanceBase):
    id: int
    logged_by_id: Optional[int] = None
    created_at: datetime
    logged_by: Optional[UserOut] = None
    vendor: Optional[VendorOut] = None

    class Config:
        from_attributes = True

# Reliability Score Schemas
class ReliabilityScoreOut(BaseModel):
    id: int
    vendor_id: int
    overall_score: float
    delivery_score: float
    quality_score: float
    communication_score: float
    compliance_score: float
    history_score: float
    issue_resolution_score: float
    risk_level: str
    recommendations: Optional[str] = None
    calculated_at: datetime

    class Config:
        from_attributes = True

# Contract Schemas
class ContractBase(BaseModel):
    contract_number: str
    vendor_id: int
    title: str
    value: float
    start_date: date
    expiry_date: date
    compliance_status: str = "Compliant"
    certification_details: Optional[str] = None

class ContractCreate(ContractBase):
    pass

class ContractUpdate(BaseModel):
    title: Optional[str] = None
    value: Optional[float] = None
    start_date: Optional[date] = None
    expiry_date: Optional[date] = None
    status: Optional[str] = None
    compliance_status: Optional[str] = None
    certification_details: Optional[str] = None

class ContractOut(ContractBase):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    vendor: VendorOut

    class Config:
        from_attributes = True

# Communication Schemas
class CommunicationBase(BaseModel):
    recipient_id: Optional[int] = None
    vendor_id: Optional[int] = None
    subject: str
    message: str

class CommunicationCreate(CommunicationBase):
    attachment_name: Optional[str] = None
    attachment_path: Optional[str] = None
    attachment_size: Optional[int] = None
    attachment_type: Optional[str] = None

class CommunicationOut(CommunicationBase):
    id: int
    sender_id: int
    is_read: bool
    created_at: datetime
    sender: UserOut
    recipient: Optional[UserOut] = None
    attachment_name: Optional[str] = None
    attachment_path: Optional[str] = None
    attachment_size: Optional[int] = None
    attachment_type: Optional[str] = None

    class Config:
        from_attributes = True

# Notification Schemas
class NotificationBase(BaseModel):
    title: str
    message: str
    type: str

class NotificationOut(NotificationBase):
    id: int
    user_id: int
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Audit Log Schemas
class AuditLogOut(BaseModel):
    id: int
    user_id: Optional[int] = None
    username: Optional[str] = None
    action: str
    module: str
    details: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Dashboard Stats Schemas
class DashboardKPIs(BaseModel):
    total_vendors: int
    active_vendors: int
    pending_approvals: int
    active_pos: int
    procurement_value: float
    average_reliability: float
    high_risk_vendors: int
    expiring_contracts: int

class DashboardChartData(BaseModel):
    spending_by_month: List[dict]
    po_status_counts: List[dict]
    vendor_reliability_distribution: List[dict]
    risk_distribution: List[dict]
    delivery_performance: List[dict]
    performance_trends: List[dict]
    recent_activities: Optional[List[dict]] = None
    risk_actions: Optional[List[dict]] = None

# Password Reset Schemas
class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordConfirm(BaseModel):
    token: str
    new_password: str

