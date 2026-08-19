from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)  # Administrator, Procurement Manager, Supply Chain Manager, Vendor, Finance Officer, Auditor
    full_name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    vendor_id = Column(Integer, ForeignKey("vendors.id", ondelete="SET NULL"), nullable=True)
    reset_token = Column(String, nullable=True)
    reset_token_expiry = Column(DateTime, nullable=True)
    phone = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)

    # Relationships
    vendor = relationship("Vendor", back_populates="users")
    procurement_requests_created = relationship("ProcurementRequest", foreign_keys="[ProcurementRequest.requested_by_id]", back_populates="requested_by")
    procurement_requests_approved = relationship("ProcurementRequest", foreign_keys="[ProcurementRequest.approved_by_id]", back_populates="approved_by")
    audit_logs = relationship("AuditLog", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    sent_communications = relationship("Communication", foreign_keys="[Communication.sender_id]", back_populates="sender")
    received_communications = relationship("Communication", foreign_keys="[Communication.recipient_id]", back_populates="recipient")


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    category = Column(String, nullable=False)  # Raw Material Supplier, Equipment Vendor, IT Vendor, etc.
    status = Column(String, default="Pending Approval")  # Pending Approval, Active, Inactive, Rejected
    address = Column(String, nullable=True)
    contact_person = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    reliability_score = Column(Float, default=100.0)
    risk_level = Column(String, default="LOW")  # LOW, MEDIUM, HIGH, CRITICAL
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    users = relationship("User", back_populates="vendor")
    procurement_requests = relationship("ProcurementRequest", back_populates="vendor")
    purchase_orders = relationship("PurchaseOrder", back_populates="vendor")
    performances = relationship("VendorPerformance", back_populates="vendor")
    reliability_scores = relationship("ReliabilityScore", back_populates="vendor")
    contracts = relationship("Contract", back_populates="vendor")
    communications = relationship("Communication", back_populates="vendor")


class ProcurementRequest(Base):
    __tablename__ = "procurement_requests"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(String, default="Medium")  # Low, Medium, High, Critical
    status = Column(String, default="Pending")  # Pending, Approved, Rejected, Cancelled, Ordered, Delivered, Completed
    estimated_cost = Column(Float, nullable=False)
    requested_by_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    approved_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    requested_by = relationship("User", foreign_keys=[requested_by_id], back_populates="procurement_requests_created")
    approved_by = relationship("User", foreign_keys=[approved_by_id], back_populates="procurement_requests_approved")
    vendor = relationship("Vendor", back_populates="procurement_requests")
    purchase_orders = relationship("PurchaseOrder", back_populates="procurement_request")


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    po_number = Column(String, unique=True, index=True, nullable=False)
    procurement_request_id = Column(Integer, ForeignKey("procurement_requests.id", ondelete="CASCADE"), nullable=False)
    vendor_id = Column(Integer, ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String, default="Pending Approval")  # Pending Approval, Approved, Ordered, Delivered, Completed, Cancelled
    order_date = Column(DateTime, default=datetime.utcnow)
    expected_delivery_date = Column(DateTime, nullable=False)
    actual_delivery_date = Column(DateTime, nullable=True)
    invoice_status = Column(String, default="Unpaid")  # Unpaid, Paid, Invoiced
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    procurement_request = relationship("ProcurementRequest", back_populates="purchase_orders")
    vendor = relationship("Vendor", back_populates="purchase_orders")
    performances = relationship("VendorPerformance", back_populates="purchase_order")


class VendorPerformance(Base):
    __tablename__ = "vendor_performances"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id", ondelete="SET NULL"), nullable=True)
    delivery_on_time = Column(Boolean, default=True)
    delivery_delay_days = Column(Integer, default=0)
    quality_rating = Column(Float, default=100.0)  # 0 to 100
    communication_rating = Column(Float, default=100.0)  # 0 to 100
    compliance_rating = Column(Float, default=100.0)  # 0 to 100
    issue_resolution_rating = Column(Float, default=100.0)  # 0 to 100
    comments = Column(Text, nullable=True)
    logged_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    vendor = relationship("Vendor", back_populates="performances")
    purchase_order = relationship("PurchaseOrder", back_populates="performances")
    logged_by = relationship("User")


class ReliabilityScore(Base):
    __tablename__ = "reliability_scores"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False)
    overall_score = Column(Float, nullable=False)
    delivery_score = Column(Float, nullable=False)
    quality_score = Column(Float, nullable=False)
    communication_score = Column(Float, nullable=False)
    compliance_score = Column(Float, nullable=False)
    history_score = Column(Float, nullable=False)
    issue_resolution_score = Column(Float, nullable=False)
    risk_level = Column(String, nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    recommendations = Column(Text, nullable=True)
    calculated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    vendor = relationship("Vendor", back_populates="reliability_scores")


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    contract_number = Column(String, unique=True, index=True, nullable=False)
    vendor_id = Column(Integer, ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    start_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=False)
    status = Column(String, default="Active")  # Active, Expiring Soon, Expired, Renewed, Terminated
    compliance_status = Column(String, default="Compliant")  # Compliant, Non-Compliant, Under Review
    certification_details = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    vendor = relationship("Vendor", back_populates="contracts")


class Communication(Base):
    __tablename__ = "communications"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id", ondelete="SET NULL"), nullable=True)
    subject = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    attachment_name = Column(String, nullable=True)
    attachment_path = Column(String, nullable=True)
    attachment_size = Column(Integer, nullable=True)
    attachment_type = Column(String, nullable=True)

    # Relationships
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_communications")
    recipient = relationship("User", foreign_keys=[recipient_id], back_populates="received_communications")
    vendor = relationship("Vendor", back_populates="communications")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String, nullable=False)  # Procurement, Delivery, Vendor Approval, Contract Expiry, Compliance, Communication
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="notifications")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    username = Column(String, nullable=True)
    action = Column(String, nullable=False)
    module = Column(String, nullable=False)
    details = Column(Text, nullable=True)
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="audit_logs")
