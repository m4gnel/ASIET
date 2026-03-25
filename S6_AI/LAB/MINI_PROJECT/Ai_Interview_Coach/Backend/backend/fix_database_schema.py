#!/usr/bin/env python3
"""Fix database schema - add missing columns"""
from app import *
import traceback

with app.app_context():
    try:
        # Check what columns are missing
        inspector = __import__('sqlalchemy').inspect(db.engine)
        interviews_columns = [col['name'] for col in inspector.get_columns('interviews')]
        
        print("Current columns in 'interviews' table:")
        print(interviews_columns)
        
        missing_columns = []
        required_columns = ['question_type', 'mode', 'user_profile_snapshot', 'question_prompt']
        
        for col in required_columns:
            if col not in interviews_columns:
                missing_columns.append(col)
                print(f"  ❌ Missing: {col}")
            else:
                print(f"  ✓ Found: {col}")
        
        # Add missing columns
        if missing_columns:
            print(f"\nAdding {len(missing_columns)} missing columns...")
            with db.engine.connect() as conn:
                # Add question_type (string, default 'mock')
                if 'question_type' in missing_columns:
                    try:
                        conn.execute(__import__('sqlalchemy').text(
                            "ALTER TABLE interviews ADD COLUMN question_type VARCHAR(50) DEFAULT 'mock'"
                        ))
                        print("  ✓ Added question_type column")
                    except Exception as e:
                        print(f"  ⚠ Error adding question_type: {e}")
                
                # Add mode (string, default 'text')
                if 'mode' in missing_columns:
                    try:
                        conn.execute(__import__('sqlalchemy').text(
                            "ALTER TABLE interviews ADD COLUMN mode VARCHAR(20) DEFAULT 'text'"
                        ))
                        print("  ✓ Added mode column")
                    except Exception as e:
                        print(f"  ⚠ Error adding mode: {e}")
                
                # Add user_profile_snapshot (text)
                if 'user_profile_snapshot' in missing_columns:
                    try:
                        conn.execute(__import__('sqlalchemy').text(
                            "ALTER TABLE interviews ADD COLUMN user_profile_snapshot TEXT"
                        ))
                        print("  ✓ Added user_profile_snapshot column")
                    except Exception as e:
                        print(f"  ⚠ Error adding user_profile_snapshot: {e}")
                
                # Add question_prompt (text)
                if 'question_prompt' in missing_columns:
                    try:
                        conn.execute(__import__('sqlalchemy').text(
                            "ALTER TABLE interviews ADD COLUMN question_prompt TEXT"
                        ))
                        print("  ✓ Added question_prompt column")
                    except Exception as e:
                        print(f"  ⚠ Error adding question_prompt: {e}")
                
                conn.commit()
                print("\n✓ All missing columns added successfully!")
        else:
            print("\n✓ All required columns exist!")
        
        # Verify the schema now
        inspector = __import__('sqlalchemy').inspect(db.engine)
        interviews_columns = [col['name'] for col in inspector.get_columns('interviews')]
        print(f"\nFinal column count: {len(interviews_columns)}")
        print("All columns:", interviews_columns)
        
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
