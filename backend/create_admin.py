#!/usr/bin/env python3
"""
Script to create the default admin user
"""
import os
import sys
sys.path.append('.')

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models.user import User
from services.auth_service import AuthService

def get_db_url():
    url = os.getenv(
        "POSTGRES_URL", 
        "postgres://postgres.eyriqifciwpjrxlrkpgz:p6GT4JHiGqPwBiv2@aws-1-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require"
    )
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url

def create_admin_user():
    # Create database connection
    engine = create_engine(get_db_url())
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if admin user already exists
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if existing_admin:
            print("❌ Admin user already exists!")
            return
        
        # Create admin user
        hashed_password = AuthService.hash_password("password@123")
        admin_user = User(
            username="admin",
            email="admin@example.com",
            hashed_password=hashed_password,
            role="admin",
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("✅ Admin user created successfully!")
        print(f"   Username: admin")
        print(f"   Password: password@123")
        print(f"   Role: admin")
        print(f"   ID: {admin_user.id}")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()
