from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.rate_limit import RateLimitMiddleware
from app.core.security_headers import (
    SecurityHeadersMiddleware,
    RequestSizeMiddleware,
    IPBlocklistMiddleware,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting Chama API...")
    yield
    print("👋 Shutting down...")


app = FastAPI(
    title="Chama API",
    description="Community Treasury Management API",
    version="1.0.0",
    lifespan=lifespan,
)

# Security middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(IPBlocklistMiddleware)
app.add_middleware(RequestSizeMiddleware)
app.add_middleware(RateLimitMiddleware, calls=100, period=60)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health endpoints (no auth required)
from app.api.v1.endpoints import health
app.include_router(health.router, tags=["health"])

# Import all endpoints
from app.api.v1.endpoints import (
    api_keys,
    push_notifications, email_notifications, bulk_sms,
    bulk_import, audit_logs, backup_restore,
    federations, inter_lending, super_admin, templates,
    assets, investments,
    compliance,
    budget, tax_reports, import_export, security, search,
    auth, members, contributions, loans, mpesa, treasury,
    proposals, organizations, attendance, notifications,
    uploads, reports, fines, calculator, export, webhooks,
    standing_orders, next_of_kin, bulk, announcements,
    analytics, meeting_notices, guarantors,
    auth_profile,
    marketplace,
    mpesa_config,
    messaging_wallet
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(auth_profile.router, prefix="", tags=["auth-profile"])
app.include_router(members.router, prefix="/api/v1/members", tags=["members"])
app.include_router(contributions.router, prefix="/api/v1/contributions", tags=["contributions"])
app.include_router(loans.router, prefix="/api/v1/loans", tags=["loans"])
app.include_router(mpesa.router, prefix="/api/v1/mpesa", tags=["mpesa"])
app.include_router(treasury.router, prefix="/api/v1/treasury", tags=["treasury"])
app.include_router(proposals.router, prefix="/api/v1/proposals", tags=["proposals"])
app.include_router(organizations.router, prefix="/api/v1/organizations", tags=["organizations"])
app.include_router(attendance.router, prefix="/api/v1/attendance", tags=["attendance"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"])
app.include_router(uploads.router, prefix="/api/v1", tags=["uploads"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])
app.include_router(fines.router, prefix="/api/v1", tags=["fines"])
app.include_router(calculator.router, prefix="/api/v1", tags=["calculator"])
app.include_router(export.router, prefix="/api/v1", tags=["export"])
app.include_router(webhooks.router, prefix="/api/v1", tags=["webhooks"])
app.include_router(standing_orders.router, prefix="/api/v1", tags=["standing-orders"])
app.include_router(next_of_kin.router, prefix="/api/v1", tags=["next-of-kin"])
app.include_router(bulk.router, prefix="/api/v1", tags=["bulk"])
app.include_router(announcements.router, prefix="/api/v1", tags=["announcements"])
app.include_router(meeting_notices.router, prefix="/api/v1", tags=["meeting-notices"])
app.include_router(guarantors.router, prefix="/api/v1", tags=["guarantors"])
app.include_router(marketplace.router, prefix="/api/v1", tags=["marketplace"])
app.include_router(mpesa_config.router, prefix="/api/v1", tags=["mpesa-config"])
app.include_router(messaging_wallet.router, prefix="/api/v1", tags=["messaging-wallet"])
app.include_router(analytics.router, prefix="/api/v1", tags=["analytics"])
app.include_router(budget.router, prefix="/api/v1", tags=["budget"])
app.include_router(tax_reports.router, prefix="/api/v1", tags=["tax-reports"])
app.include_router(import_export.router, prefix="/api/v1", tags=["import-export"])
app.include_router(security.router, prefix="/api/v1", tags=["security"])
app.include_router(search.router, prefix="/api/v1", tags=["search"])
app.include_router(compliance.router, prefix="/api/v1", tags=["compliance"])
app.include_router(assets.router, prefix="/api/v1", tags=["assets"])
app.include_router(investments.router, prefix="/api/v1", tags=["investments"])
app.include_router(federations.router, prefix="/api/v1", tags=["federations"])
app.include_router(inter_lending.router, prefix="/api/v1", tags=["inter-lending"])
app.include_router(super_admin.router, prefix="/api/v1", tags=["super-admin"])
app.include_router(templates.router, prefix="/api/v1", tags=["templates"])
app.include_router(bulk_import.router, prefix="/api/v1", tags=["bulk-import"])
app.include_router(audit_logs.router, prefix="/api/v1", tags=["audit-logs"])
app.include_router(backup_restore.router, prefix="/api/v1", tags=["backup-restore"])
app.include_router(push_notifications.router, prefix="/api/v1", tags=["push"])
app.include_router(email_notifications.router, prefix="/api/v1", tags=["email"])
app.include_router(bulk_sms.router, prefix="/api/v1", tags=["sms"])
app.include_router(api_keys.router, prefix="/api/v1", tags=["api-keys"])


@app.get("/")
def root():
    return {
        "name": "Chama API",
        "version": "1.0.0",
        "docs": "/docs"
    }
