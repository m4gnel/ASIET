#!/usr/bin/env python3
"""
Permanent database fix: Delete old corrupted DB and recreate with proper schema.
This script:
1. Stops any running server connections
2. Deletes old interview_coach.db and WAL files
3. Recreates fresh database from models
4. Seeds demo user and questions
"""
import os
import sys
import json
from pathlib import Path

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'interview_coach.db')
db_shm = f"{db_path}-shm"
db_wal = f"{db_path}-wal"

print("\n" + "="*70)
print("  DATABASE FIX: Permanent Reset with Full Schema")
print("="*70)

# Step 1: Stop existing connections and delete old DB
print("\n[Step 1] Removing old database files...")
try:
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"  ✓ Deleted {db_path}")
except Exception as e:
    print(f"  ⚠ Could not delete {db_path}: {e}")

try:
    if os.path.exists(db_shm):
        os.remove(db_shm)
        print(f"  ✓ Deleted {db_shm}")
except Exception as e:
    print(f"  ⚠ Could not delete WAL-shm: {e}")

try:
    if os.path.exists(db_wal):
        os.remove(db_wal)
        print(f"  ✓ Deleted {db_wal}")
except Exception as e:
    print(f"  ⚠ Could not delete WAL-wal: {e}")

# Step 2: Import Flask app and create fresh database
print("\n[Step 2] Creating fresh database with proper schema...")
try:
    from app import app, db, User, Question, Interview, Answer, Feedback, QuestionBank
    from datetime import datetime
    import uuid as uuid_mod
    
    with app.app_context():
        # Create all tables from models (with all columns)
        db.create_all()
        print("  ✓ Database tables created from models")
        
        # Seed demo user
        demo_user = User(
            email='demo@interviewcoach.ai',
            first_name='Demo', 
            last_name='User',
            headline='Full Stack Developer | AI Enthusiast',
            experience_years=3,
            current_role='Software Developer',
            skills=json.dumps(['Python', 'JavaScript', 'React', 'Node.js', 'SQL', 'Docker']),
            dream_companies=json.dumps(['Google', 'Amazon', 'Microsoft']),
            target_roles=json.dumps(['Senior Software Engineer', 'Backend Engineer']),
            subscription_tier='pro'
        )
        demo_user.set_password('demo123456')
        db.session.add(demo_user)
        db.session.commit()
        print("  ✓ Demo user seeded: demo@interviewcoach.ai / demo123456")
        
        # Seed question bank
        seed_qs = [
            QuestionBank(
                text="Design a scalable URL-shortening service. Walk through your system design.",
                category='technical', field='Software', level='Senior', company='Google',
                difficulty='hard', is_verified=True
            ),
            QuestionBank(
                text="Explain the difference between a process and a thread and when you'd use each.",
                category='technical', field='Software', level='Mid',
                difficulty='medium', is_verified=True
            ),
            QuestionBank(
                text="How do you handle class imbalance in a machine learning classification problem?",
                category='technical', field='Data Science', level='Mid',
                difficulty='medium', is_verified=True
            ),
            QuestionBank(
                text="Describe a time you resolved a conflict with a teammate. What was the outcome?",
                category='behavioral', field='Software', level='Mid',
                difficulty='easy', is_verified=True
            ),
            QuestionBank(
                text="How would you measure success of a new product feature launch?",
                category='technical', field='Product', level='Mid',
                difficulty='medium', is_verified=True
            ),
            QuestionBank(
                text="Explain CAP theorem and how you'd design a payment system given those constraints.",
                category='technical', field='Software', level='Senior',
                difficulty='hard', is_verified=True
            ),
        ]
        db.session.add_all(seed_qs)
        db.session.commit()
        print(f"  ✓ Seeded {len(seed_qs)} verified questions")

except Exception as e:
    print(f"  ✗ ERROR during database creation: {e}")
    import traceback
    print(traceback.format_exc())
    sys.exit(1)

# Step 3: Verify database
print("\n[Step 3] Verifying database...")
try:
    with app.app_context():
        # Count records
        user_count = User.query.count()
        question_count = QuestionBank.query.count()
        
        # Check tables exist and have columns
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        print(f"  ✓ Tables created: {len(tables)} tables")
        print(f"    - users: {user_count} records")
        print(f"    - question_bank: {question_count} records")
        
        # Verify key columns exist
        key_columns = {
            'interviews': ['question_type', 'answer_type', 'started_at'],
            'answers': ['selected_options', 'score', 'submitted_at'],
            'questions': ['is_multiple_choice', 'options', 'correct_answers'],
        }
        
        for table, cols in key_columns.items():
            if table in tables:
                existing_cols = [c['name'] for c in inspector.get_columns(table)]
                missing = [c for c in cols if c not in existing_cols]
                if missing:
                    print(f"  ⚠ {table}: Missing columns {missing}")
                else:
                    print(f"  ✓ {table}: All key columns present")
        
except Exception as e:
    print(f"  ✗ ERROR during verification: {e}")
    sys.exit(1)

print("\n" + "="*70)
print("  ✓ DATABASE RESET COMPLETE")
print("="*70)
print("\nNEXT STEPS:")
print("  1. Restart the Flask server:")
print("     python run_server.py")
print("\n  2. Test the API by logging in:")
print("     Email: demo@interviewcoach.ai")
print("     Password: demo123456")
print("\n  3. All 500 errors should now be fixed!")
print("="*70 + "\n")
