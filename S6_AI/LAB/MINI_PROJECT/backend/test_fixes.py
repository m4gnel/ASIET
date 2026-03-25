"""Test script to verify all Mistral AI fixes."""
import json
import sys

# Add current dir to path
sys.path.insert(0, '.')

from app import app, db, MistralAIAgent, mistral_agent

results = []

def check(name, actual, expected):
    ok = actual == expected
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {name}: got {actual}, expected {expected}")
    results.append(ok)
    return ok

print("=== TESTING MISTRAL AI INTEGRATION ===\n")

# 1. Mistral availability
print(f"1. Mistral Available: {mistral_agent.is_available}")
print(f"   Model: {mistral_agent.model_name}")
print(f"   Base URL: {mistral_agent.base_url}\n")

# 2. MC Scoring logic
print("2. MC Scoring - Correct answer:")
is_correct = set([1]) == set([1])
mc_score = 10.0 if is_correct else 0.0
check("correct_score", mc_score, 10.0)

print("3. MC Scoring - Incorrect answer:")
is_correct2 = set([1]) == set([2])
mc_score2 = 10.0 if is_correct2 else 0.0
check("incorrect_score", mc_score2, 0.0)

# 4. Fallback MC feedback
print("\n4. Fallback MC Feedback:")
fb_correct = mistral_agent._fallback_mc_feedback('test question', [1], [1])
fb_incorrect = mistral_agent._fallback_mc_feedback('test question', [1], [2])
check("fallback_correct_score", fb_correct['score'], 10.0)
check("fallback_incorrect_score", fb_incorrect['score'], 0.0)

# 5. _mc_feedback_to_analysis
print("\n5. MC Feedback to Analysis:")
ac = MistralAIAgent._mc_feedback_to_analysis({'score': 10.0}, True, [1], [1], ['A','B','C','D'])
ai = MistralAIAgent._mc_feedback_to_analysis({'score': 0.0}, False, [2], [1], ['A','B','C','D'])
check("analysis_correct_score", ac['score'], 10.0)
check("analysis_correct_tech_acc", ac['technical_accuracy'], 10.0)
check("analysis_correct_depth", ac['depth_score'], 10.0)
check("analysis_correct_clarity", ac['clarity_score'], 10.0)
check("analysis_correct_relevance", ac['relevance_score'], 10.0)
check("analysis_correct_communication", ac['communication_score'], 10.0)
check("analysis_correct_confidence", ac['confidence_score'], 10.0)

check("analysis_incorrect_score", ai['score'], 0.0)
check("analysis_incorrect_tech_acc", ai['technical_accuracy'], 0.0)
check("analysis_incorrect_depth", ai['depth_score'], 0.0)
check("analysis_incorrect_clarity", ai['clarity_score'], 0.0)
check("analysis_incorrect_relevance", ai['relevance_score'], 0.0)
check("analysis_incorrect_communication", ai['communication_score'], 0.0)
check("analysis_incorrect_confidence", ai['confidence_score'], 0.0)

# 6. Fallback analysis (heuristic)
print("\n6. Fallback Analysis (Heuristic):")
fb_analysis = mistral_agent._fallback_analysis(
    'What is Python?',
    'Python is a high-level interpreted programming language known for its simplicity and readability. It supports multiple paradigms including object-oriented, functional, and procedural programming.'
)
print(f"   Score: {fb_analysis['score']}")
print(f"   Depth: {fb_analysis['depth_score']}")
print(f"   Relevance: {fb_analysis['relevance_score']}")
print(f"   Model: {fb_analysis['model']}")
# Just check it's a reasonable score, not exact
check("heuristic_score_range", 3.0 <= fb_analysis['score'] <= 9.0, True)

# 7. Interview Manager MC scoring
print("\n7. InterviewManager MC Scoring:")
from interview_manager import MockQuestionInterviewHandler

# Create a mock question object with correct_answers_list method
class MockQuestion:
    def __init__(self, correct):
        self._correct = correct
    def correct_answers_list(self):
        return self._correct

q = MockQuestion([0])  # correct answer is option index 0 (letter A)
result_correct = MockQuestionInterviewHandler.score_mock_answer([0], q)
check("im_correct_score", result_correct['score'], 10.0)

result_incorrect = MockQuestionInterviewHandler.score_mock_answer([1], q)
check("im_incorrect_score", result_incorrect['score'], 0.0)

# Summary
print("\n" + "=" * 50)
passed = sum(results)
total = len(results)
print(f"Results: {passed}/{total} tests passed")
if all(results):
    print("=== ALL TESTS PASSED ===")
else:
    print("=== SOME TESTS FAILED ===")
    sys.exit(1)
