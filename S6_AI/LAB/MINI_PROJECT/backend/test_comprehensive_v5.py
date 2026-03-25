#!/usr/bin/env python3
"""
Comprehensive E2E test for Session 5 changes:
- 5 questions always generated (mock and written)
- interview_type matching (technical, behavioral, hr, system-design)
- Results data returned on completion with scores
- Database persistence (analytics, past sessions, dashboard)
- Increased Mistral token limits
"""

import json
import requests
import time

BASE = "http://127.0.0.1:5000"
PASS = 0
FAIL = 0
RESULTS = []

def log(status, msg):
    global PASS, FAIL
    if status:
        PASS += 1
        RESULTS.append(f"  PASS: {msg}")
        print(f"  PASS: {msg}")
    else:
        FAIL += 1
        RESULTS.append(f"  FAIL: {msg}")
        print(f"  FAIL: {msg}")


def get_token():
    """Register + login a fresh test user, return JWT token."""
    ts = int(time.time())
    email = f"test_v5_{ts}@test.com"
    pw = "TestPass123!"
    # Register
    r = requests.post(f"{BASE}/api/auth/register", json={
        "email": email, "password": pw, "first_name": "Test", "last_name": "V5",
        "field": "Software Engineering", "level": "Mid"
    })
    if r.status_code not in (200, 201):
        # Try login in case already registered
        pass
    # Login
    r = requests.post(f"{BASE}/api/auth/login", json={"email": email, "password": pw})
    data = r.json()
    token = data.get("access_token") or data.get("token")
    assert token, f"Login failed: {data}"
    return token, email


def headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def run_full_interview(token, question_type, interview_type, field="Software Engineering"):
    """Run a full interview and return the completion data."""
    h = headers(token)
    
    # Start interview
    start_data = {
        "field": field,
        "level": "Mid",
        "company": "Google",
        "question_type": question_type,
        "interview_type": interview_type,
        "mode": "text",
        "num_questions": 5
    }
    r = requests.post(f"{BASE}/api/interview/start", json=start_data, headers=h, timeout=120)
    assert r.status_code == 201, f"Start failed ({r.status_code}): {r.text[:200]}"
    data = r.json()
    uuid = data["interview_id"]
    questions = data["questions"]
    
    # Submit answers for all questions
    for i, q in enumerate(questions):
        if q.get("is_multiple_choice"):
            # MC: pick first option
            answer_data = {
                "question_id": q["id"],
                "selected_options": [0],
                "time_spent": 30
            }
        else:
            # Written: provide a text answer
            answer_data = {
                "question_id": q["id"],
                "answer": f"This is a detailed answer for question {i+1} about {interview_type} topics in {field}. "
                          f"I would approach this by analyzing the key concepts and applying best practices.",
                "time_spent": 60
            }
        r = requests.post(f"{BASE}/api/interview/{uuid}/submit", json=answer_data, headers=h, timeout=60)
        assert r.status_code == 201, f"Submit Q{i+1} failed ({r.status_code}): {r.text[:200]}"
    
    # Complete interview
    r = requests.post(f"{BASE}/api/interview/{uuid}/complete", headers=h, timeout=30)
    assert r.status_code == 200, f"Complete failed ({r.status_code}): {r.text[:200]}"
    return data, r.json()


print("\n" + "=" * 80)
print("SESSION 5 COMPREHENSIVE E2E TEST")
print("=" * 80)

token, email = get_token()
print(f"\nTest user: {email}")

# ─── TEST 1: Mock + Technical ─────────────────────────────────────────
print("\n--- TEST 1: Mock Interview (technical) ---")
start_data, complete_data = run_full_interview(token, "mock", "technical")
questions = start_data["questions"]
log(len(questions) == 5, f"Mock/technical: {len(questions)} questions generated (expected 5)")
mc_count = sum(1 for q in questions if q.get("is_multiple_choice"))
log(mc_count == 5, f"Mock/technical: {mc_count}/5 are multiple-choice")
for q in questions:
    if q.get("is_multiple_choice"):
        opts = q.get("options", [])
        log(len(opts) == 4, f"  Q has {len(opts)} options (expected 4)")
        break
log(complete_data.get("overall_score") is not None, f"Score returned: {complete_data.get('overall_score')}")
log(complete_data.get("performance_grade") is not None, f"Grade returned: {complete_data.get('performance_grade')}")
log(len(complete_data.get("qa_pairs", [])) == 5, f"qa_pairs count: {len(complete_data.get('qa_pairs', []))}")
log(complete_data.get("breakdown") is not None, f"Breakdown returned: {complete_data.get('breakdown')}")

# ─── TEST 2: Written + Technical ──────────────────────────────────────
print("\n--- TEST 2: Written Interview (technical) ---")
start_data, complete_data = run_full_interview(token, "written", "technical")
questions = start_data["questions"]
log(len(questions) == 5, f"Written/technical: {len(questions)} questions generated (expected 5)")
written_count = sum(1 for q in questions if not q.get("is_multiple_choice"))
log(written_count == 5, f"Written/technical: {written_count}/5 are text questions")
log(complete_data.get("overall_score") is not None, f"Score returned: {complete_data.get('overall_score')}")
log(len(complete_data.get("qa_pairs", [])) == 5, f"qa_pairs count: {len(complete_data.get('qa_pairs', []))}")

# ─── TEST 3: Mock + Behavioral ────────────────────────────────────────
print("\n--- TEST 3: Mock Interview (behavioral) ---")
start_data, complete_data = run_full_interview(token, "mock", "behavioral")
questions = start_data["questions"]
log(len(questions) == 5, f"Mock/behavioral: {len(questions)} questions generated (expected 5)")
mc_count = sum(1 for q in questions if q.get("is_multiple_choice"))
log(mc_count == 5, f"Mock/behavioral: {mc_count}/5 are multiple-choice")
log(complete_data.get("overall_score") is not None, f"Score returned: {complete_data.get('overall_score')}")

# ─── TEST 4: Written + Behavioral ─────────────────────────────────────
print("\n--- TEST 4: Written Interview (behavioral) ---")
start_data, complete_data = run_full_interview(token, "written", "behavioral")
questions = start_data["questions"]
log(len(questions) == 5, f"Written/behavioral: {len(questions)} questions generated (expected 5)")
log(complete_data.get("overall_score") is not None, f"Score returned: {complete_data.get('overall_score')}")

# ─── TEST 5: Mock + HR ────────────────────────────────────────────────
print("\n--- TEST 5: Mock Interview (hr) ---")
start_data, complete_data = run_full_interview(token, "mock", "hr")
questions = start_data["questions"]
log(len(questions) == 5, f"Mock/hr: {len(questions)} questions generated (expected 5)")
log(complete_data.get("overall_score") is not None, f"Score returned: {complete_data.get('overall_score')}")

# ─── TEST 6: Written + System Design ──────────────────────────────────
print("\n--- TEST 6: Written Interview (system-design) ---")
start_data, complete_data = run_full_interview(token, "written", "system-design")
questions = start_data["questions"]
log(len(questions) == 5, f"Written/system-design: {len(questions)} questions generated (expected 5)")
log(complete_data.get("overall_score") is not None, f"Score returned: {complete_data.get('overall_score')}")

# ─── TEST 7: Dashboard Stats ──────────────────────────────────────────
print("\n--- TEST 7: Dashboard Stats (DB persistence) ---")
h = headers(token)
r = requests.get(f"{BASE}/api/dashboard/stats", headers=h, timeout=15)
assert r.status_code == 200
stats = r.json()
log(stats.get("total_interviews", 0) >= 6, f"Dashboard total_interviews: {stats.get('total_interviews')} (expected >=6)")
log(stats.get("average_score", 0) > 0, f"Dashboard avg_score: {stats.get('average_score')}")
log(stats.get("total_questions_answered", 0) >= 30, f"Dashboard total_questions: {stats.get('total_questions_answered')} (expected >=30)")
recent = stats.get("recent_sessions", [])
log(len(recent) >= 5, f"Dashboard recent_sessions: {len(recent)} (expected >=5)")

# ─── TEST 8: Analytics ────────────────────────────────────────────────
print("\n--- TEST 8: Analytics (DB persistence) ---")
r = requests.get(f"{BASE}/api/analytics", headers=h, timeout=15)
assert r.status_code == 200
analytics = r.json()
log(analytics.get("total_interviews", 0) >= 6, f"Analytics total_interviews: {analytics.get('total_interviews')}")
log(analytics.get("average_score", 0) > 0, f"Analytics avg_score: {analytics.get('average_score')}")
all_interviews = analytics.get("all_interviews", [])
log(len(all_interviews) >= 6, f"Analytics all_interviews: {len(all_interviews)}")

# Check interview types are stored correctly
types_found = set(i.get("interview_type") for i in all_interviews)
log("technical" in types_found, f"Analytics has 'technical' interviews: {types_found}")
log("behavioral" in types_found, f"Analytics has 'behavioral' interviews: {types_found}")

# ─── TEST 9: Completion data has all required fields ──────────────────
print("\n--- TEST 9: Completion response completeness ---")
# Use the last complete_data
log("overall_score" in complete_data, "Completion has overall_score")
log("performance_grade" in complete_data, "Completion has performance_grade")
log("breakdown" in complete_data, "Completion has breakdown")
log("qa_pairs" in complete_data, "Completion has qa_pairs")
log("duration_seconds" in complete_data, "Completion has duration_seconds")
log("total_answered" in complete_data, "Completion has total_answered")
if complete_data.get("qa_pairs"):
    qa = complete_data["qa_pairs"][0]
    log("question_text" in qa, "qa_pair has question_text")
    log("score" in qa, "qa_pair has score")
    log("strengths" in qa, "qa_pair has strengths")
    log("weaknesses" in qa, "qa_pair has weaknesses")

# ─── SUMMARY ──────────────────────────────────────────────────────────
print("\n" + "=" * 80)
print(f"RESULTS: {PASS} PASSED, {FAIL} FAILED out of {PASS + FAIL} tests")
print("=" * 80)
if FAIL > 0:
    print("\nFailed tests:")
    for r in RESULTS:
        if "FAIL" in r:
            print(r)
print()
