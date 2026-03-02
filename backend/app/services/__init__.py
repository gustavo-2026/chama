"""
Services Package
Modular service layer for future microservices architecture
"""
from app.services.core import (
    MemberService,
    ContributionService,
    LoanService,
    TreasuryService,
    ProposalService
)

from app.services.marketplace import (
    ListingService,
    OrderService,
    FeeService,
    ReviewService,
    AffiliateService
)

from app.services.payments import (
    PaymentProvider,
    PaymentService,
    MpesaService,
    EscrowService,
    RefundService
)

from app.services.notifications import (
    NotificationChannel,
    NotificationService,
    TransactionalNotifications,
    BatchNotificationService
)

__all__ = [
    # Core
    "MemberService",
    "ContributionService",
    "LoanService",
    "TreasuryService",
    "ProposalService",
    
    # Marketplace
    "ListingService",
    "OrderService",
    "FeeService",
    "ReviewService",
    "AffiliateService",
    
    # Payments
    "PaymentProvider",
    "PaymentService",
    "MpesaService",
    "EscrowService",
    "RefundService",
    
    # Notifications
    "NotificationChannel",
    "NotificationService",
    "TransactionalNotifications",
    "BatchNotificationService"
]


# Service locator for dependency injection
class ServiceLocator:
    """Simple service locator for future microservice migration"""
    
    _services = {}
    
    @classmethod
    def register(cls, name: str, service):
        cls._services[name] = service
    
    @classmethod
    def get(cls, name: str):
        return cls._services.get(name)
    
    @classmethod
    def init(cls, db):
        """Initialize with database session"""
        # Register services with db session
        cls.register("members", MemberService)
        cls.register("contributions", ContributionService)
        cls.register("loans", LoanService)
        cls.register("treasury", TreasuryService)
        cls.register("proposals", ProposalService)
        cls.register("marketplace.listing", ListingService)
        cls.register("marketplace.order", OrderService)
        cls.register("marketplace.fees", FeeService)
        cls.register("payments", PaymentService)
        cls.register("payments.mpesa", MpesaService)
        cls.register("payments.escrow", EscrowService)
        cls.register("notifications", NotificationService)


# Quick access aliases
services = ServiceLocator
