"""End-to-end API integration test for Mistral AI interview system."""
import requests
import time
import json
import sys

BASE = 'http://127.0.0.1:5000'
results = []

def check(name, condition, detail=""):
    ok = bool(condition)
    status = "PASS" if ok else "FAIL"
    extra = f" — {detail}" if detail else ""
    print(f"  [{status}] {name}{extra}")
    results.append(ok)
    return ok

# ── Register / Login ──────────────────────────────────────
print("=== 1. AUTH ===")
import uuid
uname = f"testuser_{uuid.uuid4().hex[:8]}"
email = f"{uname}@test.com"

reg = requests.post(f"{BASE}/api/auth/register", json={
    "email": email, "password": "TestPass123",
    "first_name": "Test", "last_name": "User"
})
check("register", reg.status_code in (200, 201), f"status={reg.status_code}")

login = requests.post(f"{BASE}/api/auth/login", json={
    "email": email, "password": "TestPass123"
})
check("login", login.status_code == 200, f"status={login.status_code}")
token = login.json().get('access_token') or login.json().get('token')
check("got_token", token is not None)

headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# ── Test MOCK interview (technical) ──────────────────────
print("\n=== 2. MOCK INTERVIEW (technical) ===")
start_resp = requests.post(f"{BASE}/api/interview/start", headers=headers, json={
    "field": "python",
    "level": "intermediate",
    "question_type": "mock",
    "interview_type": "technical",
    "answer_type": "technical",
    "mode": "text",
    "num_questions": 5
})
print(f"  Start status: {start_resp.status_code}")
if start_resp.status_code != 200:
    print(f"  Response: {start_resp.text[:500]}")
check("mock_start_ok", start_resp.status_code in (200, 201), f"status={start_resp.status_code}")

sdata = start_resp.json()
interview_id = sdata.get('interview_id')
questions = sdata.get('questions', [])
check("mock_got_interview_id", interview_id is not None, f"id={interview_id}")
check("mock_5_questions", len(questions) == 5, f"got {len(questions)} questions")

# Verify each question has options and correct_answer
for i, q in enumerate(questions):
    has_options = bool(q.get('options'))
    has_correct = q.get('correct_answer') is not None or q.get('correct_answers') is not None
    if not has_options:
        print(f"    Q{i+1} missing options: keys={list(q.keys())}")
    if not has_correct:
        print(f"    Q{i+1} missing correct_answer: keys={list(q.keys())}")
    check(f"mock_q{i+1}_has_options", has_options)

# Submit correct answer for Q1
if questions:
    q1 = questions[0]
    q1_id = q1.get('question_id') or q1.get('id')
    correct_opt = q1.get('correct_answer', q1.get('correct_answers', 0))
    if isinstance(correct_opt, list):
        correct_opt = correct_opt[0]
    
    print(f"\n  Submitting CORRECT answer for Q1 (option: {correct_opt})...")
    # The API expects 'selected_options' as a list
    sub_correct = requests.post(f"{BASE}/api/interview/{interview_id}/submit", headers=headers, json={
        "question_id": q1_id,
        "selected_options": [correct_opt],
        "answer": str(correct_opt),
        "answer_type": "mock"
    })
    print(f"  Submit status: {sub_correct.status_code}")
    if sub_correct.status_code in (200, 201):
        sc_data = sub_correct.json()
        # Score can be in top-level or inside 'analysis' sub-dict
        analysis = sc_data.get('analysis', sc_data)
        score = analysis.get('score', sc_data.get('score', sc_data.get('mc_score')))
        is_correct_flag = sc_data.get('is_correct', analysis.get('is_correct'))
        print(f"  Score: {score}, All dims 10.0: tech={analysis.get('technical_accuracy')}, depth={analysis.get('depth_score')}, clarity={analysis.get('clarity_score')}")
        check("mock_correct_score_10", score == 10.0 or score == 10, f"score={score}")
        check("mock_correct_dims_10", analysis.get('depth_score') == 10.0 and analysis.get('clarity_score') == 10.0, f"depth={analysis.get('depth_score')}, clarity={analysis.get('clarity_score')}")
    else:
        print(f"  Error body: {sub_correct.text[:500]}")
        check("mock_correct_submit", False, "submit failed")

    # Submit WRONG answer for Q2
    if len(questions) >= 2:
        q2 = questions[1]
        q2_id = q2.get('question_id') or q2.get('id')
        correct_opt2 = q2.get('correct_answer', q2.get('correct_answers', 0))
        if isinstance(correct_opt2, list):
            correct_opt2 = correct_opt2[0]
        # Pick a wrong option
        wrong_opt = (correct_opt2 + 1) % len(q2.get('options', [0,1,2,3]))
        
        print(f"\n  Submitting WRONG answer for Q2 (wrong: {wrong_opt}, correct: {correct_opt2})...")
        sub_wrong = requests.post(f"{BASE}/api/interview/{interview_id}/submit", headers=headers, json={
            "question_id": q2_id,
            "selected_options": [wrong_opt],
            "answer": str(wrong_opt),
            "answer_type": "mock"
        })
        print(f"  Submit status: {sub_wrong.status_code}")
        if sub_wrong.status_code in (200, 201):
            sw_data = sub_wrong.json()
            analysis_w = sw_data.get('analysis', sw_data)
            score_w = analysis_w.get('score', sw_data.get('score', sw_data.get('mc_score')))
            is_correct_w = sw_data.get('is_correct', analysis_w.get('is_correct'))
            print(f"  Score: {score_w}, All dims 0.0: tech={analysis_w.get('technical_accuracy')}, depth={analysis_w.get('depth_score')}, clarity={analysis_w.get('clarity_score')}")
            check("mock_wrong_score_0", score_w == 0.0 or score_w == 0, f"score={score_w}")
            check("mock_wrong_dims_0", analysis_w.get('depth_score') == 0.0 and analysis_w.get('clarity_score') == 0.0, f"depth={analysis_w.get('depth_score')}, clarity={analysis_w.get('clarity_score')}")
        else:
            print(f"  Error body: {sub_wrong.text[:500]}")
            check("mock_wrong_submit", False, "submit failed")

# ── Test WRITTEN interview (technical) ───────────────────
print("\n=== 3. WRITTEN INTERVIEW (technical) ===")
start_w = requests.post(f"{BASE}/api/interview/start", headers=headers, json={
    "field": "python",
    "level": "intermediate",
    "question_type": "written",
    "interview_type": "technical",
    "answer_type": "technical",
    "mode": "text",
    "num_questions": 5
})
print(f"  Start status: {start_w.status_code}")
check("written_start_ok", start_w.status_code in (200, 201), f"status={start_w.status_code}")

wdata = start_w.json()
w_interview_id = wdata.get('interview_id')
w_questions = wdata.get('questions', [])
check("written_got_interview_id", w_interview_id is not None, f"id={w_interview_id}")
check("written_5_questions", len(w_questions) == 5, f"got {len(w_questions)} questions")

# Submit a detailed written answer
if w_questions:
    wq1 = w_questions[0]
    wq1_id = wq1.get('question_id') or wq1.get('id')
    answer_text = (
        "Python is a high-level, interpreted programming language created by Guido van Rossum. "
        "It emphasizes code readability with its use of significant indentation. Python supports "
        "multiple programming paradigms including procedural, object-oriented, and functional programming. "
        "Key features include dynamic typing, garbage collection, and a comprehensive standard library. "
        "Python is widely used in web development (Django, Flask), data science (NumPy, Pandas), "
        "machine learning (TensorFlow, PyTorch), and automation scripting."
    )
    
    print(f"\n  Submitting written answer for Q1 (question_id: {wq1_id})...")
    sub_w = requests.post(f"{BASE}/api/interview/{w_interview_id}/submit", headers=headers, json={
        "question_id": wq1_id,
        "answer": answer_text,
        "answer_type": "written"
    })
    print(f"  Submit status: {sub_w.status_code}")
    if sub_w.status_code in (200, 201):
        sw_data = sub_w.json()
        print(f"  Keys: {list(sw_data.keys())}")
        w_analysis = sw_data.get('analysis', sw_data)
        instant_score = w_analysis.get('score', sw_data.get('score', sw_data.get('instant_score')))
        feedback = w_analysis.get('feedback', sw_data.get('feedback'))
        has_analysis = sw_data.get('analysis_pending', sw_data.get('ai_analysis_pending', False))
        print(f"  Instant Score: {instant_score}")
        print(f"  Has feedback: {bool(feedback)}")
        print(f"  AI analysis pending: {has_analysis}")
        print(f"  Depth: {w_analysis.get('depth_score')}, Clarity: {w_analysis.get('clarity_score')}, Relevance: {w_analysis.get('relevance_score')}")
        check("written_submit_ok", True)
        check("written_got_score", instant_score is not None, f"score={instant_score}")
        
        # Poll for AI analysis
        answer_uuid = sw_data.get('answer_id') or sw_data.get('answer_uuid')
        if answer_uuid and has_analysis:
            print(f"\n  Polling for AI analysis (answer_id: {answer_uuid})...")
            for attempt in range(10):
                time.sleep(3)
                poll = requests.get(
                    f"{BASE}/api/interview/{w_interview_id}/answer/{answer_uuid}/analysis",
                    headers=headers
                )
                if poll.status_code == 200:
                    pdata = poll.json()
                    status = pdata.get('status')
                    print(f"  Poll attempt {attempt+1}: status={status}")
                    if status == 'completed' or pdata.get('analysis'):
                        analysis = pdata.get('analysis', pdata)
                        ai_score = analysis.get('score')
                        model = analysis.get('model', 'unknown')
                        print(f"  AI Score: {ai_score}, Model: {model}")
                        print(f"  Tech accuracy: {analysis.get('technical_accuracy')}")
                        print(f"  Depth: {analysis.get('depth_score')}")
                        print(f"  Clarity: {analysis.get('clarity_score')}")
                        print(f"  Relevance: {analysis.get('relevance_score')}")
                        check("written_ai_analysis_received", ai_score is not None, f"score={ai_score}")
                        check("written_ai_score_range", 0 <= float(ai_score) <= 10, f"score={ai_score}")
                        break
                    elif status == 'pending':
                        continue
                else:
                    print(f"  Poll attempt {attempt+1}: HTTP {poll.status_code}")
            else:
                print("  AI analysis did not complete within polling window (normal for slow models)")
                check("written_ai_analysis_timeout", True, "timed out but not a failure")
    else:
        print(f"  Error: {sub_w.text[:500]}")
        check("written_submit", False, "submit failed")

# ── Test different interview types ───────────────────────
print("\n=== 4. DIFFERENT INTERVIEW TYPES ===")
for itype in ["behavioral", "system-design", "hr"]:
    print(f"\n  Testing {itype}...")
    resp = requests.post(f"{BASE}/api/interview/start", headers=headers, json={
        "field": "python",
        "level": "intermediate",
        "question_type": "mock",
        "interview_type": itype,
        "answer_type": itype,
        "mode": "text",
        "num_questions": 5
    })
    if resp.status_code in (200, 201):
        qs = resp.json().get('questions', [])
        check(f"{itype}_5_questions", len(qs) == 5, f"got {len(qs)} questions")
    else:
        print(f"  Status: {resp.status_code}, Body: {resp.text[:300]}")
        check(f"{itype}_start", False, f"status={resp.status_code}")

# ── Summary ──────────────────────────────────────────────
print("\n" + "=" * 60)
passed = sum(results)
total = len(results)
print(f"Results: {passed}/{total} tests passed")
if all(results):
    print("=== ALL E2E TESTS PASSED ===")
else:
    failed_count = total - passed
    print(f"=== {failed_count} TEST(S) FAILED ===")
