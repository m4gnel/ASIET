#!/usr/bin/env python3
"""Test the interview history endpoint"""
from app import *
import json

with app.app_context():
    user = User.query.first()
    if not user:
        print("No users!")
        exit(1)
    
    with app.test_client() as client:
        from flask_jwt_extended import create_access_token
        token = create_access_token(identity=str(user.id))
        
        # Test /api/interview/history
        print("Testing /api/interview/history?per_page=20")
        response = client.get(f'/api/interview/history?per_page=20', 
                             headers={'Authorization': f'Bearer {token}'})
        print(f"Status: {response.status_code}")
        data = response.get_json()
        print(json.dumps(data, indent=2))
        
        # Test /api/user/profile
        print("\n\nTesting /api/user/profile")
        response = client.get('/api/user/profile',
                             headers={'Authorization': f'Bearer {token}'})
        print(f"Status: {response.status_code}")
        data = response.get_json()
        print(json.dumps(data, indent=2))
