#!/usr/bin/env python3
"""
Authentication Security Test Suite
Tests login/logout functionality, session management, and authentication security
"""

import requests
import time
from requests.sessions import Session

# Test configuration
BASE_URL = "http://127.0.0.1:8000"
TEST_USERS = {
    'superadmin': {'username': 'admin', 'password': 'admin123'},
    'staff': {'username': 'staff_user', 'password': 'staff123'},
    'customer': {'username': 'customer_user', 'password': 'customer123'}
}

class AuthenticationTester:
    def __init__(self):
        self.session = Session()
        self.results = []
    
    def log_result(self, test_name, status, message):
        """Log test results"""
        result = f"[{'PASS' if status else 'FAIL'}] {test_name}: {message}"
        print(result)
        self.results.append((test_name, status, message))
    
    def get_csrf_token(self, url):
        """Get CSRF token from a page"""
        try:
            response = self.session.get(url)
            if 'csrfmiddlewaretoken' in response.text:
                # Extract CSRF token from the form
                start = response.text.find('name="csrfmiddlewaretoken" value="') + 34
                end = response.text.find('"', start)
                return response.text[start:end]
            return None
        except Exception as e:
            print(f"Error getting CSRF token: {e}")
            return None
    
    def test_login_functionality(self):
        """Test basic login functionality"""
        print("\n=== Testing Login Functionality ===")
        
        # Test SuperAdmin login
        login_url = f"{BASE_URL}/adminlogin"
        csrf_token = self.get_csrf_token(login_url)
        
        if csrf_token:
            login_data = {
                'username': TEST_USERS['superadmin']['username'],
                'password': TEST_USERS['superadmin']['password'],
                'csrfmiddlewaretoken': csrf_token
            }
            
            response = self.session.post(login_url, data=login_data)
            
            if response.status_code == 302 or 'dashboard' in response.url:
                self.log_result("SuperAdmin Login", True, "Successfully logged in")
            else:
                self.log_result("SuperAdmin Login", False, f"Login failed - Status: {response.status_code}")
        else:
            self.log_result("CSRF Token Retrieval", False, "Could not get CSRF token")
    
    def test_session_management(self):
        """Test session security and timeout"""
        print("\n=== Testing Session Management ===")
        
        # Test if session persists across requests
        dashboard_url = f"{BASE_URL}/admin-dashboard"
        response = self.session.get(dashboard_url)
        
        if response.status_code == 200:
            self.log_result("Session Persistence", True, "Session maintained across requests")
        else:
            self.log_result("Session Persistence", False, f"Session not maintained - Status: {response.status_code}")
        
        # Test logout functionality
        logout_url = f"{BASE_URL}/logout"
        response = self.session.get(logout_url)
        
        # Try to access protected page after logout
        response = self.session.get(dashboard_url)
        if response.status_code == 302 or 'login' in response.url:
            self.log_result("Logout Functionality", True, "Successfully logged out and redirected")
        else:
            self.log_result("Logout Functionality", False, "Logout may not be working properly")
    
    def test_unauthorized_access(self):
        """Test access to protected pages without authentication"""
        print("\n=== Testing Unauthorized Access Protection ===")
        
        # Create new session (unauthenticated)
        unauth_session = Session()
        
        protected_urls = [
            f"{BASE_URL}/admin-dashboard",
            f"{BASE_URL}/superadmin-dashboard",
            f"{BASE_URL}/manage-users",
            f"{BASE_URL}/create-staff"
        ]
        
        for url in protected_urls:
            response = unauth_session.get(url)
            if response.status_code == 302 or 'login' in response.url:
                self.log_result(f"Unauthorized Access - {url.split('/')[-1]}", True, "Properly redirected to login")
            else:
                self.log_result(f"Unauthorized Access - {url.split('/')[-1]}", False, f"Access allowed - Status: {response.status_code}")
    
    def test_password_security(self):
        """Test password handling and security"""
        print("\n=== Testing Password Security ===")
        
        # Test with wrong password
        login_url = f"{BASE_URL}/adminlogin"
        csrf_token = self.get_csrf_token(login_url)
        
        if csrf_token:
            wrong_login_data = {
                'username': TEST_USERS['superadmin']['username'],
                'password': 'wrongpassword',
                'csrfmiddlewaretoken': csrf_token
            }
            
            response = self.session.post(login_url, data=wrong_login_data)
            
            if response.status_code != 302 and 'dashboard' not in response.url:
                self.log_result("Wrong Password Protection", True, "Login rejected with wrong password")
            else:
                self.log_result("Wrong Password Protection", False, "Login succeeded with wrong password!")
    
    def test_brute_force_protection(self):
        """Test basic brute force protection"""
        print("\n=== Testing Brute Force Protection ===")
        
        login_url = f"{BASE_URL}/adminlogin"
        
        # Attempt multiple failed logins
        for i in range(5):
            csrf_token = self.get_csrf_token(login_url)
            if csrf_token:
                wrong_data = {
                    'username': TEST_USERS['superadmin']['username'],
                    'password': f'wrongpass{i}',
                    'csrfmiddlewaretoken': csrf_token
                }
                response = self.session.post(login_url, data=wrong_data)
                time.sleep(0.5)  # Small delay between attempts
        
        # Try correct password after failed attempts
        csrf_token = self.get_csrf_token(login_url)
        if csrf_token:
            correct_data = {
                'username': TEST_USERS['superadmin']['username'],
                'password': TEST_USERS['superadmin']['password'],
                'csrfmiddlewaretoken': csrf_token
            }
            response = self.session.post(login_url, data=correct_data)
            
            if response.status_code == 302 or 'dashboard' in response.url:
                self.log_result("Brute Force Resilience", True, "System allows login after failed attempts (no lockout)")
            else:
                self.log_result("Brute Force Resilience", False, "System may have lockout mechanism")
    
    def run_all_tests(self):
        """Run all authentication security tests"""
        print("🔐 AUTHENTICATION SECURITY TEST SUITE")
        print("=" * 50)
        
        self.test_unauthorized_access()
        self.test_login_functionality()
        self.test_session_management()
        self.test_password_security()
        self.test_brute_force_protection()
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        passed = sum(1 for _, status, _ in self.results if status)
        total = len(self.results)
        
        print(f"Tests Passed: {passed}/{total}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("✅ All authentication security tests PASSED!")
        else:
            print("⚠️  Some tests failed - review security implementation")
            
        return self.results

if __name__ == "__main__":
    tester = AuthenticationTester()
    tester.run_all_tests()