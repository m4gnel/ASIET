"""
Database Migration: Add password reset fields to users table
This adds support for the forgot password functionality
"""
import sqlite3
import sys

def migrate_database(db_path='interview_coach.db'):
    """Add password reset columns to users table if they don't exist"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print("Current columns in users table:")
        for col in columns:
            print(f"  ✓ {col}")
        
        # Add password_reset_token column if it doesn't exist
        if 'password_reset_token' not in columns:
            print("\n→ Adding password_reset_token column...")
            cursor.execute("""
                ALTER TABLE users ADD COLUMN password_reset_token VARCHAR(255)
            """)
            print("  ✓ password_reset_token column added")
        else:
            print("\n  ✓ password_reset_token column already exists")
        
        # Add password_reset_token_expiry column if it doesn't exist
        if 'password_reset_token_expiry' not in columns:
            print("→ Adding password_reset_token_expiry column...")
            cursor.execute("""
                ALTER TABLE users ADD COLUMN password_reset_token_expiry DATETIME
            """)
            print("  ✓ password_reset_token_expiry column added")
        else:
            print("  ✓ password_reset_token_expiry column already exists")
        
        conn.commit()
        
        # Verify migration
        cursor.execute("PRAGMA table_info(users)")
        new_columns = [column[1] for column in cursor.fetchall()]
        
        if 'password_reset_token' in new_columns and 'password_reset_token_expiry' in new_columns:
            print("\n✓ Migration completed successfully!")
            print("  Database is now ready for forgot password functionality")
            return True
        else:
            print("\n✗ Migration failed: Columns not properly added")
            return False
            
    except Exception as e:
        print(f"\n✗ Migration error: {e}")
        return False
    finally:
        try:
            conn.close()
        except:
            pass

if __name__ == '__main__':
    db_path = 'interview_coach.db'
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    print("="*60)
    print("DATABASE MIGRATION: Add Password Reset Support")
    print("="*60)
    print(f"\nDatabase: {db_path}")
    print()
    
    success = migrate_database(db_path)
    
    print("\n" + "="*60)
    if success:
        print("Status: ✓ READY")
        sys.exit(0)
    else:
        print("Status: ✗ FAILED")
        sys.exit(1)
