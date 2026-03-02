"""
Marketplace Comprehensive Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import jwt
import math

from app.db.database import get_db
from app.models import Member
from app.models.marketplace import (
    MarketplaceListing, MarketplaceOrder, MarketplacePayment, 
    MarketplaceReview, MarketplaceFavorite, AffiliateChama, AffiliatePayout,
    MarketplaceCategory, ListingStatus, OrderStatus
)
from app.core.config import settings
from app.models import MarketplaceSettings

router = APIRouter()


# ============ Helper Functions ============

def get_current_member_optional(db: Session = Depends(get_db), authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        member_id = payload.get("sub")
        return db.query(Member).filter(Member.id == member_id).first()
    except:
        return None


def require_member(db: Session = Depends(get_db), authorization: str = Header(None)) -> Member:
    member = get_current_member_optional(db=db, authorization=authorization)
    if not member:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return member


def calculate_fees(amount: float, affiliate_rate: float = 0) -> dict:
    """Calculate platform fee and affiliate commission"""
    org_settings = get_org_fee_settings(db, organization_id)
    platform_fee = max(amount * (org_settings["platform_fee_percent"] / 100), org_settings["minimum_fee"])
    affiliate_commission = amount * (affiliate_rate / 100) if affiliate_rate else 0
    seller_net = amount - platform_fee - affiliate_commission
    return {
        "subtotal": amount,
        "platform_fee": round(platform_fee, 2),
        "affiliate_commission": round(affiliate_commission, 2),
        "seller_net": round(seller_net, 2)
    }


# ============ Schemas ============

class ListingCreate(BaseModel):
    title: str
    description: str
    category: str
    price: float
    images: Optional[List[str]] = None
    video_url: Optional[str] = None
    location: Optional[str] = None
    condition: Optional[str] = None
    brand: Optional[str] = None
    sku: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    show_contact: bool = True
    weight_kg: Optional[float] = None
    dimensions: Optional[str] = None
    shipping_available: bool = False
    shipping_cost: float = 0
    discount_price: Optional[float] = None
    discount_until: Optional[datetime] = None
    tags: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    expires_days: int = 30


class OrderCreate(BaseModel):
    listing_id: str
    quantity: int = 1
    shipping_address: Optional[str] = None
    buyer_notes: Optional[str] = None


class PaymentRequest(BaseModel):
    order_id: str
    phone: str


class ShippingUpdate(BaseModel):
    tracking_number: Optional[str] = None
    status: Optional[str] = None


class ReviewCreate(BaseModel):
    order_id: str
    rating: int  # 1-5
    title: Optional[str] = None
    comment: Optional[str] = None


# ============ Listing Endpoints ============

@router.get("/marketplace/categories")
def list_categories():
    return [
        {"id": "PRODUCTS", "name": "Products", "icon": "shopping-bag"},
        {"id": "SERVICES", "name": "Services", "icon": "tool"},
        {"id": "JOBS", "name": "Jobs", "icon": "briefcase"},
        {"id": "HOUSING", "name": "Housing", "icon": "home"},
        {"id": "VEHICLES", "name": "Vehicles", "icon": "car"},
        {"id": "OTHER", "name": "Other", "icon": "box"},
    ]


@router.get("/marketplace")
def list_marketplace(
    category: Optional[str] = None,
    status: str = "ACTIVE",
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    condition: Optional[str] = None,
    location: Optional[str] = None,
    sort: str = "newest",  # newest, price_low, price_high, popular
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current: Member = Depends(get_current_member_optional)
):
    query = db.query(MarketplaceListing).filter(MarketplaceListing.status == ListingStatus.ACTIVE)
    
    if category:
        query = query.filter(MarketplaceListing.category == category)
    
    if search:
        query = query.filter(
            (MarketplaceListing.title.ilike(f"%{search}%")) |
            (MarketplaceListing.description.ilike(f"%{search}%"))
        )
    
    if min_price:
        query = query.filter(MarketplaceListing.price >= min_price)
    if max_price:
        query = query.filter(MarketplaceListing.price <= max_price)
    if condition:
        query = query.filter(MarketplaceListing.condition == condition)
    if location:
        query = query.filter(MarketplaceListing.location.ilike(f"%{location}%"))
    
    # Sorting
    if sort == "price_low":
        query = query.order_by(MarketplaceListing.price.asc())
    elif sort == "price_high":
        query = query.order_by(MarketplaceListing.price.desc())
    elif sort == "popular":
        query = query.order_by(MarketplaceListing.views.desc())
    else:
        query = query.order_by(MarketplaceListing.created_at.desc())
    
    total = query.count()
    listings = query.offset(offset).limit(limit).all()
    
    return {"total": total, "listings": listings}


@router.post("/marketplace")
def create_listing(
    listing: ListingCreate,
    db: Session = Depends(get_db),
    current: Member = Depends(require_member)
):
    expires_at = datetime.utcnow() + timedelta(days=listing.expires_days) if listing.expires_days else None
    
    new_listing = MarketplaceListing(
        organization_id=current.organization_id,
        member_id=current.id,
        title=listing.title,
        description=listing.description,
        category=listing.category,
        price=listing.price,
        images=",".join(listing.images) if listing.images else None,
        video_url=listing.video_url,
        location=listing.location,
        condition=listing.condition,
        brand=listing.brand,
        sku=listing.sku,
        contact_phone=listing.contact_phone,
        contact_email=listing.contact_email,
        show_contact=listing.show_contact,
        weight_kg=listing.weight_kg,
        dimensions=listing.dimensions,
        shipping_available=listing.shipping_available,
        shipping_cost=listing.shipping_cost,
        discount_price=listing.discount_price,
        discount_until=listing.discount_until,
        tags=listing.tags,
        meta_title=listing.meta_title,
        meta_description=listing.meta_description,
        expires_at=expires_at
    )
    
    db.add(new_listing)
    db.commit()
    db.refresh(new_listing)
    return new_listing


@router.get("/marketplace/{listing_id}")
def get_listing(listing_id: str, db: Session = Depends(get_db), current: Member = Depends(get_current_member_optional)):
    listing = db.query(MarketplaceListing).filter(MarketplaceListing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    # Increment views
    listing.views = str(int(listing.views or 0) + 1)
    db.commit()
    
    return listing


@router.delete("/marketplace/{listing_id}")
def delete_listing(listing_id: str, db: Session = Depends(get_db), current: Member = Depends(require_member)):
    listing = db.query(MarketplaceListing).filter(
        MarketplaceListing.id == listing_id,
        MarketplaceListing.member_id == current.id
    ).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    listing.status = ListingStatus.CANCELLED
    db.commit()
    return {"message": "Listing cancelled"}


@router.post("/marketplace/{listing_id}/favorite")
def toggle_favorite(listing_id: str, db: Session = Depends(get_db), current: Member = Depends(require_member)):
    listing = db.query(MarketplaceListing).filter(MarketplaceListing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    existing = db.query(MarketplaceFavorite).filter(
        MarketplaceFavorite.listing_id == listing_id,
        MarketplaceFavorite.member_id == current.id
    ).first()
    
    if existing:
        db.delete(existing)
        return {"favorited": False}
    
    favorite = MarketplaceFavorite(listing_id=listing_id, member_id=current.id)
    db.add(favorite)
    listing.saves = str(int(listing.saves or 0) + 1)
    db.commit()
    return {"favorited": True}


# ============ Order Endpoints ============

@router.post("/marketplace/orders")
def create_order(order: OrderCreate, db: Session = Depends(get_db), current: Member = Depends(require_member)):
    listing = db.query(MarketplaceListing).filter(
        MarketplaceListing.id == order.listing_id,
        MarketplaceListing.status == ListingStatus.ACTIVE
    ).first()
    
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    # Can't buy own listing
    if listing.member_id == current.id:
        raise HTTPException(status_code=400, detail="Cannot buy your own listing")
    
    # Calculate fees
    unit_price = float(listing.discount_price or listing.price)
    subtotal = unit_price * order.quantity
    shipping = float(listing.shipping_cost or 0) * order.quantity if listing.shipping_available else 0
    
    # Get affiliate commission if applicable
    affiliate_commission = 0
    if listing.is_affiliate:
        affiliate_commission = subtotal * (float(listing.affiliate_commission or 0) / 100)
    
    fees = calculate_cross_chama_fees(db, subtotal, listing.organization_id, current.organization_id, float(listing.affiliate_commission or 0) if listing.is_affiliate else 0)
    
    new_order = MarketplaceOrder(
        buyer_org_id=current.organization_id,
        buyer_member_id=current.id,
        seller_org_id=listing.organization_id,
        seller_member_id=listing.member_id,
        listing_id=listing.id,
        unit_price=unit_price,
        quantity=str(order.quantity),
        subtotal=subtotal,
        shipping_cost=shipping,
        platform_fee=fees["platform_fee"],
        affiliate_commission=fees["affiliate_commission"],
        total=subtotal + shipping,
        shipping_address=order.shipping_address,
        buyer_notes=order.buyer_notes,
        status=OrderStatus.PENDING
    )
    
    db.add(new_order)
    
    # Update listing status
    listing.status = ListingStatus.PENDING_PAYMENT
    db.commit()
    db.refresh(new_order)
    
    return new_order


@router.get("/marketplace/orders")
def list_orders(
    role: str = "buyer",  # buyer, seller
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current: Member = Depends(require_member)
):
    if role == "buyer":
        query = db.query(MarketplaceOrder).filter(MarketplaceOrder.buyer_member_id == current.id)
    else:
        query = db.query(MarketplaceOrder).filter(MarketplaceOrder.seller_member_id == current.id)
    
    if status:
        query = query.filter(MarketplaceOrder.status == status)
    
    return query.order_by(MarketplaceOrder.created_at.desc()).all()


@router.get("/marketplace/orders/{order_id}")
def get_order(order_id: str, db: Session = Depends(get_db), current: Member = Depends(require_member)):
    order = db.query(MarketplaceOrder).filter(MarketplaceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check access
    if order.buyer_member_id != current.id and order.seller_member_id != current.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return order


# ============ Payment Endpoints ============

@router.post("/marketplace/orders/{order_id}/pay")
def initiate_payment(
    order_id: str,
    payment: PaymentRequest,
    db: Session = Depends(get_db),
    current: Member = Depends(require_member)
):
    order = db.query(MarketplaceOrder).filter(
        MarketplaceOrder.id == order_id,
        MarketplaceOrder.buyer_member_id == current.id
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.status != OrderStatus.PENDING:
        raise HTTPException(status_code=400, detail="Order cannot be paid")
    
    # Create payment record
    payment_record = MarketplacePayment(
        order_id=order_id,
        amount=order.total,
        phone=payment.phone,
        status="PENDING"
    )
    db.add(payment_record)
    
    # Update order status
    order.status = OrderStatus.AWAITING_PAYMENT
    db.commit()
    
    # In production, initiate M-Pesa STK Push here
    # For now, simulate success
    payment_record.status = "COMPLETED"
    payment_record.mpesa_code = f"sim_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    payment_record.completed_at = datetime.utcnow()
    
    order.status = OrderStatus.PAID
    order.mpesa_receipt = payment_record.mpesa_code
    order.paid_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "message": "Payment successful",
        "order_id": order.id,
        "mpesa_receipt": payment_record.mpesa_code
    }


@router.post("/marketplace/orders/{order_id}/deliver")
def mark_delivered(order_id: str, db: Session = Depends(get_db), current: Member = Depends(require_member)):
    order = db.query(MarketplaceOrder).filter(
        MarketplaceOrder.id == order_id,
        MarketplaceOrder.seller_member_id == current.id
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.status != OrderStatus.PAID:
        raise HTTPException(status_code=400, detail="Order not paid")
    
    order.status = OrderStatus.SHIPPED
    order.shipped_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Order marked as shipped"}


@router.post("/marketplace/orders/{order_id}/complete")
def mark_complete(order_id: str, db: Session = Depends(get_db), current: Member = Depends(require_member)):
    order = db.query(MarketplaceOrder).filter(
        MarketplaceOrder.id == order_id,
        MarketplaceOrder.buyer_member_id == current.id
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order.status = OrderStatus.DELIVERED
    order.delivered_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Order completed"}


# ============ Review Endpoints ============

@router.post("/marketplace/reviews")
def create_review(review: ReviewCreate, db: Session = Depends(get_db), current: Member = Depends(require_member)):
    order = db.query(MarketplaceOrder).filter(
        MarketplaceOrder.id == review.order_id,
        MarketplaceOrder.buyer_member_id == current.id,
        MarketplaceOrder.status == OrderStatus.DELIVERED
    ).first()
    
    if not order:
        raise HTTPException(status_code=400, detail="Order not found or not delivered")
    
    # Check if already reviewed
    existing = db.query(MarketplaceReview).filter(
        MarketplaceReview.order_id == review.order_id,
        MarketplaceReview.reviewer_id == current.id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Already reviewed")
    
    new_review = MarketplaceReview(
        order_id=review.order_id,
        reviewer_id=current.id,
        seller_member_id=order.seller_member_id,
        rating=review.rating,
        title=review.title,
        comment=review.comment
    )
    db.add(new_review)
    db.commit()
    
    return new_review


@router.get("/marketplace/sellers/{seller_id}/reviews")
def seller_reviews(seller_id: str, db: Session = Depends(get_db)):
    reviews = db.query(MarketplaceReview).filter(
        MarketplaceReview.seller_member_id == seller_id
    ).order_by(MarketplaceReview.created_at.desc()).all()
    
    # Calculate average
    total = len(reviews)
    avg_rating = sum(int(r.rating) for r in reviews) / total if total > 0 else 0
    
    return {
        "average_rating": round(avg_rating, 1),
        "total_reviews": total,
        "reviews": reviews
    }


# ============ Affiliate Endpoints ============

@router.get("/marketplace/affiliates")
def list_affiliates(status: str = "ACTIVE", db: Session = Depends(get_db), current: Member = Depends(require_member)):
    return db.query(AffiliateChama).filter(AffiliateChama.status == status).all()


@router.post("/marketplace/affiliates")
def add_affiliate(
    organization_id: str,
    commission_rate: float = 2.0,
    db: Session = Depends(get_db),
    current: Member = Depends(require_member)
):
    if current.role not in ["TREASURER", "CHAIR"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    existing = db.query(AffiliateChama).filter(
        AffiliateChama.organization_id == organization_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Already an affiliate")
    
    affiliate = AffiliateChama(
        organization_id=organization_id,
        invited_by=current.organization_id,
        commission_rate=commission_rate,
        status="ACTIVE"
    )
    db.add(affiliate)
    db.commit()
    
    return {"message": "Affiliate added", "commission_rate": commission_rate}


@router.get("/marketplace/affiliates/earnings")
def affiliate_earnings(db: Session = Depends(get_db), current: Member = Depends(require_member)):
    affiliate = db.query(AffiliateChama).filter(
        AffiliateChama.organization_id == current.organization_id
    ).first()
    
    if not affiliate:
        return {"total_earnings": 0, "pending": 0, "paid": 0}
    
    # Calculate from orders
    orders = db.query(MarketplaceOrder).filter(
        MarketplaceOrder.seller_org_id == current.organization_id,
        MarketplaceOrder.status.in_([OrderStatus.PAID, OrderStatus.DELIVERED])
    ).all()
    
    total = sum(float(o.affiliate_commission or 0) for o in orders)
    pending = sum(float(o.affiliate_commission or 0) for o in orders if o.status == OrderStatus.PAID)
    paid = total - pending
    
    return {
        "total_earnings": round(total, 2),
        "pending": round(pending, 2),
        "paid": round(paid, 2),
        "commission_rate": float(affiliate.commission_rate)
    }


# ============ Analytics ============

@router.get("/marketplace/stats")
def marketplace_stats(db: Session = Depends(get_db), current: Member = Depends(require_member)):
    # My listings
    my_listings = db.query(MarketplaceListing).filter(
        MarketplaceListing.member_id == current.id
    ).all()
    
    # My orders as buyer
    buyer_orders = db.query(MarketplaceOrder).filter(
        MarketplaceOrder.buyer_member_id == current.id
    ).all()
    
    # My orders as seller
    seller_orders = db.query(MarketplaceOrder).filter(
        MarketplaceOrder.seller_member_id == current.id
    ).all()
    
    return {
        "my_listings": {
            "active": len([l for l in my_listings if l.status == ListingStatus.ACTIVE]),
            "total": len(my_listings),
            "views": sum(int(l.views or 0) for l in my_listings)
        },
        "purchases": {
            "total": len(buyer_orders),
            "pending": len([o for o in buyer_orders if o.status == OrderStatus.PENDING]),
            "completed": len([o for o in buyer_orders if o.status == OrderStatus.DELIVERED])
        },
        "sales": {
            "total": len(seller_orders),
            "pending": len([o for o in seller_orders if o.status == OrderStatus.PAID]),
            "completed": len([o for o in seller_orders if o.status == OrderStatus.DELIVERED]),
            "earnings": sum(float(o.subtotal or 0) - float(o.platform_fee or 0) for o in seller_orders if o.status.in_([OrderStatus.PAID, OrderStatus.DELIVERED]))
        }
    }


# ============ My Items ============

@router.get("/marketplace/my/listings")
def my_listings(db: Session = Depends(get_db), current: Member = Depends(require_member)):
    return db.query(MarketplaceListing).filter(
        MarketplaceListing.member_id == current.id
    ).order_by(MarketplaceListing.created_at.desc()).all()


@router.get("/marketplace/my/favorites")
def my_favorites(db: Session = Depends(get_db), current: Member = Depends(require_member)):
    favorites = db.query(MarketplaceFavorite).filter(
        MarketplaceFavorite.member_id == current.id
    ).all()
    listing_ids = [f.listing_id for f in favorites]
    return db.query(MarketplaceListing).filter(MarketplaceListing.id.in_(listing_ids)).all()


# ============ Settings Endpoints ============

@router.get("/marketplace/settings")
def get_marketplace_settings(db: Session = Depends(get_db), current: Member = Depends(require_member)):
    """Get organization's marketplace settings"""
    settings = db.query(MarketplaceSettings).filter(
        MarketplaceSettings.organization_id == current.organization_id
    ).first()
    
    if not settings:
        return {
            "platform_fee_percent": settings.MARKETPLACE_FEE_PERCENT,
            "minimum_fee": settings.MARKETPLACE_MIN_FEE,
            "marketplace_enabled": True,
            "affiliate_enabled": True
        }
    
    return {
        "platform_fee_percent": 2.0,  # Platform default
        "chama_fee_percent": float(settings.chama_fee_percent) if settings.chama_fee_percent else 0,
        "cross_chama_premium": float(settings.cross_chama_premium) if settings.cross_chama_premium else 0,
        "minimum_fee": float(settings.minimum_fee),
        "marketplace_enabled": settings.marketplace_enabled,
        "affiliate_enabled": settings.affiliate_enabled,
        "mpesa_enabled": settings.mpesa_enabled,
        "support_email": settings.support_email,
        "support_phone": settings.support_phone
    }


@router.post("/marketplace/settings")
def update_marketplace_settings(
    platform_fee_percent: float = 0,  # 0 = use platform default
    chama_fee_percent: float = 0,
    cross_chama_premium: float = 0,
    minimum_fee: float = 10.0,
    marketplace_enabled: bool = True,
    affiliate_enabled: bool = True,
    mpesa_enabled: bool = True,
    support_email: str = None,
    support_phone: str = None,
    db: Session = Depends(get_db),
    current: Member = Depends(require_member)
):
    """Update organization's marketplace settings (Chair/Treasurer only)"""
    if current.role not in ["TREASURER", "CHAIR"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    settings = db.query(MarketplaceSettings).filter(
        MarketplaceSettings.organization_id == current.organization_id
    ).first()
    
    if settings:
        settings.platform_fee_percent = platform_fee_percent,
        settings.chama_fee_percent = chama_fee_percent,
        settings.cross_chama_premium = cross_chama_premium
        settings.minimum_fee = minimum_fee
        settings.marketplace_enabled = marketplace_enabled
        settings.affiliate_enabled = affiliate_enabled
        settings.mpesa_enabled = mpesa_enabled
        settings.support_email = support_email
        settings.support_phone = support_phone
    else:
        settings = MarketplaceSettings(
            organization_id=current.organization_id,
            platform_fee_percent=platform_fee_percent,
            minimum_fee=minimum_fee,
            marketplace_enabled=marketplace_enabled,
            affiliate_enabled=affiliate_enabled,
            mpesa_enabled=mpesa_enabled,
            support_email=support_email,
            support_phone=support_phone
        )
        db.add(settings)
    
    db.commit()
    return {"message": "Settings updated"}


def get_platform_fee_settings(db: Session) -> dict:
    from app.models.models import PlatformMarketplaceSettings
    settings = db.query(PlatformMarketplaceSettings).first()
    
    if settings:
        return {
            "platform_fee_percent": float(settings.platform_fee_percent or 2.0),
            "minimum_platform_fee": float(settings.minimum_platform_fee or 10.0)
        }
    return {
        "platform_fee_percent": 2.0,
        "minimum_platform_fee": 10.0
    }


def calculate_order_fees(db: Session, amount: float, seller_org_id: str, buyer_org_id: str, affiliate_rate: float = 0) -> dict:
    """Calculate all fees: platform fee + chama fee + affiliate commission"""
    
    # Get platform fee settings
    platform_settings = get_platform_fee_settings(db)
    
    # Get chama fee (seller's organization)
    from app.models.models import MarketplaceSettings
    chama_settings = db.query(MarketplaceSettings).filter(
        MarketplaceSettings.organization_id == seller_org_id
    ).first()
    
    chama_fee_percent = float(chama_settings.chama_fee_percent) if chama_settings and chama_settings.chama_fee_percent else 0
    
    # Calculate fees
    platform_fee = max(amount * (platform_settings["platform_fee_percent"] / 100), platform_settings["minimum_platform_fee"])
    chama_fee = amount * (chama_fee_percent / 100) if chama_fee_percent else 0
    affiliate_commission = amount * (affiliate_rate / 100) if affiliate_rate else 0
    
    seller_net = amount - platform_fee - chama_fee - affiliate_commission
    
    return {
        "subtotal": amount,
        "platform_fee": round(platform_fee, 2),
        "chama_fee": round(chama_fee, 2),
        "affiliate_commission": round(affiliate_commission, 2),
        "seller_net": round(seller_net, 2)
    }


# ============ Platform Settings (Super Admin) ============

@router.get("/admin/marketplace/platform-settings")
def get_platform_settings(db: Session = Depends(get_db), current: Member = Depends(require_member)):
    """Get platform marketplace settings (super admin)"""
    if current.role not in ["CHAIR"]:
        raise HTTPException(status_code=403, detail="Super admin only")
    
    from app.models.models import PlatformMarketplaceSettings
    settings = db.query(PlatformMarketplaceSettings).first()
    
    if not settings:
        return {
            "platform_fee_percent": 2.0,
            "minimum_platform_fee": 10.0,
            "global_marketplace_enabled": True
        }
    
    return {
        "platform_fee_percent": float(settings.platform_fee_percent),
        "minimum_platform_fee": float(settings.minimum_platform_fee),
        "global_marketplace_enabled": settings.global_marketplace_enabled
    }


@router.post("/admin/marketplace/platform-settings")
def update_platform_settings(
    platform_fee_percent: float = 2.0,
    minimum_platform_fee: float = 10.0,
    global_marketplace_enabled: bool = True,
    db: Session = Depends(get_db),
    current: Member = Depends(require_member)
):
    """Update platform marketplace settings (super admin)"""
    if current.role not in ["CHAIR"]:
        raise HTTPException(status_code=403, detail="Super admin only")
    
    from app.models.models import PlatformMarketplaceSettings
    settings = db.query(PlatformMarketplaceSettings).first()
    
    if settings:
        settings.platform_fee_percent = platform_fee_percent
        settings.minimum_platform_fee = minimum_platform_fee
        settings.global_marketplace_enabled = global_marketplace_enabled
    else:
        settings = PlatformMarketplaceSettings(
            platform_fee_percent=platform_fee_percent,
            minimum_platform_fee=minimum_platform_fee,
            global_marketplace_enabled=global_marketplace_enabled
        )
        db.add(settings)
    
    db.commit()
    return {"message": "Platform settings updated"}


def calculate_cross_chama_fees(db: Session, amount: float, seller_org_id: str, buyer_org_id: str, affiliate_rate: float = 0) -> dict:
    """Calculate fees including cross-chama premium"""
    
    # Check if cross-chama transaction
    is_cross_chama = seller_org_id != buyer_org_id
    
    # Get platform fee settings
    platform_settings = get_platform_fee_settings(db)
    
    # Get seller chama settings
    from app.models.models import MarketplaceSettings
    chama_settings = db.query(MarketplaceSettings).filter(
        MarketplaceSettings.organization_id == seller_org_id
    ).first()
    
    # Fee percentages
    chama_fee_percent = float(chama_settings.chama_fee_percent) if chama_settings and chama_settings.chama_fee_percent else 0
    cross_chama_premium = float(chama_settings.cross_chama_premium) if chama_settings and chama_settings.cross_chama_premium else 0
    
    # Calculate fees
    platform_fee = max(amount * (platform_settings["platform_fee_percent"] / 100), platform_settings["minimum_platform_fee"])
    chama_fee = amount * (chama_fee_percent / 100) if chama_fee_percent else 0
    
    # Cross-chama premium (goes to seller chama)
    cross_chama_fee = amount * (cross_chama_premium / 100) if is_cross_chama and cross_chama_premium else 0
    
    # Affiliate commission
    affiliate_commission = amount * (affiliate_rate / 100) if affiliate_rate else 0
    
    seller_net = amount - platform_fee - chama_fee - cross_chama_fee - affiliate_commission
    
    return {
        "subtotal": amount,
        "is_cross_chama": is_cross_chama,
        "platform_fee": round(platform_fee, 2),
        "chama_fee": round(chama_fee, 2),  # Goes to seller's chama
        "cross_chama_premium": round(cross_chama_fee, 2),  # Extra for cross-chama
        "affiliate_commission": round(affiliate_commission, 2),
        "seller_net": round(seller_net, 2)
    }


# ============ Escrow & Delivery ============

@router.post("/orders/{order_id}/ship")
def ship_order(
    order_id: str,
    tracking_number: str = None,
    shipping_address: str = None,
    db: Session = Depends(get_db),
    current: Member = Depends(require_member)
):
    """Seller marks order as shipped"""
    order = db.query(MarketplaceOrder).filter(MarketplaceOrder.id == order_id).first()
    
    if not order or order.seller_id != current.id:
        raise HTTPException(status_code=404)
    
    if order.status not in [OrderStatus.PAID, OrderStatus.PROCESSING]:
        raise HTTPException(status_code=400, detail="Order not ready for shipping")
    
    order.status = OrderStatus.SHIPPED
    order.tracking_number = tracking_number
    order.shipping_address = shipping_address or order.shipping_address
    order.shipped_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Order shipped", "status": order.status}


@router.post("/orders/{order_id}/delivered")
def mark_delivered(
    order_id: str,
    db: Session = Depends(get_db),
    current: Member = Depends(require_member)
):
    """Seller marks order as delivered"""
    order = db.query(MarketplaceOrder).filter(MarketplaceOrder.id == order_id).first()
    
    if not order or order.seller_id != current.id:
        raise HTTPException(status_code=404)
    
    if order.status != OrderStatus.SHIPPED:
        raise HTTPException(status_code=400, detail="Order not shipped")
    
    order.status = OrderStatus.DELIVERED
    order.delivered_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Delivered - buyer has 7 days to confirm or dispute"}


@router.post("/orders/{order_id}/confirm")
def confirm_delivery(
    order_id: str,
    db: Session = Depends(get_db),
    current: Member = Depends(require_member)
):
    """Buyer confirms delivery - releases escrow"""
    order = db.query(MarketplaceOrder).filter(MarketplaceOrder.id == order_id).first()
    
    if not order or order.buyer_id != current.id:
        raise HTTPException(status_code=404)
    
    if order.status != OrderStatus.DELIVERED:
        raise HTTPException(status_code=400, detail="Order not delivered")
    
    # Release escrow to seller
    order.status = OrderStatus.COMPLETED
    order.escrow_status = "RELEASED"
    order.escrow_released_at = datetime.utcnow()
    order.completed_at = datetime.utcnow()
    
    # In production: Transfer funds to seller's wallet/B2C
    
    db.commit()
    
    return {"message": "Delivery confirmed - funds released to seller", "escrow_status": "RELEASED"}


@router.post("/orders/{order_id}/auto-complete")
def auto_complete_order(
    order_id: str,
    db: Session = Depends(get_db),
    current: Member = Depends(require_member)
):
    """Auto-complete order after 7 days if buyer doesn't confirm"""
    order = db.query(MarketplaceOrder).filter(MarketplaceOrder.id == order_id).first()
    
    if not order:
        raise HTTPException(status_code=404)
    
    if order.status != OrderStatus.DELIVERED:
        raise HTTPException(status_code=400, detail="Order not delivered")
    
    # Check if 7 days passed
    if order.delivered_at:
        days_since = (datetime.utcnow() - order.delivered_at).days
        if days_since < 7:
            raise HTTPException(status_code=400, detail=f"Cannot auto-complete yet. {7 - days_since} days remaining")
    
    order.status = OrderStatus.COMPLETED
    order.escrow_status = "RELEASED"
    order.escrow_released_at = datetime.utcnow()
    order.completed_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Order auto-completed - escrow released"}


# ============ Disputes ============

@router.post("/orders/{order_id}/dispute")
def open_dispute(
    order_id: str,
    reason: str,
    description: str,
    evidence_urls: str = None,  # JSON array
    db: Session = Depends(get_db),
    current: Member = Depends(require_member)
):
    """Buyer opens a dispute"""
    order = db.query(MarketplaceOrder).filter(MarketplaceOrder.id == order_id).first()
    
    if not order or order.buyer_id != current.id:
        raise HTTPException(status_code=404)
    
    if order.status not in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
        raise HTTPException(status_code=400, detail="Cannot dispute this order")
    
    dispute = Dispute(
        order_id=order_id,
        opened_by=current.id,
        reason=reason,
        description=description,
        evidence_urls=evidence_urls
    )
    db.add(dispute)
    
    order.status = OrderStatus.DISPUTED
    
    db.commit()
    
    return {"message": "Dispute opened", "dispute_id": dispute.id}


@router.get("/disputes")
def list_disputes(
    status: str = None,
    db: Session = Depends(get_db),
    current: Member = Depends(require_member)
):
    """List disputes (admin/chair only)"""
    if current.role not in ["CHAIR", "TREASURER"]:
        raise HTTPException(status_code=403)
    
    query = db.query(Dispute).filter(Dispute.order_id.in_(
        db.query(MarketplaceOrder.id).filter(MarketplaceOrder.seller_org_id == current.organization_id)
    ))
    
    if status:
        query = query.filter(Dispute.status == status)
    
    return query.order_by(Dispute.opened_at.desc()).all()


@router.get("/disputes/{dispute_id}")
def get_dispute(
    dispute_id: str,
    db: Session = Depends(get_db),
    current: Member = Depends(require_member)
):
    """Get dispute details"""
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    
    if not dispute:
        raise HTTPException(status_code=404)
    
    order = db.query(MarketplaceOrder).filter(MarketplaceOrder.id == dispute.order_id).first()
    
    # Check access
    if current.role not in ["CHAIR", "TREASURER"]:
        if order.buyer_id != current.id and order.seller_id != current.id:
            raise HTTPException(status_code=403)
    
    return {"dispute": dispute, "order": order}


@router.post("/disputes/{dispute_id}/resolve")
def resolve_dispute(
    dispute_id: str,
    resolution: str,  # REFUND, RELEASE, PARTIAL_REFUND
    resolution_notes: str = None,
    db: Session = Depends(get_db),
    current: Member = Depends(require_member)
):
    """Resolve dispute (admin only)"""
    if current.role not in ["CHAIR", "TREASURER"]:
        raise HTTPException(status_code=403)
    
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404)
    
    order = db.query(MarketplaceOrder).filter(MarketplaceOrder.id == dispute.order_id).first()
    
    # Resolve
    dispute.status = "RESOLVED"
    dispute.resolution = resolution
    dispute.resolved_by = current.id
    dispute.resolution_notes = resolution_notes
    dispute.resolved_at = datetime.utcnow()
    
    if resolution == "REFUND":
        # Refund buyer, seller doesn't get paid
        order.escrow_status = "REFUNDED"
        order.status = OrderStatus.REFUNDED
    elif resolution == "RELEASE":
        # Release to seller
        order.escrow_status = "RELEASED"
        order.escrow_released_at = datetime.utcnow()
        order.status = OrderStatus.COMPLETED
        order.completed_at = datetime.utcnow()
    elif resolution == "PARTIAL_REFUND":
        # Partial refund, rest to seller
        order.escrow_status = "RELEASED"
        order.escrow_released_at = datetime.utcnow()
        order.status = OrderStatus.COMPLETED
    
    db.commit()
    
    return {"message": f"Dispute resolved: {resolution}", "order_status": order.status}
