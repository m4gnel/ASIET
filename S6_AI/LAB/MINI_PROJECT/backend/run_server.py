#!/usr/bin/env python3
"""
Run the Flask app with proper encoding configuration
"""
import os
import sys
import io

# Fix Unicode encoding on Windows
if sys.platform == 'win32':
    import codecs
    codecs.register_error('strict', codecs.ignore_errors)
    
    # Redirect stdout and stderr to handle Unicode
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Set environment
os.environ['FLASK_ENV'] = 'development'
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Import and run
from app import app

if __name__ == '__main__':
    print("\n" + "="*70)
    print("[SERVER] AI INTERVIEW COACH - BACKEND STARTING")
    print("="*70)
    print("[INFO] Server: http://127.0.0.1:5000")
    print("[INFO] Database: interview_coach.db")
    print("="*70 + "\n")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        print(f"[ERROR] Failed to start server: {e}")
        sys.exit(1)
