from datetime import datetime, date, timedelta
import sys
from sqlalchemy.orm import Session
from .database import SessionLocal, Base, engine
from .models import User, Vendor, ProcurementRequest, PurchaseOrder, VendorPerformance, ReliabilityScore, Contract, Communication, Notification, AuditLog
from .utils.security import get_password_hash

def seed_db(db: Session, clear_existing: bool = False, repair_demo: bool = False):
    if clear_existing:
        print("Clearing database tables...")
        db.query(AuditLog).delete()
        db.query(Notification).delete()
        db.query(Communication).delete()
        db.query(Contract).delete()
        db.query(ReliabilityScore).delete()
        db.query(VendorPerformance).delete()
        db.query(PurchaseOrder).delete()
        db.query(ProcurementRequest).delete()
        db.query(User).delete()
        db.query(Vendor).delete()
        db.commit()
    else:
        print("Running in safe seeding mode (no tables cleared).")

    print("Seeding vendors...")
    vendors_data = [
        {"name": "Apex Raw Materials", "category": "Raw Material Supplier", "status": "Active", "address": "123 Steel Rd, Pittsburgh, PA", "contact_person": "John Doe", "email": "john@apexmaterials.com", "phone": "123-456-7890"},
        {"name": "Titan Heavy Equipment", "category": "Equipment Vendor", "status": "Active", "address": "456 Industrial Blvd, Chicago, IL", "contact_person": "Jane Smith", "email": "jane@titanequip.com", "phone": "234-567-8901"},
        {"name": "IT Solutions Group", "category": "IT Vendor", "status": "Active", "address": "789 Tech Park, San Jose, CA", "contact_person": "Robert Johnson", "email": "robert@itsolutions.com", "phone": "345-678-9012"},
        {"name": "Logistics Express", "category": "Logistics Partner", "status": "Active", "address": "101 Transport Way, Atlanta, GA", "contact_person": "Mary Davis", "email": "mary@logistics-express.com", "phone": "456-789-0123"},
        {"name": "Apex Janitorial Services", "category": "Service Provider", "status": "Active", "address": "202 Clean St, Austin, TX", "contact_person": "James Wilson", "email": "james@apexclean.com", "phone": "567-890-1234"},
        {"name": "Standard Maintenance Inc.", "category": "Maintenance Vendor", "status": "Active", "address": "303 Fixit Ave, Detroit, MI", "contact_person": "William Moore", "email": "william@standardmaint.com", "phone": "678-901-2345"},
        {"name": "Future Electronics", "category": "Equipment Vendor", "status": "Pending Approval", "address": "404 Silicon Way, Seattle, WA", "contact_person": "Patricia Taylor", "email": "patricia@futureelec.com", "phone": "789-012-3456"},
        {"name": "Global Office Supplies", "category": "Service Provider", "status": "Active", "address": "505 Paper Rd, Boston, MA", "contact_person": "Michael Anderson", "email": "michael@globalsupplies.com", "phone": "890-123-4567"},
        {"name": "National Safe Transport", "category": "Logistics Partner", "status": "Active", "address": "606 Cargo Dr, Dallas, TX", "contact_person": "Elizabeth Thomas", "email": "elizabeth@safetransport.com", "phone": "901-234-5678"},
        {"name": "Secure Net IT", "category": "IT Vendor", "status": "Inactive", "address": "707 Cyber St, Denver, CO", "contact_person": "David Jackson", "email": "david@securenetit.com", "phone": "012-345-6789"}
    ]

    vendors = []
    for v_data in vendors_data:
        vendor = db.query(Vendor).filter(Vendor.name == v_data["name"]).first()
        if not vendor:
            vendor = Vendor(**v_data)
            db.add(vendor)
            db.commit()
            db.refresh(vendor)
            print(f"Created vendor: {vendor.name}")
        else:
            if repair_demo:
                print(f"Repairing vendor details: {vendor.name}")
                for key, val in v_data.items():
                    setattr(vendor, key, val)
                db.commit()
                db.refresh(vendor)
            else:
                print(f"Vendor already exists: {vendor.name}")
        vendors.append(vendor)

    print("Seeding users...")
    password_hash = get_password_hash("password123")
    
    users_data = [
        {"username": "admin", "email": "admin@vendoriq.com", "hashed_password": password_hash, "role": "Administrator", "full_name": "System Administrator", "is_active": True},
        {"username": "procurement", "email": "procurement@vendoriq.com", "hashed_password": password_hash, "role": "Procurement Manager", "full_name": "Sarah Connor", "is_active": True},
        {"username": "supplychain", "email": "supplychain@vendoriq.com", "hashed_password": password_hash, "role": "Supply Chain Manager", "full_name": "John Connor", "is_active": True},
        {"username": "finance", "email": "finance@vendoriq.com", "hashed_password": password_hash, "role": "Finance Officer", "full_name": "Marcus Wright", "is_active": True},
        {"username": "auditor", "email": "auditor@vendoriq.com", "hashed_password": password_hash, "role": "Auditor", "full_name": "Grace Harper", "is_active": True},
        {"username": "vendor_apex", "email": "contact@apexmaterials.com", "hashed_password": password_hash, "role": "Vendor", "full_name": "John Doe (Apex)", "is_active": True, "vendor_id": vendors[0].id},
        {"username": "vendor_titan", "email": "contact@titanequip.com", "hashed_password": password_hash, "role": "Vendor", "full_name": "Jane Smith (Titan)", "is_active": True, "vendor_id": vendors[1].id}
    ]

    users = []
    for u_data in users_data:
        user = db.query(User).filter(User.username == u_data["username"]).first()
        if not user:
            user = User(**u_data)
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"Created user: {user.username}")
        else:
            if repair_demo:
                print(f"Repairing user details and credentials: {user.username}")
                user.email = u_data["email"]
                user.hashed_password = u_data["hashed_password"]
                user.role = u_data["role"]
                user.full_name = u_data["full_name"]
                user.vendor_id = u_data.get("vendor_id")
                user.is_active = u_data.get("is_active", True)
                db.commit()
                db.refresh(user)
            else:
                print(f"User already exists: {user.username}")
        users.append(user)

    admin_user = users[0]
    proc_user = users[1]
    scm_user = users[2]
    finance_user = users[3]

    print("Seeding procurement requests...")
    reqs_data = [
        {"title": "Bulk Steel Rebar Supply", "description": "Need 500 tons of high-strength steel rebar for construction project.", "priority": "High", "status": "Completed", "estimated_cost": 250000.0, "requested_by_id": proc_user.id, "approved_by_id": scm_user.id, "vendor_id": vendors[0].id},
        {"title": "Excavator Leasing Q3", "description": "Lease 3 heavy-duty excavators for site excavation work.", "priority": "High", "status": "Completed", "estimated_cost": 45000.0, "requested_by_id": proc_user.id, "approved_by_id": scm_user.id, "vendor_id": vendors[1].id},
        {"title": "Laptops for Dev Team", "description": "15 high-performance developer laptops.", "priority": "Medium", "status": "Completed", "estimated_cost": 30000.0, "requested_by_id": proc_user.id, "approved_by_id": admin_user.id, "vendor_id": vendors[2].id},
        {"title": "Warehouse Logistics Shipment", "description": "Interstate transport of critical parts to central warehouse.", "priority": "High", "status": "Completed", "estimated_cost": 15000.0, "requested_by_id": proc_user.id, "approved_by_id": scm_user.id, "vendor_id": vendors[3].id},
        {"title": "Office Cleaning Contract", "description": "Weekly janitorial services for corporate HQ.", "priority": "Low", "status": "Completed", "estimated_cost": 5000.0, "requested_by_id": proc_user.id, "approved_by_id": finance_user.id, "vendor_id": vendors[4].id},
        {"title": "Server HVAC Maintenance", "description": "Annual contract for server room climate control maintenance.", "priority": "Critical", "status": "Completed", "estimated_cost": 12000.0, "requested_by_id": proc_user.id, "approved_by_id": scm_user.id, "vendor_id": vendors[5].id},
        {"title": "Additional Timber Batch", "description": "Emergency raw timber acquisition.", "priority": "Medium", "status": "Ordered", "estimated_cost": 8500.0, "requested_by_id": proc_user.id, "approved_by_id": scm_user.id, "vendor_id": vendors[0].id},
        {"title": "Safety Helmets and Gear", "description": "100 safety gear sets for construction site.", "priority": "Low", "status": "Ordered", "estimated_cost": 3500.0, "requested_by_id": proc_user.id, "approved_by_id": finance_user.id, "vendor_id": vendors[7].id},
        {"title": "Cloud Server Scaling Q4", "description": "AWS node scale-up request for holiday traffic.", "priority": "Critical", "status": "Delivered", "estimated_cost": 28000.0, "requested_by_id": proc_user.id, "approved_by_id": admin_user.id, "vendor_id": vendors[2].id},
        {"title": "Global Cargo Freight", "description": "Freight forwarding from international supply center.", "priority": "High", "status": "Approved", "estimated_cost": 75000.0, "requested_by_id": proc_user.id, "approved_by_id": scm_user.id, "vendor_id": vendors[8].id},
        {"title": "Copper Wiring Batch A", "description": "Request for copper electrical conduits.", "priority": "Medium", "status": "Pending", "estimated_cost": 14000.0, "requested_by_id": proc_user.id, "approved_by_id": None, "vendor_id": vendors[0].id},
        {"title": "Hydraulic Lift Repair", "description": "Urgent repair of dock bay elevator.", "priority": "High", "status": "Pending", "estimated_cost": 9500.0, "requested_by_id": proc_user.id, "approved_by_id": None, "vendor_id": vendors[5].id},
        {"title": "Annual Office Furniture Refresh", "description": "Ergonomic chairs and desks.", "priority": "Low", "status": "Rejected", "estimated_cost": 18000.0, "requested_by_id": proc_user.id, "approved_by_id": finance_user.id, "vendor_id": vendors[7].id},
        {"title": "Software Licences renewal", "description": "Renewal of design and CAD utilities licenses.", "priority": "Medium", "status": "Cancelled", "estimated_cost": 6000.0, "requested_by_id": proc_user.id, "approved_by_id": None, "vendor_id": vendors[2].id},
        {"title": "Spare Engine Parts", "description": "Fleet vehicle replacement gaskets and seals.", "priority": "High", "status": "Approved", "estimated_cost": 22000.0, "requested_by_id": proc_user.id, "approved_by_id": scm_user.id, "vendor_id": vendors[1].id}
    ]

    proc_reqs = []
    for r_data in reqs_data:
        req = db.query(ProcurementRequest).filter(ProcurementRequest.title == r_data["title"]).first()
        if not req:
            req = ProcurementRequest(**r_data)
            db.add(req)
            db.commit()
            db.refresh(req)
            print(f"Created procurement request: {req.title}")
        else:
            print(f"Procurement request already exists: {req.title}")
        proc_reqs.append(req)

    print("Seeding purchase orders...")
    today = datetime.utcnow()
    pos_data = [
        {"po_number": "PO-2026-0001", "procurement_request_id": proc_reqs[0].id, "vendor_id": vendors[0].id, "amount": 250000.0, "status": "Completed", "order_date": today - timedelta(days=60), "expected_delivery_date": today - timedelta(days=45), "actual_delivery_date": today - timedelta(days=45), "invoice_status": "Paid"},
        {"po_number": "PO-2026-0002", "procurement_request_id": proc_reqs[1].id, "vendor_id": vendors[1].id, "amount": 45000.0, "status": "Completed", "order_date": today - timedelta(days=50), "expected_delivery_date": today - timedelta(days=35), "actual_delivery_date": today - timedelta(days=33), "invoice_status": "Paid"},
        {"po_number": "PO-2026-0003", "procurement_request_id": proc_reqs[2].id, "vendor_id": vendors[2].id, "amount": 30000.0, "status": "Completed", "order_date": today - timedelta(days=45), "expected_delivery_date": today - timedelta(days=30), "actual_delivery_date": today - timedelta(days=20), "invoice_status": "Paid"},
        {"po_number": "PO-2026-0004", "procurement_request_id": proc_reqs[3].id, "vendor_id": vendors[3].id, "amount": 15000.0, "status": "Completed", "order_date": today - timedelta(days=40), "expected_delivery_date": today - timedelta(days=35), "actual_delivery_date": today - timedelta(days=35), "invoice_status": "Paid"},
        {"po_number": "PO-2026-0005", "procurement_request_id": proc_reqs[4].id, "vendor_id": vendors[4].id, "amount": 5000.0, "status": "Completed", "order_date": today - timedelta(days=30), "expected_delivery_date": today - timedelta(days=23), "actual_delivery_date": today - timedelta(days=15), "invoice_status": "Paid"},
        {"po_number": "PO-2026-0006", "procurement_request_id": proc_reqs[5].id, "vendor_id": vendors[5].id, "amount": 12000.0, "status": "Completed", "order_date": today - timedelta(days=25), "expected_delivery_date": today - timedelta(days=15), "actual_delivery_date": today - timedelta(days=15), "invoice_status": "Paid"},
        {"po_number": "PO-2026-0007", "procurement_request_id": proc_reqs[6].id, "vendor_id": vendors[0].id, "amount": 8500.0, "status": "Ordered", "order_date": today - timedelta(days=10), "expected_delivery_date": today + timedelta(days=5), "actual_delivery_date": None, "invoice_status": "Unpaid"},
        {"po_number": "PO-2026-0008", "procurement_request_id": proc_reqs[7].id, "vendor_id": vendors[7].id, "amount": 3500.0, "status": "Ordered", "order_date": today - timedelta(days=8), "expected_delivery_date": today + timedelta(days=4), "actual_delivery_date": None, "invoice_status": "Unpaid"},
        {"po_number": "PO-2026-0009", "procurement_request_id": proc_reqs[8].id, "vendor_id": vendors[2].id, "amount": 28000.0, "status": "Delivered", "order_date": today - timedelta(days=15), "expected_delivery_date": today - timedelta(days=2), "actual_delivery_date": today - timedelta(days=1), "invoice_status": "Invoiced"},
        {"po_number": "PO-2026-0010", "procurement_request_id": proc_reqs[9].id, "vendor_id": vendors[8].id, "amount": 75000.0, "status": "Approved", "order_date": today - timedelta(days=3), "expected_delivery_date": today + timedelta(days=12), "actual_delivery_date": None, "invoice_status": "Unpaid"},
        {"po_number": "PO-2026-0011", "procurement_request_id": proc_reqs[14].id, "vendor_id": vendors[1].id, "amount": 22000.0, "status": "Pending Approval", "order_date": today, "expected_delivery_date": today + timedelta(days=15), "actual_delivery_date": None, "invoice_status": "Unpaid"}
    ]

    purchase_orders = []
    for po_d in pos_data:
        po = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == po_d["po_number"]).first()
        if not po:
            po = PurchaseOrder(**po_d)
            db.add(po)
            db.commit()
            db.refresh(po)
            print(f"Created purchase order: {po.po_number}")
        else:
            print(f"Purchase order already exists: {po.po_number}")
        purchase_orders.append(po)

    print("Seeding performance records...")
    perf_data = [
        {"vendor_id": vendors[0].id, "purchase_order_id": purchase_orders[0].id, "delivery_on_time": True, "delivery_delay_days": 0, "quality_rating": 95.0, "communication_rating": 90.0, "compliance_rating": 95.0, "issue_resolution_rating": 90.0, "comments": "Excellent high quality steel rebars, delivered exactly on time.", "logged_by_id": scm_user.id},
        {"vendor_id": vendors[1].id, "purchase_order_id": purchase_orders[1].id, "delivery_on_time": False, "delivery_delay_days": 2, "quality_rating": 85.0, "communication_rating": 80.0, "compliance_rating": 85.0, "issue_resolution_rating": 80.0, "comments": "Excavator dispatch delayed by 2 days, equipment functioned well.", "logged_by_id": scm_user.id},
        {"vendor_id": vendors[2].id, "purchase_order_id": purchase_orders[2].id, "delivery_on_time": False, "delivery_delay_days": 10, "quality_rating": 50.0, "communication_rating": 40.0, "compliance_rating": 60.0, "issue_resolution_rating": 50.0, "comments": "Development laptops were highly delayed and OS setup was incomplete.", "logged_by_id": admin_user.id},
        {"vendor_id": vendors[3].id, "purchase_order_id": purchase_orders[3].id, "delivery_on_time": True, "delivery_delay_days": 0, "quality_rating": 90.0, "communication_rating": 90.0, "compliance_rating": 95.0, "issue_resolution_rating": 90.0, "comments": "Truck was punctual, packaging intact.", "logged_by_id": scm_user.id},
        {"vendor_id": vendors[4].id, "purchase_order_id": purchase_orders[4].id, "delivery_on_time": False, "delivery_delay_days": 8, "quality_rating": 40.0, "communication_rating": 30.0, "compliance_rating": 50.0, "issue_resolution_rating": 35.0, "comments": "Repeated cleaning service delays and poor cleaning execution.", "logged_by_id": finance_user.id},
        {"vendor_id": vendors[5].id, "purchase_order_id": purchase_orders[5].id, "delivery_on_time": True, "delivery_delay_days": 0, "quality_rating": 85.0, "communication_rating": 80.0, "compliance_rating": 85.0, "issue_resolution_rating": 80.0, "comments": "HVAC checked and filters changed accurately.", "logged_by_id": scm_user.id}
    ]

    for pf in perf_data:
        perf = db.query(VendorPerformance).filter(VendorPerformance.purchase_order_id == pf["purchase_order_id"]).first()
        if not perf:
            perf = VendorPerformance(**pf)
            db.add(perf)
            print(f"Created performance record for PO ID: {pf['purchase_order_id']}")
        else:
            print(f"Performance record already exists for PO ID: {pf['purchase_order_id']}")
    db.commit()

    print("Running initial scoring calculation for seeded vendors...")
    for v in vendors:
        if v.status == "Active":
            try:
                from .routes.reliability import calculate_vendor_score_logic
                calculate_vendor_score_logic(v.id, db)
            except Exception as e:
                print(f"Error calculating score for vendor {v.name}: {e}")

    print("Seeding contracts...")
    today_date = date.today()
    contracts_data = [
        {"contract_number": "CON-2026-0001", "vendor_id": vendors[0].id, "title": "Primary Steel Supply Agreement", "value": 1500000.0, "start_date": today_date - timedelta(days=120), "expiry_date": today_date + timedelta(days=240), "status": "Active", "compliance_status": "Compliant", "certification_details": "ISO 9001, OHSAS 18001"},
        {"contract_number": "CON-2026-0002", "vendor_id": vendors[1].id, "title": "Heavy Fleet Leasing Blanket Purchase", "value": 300000.0, "start_date": today_date - timedelta(days=90), "expiry_date": today_date + timedelta(days=15), "status": "Expiring Soon", "compliance_status": "Compliant", "certification_details": "Heavy Equipment safety cleared"},
        {"contract_number": "CON-2026-0003", "vendor_id": vendors[2].id, "title": "Enterprise Cloud & IT Support SLA", "value": 180000.0, "start_date": today_date - timedelta(days=365), "expiry_date": today_date - timedelta(days=5), "status": "Expired", "compliance_status": "Non-Compliant", "certification_details": "GDPR compliance verification failed"},
        {"contract_number": "CON-2026-0004", "vendor_id": vendors[3].id, "title": "National Transport Services Contract", "value": 500000.0, "start_date": today_date - timedelta(days=60), "expiry_date": today_date + timedelta(days=300), "status": "Active", "compliance_status": "Compliant", "certification_details": "DOT Registered Carrier License"},
        {"contract_number": "CON-2026-0005", "vendor_id": vendors[4].id, "title": "HQ Janitorial Services Contract", "value": 60000.0, "start_date": today_date - timedelta(days=30), "expiry_date": today_date + timedelta(days=20), "status": "Expiring Soon", "compliance_status": "Under Review", "certification_details": "Local business license certified"}
    ]

    for c_d in contracts_data:
        contract = db.query(Contract).filter(Contract.contract_number == c_d["contract_number"]).first()
        if not contract:
            contract = Contract(**c_d)
            db.add(contract)
            print(f"Created contract: {c_d['contract_number']}")
        else:
            print(f"Contract already exists: {c_d['contract_number']}")
    db.commit()

    if clear_existing or db.query(Communication).count() == 0:
        print("Seeding communications...")
        comm_data = [
            {"sender_id": proc_user.id, "recipient_id": users[5].id, "vendor_id": vendors[0].id, "subject": "Steel Rebar Delivery Schedule", "message": "Hi John, could you please verify the dispatch timeline for the remaining 100 tons?", "is_read": True},
            {"sender_id": users[5].id, "recipient_id": proc_user.id, "vendor_id": vendors[0].id, "subject": "Re: Steel Rebar Delivery Schedule", "message": "Yes Sarah, the dispatch is scheduled for this Friday. You should receive the loading manifest today.", "is_read": False},
            {"sender_id": scm_user.id, "recipient_id": users[6].id, "vendor_id": vendors[1].id, "subject": "Excavator Leasing Re-Inspection", "message": "Jane, we noticed hydraulic pressure fluctuations on unit #3. Please send a tech.", "is_read": True},
            {"sender_id": users[6].id, "recipient_id": scm_user.id, "vendor_id": vendors[1].id, "subject": "Re: Excavator Leasing Re-Inspection", "message": "Will do. A mobile technician will be dispatched to your site tomorrow morning.", "is_read": False}
        ]
        for cm in comm_data:
            comm = Communication(**cm)
            db.add(comm)
        db.commit()
    else:
        print("Communications table already contains data. Skipping.")

    if clear_existing or db.query(Notification).count() == 0:
        print("Seeding notifications...")
        notif_data = [
            {"user_id": proc_user.id, "title": "Vendor Profile Submitted", "message": "Future Electronics has requested vendor approval.", "type": "Vendor Approval", "is_read": False},
            {"user_id": proc_user.id, "title": "PO Created", "message": "Purchase Order PO-2026-0011 requires approval.", "type": "Procurement", "is_read": False},
            {"user_id": scm_user.id, "title": "Contract Expiring Soon", "message": "Leasing contract for Titan Heavy Equipment expires in 15 days.", "type": "Contract Expiry", "is_read": False},
            {"user_id": scm_user.id, "title": "Critical Reliability Alert", "message": "IT Solutions Group score dropped below 50. High risk flagged.", "type": "Compliance", "is_read": False}
        ]
        for nf in notif_data:
            notif = Notification(**nf)
            db.add(notif)
        db.commit()
    else:
        print("Notifications table already contains data. Skipping.")

    if clear_existing or db.query(AuditLog).count() == 0:
        print("Seeding audit logs...")
        audits = [
            {"user_id": admin_user.id, "username": admin_user.username, "action": "Database Seeded", "module": "Auth", "details": "System database tables initialized and demo data loaded."},
            {"user_id": admin_user.id, "username": admin_user.username, "action": "User Login", "module": "Auth", "details": "Admin logged in successfully."},
            {"user_id": proc_user.id, "username": proc_user.username, "action": "Create Procurement Request", "module": "Procurement", "details": "Created request for Bulk Steel Rebar Supply."},
            {"user_id": scm_user.id, "username": scm_user.username, "action": "Approve Procurement Request", "module": "Procurement", "details": "Approved request: Bulk Steel Rebar Supply."},
            {"user_id": proc_user.id, "username": proc_user.username, "action": "Create Purchase Order", "module": "Purchase Orders", "details": "Generated PO-2026-0001."}
        ]
        for ad in audits:
            audit = AuditLog(**ad)
            db.add(audit)
        db.commit()
    else:
        print("Audit logs table already contains data. Skipping.")

    print("Seeding completed successfully!")

if __name__ == "__main__":
    db = SessionLocal()
    clear_opt = "--clear" in sys.argv
    repair_opt = "--repair" in sys.argv
    try:
        seed_db(db, clear_existing=clear_opt, repair_demo=repair_opt)
    finally:
        db.close()
