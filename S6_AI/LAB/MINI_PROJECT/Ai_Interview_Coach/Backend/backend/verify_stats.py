#!/usr/bin/env python3
"""Verify statistics are calculated correctly"""
from app import *

with app.app_context():
    print("=== Database Statistics ===\n")
    
    # Check users and their interview counts
    users = User.query.all()
    print(f"Total Users: {len(users)}")
    
    for user in users:
        print(f"\nUser: {user.first_name} {user.last_name} (ID: {user.id})")
        print(f"  Email: {user.email}")
        
        # Get completed interviews
        completed = Interview.query.filter_by(user_id=user.id, status='completed').all()
        all_interviews = Interview.query.filter_by(user_id=user.id).all()
        
        print(f"  Total Interviews: {len(all_interviews)}")
        print(f"  Completed Interviews: {len(completed)}")
        
        if completed:
            scores = [i.overall_score for i in completed if i.overall_score]
            print(f"    Scores: {scores}")
            if scores:
                print(f"    Average: {sum(scores) / len(scores):.2f}")
                print(f"    Best: {max(scores):.2f}")
                print(f"    Total Time: {sum(i.duration_seconds or 0 for i in completed)}s")
        
        # Get total questions  
        total_q = 0
        for interview in all_interviews:
            answers = Answer.query.filter_by(interview_id=interview.id).all()
            total_q += len(answers)
        print(f"  Total Questions Answered: {total_q}")
        
        # Check User stats columns
        print(f"  User.total_interviews: {user.total_interviews}")
        print(f"  User.average_score: {user.average_score}")
        print(f"  User.best_score: {user.best_score}")
        print(f"  User.total_questions_answered: {user.total_questions_answered}")
        print(f"  User.total_practice_time: {user.total_practice_time}s")
        print(f"  User.current_streak: {user.current_streak}")
