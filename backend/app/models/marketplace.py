"""
Marketplace Models - Comprehensive with Payments
"""
from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey, Numeric, Integer, Enum as SQLEnum
from sqlalchemy.sql import func
from app.db.database import Base
import enum


class MarketplaceCategory(str, enum.Enum):
    PRODUCTS = "PRODUCTS"
    SERVICES = "SERVICES"
    JOBS = "JOBS"
    HOUSING = "HOUSING"
    VEHICLES = "VEHICLES"
    OTHER = "OTHER"


class ListingStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PENDING_PAYMENT = "PENDING_PAYMENT"
    PAID = "PAID"
    SOLD = "SOLD"
    EXPIRED = "EXPIRED"
    HIDDEN = "HIDDEN"
    CANCELLED = "CANCELLED"


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    AWAITING_PAYMENT = "AWAITING_PAYMENT"
    PAID = "PAID"
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


class MarketplaceListing(Base):
    __tablename__ = "marketplace_listings"
    
    id = Column(String, primary_key=True, default=lambda: f"mkl_{func.random(16)}")
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    member_id = Column(String, ForeignKey("members.id"), nullable=False)
    
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    category = Column(SQLEnum(MarketplaceCategory), nullable=False)
    price = Column(Numeric(12, 2), nullable=False)
    
    # Media
    images = Column(Text)  # JSON array
    video_url = Column(String)
    
    # Details
    location = Column(String)
    condition = Column(String)  # new, like_new, used, refurbished
    brand = Column(String)
    sku = Column(String)
    
    # Contact
    contact_phone = Column(String)
    contact_email = Column(String)
    show_contact = Column(Boolean, default=True)
    
    # Shipping
    weight_kg = Column(Numeric(10, 2))
    dimensions = Column(String)  # LxWxH
    shipping_available = Column(Boolean, default=False)
    shipping_cost = Column(Numeric(10, 2), default=0)
    
    # Pricing
    discount_price = Column(Numeric(12, 2))  # If on sale
    discount_until = Column(DateTime)
    
    # Status
    status = Column(SQLEnum(ListingStatus), default=ListingStatus.ACTIVE)
    views = Column(String, default="0")
    saves = Column(String, default="0")
    
    # Affiliate
    is_affiliate = Column(Boolean, default=False)
    affiliate_org_id = Column(String, ForeignKey("organizations.id"))
    affiliate_commission = Column(Numeric(5, 2), default="2.00")
    
    # SEO
    tags = Column(Text)  # comma-separated
    meta_title = Column(String)
    meta_description = Column(Text)
    
    expires_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class MarketplaceOrder(Base):
    __tablename__ = "marketplace_orders"
    
    id = Column(String, primary_key=True, default=lambda: f"mko_{func.random(16)}")
    
    # Buyer
    buyer_org_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    buyer_member_id = Column(String, ForeignKey("members.id"), nullable=False)
    
    # Seller
    seller_org_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    seller_member_id = Column(String, ForeignKey("members.id"))
    
    # Listing
    listing_id = Column(String, ForeignKey("marketplace_listings.id"), nullable=False)
    
    # Pricing
    unit_price = Column(Numeric(12, 2), nullable=False)
    quantity = Column(String, default="1")
    subtotal = Column(Numeric(12, 2), nullable=False)
    shipping_cost = Column(Numeric(10, 2), default=0)
    platform_fee = Column(Numeric(12, 2), default=0)  # 2% default
    affiliate_commission = Column(Numeric(12, 2), default=0)
    total = Column(Numeric(12, 2), nullable=False)
    
    # Status
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING)
    
    # Payment
    mpesa_receipt = Column(String)
    paid_at = Column(DateTime)
    
    # Shipping
    shipping_address = Column(Text)
    tracking_number = Column(String)
    shipped_at = Column(DateTime)
    delivered_at = Column(DateTime)
    
    # Notes
    buyer_notes = Column(Text)
    seller_notes = Column(Text)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class MarketplacePayment(Base):
    __tablename__ = "marketplace_payments"
    
    id = Column(String, primary_key=True, default=lambda: f"mkp_{func.random(16)}")
    order_id = Column(String, ForeignKey("marketplace_orders.id"), nullable=False)
    
    amount = Column(Numeric(12, 2), nullable=False)
    mpesa_receipt = Column(String)
    mpesa_code = Column(String)
    phone = Column(String)
    
    status = Column(String, default="PENDING")  # PENDING, COMPLETED, FAILED
    failed_reason = Column(String)
    
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)


class MarketplaceReview(Base):
    __tablename__ = "marketplace_reviews"
    
    id = Column(String, primary_key=True, default=lambda: f"mkr_{func.random(16)}")
    order_id = Column(String, ForeignKey("marketplace_orders.id"), nullable=False)
    reviewer_id = Column(String, ForeignKey("members.id"), nullable=False)
    reviewee_id = Column(String, ForeignKey("members.id"))  # Seller
    
    rating = Column(String, nullable=False)  # 1-5
    title = Column(String)
    comment = Column(Text)
    
    is_verified_purchase = Column(Boolean, default=True)
    
    created_at = Column(DateTime, server_default=func.now())


class MarketplaceFavorite(Base):
    __tablename__ = "marketplace_favorites"
    
    id = Column(String, primary_key=True, default=lambda: f"mkf_{func.random(16)}")
    listing_id = Column(String, ForeignKey("marketplace_listings.id"), nullable=False)
    member_id = Column(String, ForeignKey("members.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class AffiliateChama(Base):
    __tablename__ = "affiliate_chamas"
    
    id = Column(String, primary_key=True, default=lambda: f"afc_{func.random(16)}")
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    invited_by = Column(String, ForeignKey("organizations.id"))
    status = Column(String, default="PENDING")  # PENDING, ACTIVE, SUSPENDED
    
    commission_rate = Column(Numeric(5, 2), default="2.00")
    notes = Column(Text)
    
    created_at = Column(DateTime, server_default=func.now())


class AffiliatePayout(Base):
    __tablename__ = "affiliate_payouts"
    
    id = Column(String, primary_key=True, default=lambda: f"afp_{func.random(16)}")
    affiliate_id = Column(String, ForeignKey("affiliate_chamas.id"), nullable=False)
    
    amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String, default="PENDING")  # PENDING, PROCESSING, PAID, FAILED
    
    mpesa_phone = Column(String)
    mpesa_receipt = Column(String)
    
    processed_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())


    # Buyer & Seller
    buyer_id = Column(String, ForeignKey("members.id"), nullable=False)
    buyer_org_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    seller_id = Column(String, ForeignKey("members.id"), nullable=False)
    seller_org_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    
    # Listing
    listing_id = Column(String, ForeignKey("marketplace_listings.id"), nullable=False)
    
    # Amounts
    amount = Column(Numeric(12, 2), nullable=False)
    platform_fee = Column(Numeric(12, 2), default=0)
    chama_fee = Column(Numeric(12, 2), default=0)
    cross_chama_premium = Column(Numeric(12, 2), default=0)
    affiliate_commission = Column(Numeric(12, 2), default=0)
    shipping_cost = Column(Numeric(12, 2), default=0)
    total = Column(Numeric(12, 2), nullable=False)
    
    # Escrow
    escrow_status = Column(String, default="HELD")  # HELD, RELEASED, REFUNDED
    escrow_released_at = Column(DateTime)
    auto_release_days = Column(Integer, default=7)  # Auto-release after 7 days
    
    # Status
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING)
    
    # Shipping
    shipping_address = Column(Text)
    tracking_number = Column(String)
    
    # Payment
    mpesa_code = Column(String)
    paid_at = Column(DateTime)
    
    # Timeline
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    shipped_at = Column(DateTime)
    delivered_at = Column(DateTime)
    completed_at = Column(DateTime)


class Dispute(Base):
    __tablename__ = "marketplace_disputes"
    
    id = Column(String, primary_key=True, default=lambda: f"dis_{func.random(16)}")
    
    order_id = Column(String, ForeignKey("marketplace_orders.id"), nullable=False)
    opened_by = Column(String, ForeignKey("members.id"), nullable=False)
    
    # Reason
    reason = Column(String, nullable=False)  # NOT_RECEIVED, NOT_AS_DESCRIBED, DAMAGED, OTHER
    description = Column(Text, nullable=False)
    
    # Resolution
    status = Column(String, default="OPEN")  # OPEN, UNDER_REVIEW, RESOLVED, CLOSED
    resolution = Column(String)  # REFUND, RELEASE, PARTIAL_REFUND
    resolved_by = Column(String, ForeignKey("members.id"))
    resolution_notes = Column(Text)
    
    # Evidence
    evidence_urls = Column(Text)  # JSON array
    
    # Timeline
    opened_at = Column(DateTime, server_default=func.now())
    resolved_at = Column(DateTime)
