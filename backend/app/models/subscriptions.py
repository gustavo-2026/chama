"""
Subscription Tiers
"""
from sqlalchemy import Column, String, DateTime, Text, Boolean, Numeric, ForeignKey, Integer
from sqlalchemy.sql import func
from app.db.database import Base


class SubscriptionTier(Base):
    __tablename__ = "subscription_tiers"
    
    id = Column(String, primary_key=True, default=lambda: f"tier_{func.random(16)}")
    
    name = Column(String, nullable=False)  # free, pro, enterprise
    display_name = Column(String, nullable=False)
    description = Column(Text)
    
    # Pricing
    monthly_price = Column(Numeric(10, 2), default=0)
    yearly_price = Column(Numeric(10, 2), default=0)
    
    # Features
    max_members = Column(Integer, default=10)  # 0 = unlimited
    max_listings = Column(Integer, default=100)
    marketplace_enabled = Column(Boolean, default=True)
    custom_branding = Column(Boolean, default=False)
    priority_support = Column(Boolean, default=False)
    analytics_advanced = Column(Boolean, default=False)
    api_access = Column(Boolean, default=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    
    created_at = Column(DateTime, server_default=func.now())


class OrganizationSubscription(Base):
    __tablename__ = "organization_subscriptions"
    
    id = Column(String, primary_key=True, default=lambda: f"sub_{func.random(16)}")
    
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    tier_id = Column(String, ForeignKey("subscription_tiers.id"), nullable=False)
    
    # Billing
    billing_cycle = Column(String, default="monthly")  # monthly, yearly
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    
    # Payment
    payment_status = Column(String, default="ACTIVE")  # ACTIVE, PAST_DUE, CANCELLED
    mpesa_receipt = Column(String)
    
    # Auto-renewal
    auto_renew = Column(Boolean, default=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class SubscriptionPayment(Base):
    __tablename__ = "subscription_payments"
    
    id = Column(String, primary_key=True, default=lambda: f"spay_{func.random(16)}")
    
    subscription_id = Column(String, ForeignKey("organization_subscriptions.id"), nullable=False)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    
    amount = Column(Numeric(10, 2), nullable=False)
    billing_cycle = Column(String)  # monthly, yearly
    
    # Payment
    mpesa_code = Column(String)
    mpesa_receipt = Column(String)
    status = Column(String, default="PENDING")  # PENDING, COMPLETED, FAILED
    
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    created_at = Column(DateTime, server_default=func.now())
