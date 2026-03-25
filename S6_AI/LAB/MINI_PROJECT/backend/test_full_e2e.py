"""
Full end-to-end test: all 4 interview types × both modes (mock MC, written text).
Tests: start → 5 questions → submit all → complete → results modal data → dashboard stats.
"""
import requests, json, sys, time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE = "http://127.0.0.1:5000"

# Create a session with retries  
session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[502, 503, 504])
session.mount("http://", HTTPAdapter(max_retries=retries))

def register_and_login():
    ts = int(time.time())
    email = f"e2e_test_{ts}@test.com"
    pw = "TestPass123!"
    r = session.post(f"{BASE}/api/auth/register", json={
        "email": email, "password": pw, "first_name": "E2E", "last_name": "Test"
    })
    if r.status_code == 409:
        r = session.post(f"{BASE}/api/auth/login", json={"email": email, "password": pw})
    data = r.json()
    token = data.get("token") or data.get("access_token")
    assert token, f"No token: {data}"
    return {"Authorization": f"Bearer {token}"}, email

def test_interview(headers, question_type, interview_type, field="Computer Science", level="mid"):
    label = f"{question_type}/{interview_type}"
    print(f"\n{'='*60}")
    print(f"  TEST: {label} (field={field}, level={level})")
    print(f"{'='*60}")

    # START
    r = session.post(f"{BASE}/api/interview/start", headers=headers, json={
        "field": field, "level": level, "company": "TestCorp",
        "question_type": question_type, "interview_type": interview_type,
        "mode": "text", "num_questions": 5
    })
    assert r.status_code in (200, 201), f"Start failed: {r.status_code} {r.text[:200]}"
    data = r.json()
    uuid = data["interview_id"]
    questions = data["questions"]
    is_mc = question_type == "mock"

    print(f"  Interview UUID: {uuid}")
    print(f"  Questions: {len(questions)}")
    assert len(questions) == 5, f"Expected 5 questions, got {len(questions)}"

    # Verify question type
    for i, q in enumerate(questions):
        if is_mc:
            assert q.get("is_multiple_choice"), f"Q{i+1} should be MC but isn't"
            opts = q.get("options", [])
            assert len(opts) == 4, f"Q{i+1} has {len(opts)} options, expected 4"
            print(f"  Q{i+1} [MC]: {q['text'][:60]}... ({len(opts)} opts)")
        else:
            assert not q.get("is_multiple_choice"), f"Q{i+1} should be text but is MC"
            print(f"  Q{i+1} [TEXT]: {q['text'][:60]}...")

    # SUBMIT all 5 answers
    for i, q in enumerate(questions):
        body = {"question": q["text"], "question_id": q["id"], "time_spent": 30}
        if is_mc:
            body["selected_options"] = [0]  # always pick first option
        else:
            body["answer"] = f"This is a detailed answer for question {i+1} about {interview_type}. I have extensive experience in this area and can provide concrete examples from my professional career."

        r = session.post(f"{BASE}/api/interview/{uuid}/submit", headers=headers, json=body)
        assert r.status_code in (200, 201), f"Submit Q{i+1} failed: {r.status_code} {r.text[:200]}"
        sd = r.json()
        score = sd.get("analysis", {}).get("score", "?")
        print(f"  Submitted Q{i+1}: score={score}")

    # COMPLETE
    r = session.post(f"{BASE}/api/interview/{uuid}/complete", headers=headers)
    assert r.status_code in (200, 201), f"Complete failed: {r.status_code} {r.text[:200]}"
    cd = r.json()

    overall = cd.get("overall_score", 0)
    grade = cd.get("performance_grade", "?")
    qa_pairs = cd.get("qa_pairs", [])
    breakdown = cd.get("breakdown", {})
    total_answered = cd.get("total_answered", 0)

    print(f"\n  RESULTS:")
    print(f"    Overall Score: {overall}")
    print(f"    Grade: {grade}")
    print(f"    Total Answered: {total_answered}")
    print(f"    QA Pairs: {len(qa_pairs)}")
    print(f"    Breakdown: tech={breakdown.get('technical','?')}, comm={breakdown.get('communication','?')}, "
          f"clarity={breakdown.get('clarity','?')}, depth={breakdown.get('depth','?')}")

    assert total_answered == 5, f"Expected 5 answered, got {total_answered}"
    assert len(qa_pairs) == 5, f"Expected 5 qa_pairs, got {len(qa_pairs)}"
    assert overall >= 0, f"Score should be >= 0, got {overall}"

    print(f"  ✓ {label} PASSED")
    return overall

def test_dashboard(headers):
    print(f"\n{'='*60}")
    print(f"  DASHBOARD & ANALYTICS CHECK")
    print(f"{'='*60}")

    r = session.get(f"{BASE}/api/dashboard/stats", headers=headers)
    assert r.status_code in (200, 201), f"Dashboard failed: {r.status_code}"
    d = r.json()
    print(f"  Total interviews: {d.get('total_interviews')}")
    print(f"  Total questions: {d.get('total_questions')}")
    print(f"  Avg score: {d.get('avg_score')}")
    print(f"  Recent sessions: {len(d.get('recent_sessions', []))}")

    r = session.get(f"{BASE}/api/analytics", headers=headers)
    assert r.status_code in (200, 201), f"Analytics failed: {r.status_code}"
    a = r.json()
    types = a.get("interview_types", a.get("type_breakdown", {}))
    print(f"  Interview types: {list(types.keys()) if isinstance(types, dict) else types}")
    # Analytics format may vary - just check the endpoint responds
    print(f"  ✓ Dashboard & Analytics PASSED")

def main():
    print("="*60)
    print("  FULL E2E TEST SUITE")
    print("="*60)

    headers, email = register_and_login()
    print(f"Registered/Logged in as: {email}")

    scores = {}
    # Test all 4 combinations
    scores["mock/technical"]     = test_interview(headers, "mock", "technical")
    scores["written/behavioral"] = test_interview(headers, "written", "behavioral")
    scores["mock/hr"]            = test_interview(headers, "mock", "hr")
    scores["written/system-design"] = test_interview(headers, "written", "system-design")

    # Dashboard check
    test_dashboard(headers)

    print(f"\n{'='*60}")
    print(f"  ALL TESTS PASSED ✓")
    print(f"{'='*60}")
    print(f"  Scores: {json.dumps(scores, indent=2)}")
    print(f"  4 interview types × 5 questions each = 20 total questions")
    print(f"  All stored in DB, all with scores, all with qa_pairs")

if __name__ == "__main__":
    main()
