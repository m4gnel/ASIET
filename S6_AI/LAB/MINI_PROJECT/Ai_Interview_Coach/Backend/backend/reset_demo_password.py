from app import db, User, app

with app.app_context():
    # Reset demo account password to original
    user = User.query.filter_by(email='demo@interviewcoach.ai').first()
    if user:
        user.set_password('demo@123456')
        db.session.commit()
        print("✓ Demo account password reset to: demo@123456")
    else:
        print("✗ Demo account not found")
