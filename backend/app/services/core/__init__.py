"""
Core Banking Service Interface
Future microservice: core-service
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session


class MemberService:
    """Member management operations"""
    
    @staticmethod
    def create_member(db: Session, data: dict):
        from app.models import Member
        member = Member(**data)
        db.add(member)
        db.commit()
        return member
    
    @staticmethod
    def get_member(db: Session, member_id: str):
        from app.models import Member
        return db.query(Member).filter(Member.id == member_id).first()
    
    @staticmethod
    def list_members(db: Session, org_id: str, limit: int = 50):
        from app.models import Member
        return db.query(Member).filter(Member.organization_id == org_id).limit(limit).all()


class ContributionService:
    """Contribution/membership fee operations"""
    
    @staticmethod
    def create_contribution(db: Session, member_id: str, amount: float, method: str):
        from app.models import Contribution
        contrib = Contribution(
            member_id=member_id,
            amount=amount,
            method=method,
            status="COMPLETED"
        )
        db.add(contrib)
        db.commit()
        return contrib
    
    @staticmethod
    def get_member_contributions(db: Session, member_id: str):
        from app.models import Contribution
        return db.query(Contribution).filter(Contribution.member_id == member_id).all()
    
    @staticmethod
    def get_org_total(db: Session, org_id: str, start_date=None, end_date=None):
        from app.models import Contribution, Member
        query = db.query(Contribution).join(Member).filter(Member.organization_id == org_id)
        if start_date:
            query = query.filter(Contribution.created_at >= start_date)
        if end_date:
            query = query.filter(Contribution.created_at <= end_date)
        return query.all()


class LoanService:
    """Loan management operations"""
    
    @staticmethod
    def create_loan(db: Session, member_id: str, amount: float, term_months: int, purpose: str):
        from app.models import Loan
        loan = Loan(
            member_id=member_id,
            principal_amount=amount,
            term_months=term_months,
            purpose=purpose,
            status="PENDING"
        )
        db.add(loan)
        db.commit()
        return loan
    
    @staticmethod
    def approve_loan(db: Session, loan_id: str, approved_by: str):
        from app.models import Loan
        loan = db.query(Loan).filter(Loan.id == loan_id).first()
        if loan:
            loan.status = "APPROVED"
            loan.approved_by = approved_by
            loan.approved_at = datetime.utcnow()
            db.commit()
        return loan
    
    @staticmethod
    def get_loan_balance(db: Session, loan_id: str):
        from app.models import Loan, LoanRepayment
        loan = db.query(Loan).filter(Loan.id == loan_id).first()
        repayments = db.query(LoanRepayment).filter(LoanRepayment.loan_id == loan_id).all()
        paid = sum(float(r.amount) for r in repayments)
        return float(loan.principal_amount) - paid


class TreasuryService:
    """Treasury/wallet operations"""
    
    @staticmethod
    def get_org_balance(db: Session, org_id: str):
        from app.models import Contribution, Loan, LoanRepayment, Member, Expense
        # Total contributions
        contribs = db.query(Contribution).join(Member).filter(Member.organization_id == org_id).all()
        total_in = sum(float(c.amount) for c in contribs)
        
        # Total loan disbursed
        loans = db.query(Loan).join(Member).filter(Member.organization_id == org_id, Loan.status == "ACTIVE").all()
        total_out = sum(float(l.principal_amount) for l in loans)
        
        # Total repayments
        repayments = db.query(LoanRepayment).join(Loan).join(Member).filter(Member.organization_id == org_id).all()
        total_repaid = sum(float(r.amount) for r in repayments)
        
        # Expenses
        expenses = db.query(Expense).filter(Expense.organization_id == org_id).all()
        total_expenses = sum(float(e.amount) for e in expenses)
        
        return {
            "total_contributions": total_in,
            "total_loans_disbursed": total_out,
            "total_repayments": total_repaid,
            "total_expenses": total_expenses,
            "balance": total_in - total_out + total_repaid - total_expenses
        }


class ProposalService:
    """Voting/proposal operations"""
    
    @staticmethod
    def create_proposal(db: Session, org_id: str, title: str, description: str, proposed_by: str):
        from app.models import Proposal
        proposal = Proposal(
            organization_id=org_id,
            title=title,
            description=description,
            proposed_by=proposed_by,
            status="PENDING"
        )
        db.add(proposal)
        db.commit()
        return proposal
    
    @staticmethod
    def vote(db: Session, proposal_id: str, member_id: str, vote_type: str):
        from app.models import Vote
        vote = Vote(
            proposal_id=proposal_id,
            member_id=member_id,
            vote_type=vote_type  # APPROVE, REJECT, ABSTAIN
        )
        db.add(vote)
        db.commit()
        return vote
    
    @staticmethod
    def get_results(db: Session, proposal_id: str):
        from app.models import Vote
        votes = db.query(Vote).filter(Vote.proposal_id == proposal_id).all()
        return {
            "approve": sum(1 for v in votes if v.vote_type == "APPROVE"),
            "reject": sum(1 for v in votes if v.vote_type == "REJECT"),
            "abstain": sum(1 for v in votes if v.vote_type == "ABSTAIN")
        }


# Export all services
__all__ = [
    "MemberService",
    "ContributionService", 
    "LoanService",
    "TreasuryService",
    "ProposalService"
]
