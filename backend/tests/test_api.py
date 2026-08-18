import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta

from app.main import app
from app.database import Base, get_db
from app.models import User, Vendor, VendorPerformance, ProcurementRequest, PurchaseOrder, Contract
from app.utils.security import get_password_hash
from app.routes.reliability import calculate_vendor_score_logic

# Setup a test SQLite database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override get_db dependency in app
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Create an admin user for authentication tests
    hashed_password = get_password_hash("password123")
    admin_user = User(
        username="admin_test",
        email="admin@test.com",
        hashed_password=hashed_password,
        role="Administrator",
        full_name="Admin Test User",
        is_active=True
    )
    db.add(admin_test := admin_user)
    
    # Create dummy vendor
    vendor = Vendor(
        name="Test Vendor 1",
        category="IT Vendor",
        status="Active",
        reliability_score=100.0,
        risk_level="LOW"
    )
    db.add(vendor)
    db.commit()
    db.refresh(admin_test)
    db.refresh(vendor)
    
    yield db
    
    Base.metadata.drop_all(bind=engine)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_user_registration():
    reg_data = {
        "username": "new_user",
        "email": "new@user.com",
        "password": "securepass123",
        "role": "Procurement Manager",
        "full_name": "New Procurement Manager"
    }
    response = client.post("/api/auth/register", json=reg_data)
    assert response.status_code == 201
    assert response.json()["username"] == "new_user"
    assert response.json()["role"] == "Procurement Manager"

def test_user_login():
    login_data = {
        "username": "admin_test",
        "password": "password123"
    }
    response = client.post("/api/auth/login", json=login_data)
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_unauthorized_access():
    response = client.get("/api/users/")
    # Direct access to user listings requires authentication headers
    assert response.status_code == 401

def test_reliability_scoring_logic(setup_db):
    db = setup_db
    vendor = db.query(Vendor).filter(Vendor.name == "Test Vendor 1").first()
    
    # Add a performance log: On-time delivery, ratings = 90
    perf = VendorPerformance(
        vendor_id=vendor.id,
        delivery_on_time=True,
        delivery_delay_days=0,
        quality_rating=90.0,
        communication_rating=90.0,
        compliance_rating=90.0,
        issue_resolution_rating=90.0,
        comments="Solid performance",
        logged_by_id=1
    )
    db.add(perf)
    db.commit()
    
    # Run calculation
    score_record = calculate_vendor_score_logic(vendor.id, db)
    
    # Math validation:
    # delivery_score = 100.0 (since delivery_on_time is True)
    # quality_score = 90.0
    # communication_score = 90.0
    # compliance_score = 90.0
    # history_score = 60.0 (0 completed POs matches the 60 points fallback)
    # issue_resolution_score = 90.0
    # Weighted score = 25% * 100 + 20% * 90 + 15% * 90 + 15% * 90 + 10% * 60 + 15% * 90
    # = 25.0 + 18.0 + 13.5 + 13.5 + 6.0 + 13.5 = 89.5
    
    assert score_record.overall_score == 89.5
    assert score_record.risk_level == "LOW"
    assert "Recommended supplier" in score_record.recommendations

def get_role_headers(username: str, role: str, db) -> dict:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        user = User(
            username=username,
            email=f"{username}@test.com",
            hashed_password=get_password_hash("password123"),
            role=role,
            full_name=f"{role} User",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    login_data = {"username": username, "password": "password123"}
    resp = client.post("/api/auth/login", json=login_data)
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_vendor_crud_and_rbac(setup_db):
    db = setup_db
    admin_headers = get_role_headers("admin_crud", "Administrator", db)
    vendor_headers = get_role_headers("vendor_crud", "Vendor", db)
    
    # 1. Create vendor (Admin should succeed)
    payload = {
        "name": "Apex Raw Materials",
        "category": "Raw Materials",
        "contact_person": "Apex Manager",
        "email": "apex@test.com",
        "phone": "1234567890",
        "address": "123 Apex St"
    }
    response = client.post("/api/vendors/", json=payload, headers=admin_headers)
    assert response.status_code == 201
    vendor_id = response.json()["id"]
    assert response.json()["name"] == "Apex Raw Materials"
    
    # 2. RBAC check (Vendor role should fail to create a vendor)
    bad_response = client.post("/api/vendors/", json=payload, headers=vendor_headers)
    assert bad_response.status_code == 403

    # 3. Read vendor details
    get_response = client.get(f"/api/vendors/{vendor_id}", headers=admin_headers)
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Apex Raw Materials"

def test_vendor_approval_workflow(setup_db):
    db = setup_db
    scm_headers = get_role_headers("scm_approval", "Supply Chain Manager", db)
    
    # Create a pending vendor
    v = Vendor(
        name="Pending Supply Corp",
        category="Logistics",
        status="Pending Approval",
        reliability_score=100.0,
        risk_level="LOW"
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    
    # Approve vendor
    resp = client.put(
        f"/api/vendors/{v.id}/status?status_str=Active",
        headers=scm_headers
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "Active"

def test_procurement_request_workflow(setup_db):
    db = setup_db
    proc_headers = get_role_headers("proc_manager", "Procurement Manager", db)
    scm_headers = get_role_headers("scm_proc", "Supply Chain Manager", db)
    
    # Get active vendor
    v = db.query(Vendor).first()
    
    # 1. Create Requisition (Procurement Manager)
    payload = {
        "title": "Raw Copper Requisition",
        "description": "50 tons of raw copper",
        "priority": "High",
        "estimated_cost": 50000.0,
        "vendor_id": v.id
    }
    resp = client.post("/api/procurement/", json=payload, headers=proc_headers)
    assert resp.status_code == 201
    req_id = resp.json()["id"]
    assert resp.json()["status"] == "Pending"
    
    # 2. Approve Requisition (SCM)
    app_resp = client.put(
        f"/api/procurement/{req_id}/status?status_str=Approved",
        headers=scm_headers
    )
    assert app_resp.status_code == 200
    assert app_resp.json()["status"] == "Approved"

def test_purchase_order_creation(setup_db):
    db = setup_db
    proc_headers = get_role_headers("proc_po", "Procurement Manager", db)
    scm_headers = get_role_headers("scm_po", "Supply Chain Manager", db)
    
    # Create approved procurement request
    v = db.query(Vendor).first()
    req = ProcurementRequest(
        title="Seeded Request",
        description="Seeded desc",
        priority="Medium",
        estimated_cost=25000.0,
        status="Approved",
        vendor_id=v.id,
        requested_by_id=1
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    
    # Create PO (initially goes to Pending Approval status)
    payload = {
        "procurement_request_id": req.id,
        "vendor_id": v.id,
        "amount": 24500.0,
        "expected_delivery_date": (datetime.utcnow() + timedelta(days=10)).isoformat()
    }
    resp = client.post("/api/purchase-orders/", json=payload, headers=proc_headers)
    assert resp.status_code == 201
    po_id = resp.json()["id"]
    assert resp.json()["status"] == "Pending Approval"
    assert resp.json()["po_number"].startswith("PO-")
    
    # 1. Approve PO (SCM)
    app_resp = client.put(
        f"/api/purchase-orders/{po_id}/status?status_str=Approved",
        headers=scm_headers
    )
    assert app_resp.status_code == 200
    assert app_resp.json()["status"] == "Approved"

    # 2. Mark PO as Completed (SCM/Procurement)
    comp_resp = client.put(
        f"/api/purchase-orders/{po_id}/status?status_str=Completed",
        headers=proc_headers
    )
    assert comp_resp.status_code == 200
    assert comp_resp.json()["status"] == "Completed"

    # 3. Update Invoice Status to Paid (Finance Officer)
    fin_headers = get_role_headers("finance_po", "Finance Officer", db)
    update_resp = client.put(
        f"/api/purchase-orders/{po_id}",
        json={"invoice_status": "Paid", "actual_delivery_date": datetime.utcnow().isoformat()},
        headers=fin_headers
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["invoice_status"] == "Paid"

def test_contracts_endpoint(setup_db):
    db = setup_db
    scm_headers = get_role_headers("scm_contract", "Supply Chain Manager", db)
    v = db.query(Vendor).first()
    
    # Create contract
    payload = {
        "contract_number": "CON-TEST-100",
        "vendor_id": v.id,
        "title": "Logistics SLA Agreement",
        "value": 120000.0,
        "start_date": datetime.utcnow().date().isoformat(),
        "expiry_date": (datetime.utcnow() + timedelta(days=365)).date().isoformat(),
        "compliance_status": "Compliant",
        "certification_details": "ISO 9001 Compliant"
    }
    resp = client.post("/api/contracts/", json=payload, headers=scm_headers)
    assert resp.status_code == 201
    assert resp.json()["contract_number"] == "CON-TEST-100"
    
    # List contracts
    list_resp = client.get("/api/contracts/", headers=scm_headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) > 0

def test_reliability_calculation_endpoint(setup_db):
    db = setup_db
    admin_headers = get_role_headers("admin_rel", "Administrator", db)
    v = db.query(Vendor).first()
    
    # Trigger score calculation
    resp = client.post(f"/api/reliability/vendor/{v.id}/calculate", headers=admin_headers)
    assert resp.status_code == 200
    assert "overall_score" in resp.json()

def test_dashboard_kpis_endpoint(setup_db):
    db = setup_db
    auditor_headers = get_role_headers("auditor_dash", "Auditor", db)
    
    resp = client.get("/api/dashboard/kpis", headers=auditor_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_vendors" in data
    assert "procurement_value" in data
    assert "pending_approvals" in data

def test_password_reset_flow(setup_db):
    db = setup_db
    
    # 1. Forgot password with non-existent email
    resp = client.post("/api/auth/forgot-password", json={"email": "nonexistent@test.com"})
    assert resp.status_code == 200
    assert "link has been generated" in resp.json()["message"]
    
    # 2. Seed user
    u = User(
        username="reset_me",
        email="reset_me@test.com",
        hashed_password=get_password_hash("oldpassword123"),
        role="Auditor",
        full_name="Reset User",
        is_active=True
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    
    # 3. Simulate forgot-password call
    resp = client.post("/api/auth/forgot-password", json={"email": "reset_me@test.com"})
    assert resp.status_code == 200
    
    # 4. Fetch hashed token from DB and execute reset using a simulated token
    import hashlib
    import secrets
    token = "simulated_plain_token_12345"
    hashed = hashlib.sha256(token.encode()).hexdigest()
    
    # Manually configure token in DB for testing verification
    u.reset_token = hashed
    u.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
    db.commit()
    
    # 5. Fail validation if password is too short
    fail_resp = client.post("/api/auth/reset-password", json={"token": token, "new_password": "123"})
    assert fail_resp.status_code == 400
    assert "at least 6 characters" in fail_resp.json()["detail"]
    
    # 6. Reset password successfully
    success_resp = client.post("/api/auth/reset-password", json={"token": token, "new_password": "newpassword123"})
    assert success_resp.status_code == 200
    assert "successfully" in success_resp.json()["message"]
    
    # 7. Check token was invalidated
    db.refresh(u)
    assert u.reset_token is None
    assert u.reset_token_expiry is None
    
    # 8. Try log in with new password
    login_resp = client.post("/api/auth/login", json={"username": "reset_me", "password": "newpassword123"})
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()

def test_email_sms_notifications_fallback(setup_db):
    db = setup_db
    from app.services.email_service import send_email
    from app.services.sms_service import send_sms_notification
    
    # When not configured, email returns False gracefully
    assert send_email("test@email.com", "Subject", "<p>Hello</p>") is False
    # Mock SMS provider logs and returns True
    assert send_sms_notification("1234567890", "Hello Test") is True

def test_file_sharing_upload_and_download(setup_db):
    db = setup_db
    
    u1 = User(
        username="uploader",
        email="uploader@test.com",
        hashed_password=get_password_hash("password123"),
        role="Supply Chain Manager",
        full_name="Uploader User",
        is_active=True
    )
    u2 = User(
        username="receiver",
        email="receiver@test.com",
        hashed_password=get_password_hash("password123"),
        role="Vendor",
        full_name="Receiver User",
        is_active=True
    )
    db.add(u1)
    db.add(u2)
    db.commit()
    
    login_resp = client.post("/api/auth/login", json={"username": "uploader", "password": "password123"})
    token_scm = login_resp.json()["access_token"]
    headers_scm = {"Authorization": f"Bearer {token_scm}"}
    
    login_resp2 = client.post("/api/auth/login", json={"username": "receiver", "password": "password123"})
    token_vendor = login_resp2.json()["access_token"]
    headers_vendor = {"Authorization": f"Bearer {token_vendor}"}
    
    # 1. Invalid extension
    files = {"file": ("test.exe", b"executable content", "application/octet-stream")}
    resp = client.post("/api/communications/upload-file", files=files, headers=headers_scm)
    assert resp.status_code == 400
    assert "not allowed" in resp.json()["detail"]
    
    # 2. Oversized file (simulate 0 MB max limit)
    from app.config import settings
    old_max = settings.MAX_UPLOAD_SIZE_MB
    settings.MAX_UPLOAD_SIZE_MB = 0
    
    files = {"file": ("test.pdf", b"pdf content", "application/pdf")}
    resp = client.post("/api/communications/upload-file", files=files, headers=headers_scm)
    assert resp.status_code == 400
    assert "exceeds maximum limit" in resp.json()["detail"]
    
    settings.MAX_UPLOAD_SIZE_MB = old_max
    
    # 3. Valid upload
    files = {"file": ("document.pdf", b"pdf file contents dummy data", "application/pdf")}
    resp = client.post("/api/communications/upload-file", files=files, headers=headers_scm)
    assert resp.status_code == 200
    upload_data = resp.json()
    assert upload_data["attachment_name"] == "document.pdf"
    assert "attachment_path" in upload_data
    
    # 4. Create communication message with attachment
    msg_payload = {
        "recipient_id": u2.id,
        "subject": "Delivery SLA Document",
        "message": "Please review the attached PDF file.",
        "attachment_name": upload_data["attachment_name"],
        "attachment_path": upload_data["attachment_path"],
        "attachment_size": upload_data["attachment_size"],
        "attachment_type": upload_data["attachment_type"]
    }
    msg_resp = client.post("/api/communications/", json=msg_payload, headers=headers_scm)
    assert msg_resp.status_code == 201
    msg_data = msg_resp.json()
    assert msg_data["attachment_name"] == "document.pdf"
    msg_id = msg_data["id"]
    
    # 5. Authorized download
    down_resp = client.get(f"/api/communications/{msg_id}/download", headers=headers_vendor)
    assert down_resp.status_code == 200
    assert down_resp.content == b"pdf file contents dummy data"
    
    # 6. Unauthorized download
    u3 = User(
        username="intruder",
        email="intruder@test.com",
        hashed_password=get_password_hash("password123"),
        role="Vendor",
        full_name="Intruder User",
        is_active=True
    )
    db.add(u3)
    db.commit()
    
    login_resp3 = client.post("/api/auth/login", json={"username": "intruder", "password": "password123"})
    headers_intruder = {"Authorization": f"Bearer {login_resp3.json()['access_token']}"}
    
    block_resp = client.get(f"/api/communications/{msg_id}/download", headers=headers_intruder)
    assert block_resp.status_code == 403


def test_avatar_uploads_and_validation():
    db = TestingSessionLocal()
    # 1. Login as Admin
    login_resp = client.post("/api/auth/login", json={"username": "admin_test", "password": "password123"})
    admin_token = login_resp.json()["access_token"]
    headers_admin = {"Authorization": f"Bearer {admin_token}"}

    # 2. Login as regular user (non-admin) to test unauthorized upload
    pm_user = User(
        username="pm_user_test",
        email="pm@test.com",
        hashed_password=get_password_hash("password123"),
        role="Procurement Manager",
        full_name="PM Test User",
        is_active=True
    )
    db.add(pm_user)
    db.commit()

    login_resp_pm = client.post("/api/auth/login", json={"username": "pm_user_test", "password": "password123"})
    pm_token = login_resp_pm.json()["access_token"]
    headers_pm = {"Authorization": f"Bearer {pm_token}"}

    # 3. Unauthorized upload (non-admin attempting to upload an avatar)
    files = {"file": ("avatar.png", b"dummy image binary data", "image/png")}
    resp = client.post("/api/users/upload-avatar", files=files, headers=headers_pm)
    assert resp.status_code == 403

    # 4. Invalid file type upload (Admin uploading text/pdf file)
    files = {"file": ("avatar.txt", b"plain text payload data", "text/plain")}
    resp = client.post("/api/users/upload-avatar", files=files, headers=headers_admin)
    assert resp.status_code == 400
    assert "Unsupported file type" in resp.json()["detail"]

    # 5. Invalid MIME content type (Admin uploading PNG name but application/pdf MIME type)
    files = {"file": ("avatar.png", b"binary data content", "application/pdf")}
    resp = client.post("/api/users/upload-avatar", files=files, headers=headers_admin)
    assert resp.status_code == 400
    assert "Invalid image format content" in resp.json()["detail"]

    # 6. Oversized file upload (Admin uploading image > 2MB)
    huge_data = b"a" * (2 * 1024 * 1024 + 100)
    files = {"file": ("big_avatar.jpg", huge_data, "image/jpeg")}
    resp = client.post("/api/users/upload-avatar", files=files, headers=headers_admin)
    assert resp.status_code == 400
    assert "exceeds the 2MB limit" in resp.json()["detail"]

    # 7. Valid avatar upload (Admin uploading valid PNG image)
    files = {"file": ("profile.png", b"fake png data binary contents", "image/png")}
    resp = client.post("/api/users/upload-avatar", files=files, headers=headers_admin)
    assert resp.status_code == 200
    res_data = resp.json()
    assert "avatar_url" in res_data
    avatar_url = res_data["avatar_url"]
    assert avatar_url.startswith("/uploads/avatars/")

    # 8. Create user with the avatar URL and test persistence
    create_payload = {
        "username": "avatar_guy",
        "email": "avatar@guy.com",
        "password": "password123",
        "role": "Finance Officer",
        "full_name": "Avatar Guy",
        "avatar_url": avatar_url
    }
    create_resp = client.post("/api/users/", json=create_payload, headers=headers_admin)
    assert create_resp.status_code == 201
    user_data = create_resp.json()
    assert user_data["avatar_url"] == avatar_url

    # Check database persistence
    db_user = db.query(User).filter(User.username == "avatar_guy").first()
    assert db_user is not None
    assert db_user.avatar_url == avatar_url
    db.close()


def test_self_service_avatar_uploads_and_validation():
    db = TestingSessionLocal()
    # 1. Register a regular user
    pm_user = User(
        username="self_avatar_pm",
        email="self_pm@test.com",
        hashed_password=get_password_hash("password123"),
        role="Procurement Manager",
        full_name="Self PM User",
        is_active=True
    )
    db.add(pm_user)
    db.commit()

    # 2. Login as regular user
    login_resp = client.post("/api/auth/login", json={"username": "self_avatar_pm", "password": "password123"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Test invalid extension
    files = {"file": ("avatar.txt", b"plain text", "text/plain")}
    resp = client.post("/api/auth/me/avatar", files=files, headers=headers)
    assert resp.status_code == 400
    assert "Unsupported file type" in resp.json()["detail"]

    # 4. Test invalid MIME
    files = {"file": ("avatar.png", b"plain text", "application/pdf")}
    resp = client.post("/api/auth/me/avatar", files=files, headers=headers)
    assert resp.status_code == 400
    assert "Invalid image format content" in resp.json()["detail"]

    # 5. Test oversized upload
    huge_data = b"a" * (2 * 1024 * 1024 + 100)
    files = {"file": ("avatar.jpg", huge_data, "image/jpeg")}
    resp = client.post("/api/auth/me/avatar", files=files, headers=headers)
    assert resp.status_code == 400
    assert "exceeds the 2MB limit" in resp.json()["detail"]

    # 6. Valid self-service upload
    files = {"file": ("myphoto.png", b"dummy png content bytes data", "image/png")}
    resp = client.post("/api/auth/me/avatar", files=files, headers=headers)
    assert resp.status_code == 200
    user_data = resp.json()
    assert "avatar_url" in user_data
    avatar_url = user_data["avatar_url"]
    assert avatar_url.startswith("/uploads/avatars/")

    # Check persistence
    db.refresh(pm_user)
    assert pm_user.avatar_url == avatar_url

    # 7. Valid self-service remove/delete
    resp = client.delete("/api/auth/me/avatar", headers=headers)
    assert resp.status_code == 200
    user_data_deleted = resp.json()
    assert user_data_deleted["avatar_url"] is None

    # Check persistence
    db.refresh(pm_user)
    assert pm_user.avatar_url is None

    db.close()




