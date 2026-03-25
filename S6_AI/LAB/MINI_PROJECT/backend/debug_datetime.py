#!/usr/bin/env python3
from app import *
import traceback
import json

with app.app_context():
    try:
        # Check what's in the database
        interviews = Interview.query.limit(1).all()
        if interviews:
            interview = interviews[0]
            print(f'Interview ID: {interview.id}')
            print(f'started_at type: {type(interview.started_at)}')
            print(f'started_at value: {interview.started_at}')
            print(f'started_at repr: {repr(interview.started_at)}')
            
            # Try to call to_dict
            try:
                result = interview.to_dict()
                print(f'to_dict() success')
                print(f'started_at in to_dict: {result.get("started_at")}')
            except Exception as e:
                print(f'to_dict() error: {e}')
                traceback.print_exc()
        else:
            print('No interviews found')
            
        # Check all users
        users = User.query.limit(1).all()
        if users:
            user = users[0]
            print(f'\nUser ID: {user.id}')
            print(f'created_at type: {type(user.created_at)}')
            print(f'created_at value: {user.created_at}')
            if user.last_login:
                print(f'last_login type: {type(user.last_login)}')
                print(f'last_login value: {user.last_login}')
            else:
                print('last_login is None')
            
            # Try to call to_dict
            try:
                result = user.to_dict()
                print(f'User to_dict() success')
                print(f'created_at in to_dict: {result.get("created_at")}')
            except Exception as e:
                print(f'User to_dict() error: {e}')
                traceback.print_exc()
        else:
            print('No users found')
            
    except Exception as e:
        print(f'Error: {e}')
        traceback.print_exc()