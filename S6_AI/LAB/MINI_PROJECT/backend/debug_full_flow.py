#!/usr/bin/env python3
"""Full flow debug: register, login, mock+written interviews, dashboard, analytics."""
import requests, json, time

BASE = 'http://127.0.0.1:5000'

# Register + Login
ts = int(time.time())
email = f'debug_{ts}@test.com'
pw = 'TestPass123!'
r = requests.post(f'{BASE}/api/auth/register', json={
    'email': email, 'password': pw, 'first_name': 'Debug', 'last_name': 'User',
    'field': 'Software Engineering', 'level': 'Mid'
})
print(f'Register: {r.status_code}')
r = requests.post(f'{BASE}/api/auth/login', json={'email': email, 'password': pw})
token = r.json().get('access_token') or r.json().get('token')
print(f'Login: {r.status_code}, token={bool(token)}')
h = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

# ─── MOCK TECHNICAL INTERVIEW ────────────────────────────────────────
print('\n=== MOCK TECHNICAL INTERVIEW ===')
r = requests.post(f'{BASE}/api/interview/start', json={
    'field': 'Software Engineering', 'level': 'Mid', 'company': 'Google',
    'question_type': 'mock', 'interview_type': 'technical',
    'mode': 'text', 'num_questions': 5
}, headers=h, timeout=120)
print(f'Start: {r.status_code}')
data = r.json()
uuid = data['interview_id']
questions = data['questions']
print(f'Questions count: {len(questions)}')
for i, q in enumerate(questions):
    mc = q.get('is_multiple_choice', False)
    opts = q.get('options', [])
    ca = q.get('correct_answers', [])
    txt = q['text'][:80]
    print(f'  Q{i+1}: MC={mc}, opts={len(opts)}, correct={ca}, text={txt}...')

# Submit answers
for i, q in enumerate(questions):
    if q.get('is_multiple_choice'):
        body = {'question_id': q['id'], 'selected_options': [0], 'time_spent': 30}
    else:
        body = {'question_id': q['id'], 'answer': 'Test answer about software engineering.', 'time_spent': 60}
    r = requests.post(f'{BASE}/api/interview/{uuid}/submit', json=body, headers=h, timeout=60)
    score = r.json().get('analysis', {}).get('score')
    print(f'  Submit Q{i+1}: status={r.status_code}, score={score}')

# Complete
r = requests.post(f'{BASE}/api/interview/{uuid}/complete', headers=h, timeout=30)
print(f'Complete: {r.status_code}')
cd = r.json()
print(f'  overall_score: {cd.get("overall_score")}')
print(f'  grade: {cd.get("performance_grade")}')
print(f'  qa_pairs: {len(cd.get("qa_pairs", []))}')
print(f'  breakdown: {cd.get("breakdown")}')
print(f'  total_answered: {cd.get("total_answered")}')
print(f'  duration: {cd.get("duration_seconds")}')

# ─── WRITTEN BEHAVIORAL INTERVIEW ────────────────────────────────────
print('\n=== WRITTEN BEHAVIORAL INTERVIEW ===')
r = requests.post(f'{BASE}/api/interview/start', json={
    'field': 'Software Engineering', 'level': 'Mid', 'company': 'Google',
    'question_type': 'written', 'interview_type': 'behavioral',
    'mode': 'text', 'num_questions': 5
}, headers=h, timeout=120)
print(f'Start: {r.status_code}')
data2 = r.json()
uuid2 = data2['interview_id']
questions2 = data2['questions']
print(f'Questions count: {len(questions2)}')
for i, q in enumerate(questions2):
    mc = q.get('is_multiple_choice', False)
    txt = q['text'][:100]
    print(f'  Q{i+1}: MC={mc}, text={txt}...')

# Submit answers
for i, q in enumerate(questions2):
    body = {
        'question_id': q['id'],
        'answer': (
            'In my experience working at a tech company, I led a team through a critical project. '
            'I used the STAR method: Situation - we had a tight deadline. '
            'Task - I was responsible for architecting the solution. '
            'Action - I organized daily standups and broke the work into sprints. '
            'Result - we delivered on time with 99 percent test coverage.'
        ),
        'time_spent': 120
    }
    r = requests.post(f'{BASE}/api/interview/{uuid2}/submit', json=body, headers=h, timeout=60)
    score = r.json().get('analysis', {}).get('score')
    print(f'  Submit Q{i+1}: status={r.status_code}, score={score}')

# Complete
r = requests.post(f'{BASE}/api/interview/{uuid2}/complete', headers=h, timeout=30)
print(f'Complete: {r.status_code}')
cd2 = r.json()
print(f'  overall_score: {cd2.get("overall_score")}')
print(f'  grade: {cd2.get("performance_grade")}')
print(f'  qa_pairs: {len(cd2.get("qa_pairs", []))}')

# ─── MOCK HR INTERVIEW ───────────────────────────────────────────────
print('\n=== MOCK HR INTERVIEW ===')
r = requests.post(f'{BASE}/api/interview/start', json={
    'field': 'Software Engineering', 'level': 'Mid', 'company': 'Google',
    'question_type': 'mock', 'interview_type': 'hr',
    'mode': 'text', 'num_questions': 5
}, headers=h, timeout=120)
print(f'Start: {r.status_code}')
data3 = r.json()
uuid3 = data3['interview_id']
questions3 = data3['questions']
print(f'Questions count: {len(questions3)}')
for i, q in enumerate(questions3):
    mc = q.get('is_multiple_choice', False)
    opts = q.get('options', [])
    txt = q['text'][:80]
    print(f'  Q{i+1}: MC={mc}, opts={len(opts)}, text={txt}...')

# Submit answers
for i, q in enumerate(questions3):
    if q.get('is_multiple_choice'):
        # Pick the correct answer this time
        ca = q.get('correct_answers', [0])
        body = {'question_id': q['id'], 'selected_options': ca, 'time_spent': 30}
    else:
        body = {'question_id': q['id'], 'answer': 'My career goal is to become a senior engineer.', 'time_spent': 60}
    r = requests.post(f'{BASE}/api/interview/{uuid3}/submit', json=body, headers=h, timeout=60)
    score = r.json().get('analysis', {}).get('score')
    print(f'  Submit Q{i+1}: status={r.status_code}, score={score}')

# Complete
r = requests.post(f'{BASE}/api/interview/{uuid3}/complete', headers=h, timeout=30)
print(f'Complete: {r.status_code}')
cd3 = r.json()
print(f'  overall_score: {cd3.get("overall_score")}')
print(f'  grade: {cd3.get("performance_grade")}')
print(f'  qa_pairs: {len(cd3.get("qa_pairs", []))}')

# ─── WRITTEN SYSTEM-DESIGN INTERVIEW ─────────────────────────────────
print('\n=== WRITTEN SYSTEM-DESIGN INTERVIEW ===')
r = requests.post(f'{BASE}/api/interview/start', json={
    'field': 'Software Engineering', 'level': 'Senior', 'company': 'Amazon',
    'question_type': 'written', 'interview_type': 'system-design',
    'mode': 'text', 'num_questions': 5
}, headers=h, timeout=120)
print(f'Start: {r.status_code}')
data4 = r.json()
uuid4 = data4['interview_id']
questions4 = data4['questions']
print(f'Questions count: {len(questions4)}')
for i, q in enumerate(questions4):
    txt = q['text'][:100]
    print(f'  Q{i+1}: text={txt}...')

# Submit answers
for i, q in enumerate(questions4):
    body = {
        'question_id': q['id'],
        'answer': (
            'For this system design, I would use a microservices architecture with API Gateway. '
            'The system needs horizontal scaling with load balancers distributing traffic. '
            'For data storage, a combination of PostgreSQL for structured data and Redis for caching. '
            'Event-driven communication via Kafka for async processing between services. '
            'CDN for static assets, and monitoring with Prometheus and Grafana.'
        ),
        'time_spent': 180
    }
    r = requests.post(f'{BASE}/api/interview/{uuid4}/submit', json=body, headers=h, timeout=60)
    score = r.json().get('analysis', {}).get('score')
    print(f'  Submit Q{i+1}: status={r.status_code}, score={score}')

# Complete
r = requests.post(f'{BASE}/api/interview/{uuid4}/complete', headers=h, timeout=30)
print(f'Complete: {r.status_code}')
cd4 = r.json()
print(f'  overall_score: {cd4.get("overall_score")}')
print(f'  grade: {cd4.get("performance_grade")}')
print(f'  qa_pairs: {len(cd4.get("qa_pairs", []))}')

# ─── DASHBOARD STATS ─────────────────────────────────────────────────
print('\n=== DASHBOARD STATS ===')
r = requests.get(f'{BASE}/api/dashboard/stats', headers=h, timeout=15)
stats = r.json()
print(f'  total_interviews: {stats.get("total_interviews")}')
print(f'  total_questions: {stats.get("total_questions_answered")}')
print(f'  avg_score: {stats.get("average_score")}')
print(f'  best_score: {stats.get("best_score")}')
print(f'  recent_sessions: {len(stats.get("recent_sessions", []))}')
for s in stats.get('recent_sessions', []):
    print(f'    - {s.get("interview_type")}/{s.get("question_type")}: score={s.get("overall_score")}, status={s.get("status")}')

# ─── ANALYTICS ────────────────────────────────────────────────────────
print('\n=== ANALYTICS ===')
r = requests.get(f'{BASE}/api/analytics', headers=h, timeout=15)
an = r.json()
print(f'  total_interviews: {an.get("total_interviews")}')
print(f'  all_interviews: {len(an.get("all_interviews", []))}')
types = set(i.get('interview_type') for i in an.get('all_interviews', []))
print(f'  interview_types: {types}')
print(f'  avg_score: {an.get("average_score")}')
print(f'  field_breakdown: {an.get("field_breakdown")}')

print('\n=== ALL TESTS DONE ===')
