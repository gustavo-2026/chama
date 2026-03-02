"""
Core Banking Service
Microservice for members, contributions, loans, treasury
"""
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
import jwt

app = FastAPI(title="Core Banking Service")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database
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

class Member(Base):
    __tablename__ = "members"
    id = Column(String, primary_key=True)
    phone = Column(String, unique=True)
    name = Column(String)
    email = Column(String)
    organization_id = Column(String)
    role = Column(String)
    status = Column(String, default="ACTIVE")


class Contribution(Base):
    __tablename__ = "contributions"
    id = Column(String, primary_key=True)
    member_id = Column(String)
    amount = Column(Numeric)
    method = Column(String)
    status = Column(String, default="COMPLETED")
    created_at = Column(DateTime, default=datetime.utcnow)


class Loan(Base):
    __tablename__ = "loans"
    id = Column(String, primary_key=True)
    member_id = Column(String)
    principal_amount = Column(Numeric)
    term_months = Column(Integer)
    status = Column(String, default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)


# ============ Pydantic Models ============

class MemberCreate(BaseModel):
    phone: str
    name: str
    email: Optional[str] = None
    organization_id: str
    role: str = "MEMBER"


class ContributionCreate(BaseModel):
    member_id: str
    amount: float
    method: str = "CASH"


class LoanCreate(BaseModel):
    member_id: str
    principal_amount: float
    term_months: int
    purpose: str


# ============ Helpers ============

def get_current_member(db, authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401)
    token = authorization.replace("Bearer ", "")
    from app.core.config import settings
    try:
        payload = jwt.decode(token, "SECRET_KEY", algorithms=["HS256"])
        return db.query(Member).filter(Member.id == payload.get("sub")).first()
    except:
        raise HTTPException(status_code=401)


# ============ Member Endpoints ============

@app.get("/health")
def health():
    return {"status": "healthy", "service": "core"}


@app.post("/members", response_model=dict)
def create_member(data: MemberCreate, db=Depends(get_db)):
    member = Member(
        id=f"mem_{datetime.utcnow().timestamp()}",
        phone=data.phone,
        name=data.name,
        email=data.email,
        organization_id=data.organization_id,
        role=data.role
    )
    db.add(member)
    db.commit()
    return {"id": member.id, "status": "created"}


@app.get("/members/{member_id}", response_model=dict)
def get_member(member_id: str, db=Depends(get_db)):
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404)
    return {
        "id": member.id,
        "name": member.name,
        "phone": member.phone,
        "email": member.email,
        "role": member.role,
        "organization_id": member.organization_id
    }


@app.get("/members", response_model=List[dict])
def list_members(org_id: str = None, limit: int = 50, db=Depends(get_db)):
    query = db.query(Member)
    if org_id:
        query = query.filter(Member.organization_id == org_id)
    return [{"id": m.id, "name": m.name, "phone": m.phone, "role": m.role} 
            for m in query.limit(limit).all()]


# ============ Contribution Endpoints ============

@app.post("/contributions", response_model=dict)
def create_contribution(data: ContributionCreate, db=Depends(get_db)):
    contrib = Contribution(
        id=f"con_{datetime.utcnow().timestamp()}",
        member_id=data.member_id,
        amount=data.amount,
        method=data.method,
        status="COMPLETED"
    )
    db.add(contrib)
    db.commit()
    return {"id": contrib.id, "status": "created"}


@app.get("/contributions/member/{member_id}", response_model=List[dict])
def get_member_contributions(member_id: str, db=Depends(get_db)):
    contribs = db.query(Contribution).filter(Contribution.member_id == member_id).all()
    return [{"id": c.id, "amount": float(c.amount), "status": c.status, "created_at": c.created_at} 
            for c in contribs]


@app.get("/contributions/organization/{org_id}", response_model=dict)
def get_org_contributions(org_id: str, db=Depends(get_db)):
    members = db.query(Member).filter(Member.organization_id == org_id).all()
    member_ids = [m.id for m in members]
    contribs = db.query(Contribution).filter(Contribution.member_id.in_(member_ids)).all()
    total = sum(float(c.amount) for c in contribs)
    return {"total": total, "count": len(contribs)}


# ============ Loan Endpoints ============

@app.post("/loans", response_model=dict)
def create_loan(data: LoanCreate, db=Depends(get_db)):
    loan = Loan(
        id=f"lon_{datetime.utcnow().timestamp()}",
        member_id=data.member_id,
        principal_amount=data.principal_amount,
        term_months=data.term_months,
        status="PENDING"
    )
    db.add(loan)
    db.commit()
    return {"id": loan.id, "status": "pending"}


@app.get("/loans/{loan_id}", response_model=dict)
def get_loan(loan_id: str, db=Depends(get_db)):
    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404)
    return {
        "id": loan.id,
        "member_id": loan.member_id,
        "amount": float(loan.principal_amount),
        "term": loan.term_months,
        "status": loan.status
    }


@app.get("/loans/member/{member_id}", response_model=List[dict])
def get_member_loans(member_id: str, db=Depends(get_db)):
    loans = db.query(Loan).filter(Loan.member_id == member_id).all()
    return [{"id": l.id, "amount": float(l.principal_amount), "status": l.status} 
            for l in loans]


@app.post("/loans/{loan_id}/approve")
def approve_loan(loan_id: str, db=Depends(get_db), member=Depends(get_current_member)):
    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404)
    loan.status = "APPROVED"
    loan.approved_by = member.id
    loan.approved_at = datetime.utcnow()
    db.commit()
    return {"id": loan.id, "status": "approved"}


# ============ Treasury Endpoints ============

@app.get("/treasury/{org_id}", response_model=dict)
def get_treasury(org_id: str, db=Depends(get_db)):
    # Get members
    members = db.query(Member).filter(Member.organization_id == org_id).all()
    member_ids = [m.id for m in members]
    
    # Contributions
    contribs = db.query(Contribution).filter(Contribution.member_id.in_(member_ids)).all()
    total_in = sum(float(c.amount) for c in contribs)
    
    # Loans
    loans = db.query(Loan).filter(Loan.member_id.in_(member_ids), Loan.status == "APPROVED").all()
    total_loans = sum(float(l.principal_amount) for l in loans)
    
    return {
        "total_contributions": total_in,
        "total_loans_disbursed": total_loans,
        "available": total_in - total_loans,
        "member_count": len(members)
    }


# ============ Proposals ============

class Proposal(Base):
    __tablename__ = "proposals"
    id = Column(String, primary_key=True)
    organization_id = Column(String)
    title = Column(String)
    description = Column(Text)
    proposed_by = Column(String)
    status = Column(String, default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)


class Vote(Base):
    __tablename__ = "votes"
    id = Column(String, primary_key=True)
    proposal_id = Column(String)
    member_id = Column(String)
    vote_type = Column(String)


@app.post("/proposals", response_model=dict)
def create_proposal(
    organization_id: str,
    title: str,
    description: str,
    db=Depends(get_db),
    member=Depends(get_current_member)
):
    proposal = Proposal(
        id=f"prp_{datetime.utcnow().timestamp()}",
        organization_id=organization_id,
        title=title,
        description=description,
        proposed_by=member.id
    )
    db.add(proposal)
    db.commit()
    return {"id": proposal.id, "status": "pending"}


@app.get("/proposals/{org_id}", response_model=List[dict])
def list_proposals(org_id: str, db=Depends(get_db)):
    props = db.query(Proposal).filter(Proposal.organization_id == org_id).all()
    return [{"id": p.id, "title": p.title, "status": p.status} for p in props]


@app.post("/proposals/{proposal_id}/vote")
def vote_proposal(
    proposal_id: str,
    vote_type: str,
    db=Depends(get_db),
    member=Depends(get_current_member)
):
    vote = Vote(
        id=f"vot_{datetime.utcnow().timestamp()}",
        proposal_id=proposal_id,
        member_id=member.id,
        vote_type=vote_type
    )
    db.add(vote)
    db.commit()
    return {"status": "voted"}


@app.get("/proposals/{proposal_id}/results", response_model=dict)
def get_proposal_results(proposal_id: str, db=Depends(get_db)):
    votes = db.query(Vote).filter(Vote.proposal_id == proposal_id).all()
    return {
        "approve": sum(1 for v in votes if v.vote_type == "APPROVE"),
        "reject": sum(1 for v in votes if v.vote_type == "REJECT"),
        "abstain": sum(1 for v in votes if v.vote_type == "ABSTAIN")
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
