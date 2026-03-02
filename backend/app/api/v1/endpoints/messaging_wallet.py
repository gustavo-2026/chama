"""
Messaging, Subscriptions, Wallet Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import jwt

from app.db.database import get_db
from app.models import Member
from app.models.messaging import Conversation, Message, MessageAttachment
from app.models.subscriptions import SubscriptionTier, OrganizationSubscription, SubscriptionPayment
from app.models.wallet import Wallet, WalletTransaction, WalletTransfer
from app.core.config import settings

router = APIRouter()


# ============ Helpers ============

def get_member(db: Session, auth: str = Header(None)):
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401)
    token = auth.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return db.query(Member).filter(Member.id == payload.get("sub")).first()
    except:
        raise HTTPException(status_code=401)


# ============ Messaging Endpoints ============

@router.get("/messages/conversations")
def list_conversations(db: Session = Depends(get_db), current: Member = Depends(get_member)):
    """List all conversations"""
    return db.query(Conversation).filter(
        (Conversation.member1_id == current.id) | (Conversation.member2_id == current.id),
        Conversation.is_active == True
    ).order_by(Conversation.updated_at.desc()).all()


@router.post("/messages/conversations")
def create_conversation(
    member2_id: str,
    listing_id: str = None,
    order_id: str = None,
    db: Session = Depends(get_db),
    current: Member = Depends(get_member)
):
    """Start a new conversation"""
    # Check if conversation exists
    existing = db.query(Conversation).filter(
        ((Conversation.member1_id == current.id) & (Conversation.member2_id == member2_id)) |
        ((Conversation.member1_id == member2_id) & (Conversation.member2_id == current.id))
    ).first()
    
    if existing:
        return existing
    
    conv = Conversation(
        member1_id=current.id,
        member2_id=member2_id,
        listing_id=listing_id,
        order_id=order_id
    )
    db.add(conv)
    db.commit()
    return conv


@router.get("/messages/conversations/{conv_id}")
def get_conversation(conv_id: str, db: Session = Depends(get_db), current: Member = Depends(get_member)):
    """Get conversation with messages"""
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conv or (conv.member1_id != current.id and conv.member2_id != current.id):
        raise HTTPException(status_code=404)
    
    messages = db.query(Message).filter(
        Message.conversation_id == conv_id
    ).order_by(Message.created_at.asc()).all()
    
    return {"conversation": conv, "messages": messages}


@router.post("/messages/conversations/{conv_id}")
def send_message(
    conv_id: str,
    content: str,
    db: Session = Depends(get_db),
    current: Member = Depends(get_member)
):
    """Send a message"""
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conv or (conv.member1_id != current.id and conv.member2_id != current.id):
        raise HTTPException(status_code=404)
    
    msg = Message(
        conversation_id=conv_id,
        sender_id=current.id,
        content=content
    )
    db.add(msg)
    
    conv.updated_at = datetime.utcnow()
    db.commit()
    
    return msg


@router.post("/messages/conversations/{conv_id}/read")
def mark_read(conv_id: str, db: Session = Depends(get_db), current: Member = Depends(get_member)):
    """Mark messages as read"""
    db.query(Message).filter(
        Message.conversation_id == conv_id,
        Message.sender_id != current.id,
        Message.is_read == False
    ).update({"is_read": True, "read_at": datetime.utcnow()})
    db.commit()
    return {"message": "Marked as read"}


# ============ Subscription Endpoints ============

@router.get("/subscriptions/tiers")
def list_tiers(db: Session = Depends(get_db)):
    """List available subscription tiers"""
    return db.query(SubscriptionTier).filter(SubscriptionTier.is_active == True).order_by(SubscriptionTier.monthly_price.asc()).all()


@router.get("/subscriptions/current")
def current_subscription(db: Session = Depends(get_db), current: Member = Depends(get_member)):
    """Get current subscription"""
    sub = db.query(OrganizationSubscription).filter(
        OrganizationSubscription.organization_id == current.organization_id,
        OrganizationSubscription.payment_status == "ACTIVE"
    ).first()
    
    if not sub:
        # Return free tier
        return {"tier": {"name": "free", "monthly_price": 0}, "status": "active"}
    
    tier = db.query(SubscriptionTier).filter(SubscriptionTier.id == sub.tier_id).first()
    return {"subscription": sub, "tier": tier}


@router.post("/subscriptions")
def create_subscription(
    tier_id: str,
    billing_cycle: str = "monthly",
    db: Session = Depends(get_db),
    current: Member = Depends(get_member)
):
    """Subscribe to a tier"""
    if current.role not in ["CHAIR", "TREASURER"]:
        raise HTTPException(status_code=403)
    
    tier = db.query(SubscriptionTier).filter(SubscriptionTier.id == tier_id).first()
    if not tier:
        raise HTTPException(status_code=404)
    
    # Check for existing
    existing = db.query(OrganizationSubscription).filter(
        OrganizationSubscription.organization_id == current.organization_id,
        OrganizationSubscription.payment_status == "ACTIVE"
    ).first()
    
    if existing:
        existing.payment_status = "CANCELLED"
    
    # Calculate dates
    if billing_cycle == "yearly":
        price = tier.yearly_price
        end_date = datetime.utcnow() + timedelta(days=365)
    else:
        price = tier.monthly_price
        end_date = datetime.utcnow() + timedelta(days=30)
    
    sub = OrganizationSubscription(
        organization_id=current.organization_id,
        tier_id=tier_id,
        billing_cycle=billing_cycle,
        start_date=datetime.utcnow(),
        end_date=end_date,
        payment_status="ACTIVE" if float(price) == 0 else "PENDING"
    )
    db.add(sub)
    db.commit()
    
    return {"subscription": sub, "tier": tier}


# ============ Wallet Endpoints ============

@router.get("/wallet")
def get_wallet(db: Session = Depends(get_db), current: Member = Depends(get_member)):
    """Get wallet balance"""
    wallet = db.query(Wallet).filter(
        Wallet.owner_id == current.id,
        Wallet.owner_type == "member"
    ).first()
    
    if not wallet:
        wallet = Wallet(owner_id=current.id, owner_type="member")
        db.add(wallet)
        db.commit()
    
    # Get recent transactions
    transactions = db.query(WalletTransaction).filter(
        WalletTransaction.wallet_id == wallet.id
    ).order_by(WalletTransaction.created_at.desc()).limit(10).all()
    
    return {
        "wallet": wallet,
        "available": float(wallet.balance) - float(wallet.reserved or 0),
        "transactions": transactions
    }


@router.post("/wallet/deposit")
def deposit_to_wallet(
    amount: float,
    mpesa_code: str = None,
    db: Session = Depends(get_db),
    current: Member = Depends(get_member)
):
    """Deposit money to wallet (via M-Pesa)"""
    wallet = db.query(Wallet).filter(
        Wallet.owner_id == current.id,
        Wallet.owner_type == "member"
    ).first()
    
    if not wallet:
        wallet = Wallet(owner_id=current.id, owner_type="member")
        db.add(wallet)
        db.commit()
    
    # Create transaction
    tx = WalletTransaction(
        wallet_id=wallet.id,
        transaction_type="DEPOSIT",
        amount=amount,
        status="COMPLETED",
        reference_id=mpesa_code,
        description="Wallet deposit",
        completed_at=datetime.utcnow()
    )
    db.add(tx)
    
    wallet.balance = float(wallet.balance or 0) + amount
    db.commit()
    
    return {"message": "Deposit successful", "balance": wallet.balance}


@router.post("/wallet/withdraw")
def withdraw_from_wallet(
    amount: float,
    phone: str,
    db: Session = Depends(get_db),
    current: Member = Depends(get_member)
):
    """Withdraw from wallet (via M-Pesa B2C)"""
    wallet = db.query(Wallet).filter(
        Wallet.owner_id == current.id,
        Wallet.owner_type == "member"
    ).first()
    
    if not wallet:
        raise HTTPException(status_code=400, detail="No wallet")
    
    available = float(wallet.balance) - float(wallet.reserved or 0)
    if available < amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    # Create transaction
    tx = WalletTransaction(
        wallet_id=wallet.id,
        transaction_type="WITHDRAW",
        amount=amount,
        status="PENDING",
        reference_id=phone,
        description=f"Withdrawal to {phone}"
    )
    db.add(tx)
    
    wallet.balance = available - amount
    db.commit()
    
    # In production, initiate M-Pesa B2C here
    
    return {"message": "Withdrawal initiated", "balance": wallet.balance}


@router.post("/wallet/pay")
def pay_from_wallet(
    amount: float,
    order_id: str,
    db: Session = Depends(get_db),
    current: Member = Depends(get_member)
):
    """Pay for order from wallet"""
    wallet = db.query(Wallet).filter(
        Wallet.owner_id == current.id,
        Wallet.owner_type == "member"
    ).first()
    
    if not wallet:
        raise HTTPException(status_code=400, detail="No wallet")
    
    available = float(wallet.balance) - float(wallet.reserved or 0)
    if available < amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    # Reserve funds
    wallet.reserved = float(wallet.reserved or 0) + amount
    
    tx = WalletTransaction(
        wallet_id=wallet.id,
        transaction_type="PAYMENT",
        amount=amount,
        reference_id=order_id,
        reference_type="marketplace_order",
        status="COMPLETED",
        description=f"Payment for order {order_id}",
        completed_at=datetime.utcnow()
    )
    db.add(tx)
    
    # Finalize
    wallet.balance = float(wallet.balance) - amount
    wallet.reserved = float(wallet.reserved) - amount
    
    db.commit()
    
    return {"message": "Payment successful", "balance": wallet.balance}


@router.get("/wallet/transactions")
def wallet_transactions(
    limit: int = 50,
    db: Session = Depends(get_db),
    current: Member = Depends(get_member)
):
    """Get transaction history"""
    wallet = db.query(Wallet).filter(
        Wallet.owner_id == current.id,
        Wallet.owner_type == "member"
    ).first()
    
    if not wallet:
        return []
    
    return db.query(WalletTransaction).filter(
        WalletTransaction.wallet_id == wallet.id
    ).order_by(WalletTransaction.created_at.desc()).limit(limit).all()


@router.post("/wallet/link-mpesa")
def link_mpesa(phone: str, db: Session = Depends(get_db), current: Member = Depends(get_member)):
    """Link M-Pesa phone to wallet"""
    wallet = db.query(Wallet).filter(
        Wallet.owner_id == current.id,
        Wallet.owner_type == "member"
    ).first()
    
    if not wallet:
        wallet = Wallet(owner_id=current.id, owner_type="member", mpesa_phone=phone)
        db.add(wallet)
    else:
        wallet.mpesa_phone = phone
    
    db.commit()
    
    # In production, initiate STK push to verify
    
    return {"message": "M-Pesa linked", "phone": phone}
