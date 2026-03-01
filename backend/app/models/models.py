"""
Chama Backend - All Database Models
Clean, unified, well-designed model definitions
"""
from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey, Enum as SQLEnum, Integer, Numeric, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum


# ============ Enums ============

class MemberRole(str, enum.Enum):
    MEMBER = "MEMBER"
    TREASURER = "TREASURER"
    CHAIR = "CHAIR"
    AGENT = "AGENT"


class ContributionMethod(str, enum.Enum):
    CASH = "CASH"
    MPESA = "MPESA"
    BANK = "BANK"


class TransactionStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class LoanStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ACTIVE = "ACTIVE"
    PAID = "PAID"


class ProposalStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    VOTING = "VOTING"
    PASSED = "PASSED"
    REJECTED = "REJECTED"


class AssetCategory(str, enum.Enum):
    CASH = "CASH"
    BANK_ACCOUNT = "BANK_ACCOUNT"
    MOBILE_MONEY = "MOBILE_MONEY"
    PROPERTY = "PROPERTY"
    EQUIPMENT = "EQUIPMENT"
    INVESTMENT = "INVESTMENT"
    OTHER = "OTHER"


class AssetStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    DISPOSED = "DISPOSED"
    IMPAIRED = "IMPAIRED"


class InvestmentType(str, enum.Enum):
    FIXED_DEPOSIT = "FIXED_DEPOSIT"
    TREASURY_BILL = "TREASURY_BILL"
    BOND = "BOND"
    SACCO_SHARES = "SACCO_SHARES"
    STOCK = "STOCK"
    PROPERTY = "PROPERTY"
    OTHER = "OTHER"


class InvestmentStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    MATURED = "MATURED"
    CLOSED = "CLOSED"


class FederationStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    PENDING = "PENDING"


class InterChamaLoanStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    REPAID = "REPAID"
    DEFAULTED = "DEFAULTED"


class NotificationType(str, enum.Enum):
    GENERAL = "GENERAL"
    KUDOS = "KUDOS"
    LOAN_APPROVED = "LOAN_APPROVED"
    LOAN_DUE = "LOAN_DUE"
    CONTRIBUTION_REMINDER = "CONTRIBUTION_REMINDER"
    MEETING_REMINDER = "MEETING_REMINDER"
    PROPOSAL = "PROPOSAL"
    ANNOUNCEMENT = "ANNOUNCEMENT"


class NotificationChannel(str, enum.Enum):
    IN_APP = "IN_APP"
    SMS = "SMS"
    EMAIL = "EMAIL"
    PUSH = "PUSH"


# ============ Core Models ============

class Organization(Base):
    __tablename__ = "organizations"
    
    id = Column(String, primary_key=True, default=lambda: "org_" + secrets.token_hex(8))
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    phone = Column(String, nullable=False)
    email = Column(String)
    logo_url = Column(String)
    primary_color = Column(String, default="#7C3AED")
    shortcode = Column(String)
    mpesa_env = Column(String, default="sandbox")
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    members = relationship("Member", back_populates="organization")
    contributions = relationship("Contribution", back_populates="organization")
    loans = relationship("Loan", back_populates="organization")
    proposals = relationship("Proposal", back_populates="organization")


class Member(Base):
    __tablename__ = "members"
    
    id = Column(String, primary_key=True, default=lambda: "mem_" + secrets.token_hex(8))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    user_id = Column(String)  # Can store password hash or external auth ID
    phone = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=True)
    role = Column(SQLEnum(MemberRole), default=MemberRole.MEMBER)
    contribution_tier = Column(String, default="regular")
    mpesa_linked = Column(Boolean, default=False)
    mpesa_phone = Column(String)
    
    # Profile fields
    bio = Column(Text, nullable=True)
    date_of_birth = Column(String, nullable=True)
    gender = Column(String, nullable=True)  # male, female, other
    location = Column(String, nullable=True)
    occupation = Column(String, nullable=True)
    emergency_contact_name = Column(String, nullable=True)
    emergency_contact_phone = Column(String, nullable=True)
    profile_photo_url = Column(String, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    
    organization = relationship("Organization", back_populates="members")
    contributions = relationship("Contribution", back_populates="member")
    loans = relationship("Loan", back_populates="member")


class Contribution(Base):
    __tablename__ = "contributions"
    
    id = Column(String, primary_key=True, default=lambda: "con_" + secrets.token_hex(8))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    member_id = Column(String, ForeignKey("members.id"), nullable=False)
    amount = Column(String, nullable=False)
    method = Column(SQLEnum(ContributionMethod), default=ContributionMethod.CASH)
    status = Column(SQLEnum(TransactionStatus), default=TransactionStatus.PENDING)
    mpesa_receipt = Column(String)
    period_month = Column(String)
    period_year = Column(String)
    note = Column(String)
    
    created_at = Column(DateTime, server_default=func.now())
    
    member = relationship("Member", back_populates="contributions")
    organization = relationship("Organization", back_populates="contributions")


class Loan(Base):
    __tablename__ = "loans"
    
    id = Column(String, primary_key=True, default=lambda: "lon_" + secrets.token_hex(8))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    member_id = Column(String, ForeignKey("members.id"), nullable=False)
    amount = Column(String, nullable=False)
    interest_rate = Column(String, default="10.00")
    status = Column(SQLEnum(LoanStatus), default=LoanStatus.PENDING)
    purpose = Column(String)
    
    created_at = Column(DateTime, server_default=func.now())
    approved_at = Column(DateTime)
    due_date = Column(DateTime)
    
    member = relationship("Member", back_populates="loans")
    organization = relationship("Organization", back_populates="loans")


class LoanRepayment(Base):
    __tablename__ = "loan_repayments"
    
    id = Column(String, primary_key=True, default=lambda: f"rep_{func.random(16)}")
    loan_id = Column(String, ForeignKey("loans.id"), nullable=False)
    member_id = Column(String, ForeignKey("members.id"), nullable=False)
    amount = Column(String, nullable=False)
    method = Column(SQLEnum(ContributionMethod), default=ContributionMethod.CASH)
    status = Column(SQLEnum(TransactionStatus), default=TransactionStatus.PENDING)
    note = Column(String)
    
    created_at = Column(DateTime, server_default=func.now())


class Proposal(Base):
    __tablename__ = "proposals"
    
    id = Column(String, primary_key=True, default=lambda: "prp_" + secrets.token_hex(8))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    proposal_type = Column(String, nullable=False)
    status = Column(SQLEnum(ProposalStatus), default=ProposalStatus.DRAFT)
    
    created_at = Column(DateTime, server_default=func.now())
    voting_starts = Column(DateTime)
    voting_ends = Column(DateTime)
    
    organization = relationship("Organization", back_populates="proposals")


class Vote(Base):
    __tablename__ = "votes"
    
    id = Column(String, primary_key=True, default=lambda: f"vot_{func.random(16)}")
    proposal_id = Column(String, ForeignKey("proposals.id"), nullable=False)
    member_id = Column(String, ForeignKey("members.id"), nullable=False)
    choice = Column(String, nullable=False)  # yes, no, abstain
    
    created_at = Column(DateTime, server_default=func.now())


# ============ Extended Models ============

class Meeting(Base):
    __tablename__ = "meetings"
    
    id = Column(String, primary_key=True, default=lambda: f"mtg_{func.random(16)}")
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String)
    meeting_type = Column(String, default="regular")
    scheduled_at = Column(DateTime, nullable=False)
    location = Column(String)
    agenda = Column(Text)
    
    created_at = Column(DateTime, server_default=func.now())


class Attendance(Base):
    __tablename__ = "attendance"
    
    id = Column(String, primary_key=True, default=lambda: f"att_{func.random(16)}")
    meeting_id = Column(String, ForeignKey("meetings.id"), nullable=False)
    member_id = Column(String, ForeignKey("members.id"), nullable=False)
    status = Column(String, default="present")  # present, absent, late
    check_in_time = Column(DateTime)
    
    created_at = Column(DateTime, server_default=func.now())


class Announcement(Base):
    __tablename__ = "announcements"
    
    id = Column(String, primary_key=True, default=lambda: f"ann_{func.random(16)}")
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    author_id = Column(String, ForeignKey("members.id"), nullable=False)
    
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    priority = Column(String, default="normal")  # low, normal, high, urgent
    target_all = Column(Boolean, default=True)
    target_roles = Column(String)  # comma-separated roles
    
    is_published = Column(Boolean, default=False)
    published_at = Column(DateTime)
    expires_at = Column(DateTime)
    
    created_at = Column(DateTime, server_default=func.now())


class AnnouncementRead(Base):
    __tablename__ = "announcement_reads"
    
    id = Column(String, primary_key=True, default=lambda: f"ar_{func.random(16)}")
    announcement_id = Column(String, ForeignKey("announcements.id"), nullable=False)
    member_id = Column(String, ForeignKey("members.id"), nullable=False)
    read_at = Column(DateTime, server_default=func.now())


class MeetingNotice(Base):
    __tablename__ = "meeting_notices"
    
    id = Column(String, primary_key=True, default=lambda: f"mn_{func.random(16)}")
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    meeting_id = Column(String, ForeignKey("meetings.id"))
    author_id = Column(String, ForeignKey("members.id"), nullable=False)
    
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    meeting_title = Column(String)
    meeting_date = Column(DateTime)
    location = Column(String)
    reminder_before = Column(Integer, default=60)  # minutes
    
    sent = Column(Boolean, default=False)
    sent_at = Column(DateTime)
    
    created_at = Column(DateTime, server_default=func.now())


class LoanGuarantor(Base):
    __tablename__ = "loan_guarantors"
    
    id = Column(String, primary_key=True, default=lambda: f"lg_{func.random(16)}")
    loan_id = Column(String, ForeignKey("loans.id"), nullable=False)
    member_id = Column(String, ForeignKey("members.id"), nullable=False)
    amount_guaranteed = Column(String, nullable=False)
    status = Column(String, default="PENDING")  # PENDING, APPROVED, REJECTED
    responded_at = Column(DateTime)
    
    created_at = Column(DateTime, server_default=func.now())


# ============ Financial Models ============

class BudgetCategory(Base):
    __tablename__ = "budget_categories"
    
    id = Column(String, primary_key=True, default=lambda: f"bc_{func.random(16)}")
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)
    
    created_at = Column(DateTime, server_default=func.now())


class Budget(Base):
    __tablename__ = "budgets"
    
    id = Column(String, primary_key=True, default=lambda: f"bud_{func.random(16)}")
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    year = Column(String, nullable=False)
    month = Column(String, nullable=False)
    category_id = Column(String, ForeignKey("budget_categories.id"), nullable=False)
    category = Column(String, nullable=False)
    planned = Column(Numeric(12, 2), nullable=False)
    actual = Column(Numeric(12, 2), default=0)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Expense(Base):
    __tablename__ = "expenses"
    
    id = Column(String, primary_key=True, default=lambda: f"exp_{func.random(16)}")
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    member_id = Column(String, ForeignKey("members.id"), nullable=False)
    category_id = Column(String, ForeignKey("budget_categories.id"))
    description = Column(String, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    receipt_url = Column(String)
    date = Column(DateTime, server_default=func.now())
    approved = Column(String, default="PENDING")
    approved_by = Column(String)
    approved_at = Column(DateTime)
    
    created_at = Column(DateTime, server_default=func.now())


class Asset(Base):
    __tablename__ = "assets"
    
    id = Column(String, primary_key=True, default=lambda: f"ast_{func.random(16)}")
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)
    category = Column(SQLEnum(AssetCategory), nullable=False)
    status = Column(SQLEnum(AssetStatus), default=AssetStatus.ACTIVE)
    purchase_date = Column(DateTime)
    purchase_value = Column(Numeric(12, 2), default=0)
    current_value = Column(Numeric(12, 2), default=0)
    depreciation_rate = Column(Numeric(5, 2), default=0)
    location = Column(String)
    serial_number = Column(String)
    notes = Column(Text)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class AssetValuation(Base):
    __tablename__ = "asset_valuations"
    
    id = Column(String, primary_key=True, default=lambda: f"val_{func.random(16)}")
    asset_id = Column(String, ForeignKey("assets.id"), nullable=False)
    value = Column(Numeric(12, 2), nullable=False)
    valuation_date = Column(DateTime, server_default=func.now())
    notes = Column(String)
    
    created_at = Column(DateTime, server_default=func.now())


class Investment(Base):
    __tablename__ = "investments"
    
    id = Column(String, primary_key=True, default=lambda: f"inv_{func.random(16)}")
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    name = Column(String, nullable=False)
    investment_type = Column(SQLEnum(InvestmentType), nullable=False)
    status = Column(SQLEnum(InvestmentStatus), default=InvestmentStatus.ACTIVE)
    principal = Column(Numeric(12, 2), nullable=False)
    current_value = Column(Numeric(12, 2), default=0)
    expected_return = Column(Numeric(5, 2), default=0)
    actual_return = Column(Numeric(5, 2), default=0)
    investment_date = Column(DateTime, nullable=False)
    maturity_date = Column(DateTime)
    closed_date = Column(DateTime)
    institution = Column(String)
    account_number = Column(String)
    notes = Column(Text)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class InvestmentReturn(Base):
    __tablename__ = "investment_returns"
    
    id = Column(String, primary_key=True, default=lambda: f"ret_{func.random(16)}")
    investment_id = Column(String, ForeignKey("investments.id"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    return_type = Column(String, default="INTEREST")
    return_date = Column(DateTime, server_default=func.now())
    notes = Column(String)
    
    created_at = Column(DateTime, server_default=func.now())


# ============ Federation & Inter-chama Models ============

class Federation(Base):
    __tablename__ = "federations"
    
    id = Column(String, primary_key=True, default=lambda: f"fed_{func.random(16)}")
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    description = Column(Text)
    region = Column(String)
    allow_inter_lending = Column(Boolean, default=True)
    shared_interest_rate = Column(String, default="8.00")
    status = Column(SQLEnum(FederationStatus), default=FederationStatus.PENDING)
    
    created_at = Column(DateTime, server_default=func.now())


class FederationMember(Base):
    __tablename__ = "federation_members"
    
    id = Column(String, primary_key=True, default=lambda: f"fm_{func.random(16)}")
    federation_id = Column(String, ForeignKey("federations.id"), nullable=False)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    role = Column(String, default="MEMBER")
    joined_at = Column(DateTime, server_default=func.now())
    is_active = Column(Boolean, default=True)


class FederationTreasury(Base):
    __tablename__ = "federation_treasury"
    
    id = Column(String, primary_key=True, default=lambda: f"ft_{func.random(16)}")
    federation_id = Column(String, ForeignKey("federations.id"), nullable=False)
    total_shares = Column(String, default="0")
    total_value = Column(String, default="0")
    interest_earned = Column(String, default="0")
    
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class InterChamaLoan(Base):
    __tablename__ = "inter_chama_loans"
    
    id = Column(String, primary_key=True, default=lambda: f"icl_{func.random(16)}")
    lender_organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    borrower_organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    federation_id = Column(String, ForeignKey("federations.id"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    interest_rate = Column(Numeric(5, 2), default="8.00")
    status = Column(SQLEnum(InterChamaLoanStatus), default=InterChamaLoanStatus.PENDING)
    purpose = Column(String)
    approved_by = Column(String)
    approved_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    disbursed_at = Column(DateTime)
    due_date = Column(DateTime)
    fully_repaid_at = Column(DateTime)


class InterChamaRepayment(Base):
    __tablename__ = "inter_chama_repayments"
    
    id = Column(String, primary_key=True, default=lambda: f"icr_{func.random(16)}")
    loan_id = Column(String, ForeignKey("inter_chama_loans.id"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    principal = Column(Numeric(12, 2), nullable=False)
    interest = Column(Numeric(12, 2), nullable=False)
    paid_by = Column(String, ForeignKey("members.id"), nullable=False)
    paid_at = Column(DateTime, server_default=func.now())
    note = Column(String)


# ============ Security Models ============

class LoginHistory(Base):
    __tablename__ = "login_history"
    
    id = Column(String, primary_key=True, default=lambda: f"lh_{func.random(16)}")
    member_id = Column(String, ForeignKey("members.id"), nullable=False)
    ip_address = Column(String)
    user_agent = Column(String)
    device_info = Column(String)
    location = Column(String)
    success = Column(Boolean, default=True)
    failure_reason = Column(String)
    
    created_at = Column(DateTime, server_default=func.now())


class TwoFactorSetting(Base):
    __tablename__ = "two_factor_settings"
    
    id = Column(String, primary_key=True, default=lambda: f"2fa_{func.random(16)}")
    member_id = Column(String, ForeignKey("members.id"), nullable=False, unique=True)
    enabled = Column(Boolean, default=False)
    secret = Column(String)
    backup_codes = Column(String)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(String, primary_key=True, default=lambda: f"key_{func.random(16)}")
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    name = Column(String, nullable=False)
    key_hash = Column(String, nullable=False)
    prefix = Column(String, nullable=False)
    permissions = Column(String, default="read")
    expires_at = Column(DateTime)
    last_used = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, server_default=func.now())


class IPWhitelist(Base):
    __tablename__ = "ip_whitelist"
    
    id = Column(String, primary_key=True, default=lambda: f"ip_{func.random(16)}")
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    ip_address = Column(String, nullable=False)
    description = Column(String)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(String, primary_key=True, default=lambda: f"log_{func.random(16)}")
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    member_id = Column(String, ForeignKey("members.id"), nullable=False)
    action = Column(String, nullable=False)
    resource = Column(String, nullable=False)
    resource_id = Column(String)
    changes = Column(JSON)
    details = Column(Text)
    ip_address = Column(String)
    user_agent = Column(String)
    
    created_at = Column(DateTime, server_default=func.now())


# ============ Notification Models ============

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(String, primary_key=True, default=lambda: f"notif_{func.random(16)}")
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    member_id = Column(String, ForeignKey("members.id"), nullable=True)  # null for broadcast
    
    type = Column(SQLEnum(NotificationType), default=NotificationType.GENERAL)
    channel = Column(SQLEnum(NotificationChannel), default=NotificationChannel.IN_APP)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime)
    
    created_at = Column(DateTime, server_default=func.now())


class PushToken(Base):
    __tablename__ = "push_tokens"
    
    id = Column(String, primary_key=True, default=lambda: f"pt_{func.random(16)}")
    member_id = Column(String, ForeignKey("members.id"), nullable=False)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    token = Column(String, nullable=False)
    device_type = Column(String, default="ios")
    device_name = Column(String)
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime, server_default=func.now())
    
    created_at = Column(DateTime, server_default=func.now())


class PushNotification(Base):
    __tablename__ = "push_notifications"
    
    id = Column(String, primary_key=True, default=lambda: f"pn_{func.random(16)}")
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    data = Column(JSON)
    target = Column(String, default="all")
    target_id = Column(String)
    sent = Column(Boolean, default=False)
    sent_at = Column(DateTime)
    scheduled_for = Column(DateTime)
    
    created_at = Column(DateTime, server_default=func.now())


class ScheduledReport(Base):
    __tablename__ = "scheduled_reports"
    
    id = Column(String, primary_key=True, default=lambda: f"sr_{func.random(16)}")
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    name = Column(String, nullable=False)
    report_type = Column(String, nullable=False)
    frequency = Column(String, nullable=False)
    day_of_week = Column(String)
    day_of_month = Column(String)
    recipients = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    last_sent = Column(DateTime)
    next_send = Column(DateTime)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# ============ Platform Models ============

class SuperAdmin(Base):
    __tablename__ = "super_admins"
    
    id = Column(String, primary_key=True, default=lambda: f"sa_{func.random(16)}")
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, default="SUPER_ADMIN")
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    
    created_at = Column(DateTime, server_default=func.now())


class PlatformSettings(Base):
    __tablename__ = "platform_settings"
    
    id = Column(String, primary_key=True, default=lambda: f"ps_{func.random(16)}")
    key = Column(String, unique=True, nullable=False)
    value = Column(Text)
    description = Column(String)
    
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class ChamaTemplate(Base):
    __tablename__ = "chama_templates"
    
    id = Column(String, primary_key=True, default=lambda: f"tpl_{func.random(16)}")
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    description = Column(Text)
    category = Column(String, default="general")
    settings = Column(JSON, default=dict)
    features = Column(JSON, default=dict)
    primary_color = Column(String, default="#7C3AED")
    logo_url = Column(String)
    is_public = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    usage_count = Column(String, default="0")
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# ============ Additional Models ============

class StandingOrder(Base):
    __tablename__ = "standing_orders"
    
    id = Column(String, primary_key=True, default=lambda: f"so_{func.random(16)}")
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    member_id = Column(String, ForeignKey("members.id"), nullable=False)
    amount = Column(String, nullable=False)
    frequency = Column(String, nullable=False)  # weekly, biweekly, monthly
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
    last_executed = Column(DateTime)
    next_execution = Column(DateTime)
    
    created_at = Column(DateTime, server_default=func.now())


class NextOfKin(Base):
    __tablename__ = "next_of_kin"
    
    id = Column(String, primary_key=True, default=lambda: f"nok_{func.random(16)}")
    member_id = Column(String, ForeignKey("members.id"), nullable=False)
    name = Column(String, nullable=False)
    relationship = Column(String, nullable=False)
    phone = Column(String)
    email = Column(String)
    address = Column(Text)
    
    created_at = Column(DateTime, server_default=func.now())


class Fine(Base):
    __tablename__ = "fines"
    
    id = Column(String, primary_key=True, default=lambda: f"fine_{func.random(16)}")
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    member_id = Column(String, ForeignKey("members.id"), nullable=False)
    amount = Column(String, nullable=False)
    reason = Column(String, nullable=False)
    status = Column(String, default="PENDING")  # PENDING, PAID, WAIVED
    paid_at = Column(DateTime)
    waived_at = Column(DateTime)
    waived_by = Column(String)
    
    created_at = Column(DateTime, server_default=func.now())


# Export all for easy importing
__all__ = [
    # Enums
    "MemberRole", "ContributionMethod", "TransactionStatus", "LoanStatus", "ProposalStatus",
    "AssetCategory", "AssetStatus", "InvestmentType", "InvestmentStatus",
    "FederationStatus", "InterChamaLoanStatus",
    
    # Core
    "Organization", "Member", "Contribution", "Loan", "LoanRepayment", "Proposal",
    
    # Extended
    "Meeting", "Attendance", "Announcement", "AnnouncementRead", "MeetingNotice", "LoanGuarantor",
    
    # Financial
    "BudgetCategory", "Budget", "Expense", "Asset", "AssetValuation", "Investment", "InvestmentReturn",
    
    # Federation
    "Federation", "FederationMember", "FederationTreasury", "InterChamaLoan", "InterChamaRepayment",
    
    # Security
    "LoginHistory", "TwoFactorSetting", "APIKey", "IPWhitelist", "AuditLog",
    
    # Notifications
    "PushToken", "PushNotification", "ScheduledReport",
    
    # Platform
    "SuperAdmin", "PlatformSettings", "ChamaTemplate",
    
    # Additional
    "StandingOrder", "NextOfKin", "Fine",
]


# ============ ID Generator ============
import secrets

def generate_id(prefix: str) -> str:
    """Generate a unique ID with prefix"""
    return f"{prefix}_{secrets.token_hex(8)}"


# ============ Marketplace Settings ============

class MarketplaceSettings(Base):
    __tablename__ = "marketplace_settings"
    
    id = Column(String, primary_key=True, default=lambda: f"mks_{func.random(16)}")
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False, unique=True)
    
    # Fee settings
    platform_fee_percent = Column(Numeric(5, 2), default=2.0)  # Platform fee
    chama_fee_percent = Column(Numeric(5, 2), default=0)  # Chama fee
    minimum_fee = Column(Numeric(10, 2), default=10.0)
    
    # Features
    marketplace_enabled = Column(Boolean, default=True)
    affiliate_enabled = Column(Boolean, default=True)
    
    # Payment settings
    mpesa_enabled = Column(Boolean, default=True)
    
    # Contact
    support_email = Column(String)
    support_phone = Column(String)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# ============ Platform Marketplace Settings ============

class PlatformMarketplaceSettings(Base):
    __tablename__ = "platform_marketplace_settings"
    
    id = Column(String, primary_key=True, default=lambda: f"pms_{func.random(16)}")
    
    # Platform fee (goes to platform)
    platform_fee_percent = Column(Numeric(5, 2), default=2.0)  # Platform fee
    chama_fee_percent = Column(Numeric(5, 2), default=0)  # Chama fee
    minimum_platform_fee = Column(Numeric(10, 2), default=10.0)
    
    # Global settings
    global_marketplace_enabled = Column(Boolean, default=True)
    max_listing_images = Column(Integer, default=5)
    
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
