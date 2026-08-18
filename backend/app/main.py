import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import text
from .database import engine, Base, get_db
from .config import settings

# Import routers
from .routes import auth, users, vendors, procurement, purchase_orders, performance, reliability, contracts, communications, notifications, reports, dashboard, audit_logs

# Create tables only if using SQLite (e.g. local quick testing)
if engine.url.drivername == "sqlite":
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Error creating SQLite tables: {e}")

app = FastAPI(
    title="VendorIQ API",
    description="Vendor Reliability Intelligence & Procurement Risk Management Platform API",
    version="1.0.0"
)

# Ensure uploads/avatars directory exists and mount static serving
os.makedirs(os.path.join("uploads", "avatars"), exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# CORS configuration
raw_origins = settings.CORS_ORIGINS.split(",")
origins = [o.strip() for o in raw_origins if o.strip()]

# Include localhost defaults if not present
for local_origin in ["http://localhost:4200", "http://localhost:80", "http://localhost"]:
    if local_origin not in origins:
        origins.append(local_origin)

if settings.FRONTEND_URL:
    fe_url = settings.FRONTEND_URL.rstrip("/")
    if fe_url not in origins:
        origins.append(fe_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers under /api
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(vendors.router, prefix="/api")
app.include_router(procurement.router, prefix="/api")
app.include_router(purchase_orders.router, prefix="/api")
app.include_router(performance.router, prefix="/api")
app.include_router(reliability.router, prefix="/api")
app.include_router(contracts.router, prefix="/api")
app.include_router(communications.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(audit_logs.router, prefix="/api")

@app.get("/health")
@app.get("/api/health")
def health_check(db: Session = Depends(get_db)):
    try:
        # Check database connection
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "mode": settings.ENV_MODE
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database connection error: {str(e)}"
        )
