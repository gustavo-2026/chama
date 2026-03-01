"""
M-Pesa Configuration Models
"""
from sqlalchemy import Column, String, DateTime, Text, Boolean, Numeric, ForeignKey
from sqlalchemy.sql import func
from app.db.database import Base


class MpesaConfig(Base):
    """Platform-wide M-Pesa configuration"""
    __tablename__ = "mpesa_config"
    
    id = Column(String, primary_key=True, default=lambda: f"mpc_{func.random(16)}")
    
    # Shortcode & Credentials
    shortcode = Column(String, nullable=False)  # Paybill/Till number
    consumer_key = Column(String, nullable=False)
    consumer_secret = Column(String, nullable=False)  # Should be encrypted
    passkey = Column(String)  # For STK Push
    
    # Environment
    environment = Column(String, default="sandbox")  # sandbox, production
    
    # Payment flow mode
    payment_mode = Column(String, default="central")  # central, chama, hybrid
    
    # Settlement settings
    auto_settle = Column(Boolean, default=True)
    settle_hours = Column(Integer, default=24)
    
    # Feature toggles
    allow_stk_push = Column(Boolean, default=True)
    allow_c2b = Column(Boolean, default=True)
    allow_b2c = Column(Boolean, default=True)
    
    # Allow chamas to use their own tills
    allow_chama_till = Column(Boolean, default=False)
    
    # Callbacks
    stk_callback_url = Column(String)
    b2c_callback_url = Column(String)
    c2b_callback_url = Column(String)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class ChamaMpesaConfig(Base):
    """Per-chama M-Pesa configuration"""
    __tablename__ = "chama_mpesa_config"
    
    id = Column(String, primary_key=True, default=lambda: f"cmc_{func.random(16)}")
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False, unique=True)
    
    # Override platform settings
    use_own_till = Column(Boolean, default=False)
    
    # Their own M-Pesa credentials (if using own)
    shortcode = Column(String)
    consumer_key = Column(String)
    consumer_secret = Column(String)
    passkey = Column(String)
    
    # Payment preferences
    prefer_own_till = Column(Boolean, default=False)
    
    # Settlement
    settlement_phone = Column(String)  # Where to receive payouts
    
    # Status
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class MpesaTransaction(Base):
    """Track all M-Pesa transactions"""
    __tablename__ = "mpesa_transactions"
    
    id = Column(String, primary_key=True, default=lambda: f"mpt_{func.random(16)}")
    
    # Transaction details
    transaction_type = Column(String, nullable=False)  # STK_PUSH, C2B, B2C
    transaction_id = Column(String, unique=True)  # M-Pesa transaction ID
    mpesa_code = Column(String)  # e.g., "LGH..."
    
    # Amounts
    amount = Column(String, nullable=False)
    callback_amount = Column(String)
    
    # Parties
    phone = Column(String, nullable=False)  # Customer phone
    shortcode = Column(String)  # Business shortcode
    
    # References
    order_id = Column(String, ForeignKey("marketplace_orders.id"))
    organization_id = Column(String, ForeignKey("organizations.id"))
    member_id = Column(String, ForeignKey("members.id"))
    
    # Status
    status = Column(String, default="PENDING")  # PENDING, COMPLETED, FAILED
    failure_reason = Column(String)
    
    # Callback data
    callback_raw = Column(Text)
    
    # Timing
    initiated_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)
