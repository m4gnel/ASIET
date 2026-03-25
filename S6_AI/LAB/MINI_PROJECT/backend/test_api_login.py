import requests
import json

# Assuming the Flask server is running on localhost:5000
BASE_URL = 'http://127.0.0.1:5000'

# Test login with correct credentials
test_credentials = [
    {
        'email': 'demo@interviewcoach.ai',
        'password': 'demo@123456'
    },
    {
        'email': 'magnelolivero@gmail.com',
        'password': 'Welcome@123'
    }
]

print("Testing login endpoint:\n")
for creds in test_credentials:
    response = requests.post(
        f'{BASE_URL}/api/auth/login',
        json=creds,
        headers={'Content-Type': 'application/json'}
    )
    
    status = '✓ SUCCESS' if response.status_code == 200 else '✗ FAILED'
    print(f"{status}: {creds['email']}")
    print(f"         Status Code: {response.status_code}")
    
    data = response.json()
    if response.status_code == 200:
        print(f"         Token: {data.get('access_token', 'N/A')[:50]}...")
        print(f"         User: {data.get('user', {}).get('email')}")
    else:
        print(f"         Error: {data.get('error')}")
    print()
