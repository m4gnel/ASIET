import requests, json
BASE = 'http://127.0.0.1:5000'

# Register/login
r = requests.post(f'{BASE}/api/auth/register', json={'email':'debugq2@test.com','password':'Test123!','first_name':'Debug','last_name':'Q'})
if r.status_code == 409:
    r = requests.post(f'{BASE}/api/auth/login', json={'email':'debugq2@test.com','password':'Test123!'})
token = r.json().get('token') or r.json().get('access_token')
h = {'Authorization': f'Bearer {token}'}

# Test MOCK/TECHNICAL
print("=" * 50)
print("TEST 1: MOCK/TECHNICAL")
r1 = requests.post(f'{BASE}/api/interview/start', headers=h, json={
    'field': 'Computer Science', 'level': 'mid', 'company': 'TestCorp',
    'question_type': 'mock', 'interview_type': 'technical', 'mode': 'text', 'num_questions': 5
})
d1 = r1.json()
qs1 = d1.get('questions', [])
print(f"Status: {r1.status_code}, Questions returned: {len(qs1)}")
for i, q in enumerate(qs1):
    print(f"  Q{i+1}: mc={q.get('is_multiple_choice')}, opts={len(q.get('options', []))}, text={q['text'][:70]}")

# Test WRITTEN/BEHAVIORAL
print("=" * 50)
print("TEST 2: WRITTEN/BEHAVIORAL")
r2 = requests.post(f'{BASE}/api/interview/start', headers=h, json={
    'field': 'Computer Science', 'level': 'mid', 'company': 'TestCorp',
    'question_type': 'written', 'interview_type': 'behavioral', 'mode': 'text', 'num_questions': 5
})
d2 = r2.json()
qs2 = d2.get('questions', [])
print(f"Status: {r2.status_code}, Questions returned: {len(qs2)}")
for i, q in enumerate(qs2):
    print(f"  Q{i+1}: mc={q.get('is_multiple_choice')}, text={q['text'][:70]}")

# Test MOCK/HR
print("=" * 50)
print("TEST 3: MOCK/HR")
r3 = requests.post(f'{BASE}/api/interview/start', headers=h, json={
    'field': 'Computer Science', 'level': 'mid', 'company': 'TestCorp',
    'question_type': 'mock', 'interview_type': 'hr', 'mode': 'text', 'num_questions': 5
})
d3 = r3.json()
qs3 = d3.get('questions', [])
print(f"Status: {r3.status_code}, Questions returned: {len(qs3)}")
for i, q in enumerate(qs3):
    print(f"  Q{i+1}: mc={q.get('is_multiple_choice')}, opts={len(q.get('options', []))}, text={q['text'][:70]}")

# Test WRITTEN/SYSTEM-DESIGN
print("=" * 50)
print("TEST 4: WRITTEN/SYSTEM-DESIGN")
r4 = requests.post(f'{BASE}/api/interview/start', headers=h, json={
    'field': 'Computer Science', 'level': 'mid', 'company': 'TestCorp',
    'question_type': 'written', 'interview_type': 'system-design', 'mode': 'text', 'num_questions': 5
})
d4 = r4.json()
qs4 = d4.get('questions', [])
print(f"Status: {r4.status_code}, Questions returned: {len(qs4)}")
for i, q in enumerate(qs4):
    print(f"  Q{i+1}: mc={q.get('is_multiple_choice')}, text={q['text'][:70]}")

print("=" * 50)
print(f"SUMMARY: mock/tech={len(qs1)}, written/beh={len(qs2)}, mock/hr={len(qs3)}, written/sd={len(qs4)}")
all_five = all(len(x) == 5 for x in [qs1, qs2, qs3, qs4])
print(f"All return 5 questions: {all_five}")
