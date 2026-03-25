from app import db, User, app

with app.app_context():
    # Reset passwords for all existing users
    users = User.query.all()
    
    if users:
        print("Resetting passwords for users:")
        for user in users:
            # Set a default password for demo accounts
            if 'demo' in user.email.lower():
                new_password = 'demo@123456'
            else:
                new_password = 'Welcome@123'
            
            user.set_password(new_password)
            db.session.add(user)
            print(f"  ✓ {user.email}: password reset to '{new_password}'")
        
        db.session.commit()
        print("\n✓ All passwords updated and saved to database!")
    else:
        print("No users found in database")
