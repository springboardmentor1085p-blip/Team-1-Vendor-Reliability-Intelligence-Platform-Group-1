"""fix_finance_officer_account

Revision ID: 75530cdbd15a
Revises: 5013bbc35f3d
Create Date: 2026-08-18 11:34:41.115685

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '75530cdbd15a'
down_revision: Union[str, Sequence[str], None] = '5013bbc35f3d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)
    
    from app.models import User
    from app.utils.security import verify_password
    
    # Check if finance user exists
    finance_user = session.query(User).filter(User.username == "finance").first()
    if finance_user:
        print(f"\n[ALEMBIC MIGRATION] Finance Officer user exists. Username: {finance_user.username}, Email: {finance_user.email}, Role: {finance_user.role}")
        pwd_ok = verify_password("password123", finance_user.hashed_password)
        role_ok = (finance_user.role == "Finance Officer")
        
        problems = []
        if not pwd_ok:
            problems.append("password hash does not match default demo settings")
        if not role_ok:
            problems.append(f"role is '{finance_user.role}' instead of 'Finance Officer'")
            
        if problems:
            print(f"[WARNING] Demo Finance Officer account has issues: {', '.join(problems)}.")
            print("[INFO] To safely repair and reset default demo accounts, please run: python -m app.seeds --repair\n")
        else:
            print("[ALEMBIC MIGRATION] Finance Officer account is healthy.")
    else:
        print("\n[WARNING] Demo Finance Officer user ('finance') is missing in the database.")
        print("[INFO] Please run: python -m app.seeds to safely seed missing demo users.\n")
        
    # Also verify other demo users to check if they are present and healthy
    demo_users = [
        {"username": "admin", "role": "Administrator"},
        {"username": "procurement", "role": "Procurement Manager"},
        {"username": "supplychain", "role": "Supply Chain Manager"},
        {"username": "auditor", "role": "Auditor"},
    ]
    
    for du in demo_users:
        user = session.query(User).filter(User.username == du["username"]).first()
        if not user:
            print(f"[WARNING] Demo user '{du['username']}' is missing in the database. Run 'python -m app.seeds' to restore.")
        else:
            pwd_ok = verify_password("password123", user.hashed_password)
            role_ok = (user.role == du["role"])
            if not pwd_ok or not role_ok:
                print(f"[INFO] Demo user '{du['username']}' deviates from default configuration. Run 'python -m app.seeds --repair' if you want to restore defaults.")


def downgrade() -> None:
    """Downgrade schema."""
    pass
