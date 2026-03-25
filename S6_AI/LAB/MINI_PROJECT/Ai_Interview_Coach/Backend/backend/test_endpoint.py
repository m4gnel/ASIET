#!/usr/bin/env python3
"""Test the dashboard endpoint directly"""
from app import *
import json
import traceback

with app.app_context():
    try:
        # Create a test user for auth
        user = User.query.first()
        if not user:
            print("No users in database!")
            exit(1)
        
        print(f"Testing with User ID: {user.id}")
        
        # Create a test request context
        with app.test_request_context():
            # Mock JWT identity
            from flask_jwt_extended import create_access_token
            token = create_access_token(identity=str(user.id))
            print(f"Created token: {token[:20]}...")
            
            # Make the request
            from flask import request
            with app.test_client() as client:
                headers = {'Authorization': f'Bearer {token}'}
                response = client.get('/api/dashboard/stats', headers=headers)
                
                print(f"Status Code: {response.status_code}")
                print(f"Response:")
                try:
                    data = response.get_json()
                    print(json.dumps(data, indent=2))
                except:
                    print(response.data.decode())
                
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
