"""
DATABASE VERIFICATION SCRIPT
Run this to verify your database is working correctly
"""

import sqlite3
import sys
import os

def verify_database():
    """Verify database structure and test data"""
    
    db_path = 'interview_coach.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        print(f"💡 Make sure you're in the same directory as interview_coach.db")
        return False
    
    print(f"✅ Database found: {db_path}")
    print("="*70)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]
        
        print("\n📊 DATABASE TABLES:")
        required_tables = ['users', 'interviews', 'questions', 'answers', 'feedback']
        
        for table in required_tables:
            if table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   ✅ {table:15} - {count} records")
            else:
                print(f"   ❌ {table:15} - MISSING!")
        
        # Check foreign keys
        print("\n🔗 FOREIGN KEY CHECKS:")
        
        # Check interviews -> users
        cursor.execute("""
            SELECT COUNT(*) FROM interviews 
            WHERE user_id NOT IN (SELECT id FROM users)
        """)
        orphaned_interviews = cursor.fetchone()[0]
        
        if orphaned_interviews == 0:
            print(f"   ✅ interviews.user_id → users.id (No orphaned records)")
        else:
            print(f"   ⚠️  interviews.user_id → users.id ({orphaned_interviews} orphaned)")
        
        # Check answers -> interviews
        cursor.execute("""
            SELECT COUNT(*) FROM answers 
            WHERE interview_id NOT IN (SELECT id FROM interviews)
        """)
        orphaned_answers = cursor.fetchone()[0]
        
        if orphaned_answers == 0:
            print(f"   ✅ answers.interview_id → interviews.id (No orphaned records)")
        else:
            print(f"   ⚠️  answers.interview_id → interviews.id ({orphaned_answers} orphaned)")
        
        # Check feedback -> users
        cursor.execute("""
            SELECT COUNT(*) FROM feedback 
            WHERE user_id NOT IN (SELECT id FROM users)
        """)
        orphaned_feedback_users = cursor.fetchone()[0]
        
        if orphaned_feedback_users == 0:
            print(f"   ✅ feedback.user_id → users.id (No orphaned records)")
        else:
            print(f"   ⚠️  feedback.user_id → users.id ({orphaned_feedback_users} orphaned)")
        
        # Check feedback -> answers
        cursor.execute("""
            SELECT COUNT(*) FROM feedback 
            WHERE answer_id NOT IN (SELECT id FROM answers)
        """)
        orphaned_feedback_answers = cursor.fetchone()[0]
        
        if orphaned_feedback_answers == 0:
            print(f"   ✅ feedback.answer_id → answers.id (No orphaned records)")
        else:
            print(f"   ⚠️  feedback.answer_id → answers.id ({orphaned_feedback_answers} orphaned)")
        
        # Show sample data
        print("\n📝 SAMPLE DATA:")
        
        cursor.execute("SELECT id, email, first_name, total_interviews FROM users LIMIT 3")
        users = cursor.fetchall()
        if users:
            print("   Users:")
            for user in users:
                print(f"      ID:{user[0]} - {user[1]} ({user[2]}) - {user[3]} interviews")
        else:
            print("   No users yet (register to create one)")
        
        cursor.execute("""
            SELECT i.id, i.field, i.level, i.status, i.overall_score 
            FROM interviews i LIMIT 3
        """)
        interviews = cursor.fetchall()
        if interviews:
            print("   Interviews:")
            for interview in interviews:
                print(f"      ID:{interview[0]} - {interview[1]} ({interview[2]}) - Status:{interview[3]} - Score:{interview[4]}")
        else:
            print("   No interviews yet (start one to create)")
        
        conn.close()
        
        print("\n" + "="*70)
        print("✅ DATABASE VERIFICATION COMPLETE")
        print("="*70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error verifying database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = verify_database()
    sys.exit(0 if success else 1)
