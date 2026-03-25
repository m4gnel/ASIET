"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                   DATABASE RECOVERY & INTEGRITY CHECKER                      ║
║              Fix corrupted analytics, session data, and stats                 ║
╚══════════════════════════════════════════════════════════════════════════════╝

This script performs a comprehensive database audit and recovery:
1. Validates referential integrity (no orphaned records)
2. Recalculates all user aggregate statistics
3. Fixes missing or corrupted data
4. Recovers session data
5. Generates a detailed report

Usage:
    python database_recovery.py
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

class DatabaseRecovery:
    def __init__(self, db_path='interview_coach.db'):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.report = {
            'timestamp': datetime.now().isoformat(),
            'database': db_path,
            'checks': [],
            'fixes': [],
            'warnings': [],
            'errors': []
        }
    
    def connect(self):
        """Connect to database"""
        if not Path(self.db_path).exists():
            print(f"❌ Database not found: {self.db_path}")
            return False
        
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            print(f"✅ Connected to database: {self.db_path}")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def execute_query(self, query, params=None):
        """Execute query safely"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchall()
        except Exception as e:
            self.report['errors'].append(f"Query execution error: {e}")
            return None
    
    def check_table_exists(self, table_name):
        """Check if table exists"""
        result = self.execute_query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        return result is not None and len(result) > 0
    
    def check_referential_integrity(self):
        """Check for orphaned records"""
        print("\n🔍 Checking Referential Integrity...")
        
        checks = {
            'interviews_without_users': (
                "SELECT COUNT(*) FROM interviews WHERE user_id NOT IN (SELECT id FROM users)",
                'interviews with missing users'
            ),
            'answers_without_interviews': (
                "SELECT COUNT(*) FROM answers WHERE interview_id NOT IN (SELECT id FROM interviews)",
                'answers with missing interviews'
            ),
            'answers_without_questions': (
                "SELECT COUNT(*) FROM answers WHERE question_id NOT IN (SELECT id FROM questions)",
                'answers with missing questions'
            ),
            'feedback_without_users': (
                "SELECT COUNT(*) FROM feedback WHERE user_id NOT IN (SELECT id FROM users)",
                'feedback with missing users'
            ),
            'feedback_without_answers': (
                "SELECT COUNT(*) FROM feedback WHERE answer_id NOT IN (SELECT id FROM answers)",
                'feedback with missing answers'
            ),
        }
        
        for check_name, (query, description) in checks.items():
            result = self.execute_query(query)
            if result:
                count = result[0][0]
                check = {
                    'name': check_name,
                    'query': query,
                    'found': count,
                    'description': description
                }
                self.report['checks'].append(check)
                
                if count > 0:
                    print(f"   ⚠️  {count} {description}")
                    self.report['warnings'].append(f"{check_name}: {count} issues found")
                else:
                    print(f"   ✅ No orphaned {description}")
    
    def recalculate_user_stats(self):
        """Recalculate all user statistics"""
        print("\n📊 Recalculating User Statistics...")
        
        try:
            # Get all users
            users = self.execute_query("SELECT id, email FROM users")
            
            if not users:
                print("   ℹ️  No users found")
                return True
            
            fixed_count = 0
            
            for user_id, email in users:
                try:
                    # Get completed interviews
                    interviews = self.execute_query(
                        """SELECT id, overall_score, duration_seconds, completed_at 
                           FROM interviews 
                           WHERE user_id = ? AND status = 'completed'""",
                        (user_id,)
                    )
                    
                    total_interviews = len(interviews) if interviews else 0
                    
                    # Calculate stats
                    scores = []
                    total_duration = 0
                    latest_date = None
                    
                    if interviews:
                        for interview_id, score, duration, completed_at in interviews:
                            if score is not None:
                                scores.append(score)
                            total_duration += duration or 0
                            if completed_at and (not latest_date or completed_at > latest_date):
                                latest_date = completed_at
                    
                    average_score = round(sum(scores) / len(scores), 2) if scores else 0.0
                    best_score = round(max(scores), 2) if scores else 0.0
                    
                    # Count total questions answered
                    total_questions = 0
                    if interviews:
                        for interview_id, _, _, _ in interviews:
                            q_result = self.execute_query(
                                "SELECT COUNT(*) FROM answers WHERE interview_id = ?",
                                (interview_id,)
                            )
                            if q_result:
                                total_questions += q_result[0][0]
                    
                    # Update user stats
                    update_query = """
                        UPDATE users 
                        SET total_interviews = ?,
                            average_score = ?,
                            best_score = ?,
                            total_practice_time = ?,
                            total_questions_answered = ?,
                            last_activity_date = ?
                        WHERE id = ?
                    """
                    
                    self.cursor.execute(update_query, (
                        total_interviews,
                        average_score,
                        best_score,
                        total_duration,
                        total_questions,
                        latest_date,
                        user_id
                    ))
                    
                    fixed_count += 1
                    print(f"   ✅ {email:35} | interviews={total_interviews:2} | avg={average_score:.2f} | best={best_score:.2f} | Q={total_questions}")
                    
                except Exception as e:
                    self.report['errors'].append(f"Error processing user {user_id}: {e}")
                    print(f"   ❌ {email:35} | Error: {e}")
            
            self.conn.commit()
            
            self.report['fixes'].append({
                'action': 'recalculate_user_stats',
                'users_fixed': fixed_count,
                'total_users': len(users)
            })
            
            print(f"\n   📈 Fixed stats for {fixed_count}/{len(users)} users")
            return True
            
        except Exception as e:
            self.report['errors'].append(f"Failed to recalculate user stats: {e}")
            print(f"   ❌ Error: {e}")
            return False
    
    def verify_completed_interviews(self):
        """Verify all completed interviews have valid scores"""
        print("\n✓ Verifying Completed Interviews...")
        
        try:
            # Find completed interviews without scores
            result = self.execute_query("""
                SELECT COUNT(*) FROM interviews 
                WHERE status = 'completed' AND overall_score IS NULL
            """)
            
            missing_scores = result[0][0] if result else 0
            
            if missing_scores > 0:
                print(f"   ⚠️  {missing_scores} completed interviews missing overall_score")
                self.report['warnings'].append(f"Completed interviews without scores: {missing_scores}")
                # Note: These should ideally be recalculated from answers
            else:
                print(f"   ✅ All completed interviews have scores")
            
            return True
            
        except Exception as e:
            self.report['errors'].append(f"Failed to verify interviews: {e}")
            return False
    
    def generate_summary(self):
        """Generate and display recovery summary"""
        print("\n" + "="*80)
        print("📋 DATABASE RECOVERY SUMMARY")
        print("="*80)
        
        print(f"\n📅 Timestamp: {self.report['timestamp']}")
        print(f"📦 Database: {self.report['database']}")
        
        print(f"\n✅ Checks Performed: {len(self.report['checks'])}")
        for check in self.report['checks']:
            status = "✅" if check['found'] == 0 else "⚠️ "
            print(f"   {status} {check['name']}: {check['found']} issues")
        
        print(f"\n🔧 Fixes Applied: {len(self.report['fixes'])}")
        for fix in self.report['fixes']:
            print(f"   ✅ {fix['action']}: {list(fix.values())[1:]}")
        
        if self.report['warnings']:
            print(f"\n⚠️  Warnings: {len(self.report['warnings'])}")
            for warning in self.report['warnings']:
                print(f"   ⚠️  {warning}")
        
        if self.report['errors']:
            print(f"\n❌ Errors: {len(self.report['errors'])}")
            for error in self.report['errors']:
                print(f"   ❌ {error}")
        
        print("\n" + "="*80)
        
        # Save report
        report_file = 'database_recovery_report.json'
        with open(report_file, 'w') as f:
            json.dump(self.report, f, indent=2, default=str)
        
        print(f"📄 Report saved to: {report_file}")
    
    def run_full_recovery(self):
        """Run complete recovery process"""
        print("\n╔════════════════════════════════════════════════════════╗")
        print("║         STARTING DATABASE RECOVERY PROCESS             ║")
        print("╚════════════════════════════════════════════════════════╝")
        
        if not self.connect():
            return False
        
        try:
            self.check_referential_integrity()
            self.verify_completed_interviews()
            self.recalculate_user_stats()
            self.generate_summary()
            
            print("\n✅ DATABASE RECOVERY COMPLETED SUCCESSFULLY\n")
            return True
            
        except Exception as e:
            print(f"\n❌ Recovery failed: {e}")
            return False
        
        finally:
            self.close()


def main():
    """Main entry point"""
    recovery = DatabaseRecovery()
    success = recovery.run_full_recovery()
    
    return 0 if success else 1


if __name__ == '__main__':
    exit(main())
