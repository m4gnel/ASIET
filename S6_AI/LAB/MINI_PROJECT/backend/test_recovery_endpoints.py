"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DATABASE RECOVERY ENDPOINTS - TESTING GUIDE                     ║
║                  Verify the fixes are working correctly                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

This script tests the two new recovery endpoints:
1. POST /api/admin/recover-analytics (individual user)
2. POST /api/admin/recover-all-analytics (system-wide)

Usage:
    python test_recovery_endpoints.py
"""

import requests
import json
import sys
from datetime import datetime

class RecoveryTester:
    def __init__(self, base_url='http://localhost:5000', token=None):
        self.base_url = base_url
        self.token = token
        self.results = []
    
    def log(self, level, message):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        prefix = {
            'INFO': 'ℹ️ ',
            'SUCCESS': '✅',
            'WARNING': '⚠️ ',
            'ERROR': '❌'
        }
        print(f"[{timestamp}] {prefix.get(level, '•')} {message}")
    
    def headers(self):
        """Get request headers with auth token"""
        return {
            'Authorization': f'Bearer {self.token}' if self.token else '',
            'Content-Type': 'application/json'
        }
    
    def test_health(self):
        """Test if server is running"""
        self.log('INFO', 'Testing server health...')
        try:
            response = requests.get(f'{self.base_url}/api/health', timeout=5)
            if response.status_code == 200:
                self.log('SUCCESS', 'Server is running ✓')
                return True
            else:
                self.log('ERROR', f'Server returned {response.status_code}')
                return False
        except requests.ConnectionError:
            self.log('ERROR', f'Cannot connect to server at {self.base_url}')
            self.log('INFO', 'Make sure the Flask app is running: python run_server.py')
            return False
    
    def test_recover_analytics(self):
        """Test individual user recovery endpoint"""
        self.log('INFO', 'Testing /api/admin/recover-analytics endpoint...')
        
        if not self.token:
            self.log('WARNING', 'Skipping - no authentication token provided')
            return False
        
        try:
            response = requests.post(
                f'{self.base_url}/api/admin/recover-analytics',
                headers=self.headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log('SUCCESS', 'Recovery endpoint working ✓')
                
                if 'user_stats' in data:
                    stats = data['user_stats']
                    self.log('SUCCESS', f'  • Total interviews: {stats.get("total_interviews", "?")}')
                    self.log('SUCCESS', f'  • Average score: {stats.get("average_score", "?")}')
                    self.log('SUCCESS', f'  • Best score: {stats.get("best_score", "?")}')
                    self.log('SUCCESS', f'  • Questions answered: {stats.get("total_questions_answered", "?")}')
                    self.log('SUCCESS', f'  • Practice time: {stats.get("total_practice_time", "?")}s')
                
                return True
            else:
                self.log('ERROR', f'Endpoint returned {response.status_code}')
                self.log('ERROR', f'Response: {response.text}')
                return False
                
        except Exception as e:
            self.log('ERROR', f'Failed: {e}')
            return False
    
    def test_dashboard_stats(self):
        """Test dashboard stats endpoint"""
        self.log('INFO', 'Testing /api/dashboard/stats endpoint...')
        
        if not self.token:
            self.log('WARNING', 'Skipping - no authentication token provided')
            return False
        
        try:
            response = requests.get(
                f'{self.base_url}/api/dashboard/stats',
                headers=self.headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log('SUCCESS', 'Dashboard stats endpoint working ✓')
                
                self.log('SUCCESS', f'  • Total interviews: {data.get("total_interviews", "?")}')
                self.log('SUCCESS', f'  • Average score: {data.get("average_score", "?")}')
                self.log('SUCCESS', f'  • Best score: {data.get("best_score", "?")}')
                self.log('SUCCESS', f'  • Questions answered: {data.get("total_questions_answered", "?")}')
                
                return True
            else:
                self.log('ERROR', f'Endpoint returned {response.status_code}')
                return False
                
        except Exception as e:
            self.log('ERROR', f'Failed: {e}')
            return False
    
    def compare_stats(self):
        """Compare recovery endpoint vs dashboard endpoint"""
        self.log('INFO', 'Comparing recovery-analytics with dashboard/stats...')
        
        if not self.token:
            self.log('WARNING', 'Skipping - no authentication token provided')
            return True
        
        try:
            # Get recovery stats
            response1 = requests.post(
                f'{self.base_url}/api/admin/recover-analytics',
                headers=self.headers(),
                timeout=10
            )
            recovery_stats = response1.json().get('user_stats', {})
            
            # Get dashboard stats
            response2 = requests.get(
                f'{self.base_url}/api/dashboard/stats',
                headers=self.headers(),
                timeout=10
            )
            dashboard_stats = response2.json()
            
            # Compare key fields
            fields_to_compare = [
                'total_interviews',
                'average_score',
                'best_score',
                'total_questions_answered'
            ]
            
            all_match = True
            for field in fields_to_compare:
                rec_val = recovery_stats.get(field)
                dash_val = dashboard_stats.get(field)
                
                match = rec_val == dash_val
                status = '✓' if match else '✗'
                self.log('SUCCESS' if match else 'WARNING', 
                        f'  • {field}: recovery={rec_val}, dashboard={dash_val} {status}')
                
                if not match:
                    all_match = False
            
            if all_match:
                self.log('SUCCESS', 'Stats are perfectly synchronized ✓')
            else:
                self.log('WARNING', 'Some stats differ between endpoints')
            
            return all_match
            
        except Exception as e:
            self.log('ERROR', f'Comparison failed: {e}')
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n╔════════════════════════════════════════════════════╗")
        print("║  DATABASE RECOVERY ENDPOINTS - TEST SUITE          ║")
        print("╚════════════════════════════════════════════════════╝\n")
        
        self.log('INFO', f'Target server: {self.base_url}')
        self.log('INFO', f'Authentication: {"Enabled" if self.token else "Disabled"}\n')
        
        tests_passed = 0
        tests_total = 0
        
        # Test 1: Health
        tests_total += 1
        if self.test_health():
            tests_passed += 1
        print()
        
        # Test 2: Dashboard stats
        tests_total += 1
        if self.test_dashboard_stats():
            tests_passed += 1
        print()
        
        # Test 3: Recovery endpoint
        tests_total += 1
        if self.test_recover_analytics():
            tests_passed += 1
        print()
        
        # Test 4: Compare stats
        tests_total += 1
        if self.compare_stats():
            tests_passed += 1
        print()
        
        # Summary
        print("╔════════════════════════════════════════════════════╗")
        print(f"║  TEST SUMMARY: {tests_passed}/{tests_total} passed          ║")
        print("╚════════════════════════════════════════════════════╝\n")
        
        if tests_passed == tests_total:
            self.log('SUCCESS', 'All tests passed - System healthy! ✓')
            return True
        else:
            self.log('WARNING', f'{tests_total - tests_passed} test(s) failed')
            return False


def main():
    """Main entry point"""
    print("\n⚠️  TESTING REQUIREMENTS:\n")
    print("1. Flask backend must be running:")
    print("   $ python run_server.py")
    print("\n2. Need a valid JWT token from login:")
    print("   POST /api/auth/login with valid credentials\n")
    
    # Configuration
    base_url = 'http://localhost:5000'
    
    # Try to use test credentials
    print("→ Attempting to get authentication token...\n")
    
    try:
        # Demo user credentials (from app.py)
        login_response = requests.post(
            f'{base_url}/api/auth/login',
            json={
                'email': 'demo@interviewcoach.ai',
                'password': 'demo123456'
            },
            timeout=10
        )
        
        if login_response.status_code == 200:
            token = login_response.json().get('access_token')
            print(f"✅ Got token from demo account\n")
        else:
            print(f"⚠️  Could not authenticate: {login_response.status_code}")
            print("   Please provide token manually in the script\n")
            token = None
    
    except Exception as e:
        print(f"⚠️  Connection failed: {e}")
        print("   Make sure Flask backend is running\n")
        token = None
    
    # Run tests
    tester = RecoveryTester(base_url=base_url, token=token)
    success = tester.run_all_tests()
    
    return 0 if success else 1


if __name__ == '__main__':
    exit(main())
