import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal, engine
from app.db.models import Base, User, UserRole
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def seed():
    db = SessionLocal()
    
    # Check if users exist
    if db.query(User).count() > 0:
        print("Users already exist. Skipping seed.")
        db.close()
        return

    print("Seeding users...")
    
    # Create Team Lead
    tl = User(
        email="lead@example.com",
        name="Team Lead",
        role=UserRole.team_lead,
        hashed_password=pwd_context.hash("password123"),
        department="Engineering"
    )
    
    # Create HR
    hr = User(
        email="hr@example.com",
        name="HR Manager",
        role=UserRole.hr,
        hashed_password=pwd_context.hash("password123"),
        department="HR"
    )

    db.add(tl)
    db.add(hr)
    db.commit()
    print("Users seeded successfully!")
    print("  lead@example.com / password123")
    print("  hr@example.com / password123")
    db.close()

if __name__ == "__main__":
    seed()
