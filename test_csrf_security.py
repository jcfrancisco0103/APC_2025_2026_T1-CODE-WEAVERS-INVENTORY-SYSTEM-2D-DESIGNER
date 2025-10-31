#!/usr/bin/env python3
"""
CSRF Protection Security Test Suite
Tests Cross-Site Request Forgery protection across all forms in the application
"""

import requests
import re
from bs4 import BeautifulSoup
import time

class CSRFSecurityTester:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name, passed, details=""):
        """Log test results"""
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {test_name}: {details}")
        self.test_results.append({
            'test': test_name,
            'passed': passed,
            'details': details
        })
    
    def get_csrf_token(self, url):
        """Extract CSRF token from a form page"""
        try:
            response = self.session.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
                if csrf_input:
                    return csrf_input.get('value')
            return None
        except Exception as e:
            print(f"Error getting CSRF token from {url}: {e}")
            return None
    
    def test_login_csrf_protection(self):
        """Test CSRF protection on login forms"""
        print("\n=== Testing Login CSRF Protection ===")
        
        # Test customer login CSRF
        csrf_token = self.get_csrf_token(f"{self.base_url}/customerlogin")
        if csrf_token:
            # Test with valid CSRF token
            login_data = {
                'username': 'testuser',
                'password': 'testpass',
                'csrfmiddlewaretoken': csrf_token
            }
            response = self.session.post(f"{self.base_url}/customerlogin", data=login_data)
            self.log_test("Customer Login CSRF Token Present", True, "CSRF token found in form")
            
            # Test without CSRF token
            login_data_no_csrf = {
                'username': 'testuser',
                'password': 'testpass'
            }
            response_no_csrf = self.session.post(f"{self.base_url}/customerlogin", data=login_data_no_csrf)
            csrf_protected = response_no_csrf.status_code == 403 or "CSRF" in response_no_csrf.text
            self.log_test("Customer Login CSRF Protection", csrf_protected, 
                         "Request without CSRF token properly rejected" if csrf_protected else "CSRF protection may be missing")
        else:
            self.log_test("Customer Login CSRF Token Present", False, "No CSRF token found in login form")
        
        # Test admin login CSRF
        csrf_token = self.get_csrf_token(f"{self.base_url}/adminlogin")
        if csrf_token:
            self.log_test("Admin Login CSRF Token Present", True, "CSRF token found in admin login form")
            
            # Test without CSRF token
            login_data_no_csrf = {
                'username': 'admin',
                'password': 'adminpass'
            }
            response_no_csrf = self.session.post(f"{self.base_url}/adminlogin", data=login_data_no_csrf)
            csrf_protected = response_no_csrf.status_code == 403 or "CSRF" in response_no_csrf.text
            self.log_test("Admin Login CSRF Protection", csrf_protected,
                         "Request without CSRF token properly rejected" if csrf_protected else "CSRF protection may be missing")
        else:
            self.log_test("Admin Login CSRF Token Present", False, "No CSRF token found in admin login form")
    
    def test_registration_csrf_protection(self):
        """Test CSRF protection on registration forms"""
        print("\n=== Testing Registration CSRF Protection ===")
        
        csrf_token = self.get_csrf_token(f"{self.base_url}/customersignup")
        if csrf_token:
            self.log_test("Customer Registration CSRF Token Present", True, "CSRF token found in registration form")
            
            # Test without CSRF token
            reg_data_no_csrf = {
                'first_name': 'Test',
                'last_name': 'User',
                'username': 'testuser123',
                'email': 'test@example.com',
                'password1': 'testpassword123',
                'password2': 'testpassword123'
            }
            response_no_csrf = self.session.post(f"{self.base_url}/customersignup", data=reg_data_no_csrf)
            csrf_protected = response_no_csrf.status_code == 403 or "CSRF" in response_no_csrf.text
            self.log_test("Customer Registration CSRF Protection", csrf_protected,
                         "Request without CSRF token properly rejected" if csrf_protected else "CSRF protection may be missing")
        else:
            self.log_test("Customer Registration CSRF Token Present", False, "No CSRF token found in registration form")
    
    def test_form_csrf_tokens(self):
        """Test CSRF tokens in various forms across the application"""
        print("\n=== Testing Form CSRF Tokens ===")
        
        # List of pages that should contain forms with CSRF tokens
        form_pages = [
            ('/customerlogin', 'Customer Login'),
            ('/customersignup', 'Customer Registration'),
            ('/adminlogin', 'Admin Login'),
            ('/contact', 'Contact Form'),
        ]
        
        for url, page_name in form_pages:
            try:
                response = self.session.get(f"{self.base_url}{url}")
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    forms = soup.find_all('form')
                    csrf_found = False
                    
                    for form in forms:
                        csrf_input = form.find('input', {'name': 'csrfmiddlewaretoken'})
                        if csrf_input:
                            csrf_found = True
                            break
                    
                    self.log_test(f"{page_name} CSRF Token", csrf_found,
                                 "CSRF token found in form" if csrf_found else "No CSRF token found")
                else:
                    self.log_test(f"{page_name} CSRF Token", False, f"Page not accessible (status: {response.status_code})")
            except Exception as e:
                self.log_test(f"{page_name} CSRF Token", False, f"Error accessing page: {e}")
    
    def test_csrf_token_validation(self):
        """Test CSRF token validation with invalid tokens"""
        print("\n=== Testing CSRF Token Validation ===")
        
        # Test with invalid CSRF token
        invalid_tokens = [
            'invalid_token_123',
            '',
            'a' * 64,  # Wrong length
            '12345',   # Too short
        ]
        
        for invalid_token in invalid_tokens:
            login_data = {
                'username': 'testuser',
                'password': 'testpass',
                'csrfmiddlewaretoken': invalid_token
            }
            
            try:
                response = self.session.post(f"{self.base_url}/customerlogin", data=login_data)
                csrf_rejected = response.status_code == 403 or "CSRF" in response.text or "Forbidden" in response.text
                self.log_test(f"Invalid CSRF Token Rejection ({invalid_token[:10]}...)", csrf_rejected,
                             "Invalid token properly rejected" if csrf_rejected else "Invalid token may have been accepted")
            except Exception as e:
                self.log_test(f"Invalid CSRF Token Test ({invalid_token[:10]}...)", False, f"Error: {e}")
    
    def test_csrf_referer_validation(self):
        """Test CSRF referer header validation"""
        print("\n=== Testing CSRF Referer Validation ===")
        
        csrf_token = self.get_csrf_token(f"{self.base_url}/customerlogin")
        if csrf_token:
            # Test with malicious referer
            headers = {
                'Referer': 'http://malicious-site.com/attack'
            }
            
            login_data = {
                'username': 'testuser',
                'password': 'testpass',
                'csrfmiddlewaretoken': csrf_token
            }
            
            try:
                response = self.session.post(f"{self.base_url}/customerlogin", 
                                           data=login_data, headers=headers)
                referer_protected = response.status_code == 403 or "CSRF" in response.text
                self.log_test("CSRF Referer Validation", referer_protected,
                             "Malicious referer properly rejected" if referer_protected else "Referer validation may be missing")
            except Exception as e:
                self.log_test("CSRF Referer Validation", False, f"Error: {e}")
        else:
            self.log_test("CSRF Referer Validation", False, "Could not get CSRF token for testing")
    
    def test_ajax_csrf_protection(self):
        """Test CSRF protection for AJAX requests"""
        print("\n=== Testing AJAX CSRF Protection ===")
        
        # Test AJAX request without CSRF token
        headers = {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json'
        }
        
        ajax_data = {'test': 'data'}
        
        try:
            response = self.session.post(f"{self.base_url}/customerlogin", 
                                       json=ajax_data, headers=headers)
            csrf_protected = response.status_code == 403 or "CSRF" in response.text
            self.log_test("AJAX CSRF Protection", csrf_protected,
                         "AJAX request without CSRF token properly rejected" if csrf_protected else "AJAX CSRF protection may be missing")
        except Exception as e:
            self.log_test("AJAX CSRF Protection", False, f"Error: {e}")
    
    def run_all_tests(self):
        """Run all CSRF security tests"""
        print("🔒 Starting CSRF Protection Security Tests...")
        print("=" * 60)
        
        self.test_login_csrf_protection()
        self.test_registration_csrf_protection()
        self.test_form_csrf_tokens()
        self.test_csrf_token_validation()
        self.test_csrf_referer_validation()
        self.test_ajax_csrf_protection()
        
        # Calculate results
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print("\n" + "=" * 60)
        print("📊 CSRF PROTECTION TEST SUMMARY")
        print("=" * 60)
        print(f"Tests Passed: {passed_tests}/{total_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("✅ CSRF protection is STRONG!")
        elif success_rate >= 60:
            print("⚠️  CSRF protection needs IMPROVEMENT")
        else:
            print("❌ CSRF protection is WEAK - IMMEDIATE ACTION REQUIRED!")
        
        return success_rate

if __name__ == "__main__":
    tester = CSRFSecurityTester()
    tester.run_all_tests()