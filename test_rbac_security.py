#!/usr/bin/env python3
"""
Role-Based Access Control (RBAC) Security Test Suite
Tests SuperAdmin, Staff, and Customer access restrictions
"""

import requests
from requests.sessions import Session

# Test configuration
BASE_URL = "http://127.0.0.1:8000"

class RBACTester:
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
    
    def login_user(self, username, password, login_url):
        """Login a user and return session"""
        session = Session()
        csrf_token = self.get_csrf_token(session, login_url)
        
        if csrf_token:
            login_data = {
                'username': username,
                'password': password,
                'csrfmiddlewaretoken': csrf_token
            }
            response = session.post(login_url, data=login_data)
            return session, response.status_code
        return session, 400
    
    def test_superadmin_access(self):
        """Test SuperAdmin access to all areas"""
        print("\n=== Testing SuperAdmin Access Rights ===")
        
        # Login as SuperAdmin
        session, status = self.login_user('admin', 'admin123', f"{BASE_URL}/adminlogin")
        
        if status == 302:  # Successful login redirect
            superadmin_urls = [
                ('/admin-dashboard', 'Admin Dashboard'),
                ('/superadmin-dashboard', 'SuperAdmin Dashboard'),
                ('/manage-users', 'User Management'),
                ('/create-staff', 'Staff Creation'),
            ]
            
            for url, name in superadmin_urls:
                response = session.get(f"{BASE_URL}{url}")
                if response.status_code == 200:
                    self.log_result(f"SuperAdmin - {name}", True, "Access granted")
                else:
                    self.log_result(f"SuperAdmin - {name}", False, f"Access denied - Status: {response.status_code}")
        else:
            self.log_result("SuperAdmin Login", False, "Could not login as SuperAdmin")
    
    def test_staff_access(self):
        """Test Staff access restrictions"""
        print("\n=== Testing Staff Access Rights ===")
        
        # First, create a staff user (you may need to do this manually)
        # For testing, we'll assume staff_user exists
        session, status = self.login_user('staff_user', 'staff123', f"{BASE_URL}/adminlogin")
        
        if status == 302:  # Successful login redirect
            # Staff should access admin dashboard
            response = session.get(f"{BASE_URL}/admin-dashboard")
            if response.status_code == 200:
                self.log_result("Staff - Admin Dashboard", True, "Access granted (correct)")
            else:
                self.log_result("Staff - Admin Dashboard", False, f"Access denied - Status: {response.status_code}")
            
            # Staff should NOT access SuperAdmin areas
            superadmin_restricted_urls = [
                ('/superadmin-dashboard', 'SuperAdmin Dashboard'),
                ('/manage-users', 'User Management'),
                ('/create-staff', 'Staff Creation'),
            ]
            
            for url, name in superadmin_restricted_urls:
                response = session.get(f"{BASE_URL}{url}")
                if response.status_code == 302 or response.status_code == 403:
                    self.log_result(f"Staff - {name} Restriction", True, "Access properly denied")
                else:
                    self.log_result(f"Staff - {name} Restriction", False, f"Access granted (SECURITY ISSUE) - Status: {response.status_code}")
        else:
            self.log_result("Staff Login", False, "Could not login as Staff (user may not exist)")
    
    def test_customer_access(self):
        """Test Customer access restrictions"""
        print("\n=== Testing Customer Access Rights ===")
        
        # Login as Customer
        session, status = self.login_user('customer_user', 'customer123', f"{BASE_URL}/customerlogin")
        
        if status == 302:  # Successful login redirect
            # Customer should NOT access any admin areas
            admin_restricted_urls = [
                ('/admin-dashboard', 'Admin Dashboard'),
                ('/superadmin-dashboard', 'SuperAdmin Dashboard'),
                ('/manage-users', 'User Management'),
                ('/create-staff', 'Staff Creation'),
            ]
            
            for url, name in admin_restricted_urls:
                response = session.get(f"{BASE_URL}{url}")
                if response.status_code == 302 or response.status_code == 403:
                    self.log_result(f"Customer - {name} Restriction", True, "Access properly denied")
                else:
                    self.log_result(f"Customer - {name} Restriction", False, f"Access granted (SECURITY ISSUE) - Status: {response.status_code}")
            
            # Customer should access customer areas
            customer_urls = [
                ('/', 'Home Page'),
                ('/customer-dashboard', 'Customer Dashboard'),
            ]
            
            for url, name in customer_urls:
                response = session.get(f"{BASE_URL}{url}")
                if response.status_code == 200:
                    self.log_result(f"Customer - {name}", True, "Access granted (correct)")
                else:
                    self.log_result(f"Customer - {name}", False, f"Access denied - Status: {response.status_code}")
        else:
            self.log_result("Customer Login", False, "Could not login as Customer (user may not exist)")
    
    def test_context_processor_security(self):
        """Test that context processor correctly identifies user roles"""
        print("\n=== Testing Context Processor Security ===")
        
        # Test SuperAdmin context
        session, status = self.login_user('admin', 'admin123', f"{BASE_URL}/adminlogin")
        if status == 302:
            response = session.get(f"{BASE_URL}/admin-dashboard")
            if 'SuperAdmin' in response.text or 'superadmin' in response.text.lower():
                self.log_result("SuperAdmin Context Detection", True, "SuperAdmin role properly detected")
            else:
                self.log_result("SuperAdmin Context Detection", False, "SuperAdmin role not detected in UI")
    
    def test_direct_url_access(self):
        """Test direct URL access without proper authentication"""
        print("\n=== Testing Direct URL Access Protection ===")
        
        # Test unauthenticated access
        unauth_session = Session()
        
        protected_urls = [
            ('/admin-dashboard', 'Admin Dashboard'),
            ('/superadmin-dashboard/', 'SuperAdmin Dashboard'),
            ('/manage-users/', 'User Management'),
            ('/create-staff/', 'Staff Creation'),
        ]
        
        for url, name in protected_urls:
            response = unauth_session.get(f"{BASE_URL}{url}", allow_redirects=True)
            
            # Check if redirected to login page
            if 'adminlogin' in response.url or 'login' in response.text.lower():
                self.log_result(f"Direct Access - {name}", True, "Properly redirected to login")
            elif response.status_code == 302:  # Should redirect to login
                self.log_result(f"Direct Access - {name}", True, "Properly redirected to login")
            else:
                self.log_result(f"Direct Access - {name}", False, f"Access granted without auth - Status: {response.status_code}")
    
    def test_privilege_escalation(self):
        """Test for privilege escalation vulnerabilities"""
        print("\n=== Testing Privilege Escalation Protection ===")
        
        # Login as staff and try to access SuperAdmin functions via POST
        session, status = self.login_user('staff_user', 'staff123', f"{BASE_URL}/adminlogin")
        
        if status == 302:
            # Try to create another staff member (SuperAdmin function)
            csrf_token = self.get_csrf_token(session, f"{BASE_URL}/create-staff")
            if csrf_token:
                staff_data = {
                    'username': 'test_staff',
                    'password': 'test123',
                    'csrfmiddlewaretoken': csrf_token
                }
                response = session.post(f"{BASE_URL}/create-staff", data=staff_data)
                
                if response.status_code == 302 and 'admin-dashboard' in response.url:
                    self.log_result("Privilege Escalation - Staff Creation", False, "Staff can create other staff (SECURITY ISSUE)")
                else:
                    self.log_result("Privilege Escalation - Staff Creation", True, "Staff properly denied staff creation")
    
    def run_all_tests(self):
        """Run all RBAC security tests"""
        print("🛡️  ROLE-BASED ACCESS CONTROL TEST SUITE")
        print("=" * 50)
        
        self.test_direct_url_access()
        self.test_superadmin_access()
        self.test_staff_access()
        self.test_customer_access()
        self.test_context_processor_security()
        self.test_privilege_escalation()
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 RBAC TEST SUMMARY")
        print("=" * 50)
        
        passed = sum(1 for _, status, _ in self.results if status)
        total = len(self.results)
        
        print(f"Tests Passed: {passed}/{total}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("✅ All RBAC security tests PASSED!")
        else:
            print("⚠️  Some tests failed - review access control implementation")
            
        return self.results

if __name__ == "__main__":
    tester = RBACTester()
    tester.run_all_tests()