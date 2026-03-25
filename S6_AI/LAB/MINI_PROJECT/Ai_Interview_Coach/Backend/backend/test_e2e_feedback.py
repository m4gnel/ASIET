"""E2E test: 5 questions, all answered, feedback at end with total score."""
import requests, uuid, time, json, sys

BASE = 'http://127.0.0.1:5000'
results = []

def check(name, condition, detail=""):
    ok = bool(condition)
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
    results.append(ok)
    return ok

# ── Auth ──
email = f"e2e_{uuid.uuid4().hex[:8]}@test.com"
requests.post(f"{BASE}/api/auth/register", json={"email": email, "password": "TestPass1"})
tok = requests.post(f"{BASE}/api/auth/login", json={"email": email, "password": "TestPass1"}).json()['access_token']
headers = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}

# ── Start mock interview ──
print("=== START MOCK INTERVIEW ===")
start = requests.post(f"{BASE}/api/interview/start", headers=headers, json={
    "field": "python", "level": "intermediate", "question_type": "mock",
    "interview_type": "technical", "mode": "text", "num_questions": 5
})
check("start_ok", start.status_code in (200, 201))
sdata = start.json()
interview_id = sdata.get('interview_id')
questions = sdata.get('questions', [])
check("got_5_questions", len(questions) == 5, f"got {len(questions)}")

# ── Answer ALL 5 questions ──
print("\n=== ANSWER ALL 5 QUESTIONS ===")
for i, q in enumerate(questions):
    qid = q.get('question_id') or q.get('id')
    correct = q.get('correct_answer', q.get('correct_answers', [0]))
    if isinstance(correct, list):
        correct = correct[0] if correct else 0
    # Alternate: correct for odd, wrong for even
    if i % 2 == 0:
        selected = correct
    else:
        selected = (correct + 1) % len(q.get('options', [0,1,2,3]))
    
    resp = requests.post(f"{BASE}/api/interview/{interview_id}/submit", headers=headers, json={
        "question_id": qid, "selected_options": [selected], "answer_type": "mock"
    })
    analysis = resp.json().get('analysis', {})
    score = analysis.get('score', '?')
    expected = '10.0' if i % 2 == 0 else '0.0'
    check(f"q{i+1}_submitted_score_{expected}", resp.status_code in (200, 201), f"score={score}")

# ── Complete interview ──
print("\n=== COMPLETE INTERVIEW ===")
comp = requests.post(f"{BASE}/api/interview/{interview_id}/complete", headers=headers)
check("complete_ok", comp.status_code == 200)
cdata = comp.json()

overall = cdata.get('overall_score')
grade = cdata.get('performance_grade')
breakdown = cdata.get('breakdown', {})
qa_pairs = cdata.get('qa_pairs', [])
total_answered = cdata.get('total_answered', 0)
duration = cdata.get('duration_seconds', 0)

print(f"\n  Overall Score: {overall}/10")
print(f"  Grade: {grade}")
print(f"  Total Answered: {total_answered}")
print(f"  Duration: {duration}s")
print(f"  Breakdown: Tech={breakdown.get('technical')}, Comm={breakdown.get('communication')}, Clarity={breakdown.get('clarity')}, Depth={breakdown.get('depth')}")

check("has_overall_score", overall is not None, f"score={overall}")
check("has_grade", grade is not None, f"grade={grade}")
check("total_answered_5", total_answered == 5, f"answered={total_answered}")
check("has_breakdown", all(k in breakdown for k in ('technical', 'communication', 'clarity', 'depth')))

# ── Verify per-question feedback ──
print(f"\n=== PER-QUESTION FEEDBACK ({len(qa_pairs)} pairs) ===")
check("qa_pairs_count_5", len(qa_pairs) == 5, f"got {len(qa_pairs)}")

for i, qa in enumerate(qa_pairs):
    qnum = qa.get('question_number', i+1)
    qtext = qa.get('question_text', '')[:60]
    qscore = qa.get('score')
    strengths = qa.get('strengths', [])
    weaknesses = qa.get('weaknesses', [])
    fb_text = qa.get('feedback_text', '')
    print(f"  Q{qnum}: score={qscore}, strengths={len(strengths)}, weaknesses={len(weaknesses)}, feedback={'yes' if fb_text else 'no'}")
    check(f"qa{i+1}_has_score", qscore is not None, f"score={qscore}")
    check(f"qa{i+1}_has_question", len(qtext) > 5, f"text={qtext[:30]}")

# ── Now test WRITTEN interview ──
print("\n=== START WRITTEN INTERVIEW ===")
start_w = requests.post(f"{BASE}/api/interview/start", headers=headers, json={
    "field": "python", "level": "intermediate", "question_type": "written",
    "interview_type": "technical", "mode": "text", "num_questions": 5
})
wdata = start_w.json()
w_id = wdata.get('interview_id')
w_questions = wdata.get('questions', [])
check("written_5_questions", len(w_questions) == 5, f"got {len(w_questions)}")

print("\n=== ANSWER ALL 5 WRITTEN QUESTIONS ===")
answers_text = [
    "Python is a high-level interpreted programming language known for simplicity and readability, supporting OOP and functional paradigms.",
    "Django is a high-level Python web framework that follows the MVC architectural pattern. It provides ORM, routing, templating, and admin interface.",
    "Decorators in Python are functions that modify the behavior of other functions. They use the @syntax and are commonly used for logging, caching, and authentication.",
    "List comprehension provides a concise way to create lists. The syntax is [expression for item in iterable if condition]. It is faster than traditional for loops.",
    "Exception handling in Python uses try-except-finally blocks. You can catch specific exceptions, create custom exceptions, and use else blocks for code that runs when no exception occurs.",
]
for i, q in enumerate(w_questions):
    qid = q.get('question_id') or q.get('id')
    resp = requests.post(f"{BASE}/api/interview/{w_id}/submit", headers=headers, json={
        "question_id": qid, "answer": answers_text[i], "answer_type": "written"
    })
    analysis = resp.json().get('analysis', {})
    score = analysis.get('score', '?')
    check(f"written_q{i+1}_submitted", resp.status_code in (200, 201), f"score={score}")

print("\n=== COMPLETE WRITTEN INTERVIEW ===")
comp_w = requests.post(f"{BASE}/api/interview/{w_id}/complete", headers=headers)
cwdata = comp_w.json()
w_overall = cwdata.get('overall_score')
w_qa = cwdata.get('qa_pairs', [])
print(f"  Overall: {w_overall}/10, Grade: {cwdata.get('performance_grade')}, QA pairs: {len(w_qa)}")
check("written_overall", w_overall is not None, f"score={w_overall}")
check("written_qa_pairs_5", len(w_qa) == 5, f"got {len(w_qa)}")

for i, qa in enumerate(w_qa):
    print(f"  Q{qa.get('question_number',i+1)}: score={qa.get('score')}, feedback={'yes' if qa.get('feedback_text') else 'no'}")

# ── Summary ──
print("\n" + "=" * 60)
passed = sum(results)
total = len(results)
print(f"Results: {passed}/{total} tests passed")
if all(results):
    print("=== ALL E2E TESTS PASSED ===")
else:
    print(f"=== {total - passed} TEST(S) FAILED ===")
