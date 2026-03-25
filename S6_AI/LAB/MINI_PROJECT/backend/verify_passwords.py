from app import db, User, app
from werkzeug.security import check_password_hash

with app.app_context():
    print("Verifying password reset:\n")
    users = User.query.all()
    
    test_passwords = {
        'demo@interviewcoach.ai': 'demo@123456',
        'magnelolivero@gmail.com': 'Welcome@123'
    }
    
    for user in users:
        pwd = test_passwords.get(user.email)
        if pwd:
            result = user.check_password(pwd)
            status = '✓ SUCCESS' if result else '✗ FAILED'
            print(f"{status}: {user.email}")
            print(f"         Password: {pwd}")
            print(f"         Verified: {result}\n")
