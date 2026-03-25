#!/usr/bin/env python3
"""Check for data corruption in the database"""
from app import *
import traceback

with app.app_context():
    try:
        print("=== Checking all interviews ===")
        all_interviews = Interview.query.all()
        print(f"Total interviews: {len(all_interviews)}")
        
        for idx, interview in enumerate(all_interviews):
            print(f"\n[Interview {idx+1}]")
            print(f"  ID: {interview.id}, UUID: {interview.uuid}")
            print(f"  started_at: {interview.started_at} (type: {type(interview.started_at).__name__})")
            print(f"  completed_at: {interview.completed_at} (type: {type(interview.completed_at).__name__ if interview.completed_at else 'NoneType'})")
            print(f"  status: {interview.status}")
            
            # Try to_dict()
            try:
                d = interview.to_dict()
                print(f"  to_dict(): ✓ SUCCESS")
                print(f"    - started_at: {d.get('started_at')}")
                print(f"    - completed_at: {d.get('completed_at')}")
            except Exception as e:
                print(f"  to_dict(): ✗ ERROR - {e}")
                traceback.print_exc()
        
        print("\n=== Checking recent interviews (limit 5) ===")
        recent = Interview.query.order_by(Interview.started_at.desc()).limit(5).all()
        print(f"Recent interviews: {len(recent)}")
        
        for idx, interview in enumerate(recent):
            try:
                d = interview.to_dict()
                print(f"  {idx+1}. ID={interview.id}: ✓")
            except Exception as e:
                print(f"  {idx+1}. ID={interview.id}: ✗ {e}")
        
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
