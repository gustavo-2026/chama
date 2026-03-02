"""
Wallet System
"""
from sqlalchemy import Column, String, DateTime, Text, Numeric, Integer, Boolean, ForeignKey
from sqlalchemy.sql import func
from app.db.database import Base


class Wallet(Base):
    __tablename__ = "wallets"
    
    id = Column(String, primary_key=True, default=lambda: f"wal_{func.random(16)}")
    
    owner_id = Column(String, nullable=False)  # member_id or organization_id
    owner_type = Column(String, nullable=False)  # member, organization
    
    balance = Column(Numeric(12, 2), default=0)
    reserved = Column(Numeric(12, 2), default=0)  # Pending transactions
    
    # M-Pesa linked
    mpesa_phone = Column(String)
    is_verified = Column(Boolean, default=False)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"
    
    id = Column(String, primary_key=True, default=lambda: f"wtx_{func.random(16)}")
    
    wallet_id = Column(String, ForeignKey("wallets.id"), nullable=False)
    
    # Transaction
    transaction_type = Column(String, nullable=False)  # DEPOSIT, WITHDRAW, TRANSFER, PAYMENT, REFUND, EARNING
    amount = Column(Numeric(12, 2), nullable=False)
    fee = Column(Numeric(12, 2), default=0)
    
    # References
    reference_id = Column(String)  # Order ID, etc
    reference_type = Column(String)  # marketplace_order, etc
    
    # Status
    status = Column(String, default="PENDING")  # PENDING, COMPLETED, FAILED
    
    # Description
    description = Column(String)
    
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)


class WalletTransfer(Base):
    __tablename__ = "wallet_transfers"
    
    id = Column(String, primary_key=True, default=lambda: f"wtr_{func.random(16)}")
    
    from_wallet_id = Column(String, ForeignKey("wallets.id"), nullable=False)
    to_wallet_id = Column(String, ForeignKey("wallets.id"), nullable=False)
    
    amount = Column(Numeric(12, 2), nullable=False)
    fee = Column(Numeric(12, 2), default=0)
    
    status = Column(String, default="PENDING")
    
    note = Column(String)
    
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)
