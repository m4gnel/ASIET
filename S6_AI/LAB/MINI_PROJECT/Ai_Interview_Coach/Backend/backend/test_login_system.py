from app import db, User, app
from werkzeug.security import generate_password_hash, check_password_hash

with app.app_context():
    # Test 1: Try to fetch user and verify password
    user = User.query.filter_by(email='demo@interviewcoach.ai').first()
    if user:
        print(f"User found: {user.email}")
        print(f"Password hash: {user.password_hash[:50]}...")
        print(f"Check password 'demo': {user.check_password('demo')}")
        print(f"Check password 'demo123': {user.check_password('demo123')}")
        
        # Test 2: Set a new password and verify immediately
        print("\n--- Testing password set ---")
        user.set_password('testpassword123')
        print(f"New hash: {user.password_hash[:50]}...")
        print(f"Check new password: {user.check_password('testpassword123')}")
        db.session.commit()
        print("Password committed to database")
        
        # Test 3: Re-fetch user from database and verify
        print("\n--- Re-fetching user from database ---")
        db.session.refresh(user)
        print(f"Hash after refresh: {user.password_hash[:50]}...")
        print(f"Check password after refresh: {user.check_password('testpassword123')}")
    else:
        print("User not found")
