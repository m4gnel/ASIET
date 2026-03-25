from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3

# Test password hashing
test_password = 'testpass123'
hashed = generate_password_hash(test_password)
print(f'Generated hash: {hashed[:50]}...')
print(f'Verify same password: {check_password_hash(hashed, test_password)}')
print(f'Verify wrong password: {check_password_hash(hashed, "wrong")}')

# Now check the actual user in database
conn = sqlite3.connect('interview_coach.db')
cursor = conn.cursor()
cursor.execute('SELECT email, password_hash FROM users WHERE email = ?', ('demo@interviewcoach.ai',))
row = cursor.fetchone()
if row:
    print(f'\nUser: {row[0]}')
    print(f'Hash stored: {row[1][:50]}...')
    # Try to verify with common passwords
    for pwd in ['demo', 'password', '123456', 'demo123']:
        result = check_password_hash(row[1], pwd)
        print(f'  Password "{pwd}": {result}')
