#!/usr/bin/env python3
"""
Seed data for 5 chamas with 50+ members each
"""
import psycopg2
import random
from datetime import datetime, timedelta
import uuid

# Connect to database
conn = psycopg2.connect(
    host="localhost",
    database="chama_ms",
    user="postgres",
    password="postgres"
)
cur = conn.cursor()

print("🌱 Seeding data for 5 chamas...")

# 5 Chamas with different themes
chamas = [
    {"name": "Mwanzo Mw集合", "code": "MWANZO", "region": "Nairobi"},
    {"name": "Tujitegemee Group", "code": "TUJITE", "region": "Mombasa"},
    {"name": "Chama Cha Maendeleo", "code": "MAENDE", "region": "Kisumu"},
    {"name": "Umoja Kazi Group", "code": "UMOJA", "region": "Nakuru"},
    {"name": "Faraja Savings Circle", "code": "FARAJA", "region": "Eldoret"},
]

# Sample data
first_names_m = ["John", "Mary", "Joseph", "Grace", "David", "Faith", "Michael", "Hope", "Daniel", "Joy",
                 "Peter", "Sarah", "James", "Esther", "Stephen", "Ruth", "Samuel", "Rebecca", "Daniel", "Leah",
                 "George", "Wanjiru", "Francis", "Nyambura", "Paul", "Wambui", "Kevin", "Mumbi", "Brian", "Njeri"]

first_names_f = ["Ann", "Mary", "Grace", "Faith", "Joy", "Esther", "Ruth", "Rebecca", "Leah", "Wanjiru",
                 "Nancy", "Caroline", "Veronica", "Josephine", "Dorothy", "Pauline", "Janet", "Christine", "Lucy", "Agnes"]

last_names = ["Ochieng", "Oduya", "Mwangi", "Njoroge", "Kimani", "Waweru", "Mutua", "Ndung'u", "Kariuki", "Onyango",
              "Odhiambo", "Owino", "Otieno", "Wekesa", "Kiplagat", "Kosgei", "Jepchirchir", "Cheruiyot", "Rono", "Sang"]

# Create organizations
org_ids = []
for chama in chamas:
    org_id = f"org_{uuid.uuid4().hex[:8]}"
    org_ids.append(org_id)
    
    cur.execute("""
        INSERT INTO organizations (id, name, code, region, status, created_at)
        VALUES (%s, %s, %s, %s, 'ACTIVE', %s)
    """, (org_id, chama["name"], chama["code"], chama["region"], datetime.utcnow()))
    
    print(f"  ✅ Created: {chama['name']}")

# Create members (50+ per chama = 250+ total)
member_ids = []
for i, org_id in enumerate(org_ids):
    print(f"\n📋 Creating 50 members for chama {i+1}...")
    
    # Roles: 1 Chair, 1 Secretary, 1 Treasurer, 47 Members
    roles = ["CHAIR"] + ["SECRETARY"] + ["TREASURER"] + ["MEMBER"] * 47
    
    for j, role in enumerate(roles):
        member_id = f"mem_{uuid.uuid4().hex[:12]}"
        member_ids.append(member_id)
        
        # Generate phone (Kenyan format)
        phone = f"254{7 if random.random() > 0.5 else 1}{random.randint(10000000, 99999999)}"
        
        # Name
        if role == "CHAIR":
            first = "Peter" if i % 2 == 0 else "Mary"
            last = random.choice(last_names)
        elif role == "SECRETARY":
            first = "Grace" if i % 2 == 0 else "James"
            last = random.choice(last_names)
        elif role == "TREASURER":
            first = "David" if i % 2 == 0 else "Faith"
            last = random.choice(last_names)
        else:
            first = random.choice(first_names_m + first_names_f)
            last = random.choice(last_names)
        
        name = f"{first} {last}"
        email = f"{first.lower()}.{last.lower()}{j}@chama.co.ke"
        
        cur.execute("""
            INSERT INTO members (id, name, email, phone, organization_id, role, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, 'ACTIVE', %s)
        """, (member_id, name, email, phone, org_id, role, datetime.utcnow() - timedelta(days=random.randint(30, 365))))
        
    print(f"  ✅ Created 50 members")

# Create contributions (each member contributes monthly for 6 months)
print("\n💰 Creating contributions...")
contrib_count = 0
for i, org_id in enumerate(org_ids):
    # Get members for this org
    cur.execute("SELECT id FROM members WHERE organization_id = %s", (org_id,))
    org_members = [r[0] for r in cur.fetchall()]
    
    for member_id in org_members:
        # 6 months of contributions
        for month in range(6):
            amount = random.choice([1000, 2000, 3000, 5000, 10000])
            contrib_id = f"con_{uuid.uuid4().hex[:12]}"
            
            cur.execute("""
                INSERT INTO contributions (id, member_id, amount, method, status, created_at)
                VALUES (%s, %s, %s, %s, 'COMPLETED', %s)
            """, (contrib_id, member_id, amount, random.choice(["CASH", "MPESA", "BANK"]), 
                   datetime.utcnow() - timedelta(days=month*30)))
            contrib_count += 1

print(f"  ✅ Created {contrib_count} contributions")

# Create loans (some members get loans)
print("\n💳 Creating loans...")
loan_count = 0
for i, org_id in enumerate(org_ids):
    cur.execute("SELECT id FROM members WHERE organization_id = %s", (org_id,))
    org_members = [r[0] for r in cur.fetchall()]
    
    # 10% of members get loans
    loan_members = random.sample(org_members, min(10, len(org_members)))
    
    for member_id in loan_members:
        # Random loan amount
        principal = random.choice([10000, 20000, 30000, 50000, 100000])
        term = random.choice([3, 6, 9, 12])
        
        # Calculate interest (10% monthly reducing)
        interest = principal * 0.10 * (term / 12)
        total = principal + interest
        monthly = total / term
        
        loan_id = f"lon_{uuid.uuid4().hex[:12]}"
        
        status = random.choice(["PENDING", "APPROVED", "ACTIVE"])
        
        cur.execute("""
            INSERT INTO loans (id, member_id, principal_amount, interest_rate, term_months, monthly_payment, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (loan_id, member_id, principal, 10.0, term, monthly, status,
               datetime.utcnow() - timedelta(days=random.randint(1, 180))))
        loan_count += 1
        
        # Some repayments if loan is active/approved
        if status in ["APPROVED", "ACTIVE"]:
            for m in range(random.randint(1, term)):
                repay_id = f"rep_{uuid.uuid4().hex[:12]}"
                cur.execute("""
                    INSERT INTO loan_repayments (id, loan_id, member_id, amount, status, created_at)
                    VALUES (%s, %s, %s, %s, 'COMPLETED', %s)
                """, (repay_id, loan_id, member_id, monthly, 
                       datetime.utcnow() - timedelta(days=m*30)))

print(f"  ✅ Created {loan_count} loans")

# Create proposals
print("\n📝 Creating proposals...")
proposal_count = 0
for i, org_id in enumerate(org_ids):
    # 3-5 proposals per chama
    for p in range(random.randint(3, 5)):
        prop_id = f"prp_{uuid.uuid4().hex[:12]}"
        
        titles = [
            "Monthly Contribution Increase",
            "New Meeting Schedule",
            "Annual General Meeting",
            "Investment in Treasury Bills",
            "Loan Interest Rate Review",
            "New Member Admission",
            "Budget Approval",
            "Dividend Distribution"
        ]
        
        title = random.choice(titles)
        description = f"Proposal to {title.lower()} for the benefit of all members."
        
        cur.execute("""
            INSERT INTO proposals (id, organization_id, title, description, proposed_by, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (prop_id, org_id, title, description, random.choice(org_members[:3]),
               random.choice(["PENDING", "APPROVED", "REJECTED"]), 
               datetime.utcnow() - timedelta(days=random.randint(1, 90))))
        proposal_count += 1
        
        # Add votes
        voting_members = random.sample(org_members, random.randint(5, 20))
        for v_member in voting_members:
            vote_id = f"vot_{uuid.uuid4().hex[:12]}"
            cur.execute("""
                INSERT INTO votes (id, proposal_id, member_id, vote_type, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (vote_id, prop_id, v_member, random.choice(["APPROVE", "REJECT", "ABSTAIN"]),
                   datetime.utcnow() - timedelta(days=random.randint(1, 30))))

print(f"  ✅ Created {proposal_count} proposals with votes")

# Commit and close
conn.commit()
cur.close()
conn.close()

print(f"\n{'='*50}")
print("🎉 SEEDING COMPLETE!")
print(f"{'='*50}")
print(f"📊 Summary:")
print(f"   • 5 Chamas created")
print(f"   • 250+ Members created")
print(f"   • {contrib_count} Contributions recorded")
print(f"   • {loan_count} Loans created")
print(f"   • {proposal_count} Proposals with votes")
print(f"{'='*50}")
