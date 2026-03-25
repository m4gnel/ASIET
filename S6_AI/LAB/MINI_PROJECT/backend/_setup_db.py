"""Reset database and verify app starts correctly."""
import os, sys

# Delete old database
db_path = 'interview_coach.db'
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"[OK] Deleted old database: {db_path}")
else:
    print("[INFO] No old database found")

# Import app and setup
try:
    from app import app, db, User, Interview, Question, Answer, Feedback, QuestionBank, mistral_agent, json
    print("[OK] App imports successful")
except Exception as e:
    print(f"[ERROR] Import failed: {e}")
    sys.exit(1)

# Create all tables
try:
    with app.app_context():
        db.create_all()
        print("[OK] All tables created")

        # Check table names
        from sqlalchemy import inspect as sa_inspect
        insp = sa_inspect(db.engine)
        tables = insp.get_table_names()
        print(f"[OK] Tables in DB: {tables}")

        # Seed demo user
        if not User.query.filter_by(email='demo@interviewcoach.ai').first():
            demo = User(
                email='demo@interviewcoach.ai',
                first_name='Demo', last_name='User',
                headline='Full Stack Developer | AI Interview Coach',
                experience_years=3, current_role='Software Developer',
                skills=json.dumps(['Python','JavaScript','React','Node.js','SQL','Docker']),
                dream_companies=json.dumps(['Google','Amazon','Microsoft']),
                target_roles=json.dumps(['Senior Software Engineer','Backend Engineer'])
            )
            demo.set_password('demo123456')
            db.session.add(demo)
            db.session.commit()
            print("[OK] Demo user created: demo@interviewcoach.ai / demo123456")

        # Seed question bank
        if QuestionBank.query.count() == 0:
            seed_qs = [
                QuestionBank(text="Design a scalable URL-shortening service. Walk through your architecture.", category='technical', field='software', level='senior', difficulty='hard', is_verified=True),
                QuestionBank(text="Explain the difference between a process and a thread and when you'd use each.", category='technical', field='software', level='mid', difficulty='medium', is_verified=True),
                QuestionBank(text="How do you handle class imbalance in a machine learning classification problem?", category='technical', field='data-science', level='mid', difficulty='medium', is_verified=True),
                QuestionBank(text="Describe a time you resolved a conflict with a teammate.", category='behavioral', field='software', level='mid', difficulty='easy', is_verified=True),
                QuestionBank(text="How would you measure the success of a new product feature launch?", category='technical', field='product', level='mid', difficulty='medium', is_verified=True),
                QuestionBank(text="Explain CAP theorem and how you'd design a payment system around those constraints.", category='technical', field='software', level='senior', difficulty='hard', is_verified=True),
            ]
            db.session.add_all(seed_qs)
            db.session.commit()
            print(f"[OK] Seeded {len(seed_qs)} questions to QuestionBank")

        total_users = User.query.count()
        print(f"[OK] Database ready - {total_users} user(s)")

except Exception as e:
    import traceback
    print(f"[ERROR] DB setup failed: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n[SUCCESS] Database reset and verified. Run: python app.py")
