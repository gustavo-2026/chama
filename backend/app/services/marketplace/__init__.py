"""
Marketplace Service Interface
Future microservice: marketplace-service
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session


class ListingService:
    """Marketplace listing operations"""
    
    @staticmethod
    def create_listing(db: Session, data: dict):
        from app.models.marketplace import MarketplaceListing
        listing = MarketplaceListing(**data)
        db.add(listing)
        db.commit()
        return listing
    
    @staticmethod
    def get_listing(db: Session, listing_id: str):
        from app.models.marketplace import MarketplaceListing
        return db.query(MarketplaceListing).filter(MarketplaceListing.id == listing_id).first()
    
    @staticmethod
    def search_listings(db: Session, org_id: str = None, category: str = None, query: str = None, limit: int = 50):
        from app.models.marketplace import MarketplaceListing
        q = db.query(MarketplaceListing)
        if org_id:
            q = q.filter(MarketplaceListing.organization_id == org_id)
        if category:
            q = q.filter(MarketplaceListing.category == category)
        if query:
            q = q.filter(MarketplaceListing.title.ilike(f"%{query}%"))
        return q.limit(limit).all()


class OrderService:
    """Order and escrow operations"""
    
    @staticmethod
    def create_order(db: Session, buyer_id: str, listing_id: str, data: dict):
        from app.models.marketplace import MarketplaceOrder, OrderStatus
        order = MarketplaceOrder(
            buyer_id=buyer_id,
            listing_id=listing_id,
            **data
        )
        db.add(order)
        db.commit()
        return order
    
    @staticmethod
    def get_order(db: Session, order_id: str):
        from app.models.marketplace import MarketplaceOrder
        return db.query(MarketplaceOrder).filter(MarketplaceOrder.id == order_id).first()
    
    @staticmethod
    def update_status(db: Session, order_id: str, status: str):
        from app.models.marketplace import MarketplaceOrder
        order = db.query(MarketplaceOrder).filter(MarketplaceOrder.id == order_id).first()
        if order:
            order.status = status
            db.commit()
        return order
    
    @staticmethod
    def release_escrow(db: Session, order_id: str):
        """Release funds to seller after delivery confirmed"""
        from app.models.marketplace import MarketplaceOrder, OrderStatus
        order = db.query(MarketplaceOrder).filter(MarketplaceOrder.id == order_id).first()
        if order and order.escrow_status == "HELD":
            order.escrow_status = "RELEASED"
            order.escrow_released_at = datetime.utcnow()
            order.status = OrderStatus.COMPLETED
            db.commit()
        return order
    
    @staticmethod
    def refund_escrow(db: Session, order_id: str):
        if order and order.escrow_status == "HELD":
            order.escrow_status = "REFUNDED"
            order.status = OrderStatus.REFUNDED
            db.commit()
        return order


class FeeService:
    """Fee calculation for marketplace"""
    
    @staticmethod
    def calculate_fees(db: Session, amount: float, seller_org_id: str, buyer_org_id: str = None):
        """Calculate all applicable fees"""
        from app.models.models import PlatformMarketplaceSettings, MarketplaceSettings
        
        # Platform settings
        platform_settings = db.query(PlatformMarketplaceSettings).first()
        platform_fee_pct = float(platform_settings.platform_fee_percent) if platform_settings else 2.0
        min_platform_fee = float(platform_settings.minimum_platform_fee) if platform_settings else 10.0
        
        # Seller settings
        seller_settings = db.query(MarketplaceSettings).filter(
            MarketplaceSettings.organization_id == seller_org_id
        ).first()
        
        chama_fee_pct = float(seller_settings.chama_fee_percent) if seller_settings else 0
        cross_chama_pct = float(seller_settings.cross_chama_premium) if seller_settings else 0
        
        # Check if cross-chama
        is_cross = buyer_org_id and buyer_org_id != seller_org_id
        
        # Calculate fees
        platform_fee = max(amount * (platform_fee_pct / 100), min_platform_fee)
        chama_fee = amount * (chama_fee_pct / 100)
        cross_chama_fee = amount * (cross_chama_pct / 100) if is_cross else 0
        
        return {
            "subtotal": amount,
            "platform_fee": round(platform_fee, 2),
            "chama_fee": round(chama_fee, 2),
            "cross_chama_premium": round(cross_chama_fee, 2),
            "total_fees": round(platform_fee + chama_fee + cross_chama_fee, 2),
            "seller_net": round(amount - platform_fee - chama_fee - cross_chama_fee, 2)
        }


class ReviewService:
    """Review and rating operations"""
    
    @staticmethod
    def create_review(db: Session, order_id: str, reviewer_id: str, rating: int, comment: str = None):
        from app.models.marketplace import MarketplaceReview
        review = MarketplaceReview(
            order_id=order_id,
            reviewer_id=reviewer_id,
            rating=rating,
            comment=comment
        )
        db.add(review)
        db.commit()
        return review
    
    @staticmethod
    def get_listing_reviews(db: Session, listing_id: str):
        from app.models.marketplace import MarketplaceReview
        return db.query(MarketplaceReview).filter(MarketplaceReview.listing_id == listing_id).all()
    
    @staticmethod
    def get_average_rating(db: Session, listing_id: str):
        from app.models.marketplace import MarketplaceReview
        reviews = db.query(MarketplaceReview).filter(MarketplaceReview.listing_id == listing_id).all()
        if not reviews:
            return 0
        return sum(r.rating for r in reviews) / len(reviews)


class AffiliateService:
    """Affiliate/chama commission operations"""
    
    @staticmethod
    def create_affiliate_link(db: Session, listing_id: str, affiliate_org_id: str, commission_pct: float = 2.0):
        from app.models.marketplace import AffiliateChama
        affiliate = AffiliateChama(
            listing_id=listing_id,
            affiliate_org_id=affiliate_org_id,
            commission_percent=commission_pct
        )
        db.add(affiliate)
        db.commit()
        return affiliate
    
    @staticmethod
    def track_sale(db: Session, order_id: str, affiliate_org_id: str):
        """Track affiliate sale for commission"""
        from app.models.marketplace import AffiliatePayout
        from app.models.marketplace import MarketplaceOrder
        
        order = db.query(MarketplaceOrder).filter(MarketplaceOrder.id == order_id).first()
        if order and order.affiliate_org_id == affiliate_org_id:
            commission = float(order.affiliate_commission or 0)
            payout = AffiliatePayout(
                order_id=order_id,
                affiliate_org_id=affiliate_org_id,
                amount=commission,
                status="PENDING"
            )
            db.add(payout)
            db.commit()
        return payout


# Export
__all__ = [
    "ListingService",
    "OrderService",
    "FeeService", 
    "ReviewService",
    "AffiliateService"
]
