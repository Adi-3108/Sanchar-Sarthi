import os
import sys

# Add backend to path so we can import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import SessionLocal
from app.orm.user_account import UserAccount

def main():
    with SessionLocal() as db:
        # Get the most recently created user
        account = db.query(UserAccount).order_by(UserAccount.created_at.desc()).first()
        
        if not account:
            print("No users found in the database. Please sign up first!")
            return
            
        print(f"Found latest user with UID: {account.auth_provider_uid}")
        print(f"Current Role: {account.role}")
        
        if account.role == "admin":
            print("User is already an admin!")
            return
            
        account.role = "admin"
        db.commit()
        print("Successfully promoted user to Admin!")

if __name__ == "__main__":
    main()
