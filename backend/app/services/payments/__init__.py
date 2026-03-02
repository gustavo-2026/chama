"""
Payments Service Interface
Future microservice: payments-service
"""
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
import requests


class PaymentProvider:
    """Payment method abstraction"""
    MPESA = "mpesa"
    PESAPAL = "pesapal"
    WALLET = "wallet"


class PaymentService:
    """Unified payment operations"""
    
    @staticmethod
    def process_payment(db: Session, provider: str, amount: float, reference: str, **kwargs):
        """Route payment to appropriate provider"""
        if provider == PaymentProvider.MPESA:
            return PaymentService._mpesa_payment(amount, reference, **kwargs)
        elif provider == PaymentProvider.PESAPAL:
            return PaymentService._pesapal_payment(amount, reference, **kwargs)
        elif provider == PaymentProvider.WALLET:
            return PaymentService._wallet_payment(db, amount, reference, **kwargs)
        else:
            raise ValueError(f"Unknown payment provider: {provider}")
    
    @staticmethod
    def _mpesa_payment(amount: float, reference: str, phone: str = None, **kwargs):
        """Process M-Pesa payment"""
        # This would call the M-Pesa service
        return {
            "provider": "mpesa",
            "status": "PENDING",
            "reference": reference,
            "amount": amount
        }
    
    @staticmethod
    def _pesapal_payment(amount: float, reference: str, email: str = None, **kwargs):
        """Process Pesapal payment"""
        return {
            "provider": "pesapal",
            "status": "PENDING",
            "reference": reference,
            "amount": amount
        }
    
    @staticmethod
    def _wallet_payment(db: Session, amount: float, reference: str, member_id: str, **kwargs):
        """Process wallet payment"""
        from app.models.wallet import Wallet, WalletTransaction
        
        wallet = db.query(Wallet).filter(
            Wallet.owner_id == member_id,
            Wallet.owner_type == "member"
        ).first()
        
        if not wallet:
            raise ValueError("No wallet found")
        
        available = float(wallet.balance) - float(wallet.reserved or 0)
        if available < amount:
            raise ValueError("Insufficient balance")
        
        # Create transaction
        tx = WalletTransaction(
            wallet_id=wallet.id,
            transaction_type="PAYMENT",
            amount=amount,
            reference_id=reference,
            status="COMPLETED",
            completed_at=datetime.utcnow()
        )
        db.add(tx)
        
        wallet.balance = float(wallet.balance) - amount
        db.commit()
        
        return {
            "provider": "wallet",
            "status": "COMPLETED",
            "reference": reference,
            "amount": amount
        }


class MpesaService:
    """M-Pesa specific operations"""
    
    @staticmethod
    def initiate_stk_push(db: Session, phone: str, amount: float, reference: str):
        """Initiate STK Push"""
        from app.models.mpesa_config import MpesaConfig, MpesaTransaction
        
        config = db.query(MpesaConfig).first()
        if not config:
            raise ValueError("M-Pesa not configured")
        
        # Create pending transaction
        tx = MpesaTransaction(
            transaction_type="STK_PUSH",
            amount=str(amount),
            phone=phone,
            shortcode=config.shortcode,
            reference_id=reference,
            status="PENDING"
        )
        db.add(tx)
        db.commit()
        
        # In production, call M-Pesa API here
        return {
            "checkout_request_id": f"chk_{reference}",
            "status": "PENDING"
        }
    
    @staticmethod
    def process_callback(db: Session, checkout_id: str, mpesa_receipt: str, status: str):
        """Process M-Pesa callback"""
        from app.models.mpesa_config import MpesaTransaction
        
        tx = db.query(MpesaTransaction).filter(
            MpesaTransaction.mpesa_code == checkout_id
        ).first()
        
        if tx:
            tx.status = "COMPLETED" if status == "0" else "FAILED"
            tx.mpesa_code = mpesa_receipt
            tx.completed_at = datetime.utcnow()
            db.commit()
        
        return tx
    
    @staticmethod
    def initiate_b2c(db: Session, phone: str, amount: float, remarks: str):
        """Disburse funds to member"""
        from app.models.mpesa_config import MpesaConfig
        
        config = db.query(MpesaConfig).first()
        if not config:
            raise ValueError("M-Pesa not configured")
        
        # In production, call B2C API
        return {
            "status": "PENDING",
            "conversation_id": f"conv_{datetime.utcnow().timestamp()}"
        }


class EscrowService:
    """Escrow fund management"""
    
    @staticmethod
    def hold_funds(db: Session, order_id: str, amount: float, source: str):
        """Hold funds in escrow"""
        from app.models.wallet import Wallet, WalletTransaction
        
        # Find or create platform escrow wallet
        wallet = db.query(Wallet).filter(
            Wallet.owner_type == "platform",
            Wallet.owner_id == "escrow"
        ).first()
        
        if not wallet:
            wallet = Wallet(owner_type="platform", owner_id="escrow", balance=0)
            db.add(wallet)
            db.commit()
        
        # Create escrow transaction
        tx = WalletTransaction(
            wallet_id=wallet.id,
            transaction_type="ESCROW_HOLD",
            amount=amount,
            reference_id=order_id,
            reference_type="marketplace_order",
            status="HELD"
        )
        db.add(tx)
        
        wallet.balance = float(wallet.balance) + amount
        db.commit()
        
        return tx
    
    @staticmethod
    def release_to_seller(db: Session, order_id: str, seller_org_id: str):
        """Release escrow to seller"""
        from app.models.wallet import Wallet, WalletTransaction
        
        # Get escrow wallet
        escrow_wallet = db.query(Wallet).filter(
            Wallet.owner_type == "platform",
            Wallet.owner_id == "escrow"
        ).first()
        
        if not escrow_wallet:
            raise ValueError("No escrow wallet")
        
        # Get transaction
        tx = db.query(WalletTransaction).filter(
            WalletTransaction.reference_id == order_id,
            WalletTransaction.transaction_type == "ESCROW_HOLD"
        ).first()
        
        if not tx:
            raise ValueError("No escrow transaction found")
        
        amount = float(tx.amount)
        
        # Release to seller (in production, could be B2C or wallet credit)
        tx.status = "RELEASED"
        escrow_wallet.balance = float(escrow_wallet.balance) - amount
        
        # Create payout record
        payout_tx = WalletTransaction(
            wallet_id=escrow_wallet.id,
            transaction_type="ESCROW_RELEASE",
            amount=amount,
            reference_id=order_id,
            status="COMPLETED",
            completed_at=datetime.utcnow()
        )
        db.add(payout_tx)
        
        db.commit()
        
        return tx
    
    @staticmethod
    def refund_buyer(db: Session, order_id: str):
        """Refund buyer from escrow"""
        from app.models.wallet import Wallet, WalletTransaction
        
        escrow_wallet = db.query(Wallet).filter(
            Wallet.owner_type == "platform",
            Wallet.owner_id == "escrow"
        ).first()
        
        tx = db.query(WalletTransaction).filter(
            WalletTransaction.reference_id == order_id,
            WalletTransaction.transaction_type == "ESCROW_HOLD"
        ).first()
        
        if tx:
            amount = float(tx.amount)
            tx.status = "REFUNDED"
            escrow_wallet.balance = float(escrow_wallet.balance) - amount
            db.commit()
        
        return tx


class RefundService:
    """Refund operations"""
    
    @staticmethod
    def process_refund(db: Session, order_id: str, amount: float, reason: str):
        """Process a refund"""
        from app.models.wallet import WalletTransaction
        
        # Create refund transaction
        tx = WalletTransaction(
            wallet_id=None,  # Would be tied to buyer
            transaction_type="REFUND",
            amount=amount,
            reference_id=order_id,
            reference_type="marketplace_order",
            description=reason,
            status="COMPLETED",
            completed_at=datetime.utcnow()
        )
        db.add(tx)
        db.commit()
        
        return tx


__all__ = [
    "PaymentProvider",
    "PaymentService",
    "MpesaService",
    "EscrowService",
    "RefundService"
]
