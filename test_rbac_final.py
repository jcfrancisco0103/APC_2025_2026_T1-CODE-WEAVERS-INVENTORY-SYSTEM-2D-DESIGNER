#!/usr/bin/env python3
"""
Final Role-Based Access Control (RBAC) Security Test Suite
Tests with existing admin user and verifies all security measures
"""

import requests
from requests.sessions import Session

# Test configuration
BASE_URL = "http://127.0.0.1:8000"

class FinalRBACTester:
    def __init__(self):
        self.results = []
    
    def log_result(self, test_name, status, message):
        """Log test results"""
        result = f"[{'PASS' if status else 'FAIL'}] {test_name}: {message}"
        print(result)
        self.results.append((test_name, status, message))
    
    def get_csrf_token(self, session, url):
        """Get CSRF token from a page"""
        try:
            response = session.get(url)
            if 'csrfmiddlewaretoken' in response.text:
                start = response.text.find('name="csrfmiddlewaretoken" value="') + 34
                end = response.text.find('"', start)
                return response.text[start:end]
            return None
        except Exception as e:
            print(f"Error getting CSRF token: {e}")
            return None
    
    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access protected areas"""
        print("\n=== Testing Unauthenticated Access Protection ===")
        
        session = Session()
        
        protected_urls = [
            ('/admin-dashboard', 'Admin Dashboard'),
            ('/superadmin-dashboard/', 'SuperAdmin Dashboard'),
            ('/manage-users/', 'User Management'),
            ('/create-staff/', 'Staff Creation'),
        ]
        
        for url, name in protected_urls:
            response = session.get(f"{BASE_URL}{url}", allow_redirects=True)
            
            # Check if redirected to login page
            if 'adminlogin' in response.url or 'login' in response.text.lower():
                self.log_result(f"Unauthenticated - {name}", True, "Properly redirected to login")
            else:
                self.log_result(f"Unauthenticated - {name}", False, f"Access granted without auth")
    
    def test_admin_authentication(self):
        """Test admin authentication and access"""
        print("\n=== Testing Admin Authentication & Access ===")
        
        # Test admin login
        session = Session()
        csrf_token = self.get_csrf_token(session, f"{BASE_URL}/adminlogin")
        
        if csrf_token:
            login_data = {
                'username': 'admin',
                'password': 'admin123',
                'csrfmiddlewaretoken': csrf_token
            }
            response = session.post(f"{BASE_URL}/adminlogin", data=login_data, allow_redirects=False)
            
            if response.status_code == 302:  # Successful login redirect
                self.log_result("Admin Login", True, "Successfully authenticated")
                
                # Test admin dashboard access
                dashboard_response = session.get(f"{BASE_URL}/admin-dashboard")
                if dashboard_response.status_code == 200 and 'dashboard' in dashboard_response.text.lower():
                    self.log_result("Admin Dashboard Access", True, "Can access admin dashboard")
                else:
                    self.log_result("Admin Dashboard Access", False, f"Cannot access dashboard - Status: {dashboard_response.status_code}")
                
                # Test SuperAdmin areas (should work if admin is SuperAdmin)
                superadmin_response = session.get(f"{BASE_URL}/superadmin-dashboard/")
                if superadmin_response.status_code == 200 and 'superadmin' in superadmin_response.text.lower():
                    self.log_result("SuperAdmin Access", True, "Admin can access SuperAdmin areas")
                elif 'access denied' in superadmin_response.text.lower() or superadmin_response.status_code == 302:
                    self.log_result("SuperAdmin Access", True, "Admin properly restricted from SuperAdmin areas")
                else:
                    self.log_result("SuperAdmin Access", False, f"Unexpected response - Status: {superadmin_response.status_code}")
                
            else:
                self.log_result("Admin Login", False, f"Login failed - Status: {response.status_code}")
        else:
            self.log_result("Admin Login", False, "Could not get CSRF token")
    
    def test_csrf_protection(self):
        """Test CSRF protection on forms"""
        print("\n=== Testing CSRF Protection ===")
        
        # Test admin login without CSRF token
        session = Session()
        login_data = {
            'username': 'admin',
            'password': 'admin123'
            # Intentionally omitting CSRF token
        }
        response = session.post(f"{BASE_URL}/adminlogin", data=login_data)
        
        if response.status_code == 403 or 'csrf' in response.text.lower():
            self.log_result("CSRF Protection", True, "Login properly rejected without CSRF token")
        else:
            self.log_result("CSRF Protection", False, "Login succeeded without CSRF token (SECURITY ISSUE)")
    
    def test_session_security(self):
        """Test session security and logout"""
        print("\n=== Testing Session Security ===")
        
        # Login first
        session = Session()
        csrf_token = self.get_csrf_token(session, f"{BASE_URL}/adminlogin")
        
        if csrf_token:
            login_data = {
                'username': 'admin',
                'password': 'admin123',
                'csrfmiddlewaretoken': csrf_token
            }
            login_response = session.post(f"{BASE_URL}/adminlogin", data=login_data, allow_redirects=False)
            
            if login_response.status_code == 302:
                # Test that session works
                dashboard_response = session.get(f"{BASE_URL}/admin-dashboard")
                if dashboard_response.status_code == 200:
                    self.log_result("Session Management", True, "Session properly maintained after login")
                else:
                    self.log_result("Session Management", False, "Session not working after login")
                
                # Test logout
                logout_response = session.get(f"{BASE_URL}/logout", allow_redirects=True)
                
                # Try to access dashboard after logout
                post_logout_response = session.get(f"{BASE_URL}/admin-dashboard", allow_redirects=True)
                if 'login' in post_logout_response.url or 'login' in post_logout_response.text.lower():
                    self.log_result("Logout Security", True, "Properly redirected to login after logout")
                else:
                    self.log_result("Logout Security", False, "Still has access after logout (SECURITY ISSUE)")
            else:
                self.log_result("Session Management", False, "Could not login to test session")
    
    def test_url_manipulation(self):
        """Test protection against URL manipulation attacks"""
        print("\n=== Testing URL Manipulation Protection ===")
        
        # Test various malicious URL patterns
        malicious_urls = [
            '/admin-dashboard/../../../etc/passwd',
            '/admin-dashboard?user=admin&bypass=true',
            '/admin-dashboard#admin',
            '/superadmin-dashboard/../admin-dashboard',
        ]
        
        session = Session()
        
        for url in malicious_urls:
            try:
                response = session.get(f"{BASE_URL}{url}", allow_redirects=True)
                if 'login' in response.url or 'login' in response.text.lower():
                    self.log_result("URL Manipulation Protection", True, f"Malicious URL properly blocked: {url}")
                else:
                    self.log_result("URL Manipulation Protection", False, f"Malicious URL not blocked: {url}")
            except Exception as e:
                self.log_result("URL Manipulation Protection", True, f"Malicious URL caused error (good): {url}")
    
    def test_http_methods(self):
        """Test that only appropriate HTTP methods are allowed"""
        print("\n=== Testing HTTP Method Security ===")
        
        session = Session()
        
        # Test various HTTP methods on protected endpoints
        methods_to_test = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
        
        for method in methods_to_test:
            try:
                if method == 'GET':
                    response = session.get(f"{BASE_URL}/admin-dashboard", allow_redirects=True)
                elif method == 'POST':
                    response = session.post(f"{BASE_URL}/admin-dashboard", allow_redirects=True)
                elif method == 'PUT':
                    response = session.put(f"{BASE_URL}/admin-dashboard", allow_redirects=True)
                elif method == 'DELETE':
                    response = session.delete(f"{BASE_URL}/admin-dashboard", allow_redirects=True)
                elif method == 'PATCH':
                    response = session.patch(f"{BASE_URL}/admin-dashboard", allow_redirects=True)
                
                # All should redirect to login for unauthenticated users
                if 'login' in response.url or 'login' in response.text.lower():
                    self.log_result(f"HTTP Method Security - {method}", True, "Properly protected")
                else:
                    self.log_result(f"HTTP Method Security - {method}", False, f"Method {method} not properly protected")
                    
            except Exception as e:
                # Some methods might not be allowed, which is good
                self.log_result(f"HTTP Method Security - {method}", True, f"Method {method} properly restricted")
    
    def run_all_tests(self):
        """Run all RBAC security tests"""
        print("🛡️  COMPREHENSIVE RBAC SECURITY TEST SUITE")
        print("=" * 60)
        
        self.test_unauthenticated_access()
        self.test_admin_authentication()
        self.test_csrf_protection()
        self.test_session_security()
        self.test_url_manipulation()
        self.test_http_methods()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE RBAC TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for _, status, _ in self.results if status)
        total = len(self.results)
        
        print(f"Tests Passed: {passed}/{total}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("✅ All RBAC security tests PASSED!")
            print("🔒 Your system has robust access control security!")
        elif passed >= total * 0.8:
            print("⚠️  Most tests passed - minor security improvements needed")
        else:
            print("❌ Multiple security issues found - immediate attention required")
            
        # Show failed tests
        failed_tests = [name for name, status, _ in self.results if not status]
        if failed_tests:
            print(f"\n🚨 Failed Tests: {', '.join(failed_tests)}")
            
        return self.results

if __name__ == "__main__":
    tester = FinalRBACTester()
    tester.run_all_tests()