"""
E2E test: Full interview flow - start → submit 5 answers → complete → verify results + DB storage
Tests both mock (MC) and written interview types.
"""
import requests
import json
import time
import sys

BASE = 'http://127.0.0.1:5000'
EMAIL = f'e2etest_{int(time.time())}@test.com'
PASSWORD = 'Test123!'

def register_and_login():
    r = requests.post(f'{BASE}/api/auth/register', json={
        'email': EMAIL, 'password': PASSWORD,
        'first_name': 'E2E', 'last_name': 'Tester'
    })
    if r.status_code == 409:
        r = requests.post(f'{BASE}/api/auth/login', json={'email': EMAIL, 'password': PASSWORD})
    token = r.json().get('token') or r.json().get('access_token')
    assert token, f"Failed to get token: {r.status_code} {r.text}"
    return token

def test_interview_flow(token, question_type, interview_type, label):
    h = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    print(f"\n{'='*60}")
    print(f"TEST: {label} ({question_type}/{interview_type})")
    print(f"{'='*60}")

    # 1. Start interview
    r = requests.post(f'{BASE}/api/interview/start', headers=h, json={
        'field': 'Computer Science', 'level': 'mid', 'company': 'TestCorp',
        'question_type': question_type, 'interview_type': interview_type,
        'mode': 'text', 'num_questions': 5
    })
    assert r.status_code == 201, f"Start failed: {r.status_code} {r.text}"
    data = r.json()
    uuid = data['interview_id']
    questions = data['questions']
    assert len(questions) == 5, f"Expected 5 questions, got {len(questions)}"
    print(f"  ✓ Started interview {uuid} with {len(questions)} questions")

    # 2. Submit 5 answers
    for i, q in enumerate(questions):
        body = {
            'question': q['text'],
            'question_id': q.get('id'),
            'time_spent': 30
        }
        if q.get('is_multiple_choice'):
            # Backend expects integer indices (0-based), not option text
            body['selected_options'] = [0]
        else:
            body['answer'] = f"This is a detailed test answer for question {i+1} about {q['text'][:40]}. I have experience with this topic."

        r = requests.post(f'{BASE}/api/interview/{uuid}/submit', headers=h, json=body)
        assert r.status_code in (200, 201), f"Submit Q{i+1} failed: {r.status_code} {r.text}"
        resp = r.json()
        analysis = resp.get('analysis')
        pending = resp.get('analysis_pending', False)
        score = (analysis or {}).get('score', 'pending')
        print(f"  ✓ Submitted Q{i+1}: score={score}, pending={pending}, answer_id={resp.get('answer_id')}")

    # 3. Complete interview
    time.sleep(1)  # small delay to let any async analysis finish
    r = requests.post(f'{BASE}/api/interview/{uuid}/complete', headers=h)
    assert r.status_code == 200, f"Complete failed: {r.status_code} {r.text}"
    result = r.json()
    overall_score = result.get('overall_score', 0)
    grade = result.get('performance_grade', 'N/A')
    total_answered = result.get('total_answered', 0)
    feedback = result.get('overall_feedback', '')
    print(f"  ✓ Completed! Score: {overall_score}/10, Grade: {grade}, Answered: {total_answered}")
    print(f"    Feedback: {feedback[:120]}...")

    assert total_answered == 5, f"Expected 5 answered, got {total_answered}"
    assert overall_score > 0, f"Score should be > 0, got {overall_score}"

    return {'uuid': uuid, 'score': overall_score, 'grade': grade, 'answered': total_answered}

def test_db_storage(token):
    h = {'Authorization': f'Bearer {token}'}
    print(f"\n{'='*60}")
    print("TEST: Database Storage Verification")
    print(f"{'='*60}")

    # Check dashboard stats
    r = requests.get(f'{BASE}/api/dashboard/stats', headers=h)
    assert r.status_code == 200, f"Stats failed: {r.status_code}"
    stats = r.json()
    print(f"  Total interviews: {stats.get('total_interviews', 0)}")
    print(f"  Total questions answered: {stats.get('total_questions_answered', 0)}")
    print(f"  Avg score: {stats.get('average_score', 0)}")
    print(f"  Recent sessions: {len(stats.get('recent_sessions', []))}")

    assert stats.get('total_interviews', 0) >= 2, f"Expected >= 2 interviews in DB"
    assert stats.get('total_questions_answered', 0) >= 10, f"Expected >= 10 questions in DB, got {stats.get('total_questions_answered', 0)}"

    # Check analytics
    r = requests.get(f'{BASE}/api/analytics', headers=h)
    if r.status_code == 200:
        analytics = r.json()
        print(f"  Analytics data: {list(analytics.keys())}")
    
    print(f"  ✓ Database storage verified!")

def main():
    print("AI Interview Coach - Full E2E Test")
    print(f"Backend: {BASE}")
    print(f"Test user: {EMAIL}")

    # Health check
    r = requests.get(f'{BASE}/api/health')
    health = r.json()
    print(f"Backend status: {health['status']}, Mistral: {health['mistral']['available']}, DB: {health['database']}")
    assert health['status'] == 'healthy'
    assert health['mistral']['available']

    token = register_and_login()
    print(f"✓ Authenticated")

    results = []

    # Test 1: Mock/Technical (MC questions)
    r1 = test_interview_flow(token, 'mock', 'technical', 'Mock Technical (Multiple Choice)')
    results.append(r1)

    # Test 2: Written/Behavioral (text questions)
    r2 = test_interview_flow(token, 'written', 'behavioral', 'Written Behavioral (Text)')
    results.append(r2)

    # Test 3: DB storage
    test_db_storage(token)

    # Summary
    print(f"\n{'='*60}")
    print("FINAL SUMMARY")
    print(f"{'='*60}")
    all_pass = True
    for r in results:
        status = "PASS" if r['answered'] == 5 and r['score'] > 0 else "FAIL"
        if status == "FAIL":
            all_pass = False
        print(f"  {status}: {r['uuid'][:8]}... score={r['score']}, answered={r['answered']}, grade={r['grade']}")

    if all_pass:
        print("\n  ✅ ALL TESTS PASSED!")
    else:
        print("\n  ❌ SOME TESTS FAILED!")
        sys.exit(1)

if __name__ == '__main__':
    main()
