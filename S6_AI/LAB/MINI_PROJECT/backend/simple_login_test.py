import requests

API_BASE = 'http://localhost:5000/api/auth'

test_credentials = [
    {'email': 'demo@interviewcoach.ai', 'password': 'demo@123456'},
    {'email': 'magnelolivero@gmail.com', 'password': 'Welcome@123'}
]

print("Testing login credentials:")
print("="*60)

for creds in test_credentials:
    response = requests.post(f'{API_BASE}/login', json=creds)
    
    if response.status_code == 200:
        print(f"[OK] {creds['email']}")
        print(f"     Status: 200 - Login successful")
    else:
        print(f"[FAIL] {creds['email']}")
        print(f"       Status: {response.status_code}")
        data = response.json()
        print(f"       Error: {data.get('error')}")

print("="*60)
