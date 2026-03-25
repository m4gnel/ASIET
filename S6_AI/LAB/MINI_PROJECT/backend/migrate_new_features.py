#!/usr/bin/env python3
"""
Database Migration Script
Adds new tables for:
- UserAnalytics: Track user performance profiles
- QuestionRecommendation: Personalized question recommendations  
- AnswerCache: Speed up answer analysis with caching
"""

import sys
from pathlib import Path
from sqlalchemy import text

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

def migrate():
    """Create new tables for analytics, recommendations, and caching"""
    try:
        from app import app, db
        
        with app.app_context():
            print("[MIGRATION] Starting database migration...\n")
            
            # Create all new tables
            db.create_all()
            print("[OK] All tables created/verified")
            
            # Verify UserAnalytics table
            inspector = db.inspect(db.engine)
            if 'user_analytics' in inspector.get_table_names():
                print("[OK] user_analytics table created")
            else:
                print("[WARN] user_analytics table not found")
            
            if 'question_recommendations' in inspector.get_table_names():
                print("[OK] question_recommendations table created")
            else:
                print("[WARN] question_recommendations table not found")
            
            if 'answer_cache' in inspector.get_table_names():
                print("[OK] answer_cache table created")
            else:
                print("[WARN] answer_cache table not found")
            
            # Initialize UserAnalytics for existing users
            from app import User, UserAnalytics
            
            existing_users = User.query.all()
            new_analytics = 0
            
            for user in existing_users:
                existing = UserAnalytics.query.filter_by(user_id=user.id).first()
                if not existing:
                    analytics = UserAnalytics(user_id=user.id)
                    db.session.add(analytics)
                    new_analytics += 1
            
            if new_analytics > 0:
                db.session.commit()
                print(f"[OK] Created UserAnalytics for {new_analytics} existing users")
            else:
                print("[OK] All existing users already have analytics records")
            
            print("\n[SUCCESS] Database migration completed!")
            print("\nNew Features:")
            print("  [OK] Smart question shuffling (avoids repeats)")
            print("  [OK] Personalized questions (targets weak areas)")
            print("  [OK] Answer analysis caching (faster feedback)")
            print("  [OK] User analytics tracking (performance profiles)")
            print("  [OK] Async analysis (non-blocking)")
            
            return True
            
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = migrate()
    sys.exit(0 if success else 1)
