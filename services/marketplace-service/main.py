"""
Marketplace Service
Microservice for listings, orders, reviews, escrow
"""
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Numeric, Integer, DateTime, Text
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker, declarative_base
from enum import Enum
import os
import jwt

app = FastAPI(title="Marketplace Service")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:5432/chama")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============ Models ============

class MarketplaceCategory(str, Enum):
    PRODUCTS = "PRODUCTS"
    SERVICES = "SERVICES"
    JOBS = "JOBS"
    HOUSING = "HOUSING"


class ListingStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SOLD = "SOLD"
    HIDDEN = "HIDDEN"


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    COMPLETED = "COMPLETED"
    DISPUTED = "DISPUTED"
    REFUNDED = "REFUNDED"


class Listing(Base):
    __tablename__ = "marketplace_listings"
    id = Column(String, primary_key=True)
    organization_id = Column(String)
    member_id = Column(String)
    title = Column(String)
    description = Column(Text)
    category = Column(String)
    price = Column(Numeric)
    status = Column(String, default="ACTIVE")
    images = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class Order(Base):
    __tablename__ = "marketplace_orders"
    id = Column(String, primary_key=True)
    buyer_id = Column(String)
    buyer_org_id = Column(String)
    seller_id = Column(String)
    seller_org_id = Column(String)
    listing_id = Column(String)
    amount = Column(Numeric)
    platform_fee = Column(Numeric, default=0)
    chama_fee = Column(Numeric, default=0)
    total = Column(Numeric)
    status = Column(String, default="PENDING")
    escrow_status = Column(String, default="HELD")
    created_at = Column(DateTime, default=datetime.utcnow)


class Review(Base):
    __tablename__ = "marketplace_reviews"
    id = Column(String, primary_key=True)
    listing_id = Column(String)
    order_id = Column(String)
    reviewer_id = Column(String)
    rating = Column(Integer)
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


# ============ Pydantic Models ============

class ListingCreate(BaseModel):
    title: str
    description: str
    category: str
    price: float
    images: Optional[str] = None


class OrderCreate(BaseModel):
    listing_id: str
    quantity: int = 1


class ReviewCreate(BaseModel):
    rating: int
    comment: Optional[str] = None


# ============ Helpers ============

def get_current_member(db, authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401)
    token = authorization.replace("Bearer ", "")
    from app.core.config import settings
    try:
        payload = jwt.decode(token, "SECRET_KEY", algorithms=["HS256"])
        return {"id": payload.get("sub"), "organization_id": "org_placeholder"}
    except:
        raise HTTPException(status_code=401)


# ============ Listing Endpoints ============

@app.get("/health")
def health():
    return {"status": "healthy", "service": "marketplace"}


@app.post("/listings", response_model=dict)
def create_listing(data: ListingCreate, db: Session = Depends(get_db), member = Depends(get_current_member)):
    listing = Listing(
        id=f"lst_{datetime.utcnow().timestamp()}",
        organization_id=member.get("organization_id"),
        member_id=member["id"],
        title=data.title,
        description=data.description,
        category=data.category,
        price=data.price,
        images=data.images
    )
    db.add(listing)
    db.commit()
    return {"id": listing.id, "status": "active"}


@app.get("/listings/{listing_id}", response_model=dict)
def get_listing(listing_id: str, db: Session = Depends(get_db)):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404)
    return {
        "id": listing.id,
        "title": listing.title,
        "description": listing.description,
        "category": listing.category,
        "price": float(listing.price),
        "status": listing.status
    }


@app.get("/listings", response_model=List[dict])
def search_listings(
    category: str = None,
    org_id: str = None,
    query: str = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    q = db.query(Listing).filter(Listing.status == "ACTIVE")
    if category:
        q = q.filter(Listing.category == category)
    if org_id:
        q = q.filter(Listing.organization_id == org_id)
    if query:
        q = q.filter(Listing.title.ilike(f"%{query}%"))
    return [{"id": l.id, "title": l.title, "price": float(l.price), "category": l.category} 
            for l in q.limit(limit).all()]


# ============ Order Endpoints ============

@app.post("/orders", response_model=dict)
def create_order(data: OrderCreate, db: Session = Depends(get_db), member = Depends(get_current_member)):
    listing = db.query(Listing).filter(Listing.id == data.listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    amount = float(listing.price) * data.quantity
    platform_fee = amount * 0.02  # 2% platform fee
    total = amount + platform_fee
    
    order = Order(
        id=f"ord_{datetime.utcnow().timestamp()}",
        buyer_id=member["id"],
        buyer_org_id=member.get("organization_id"),
        seller_id=listing.member_id,
        seller_org_id=listing.organization_id,
        listing_id=listing.listing_id,
        amount=amount,
        platform_fee=platform_fee,
        total=total,
        status="PENDING"
    )
    db.add(order)
    db.commit()
    return {"id": order.id, "amount": float(order.amount), "total": float(order.total)}


@app.get("/orders/{order_id}", response_model=dict)
def get_order(order_id: str, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404)
    return {
        "id": order.id,
        "amount": float(order.amount),
        "platform_fee": float(order.platform_fee),
        "total": float(order.total),
        "status": order.status,
        "escrow_status": order.escrow_status
    }


@app.get("/orders", response_model=List[dict])
def list_orders(
    org_id: str = None,
    status: str = None,
    db: Session = Depends(get_db)
):
    q = db.query(Order)
    if org_id:
        q = q.filter((Order.buyer_org_id == org_id) | (Order.seller_org_id == org_id))
    if status:
        q = q.filter(Order.status == status)
    return [{"id": o.id, "amount": float(o.amount), "status": o.status} 
            for o in q.limit(50).all()]


# ============ Escrow Endpoints ============

@app.post("/orders/{order_id}/paid")
def mark_paid(order_id: str, mpesa_code: str = None, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404)
    order.status = "PAID"
    order.escrow_status = "HELD"
    db.commit()
    return {"status": "paid", "escrow_status": "held"}


@app.post("/orders/{order_id}/ship")
def ship_order(order_id: str, tracking: str = None, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order or order.status != "PAID":
        raise HTTPException(status_code=400)
    order.status = "SHIPPED"
    db.commit()
    return {"status": "shipped"}


@app.post("/orders/{order_id}/delivered")
def mark_delivered(order_id: str, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order or order.status != "SHIPPED":
        raise HTTPException(status_code=400)
    order.status = "DELIVERED"
    db.commit()
    return {"status": "delivered", "message": "Awaiting buyer confirmation"}


@app.post("/orders/{order_id}/confirm")
def confirm_delivery(order_id: str, db: Session = Depends(get_db)):
    """Release escrow to seller"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order or order.status != "DELIVERED":
        raise HTTPException(status_code=400)
    order.status = "COMPLETED"
    order.escrow_status = "RELELEASED"
    db.commit()
    return {"status": "completed", "escrow_status": "released", "message": "Funds released to seller"}


@app.post("/orders/{order_id}/dispute")
def open_dispute(order_id: str, reason: str, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404)
    order.status = "DISPUTED"
    order.escrow_status = "FROZEN"
    db.commit()
    return {"status": "disputed", "escrow_status": "frozen"}


# ============ Review Endpoints ============

@app.post("/reviews", response_model=dict)
def create_review(
    listing_id: str,
    order_id: str,
    data: ReviewCreate,
    db: Session = Depends(get_db),
    member=Depends(get_current_member)
):
    review = Review(
        id=f"rev_{datetime.utcnow().timestamp()}",
        listing_id=listing_id,
        order_id=order_id,
        reviewer_id=member["id"],
        rating=data.rating,
        comment=data.comment
    )
    db.add(review)
    db.commit()
    return {"id": review.id, "rating": review.rating}


@app.get("/reviews/listing/{listing_id}", response_model=List[dict])
def get_listing_reviews(listing_id: str, db: Session = Depends(get_db)):
    reviews = db.query(Review).filter(Review.listing_id == listing_id).all()
    return [{"rating": r.rating, "comment": r.comment} for r in reviews]


@app.get("/reviews/listing/{listing_id}/rating")
def get_average_rating(listing_id: str, db: Session = Depends(get_db)):
    reviews = db.query(Review).filter(Review.listing_id == listing_id).all()
    if not reviews:
        return {"average": 0, "count": 0}
    avg = sum(r.rating for r in reviews) / len(reviews)
    return {"average": round(avg, 1), "count": len(reviews)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
