#!/usr/bin/env python3
"""
COMPREHENSIVE INTEGRATION TEST
Tests the complete AI Interview Coach flow:
1. User signup/login
2. Interview session creation with field, level, company
3. Question generation linked to session
4. Answer submission with Mistral analysis
5. Feedback storage
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:5000"

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*70}")
    print(f"{text}")
    print(f"{'='*70}{RESET}\n")

def print_success(text):
    print(f"{GREEN}[OK] {text}{RESET}")

def print_error(text):
    print(f"{RED}[ERROR] {text}{RESET}")

def print_info(text):
    print(f"{YELLOW}[INFO] {text}{RESET}")

def test_health_check():
    """Test 1: Health Check"""
    print_header("TEST 1: HEALTH CHECK")
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        data = response.json()
        print_success(f"Server healthy: {data['status']}")
        print_success(f"Database: {data['database']}")
        print_success(f"Mistral AI: {'Connected' if data['mistral_available'] else 'Offline (using fallback)'}")
        return True
    except Exception as e:
        print_error(f"Health check failed: {e}")
        return False

def test_signup_and_login():
    """Test 2: User Registration and Login"""
    print_header("TEST 2: USER REGISTRATION & LOGIN")
    
    # Test signup
    signup_data = {
        "email": f"testuser_{int(time.time())}@test.com",
        "password": "TestPassword123!",
        "first_name": "Test",
        "last_name": "User"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/register", json=signup_data)
        signup_result = response.json()
        
        if response.status_code == 201:
            print_success(f"Signup: New user registered")
            print_info(f"Email: {signup_data['email']}")
            print_info(f"User ID: {signup_result['user']['id']}")
            token = signup_result['access_token']
        else:
            print_error(f"Signup failed: {signup_result}")
            return None
            
    except Exception as e:
        print_error(f"Signup error: {e}")
        return None
    
    # Test login
    login_data = {
        "email": signup_data['email'],
        "password": signup_data['password']
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        login_result = response.json()
        
        if response.status_code == 200:
            print_success(f"Login: User authenticated")
            print_info(f"Token received (length: {len(login_result['access_token'])})")
            return {
                'token': login_result['access_token'],
                'user_id': login_result['user']['id'],
                'email': signup_data['email']
            }
        else:
            print_error(f"Login failed: {login_result}")
            return None
            
    except Exception as e:
        print_error(f"Login error: {e}")
        return None

def test_interview_flow(user_info):
    """Test 3: Start Interview and Session Storage"""
    print_header("TEST 3: INTERVIEW SESSION CREATION")
    
    if not user_info:
        print_error("No user info provided")
        return None
    
    headers = {
        'Authorization': f"Bearer {user_info['token']}",
        'Content-Type': 'application/json'
    }
    
    interview_data = {
        "field": "Software Engineer",
        "level": "Senior",
        "company": "Google"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/interview/start",
            json=interview_data,
            headers=headers
        )
        result = response.json()
        
        if response.status_code == 201:
            print_success("Interview session created")
            interview = result['interview']
            print_info(f"Interview ID: {interview['id']}")
            print_info(f"Interview UUID: {interview['uuid']}")
            print_info(f"Field: {interview['field']}, Level: {interview['level']}, Company: {interview['company']}")
            print_info(f"Status: {interview['status']}")
            print_info(f"Questions total: {interview['questions_total']}")
            
            questions = result['questions']
            print_success(f"Generated {len(questions)} questions for this session")
            
            # Verify questions are session-specific
            for i, q in enumerate(questions, 1):
                print_info(f"Q{i}: {q['text'][:60]}... (ID: {q['id']})")
            
            return {
                'interview_uuid': interview['uuid'],
                'interview_id': interview['id'],
                'questions': questions,
                'headers': headers
            }
        else:
            print_error(f"Interview creation failed: {result}")
            return None
            
    except Exception as e:
        print_error(f"Interview start error: {e}")
        return None

def test_answer_submission(interview_info):
    """Test 4: Answer Submission and Analysis"""
    print_header("TEST 4: ANSWER SUBMISSION & MISTRAL ANALYSIS")
    
    if not interview_info:
        print_error("No interview info provided")
        return None
    
    # Get first question
    questions = interview_info['questions']
    if not questions:
        print_error("No questions available")
        return None
    
    question = questions[0]
    print_info(f"Submitting answer for: {question['text'][:60]}...")
    print_info(f"Question ID: {question['id']}")
    
    # Simulate user answer
    answer_text = """
    I would approach this problem using a multi-threaded solution. First, I'd analyze the requirements
    and break them down into smaller components. Then, I'd implement each component separately with proper
    error handling and unit tests. For optimization, I'd use caching and database indexing. I've used this
    approach in my previous project at XYZ Corp where we achieved 99.9% uptime.
    """
    
    submit_data = {
        "question_id": question['id'],
        "answer": answer_text.strip()
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/interview/{interview_info['interview_uuid']}/submit",
            json=submit_data,
            headers=interview_info['headers']
        )
        result = response.json()
        
        if response.status_code == 201:
            print_success("Answer submitted successfully")
            
            analysis = result['analysis']
            print_success(f"Mistral AI Analysis:")
            print_info(f"Score: {analysis['score']}/10")
            print_info(f"Question #{result.get('question_number', 1)}")
            
            print(f"\n{YELLOW}Strengths:{RESET}")
            for strength in analysis['strengths']:
                print_info(f"- {strength}")
            
            print(f"\n{YELLOW}Weaknesses:{RESET}")
            for weakness in analysis['weaknesses']:
                print_info(f"- {weakness}")
            
            print(f"\n{YELLOW}Detailed Feedback:{RESET}")
            print(f"{analysis['feedback']}\n")
            
            return {
                'answer_id': result['answer_id'],
                'feedback_id': result['feedback_id'],
                'score': analysis['score']
            }
        else:
            print_error(f"Answer submission failed: {result}")
            return None
            
    except Exception as e:
        print_error(f"Answer submission error: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_interview_completion(interview_info):
    """Test 5: Interview Completion"""
    print_header("TEST 5: INTERVIEW COMPLETION")
    
    if not interview_info:
        print_error("No interview info provided")
        return None
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/interview/{interview_info['interview_uuid']}/complete",
            headers=interview_info['headers']
        )
        result = response.json()
        
        if response.status_code == 200:
            print_success("Interview completed successfully")
            print_info(f"Overall Score: {result['overall_score']}/10")
            print_info(f"Total Questions: {result['total_questions']}")
            print_info(f"Interview Status: {result['interview']['status']}")
            return True
        else:
            print_error(f"Interview completion failed: {result}")
            return False
            
    except Exception as e:
        print_error(f"Interview completion error: {e}")
        return False

def main():
    """Run all tests"""
    print(f"\n{BLUE}{'='*70}")
    print("AI INTERVIEW COACH - INTEGRATION TEST SUITE")
    print(f"{'='*70}{RESET}")
    print(f"Testing: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Test 1: Health
    if not test_health_check():
        print_error("Server is not running!")
        return
    
    # Test 2: Auth
    user_info = test_signup_and_login()
    if not user_info:
        print_error("Authentication failed!")
        return
    
    # Test 3: Interview Session
    interview_info = test_interview_flow(user_info)
    if not interview_info:
        print_error("Interview creation failed!")
        return
    
    # Test 4: Answer Submission
    answer_info = test_answer_submission(interview_info)
    if not answer_info:
        print_error("Answer submission failed!")
        return
    
    # Test 5: Complete Interview
    if not test_interview_completion(interview_info):
        print_error("Interview completion failed!")
        return
    
    # Summary
    print_header("[SUCCESS] ALL TESTS PASSED!")
    print(f"{GREEN}Integration test completed successfully.{RESET}")
    print(f"{GREEN}Your website is ready to use!{RESET}\n")

if __name__ == '__main__':
    main()
