#!/usr/bin/env python3
"""
Initialize database with new HybridInterviewSession table and populate question bank.
Run this once after deploying the hybrid loading feature.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import app, db

def init_db():
    """Create all tables"""
    with app.app_context():
        print("\n" + "="*80)
        print("  DATABASE INITIALIZATION")
        print("="*80 + "\n")
        
        print("Creating database tables...")
        try:
            db.create_all()
            print("[OK] All tables created successfully\n")
        except Exception as e:
            print(f"✗ Error creating tables: {e}\n")
            raise
        
        # Verify tables exist
        from sqlalchemy import text
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        print("Existing tables:")
        for table in sorted(tables):
            print(f"  [OK] {table}")
        
        # Check if HybridInterviewSession table exists
        if 'hybrid_interview_sessions' in tables:
            print("\n[OK] HybridInterviewSession table is ready!")
        else:
            print("\n⚠ HybridInterviewSession table not found - creating now...")
            db.create_all()
            print("[OK] Created!")
        
        print("\n" + "="*80 + "\n")

if __name__ == '__main__':
    init_db()
    
    # Now populate question bank
    print("Next step: Run 'python populate_question_bank.py' to populate questions\n")
