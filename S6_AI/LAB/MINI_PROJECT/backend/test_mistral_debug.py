#!/usr/bin/env python
"""Test script to verify Mistral AI question generation"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

print("="*60)
print("Testing Mistral AI Integration")
print("="*60)

from app import mistral_agent, db, Interview, Question, User

print(f"\nMistral AI Available: {mistral_agent.is_available}")
print(f"Base URL: {mistral_agent.base_url}")
print(f"Model: {mistral_agent.model_name}")

# Test question generation
print("\n" + "="*60)
print("TEST 1: Generate Questions - Software Engineering, Mid, Google")
print("="*60)

qs = mistral_agent.generate_questions("Software Engineering", "Mid", "Google", 3)
print(f"Generated {len(qs)} questions:")
for i, q in enumerate(qs, 1):
    print(f"\nQ{i}: {q.get('text', 'NO TEXT')[:100]}")
    print(f"    Field: {q.get('field')}")
    print(f"    Level: {q.get('level')}")
    print(f"    Company: {q.get('company')}")
    print(f"    Difficulty: {q.get('difficulty')}")

# Test question generation - different field
print("\n" + "="*60)
print("TEST 2: Generate Questions - Data Science, Senior, Meta")
print("="*60)

qs2 = mistral_agent.generate_questions("Data Science", "Senior", "Meta", 3)
print(f"Generated {len(qs2)} questions:")
for i, q in enumerate(qs2, 1):
    print(f"\nQ{i}: {q.get('text', 'NO TEXT')[:100]}")
    print(f"    Field: {q.get('field')}")
    print(f"    Level: {q.get('level')}")
    print(f"    Company: {q.get('company')}")

# Test answer analysis
print("\n" + "="*60)
print("TEST 3: Analyze Answer")
print("="*60)

test_q = "What is the difference between REST and GraphQL?"
test_a = "REST is an architectural style that uses HTTP methods and resources. It typically returns fixed data structures. GraphQL is a query language that allows clients to request exactly the data they need."

analysis = mistral_agent.analyze_answer(test_q, test_a, "Software Engineering", "Mid", "Google")
print(f"Overall Score: {analysis.get('score')}")
print(f"Technical Accuracy: {analysis.get('technical_accuracy')}")
print(f"Depth: {analysis.get('depth_score')}")
print(f"Clarity: {analysis.get('clarity_score')}")
print(f"Relevance: {analysis.get('relevance_score')}")
print(f"Communication: {analysis.get('communication_score')}")
print(f"Confidence: {analysis.get('confidence_score')}")
print(f"\nStrengths: {analysis.get('strengths')}")
print(f"Improvements: {analysis.get('weaknesses')}")
print(f"\nFeedback: {analysis.get('feedback')[:200]}...")

print("\n" + "="*60)
print("All Tests Completed!")
print("="*60)
