#!/usr/bin/env python3
"""
Database migration script to add multiple-choice columns to the questions table
and selected_options column to the answers table
"""

import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'interview_coach.db')

def migrate_database():
    """Add new columns to questions and answers tables"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Starting database migration...")
        
        # Check if columns already exist before adding
        cursor.execute("PRAGMA table_info(questions)")
        questions_columns = {row[1] for row in cursor.fetchall()}
        
        # Add columns to questions table if they don't exist
        if 'is_multiple_choice' not in questions_columns:
            print("Adding is_multiple_choice column to questions...")
            cursor.execute("ALTER TABLE questions ADD COLUMN is_multiple_choice BOOLEAN DEFAULT 0")
        
        if 'options' not in questions_columns:
            print("Adding options column to questions...")
            cursor.execute("ALTER TABLE questions ADD COLUMN options TEXT")
        
        if 'correct_answers' not in questions_columns:
            print("Adding correct_answers column to questions...")
            cursor.execute("ALTER TABLE questions ADD COLUMN correct_answers TEXT")
        
        if 'multiple_allowed' not in questions_columns:
            print("Adding multiple_allowed column to questions...")
            cursor.execute("ALTER TABLE questions ADD COLUMN multiple_allowed BOOLEAN DEFAULT 0")
        
        # Check and add columns to answers table
        cursor.execute("PRAGMA table_info(answers)")
        answers_columns = {row[1] for row in cursor.fetchall()}
        
        if 'selected_options' not in answers_columns:
            print("Adding selected_options column to answers...")
            cursor.execute("ALTER TABLE answers ADD COLUMN selected_options TEXT")
        
        conn.commit()
        print("✅ Database migration completed successfully!")
        
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("⚠️  Columns already exist, skipping...")
        else:
            print(f"❌ Migration error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
