#!/usr/bin/env python3
"""
XSS Protection Security Test Suite
Tests Cross-Site Scripting (XSS) protection and input validation
"""

import requests
import re
from bs4 import BeautifulSoup
import urllib.parse
import time

class XSSSecurityTester:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        
        # Common XSS payloads
        self.xss_payloads = [
            '<script>alert("XSS")</script>',
            '<img src=x onerror=alert("XSS")>',
            '<svg onload=alert("XSS")>',
            'javascript:alert("XSS")',
            '<iframe src="javascript:alert(\'XSS\')"></iframe>',
            '<body onload=alert("XSS")>',
            '<input onfocus=alert("XSS") autofocus>',
            '<select onfocus=alert("XSS") autofocus>',
            '<textarea onfocus=alert("XSS") autofocus>',
            '<keygen onfocus=alert("XSS") autofocus>',
            '<video><source onerror="alert(\'XSS\')">',
            '<audio src=x onerror=alert("XSS")>',
            '<details open ontoggle=alert("XSS")>',
            '<marquee onstart=alert("XSS")>',
            '"><script>alert("XSS")</script>',
            '\';alert("XSS");//',
            '<script>document.location="http://evil.com"</script>',
            '<img src="javascript:alert(\'XSS\')">'
        ]
        
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
    
    def is_xss_filtered(self, response_text, payload):
        """Check if XSS payload was properly filtered/escaped"""
        # Check if the raw payload appears in the response
        if payload in response_text:
            return False
        
        # Check for common XSS patterns that should be escaped
        dangerous_patterns = [
            '<script',
            'javascript:',
            'onerror=',
            'onload=',
            'onfocus=',
            'onclick=',
            'onmouseover=',
            'alert(',
            'document.location',
            'window.location'
        ]
        
        response_lower = response_text.lower()
        for pattern in dangerous_patterns:
            if pattern in response_lower and pattern in payload.lower():
                # Check if it's properly escaped
                if f'&lt;{pattern[1:]}' not in response_text and f'&amp;{pattern}' not in response_text:
                    return False
        
        return True
    
    def test_registration_form_xss(self):
        """Test XSS protection in registration form"""
        print("\n=== Testing Registration Form XSS Protection ===")
        
        form_fields = [
            ('first_name', 'First Name'),
            ('last_name', 'Last Name'),
            ('username', 'Username'),
            ('email', 'Email')
        ]
        
        for field_name, field_display in form_fields:
            for i, payload in enumerate(self.xss_payloads[:5]):  # Test first 5 payloads
                csrf_token = self.get_csrf_token(f"{self.base_url}/customersignup")
                if csrf_token:
                    reg_data = {
                        'first_name': 'Test' if field_name != 'first_name' else payload,
                        'last_name': 'User' if field_name != 'last_name' else payload,
                        'username': f'testuser_{int(time.time())}' if field_name != 'username' else payload,
                        'email': f'test_{int(time.time())}@example.com' if field_name != 'email' else payload,
                        'password1': 'TestPassword123!',
                        'password2': 'TestPassword123!',
                        'csrfmiddlewaretoken': csrf_token
                    }
                    
                    try:
                        response = self.session.post(f"{self.base_url}/customersignup", data=reg_data)
                        xss_filtered = self.is_xss_filtered(response.text, payload)
                        
                        self.log_test(f"Registration {field_display} XSS Protection #{i+1}", xss_filtered,
                                     f"XSS payload properly filtered" if xss_filtered 
                                     else f"XSS payload may not be filtered: {payload[:30]}...")
                    except Exception as e:
                        self.log_test(f"Registration {field_display} XSS Protection #{i+1}", False, f"Error: {e}")
    
    def test_login_form_xss(self):
        """Test XSS protection in login form"""
        print("\n=== Testing Login Form XSS Protection ===")
        
        for i, payload in enumerate(self.xss_payloads[:3]):  # Test first 3 payloads
            csrf_token = self.get_csrf_token(f"{self.base_url}/customerlogin")
            if csrf_token:
                login_data = {
                    'username': payload,
                    'password': payload,
                    'csrfmiddlewaretoken': csrf_token
                }
                
                try:
                    response = self.session.post(f"{self.base_url}/customerlogin", data=login_data)
                    xss_filtered = self.is_xss_filtered(response.text, payload)
                    
                    self.log_test(f"Login Form XSS Protection #{i+1}", xss_filtered,
                                 f"XSS payload properly filtered" if xss_filtered 
                                 else f"XSS payload may not be filtered: {payload[:30]}...")
                except Exception as e:
                    self.log_test(f"Login Form XSS Protection #{i+1}", False, f"Error: {e}")
    
    def test_url_parameter_xss(self):
        """Test XSS protection in URL parameters"""
        print("\n=== Testing URL Parameter XSS Protection ===")
        
        # Test common URL parameters that might be reflected
        url_params = [
            ('next', 'Next Parameter'),
            ('error', 'Error Parameter'),
            ('message', 'Message Parameter'),
            ('search', 'Search Parameter'),
            ('q', 'Query Parameter')
        ]
        
        for param_name, param_display in url_params:
            for i, payload in enumerate(self.xss_payloads[:3]):  # Test first 3 payloads
                encoded_payload = urllib.parse.quote(payload)
                test_url = f"{self.base_url}/customerlogin?{param_name}={encoded_payload}"
                
                try:
                    response = self.session.get(test_url)
                    xss_filtered = self.is_xss_filtered(response.text, payload)
                    
                    self.log_test(f"URL {param_display} XSS Protection #{i+1}", xss_filtered,
                                 f"XSS payload properly filtered" if xss_filtered 
                                 else f"XSS payload may not be filtered: {payload[:30]}...")
                except Exception as e:
                    self.log_test(f"URL {param_display} XSS Protection #{i+1}", False, f"Error: {e}")
    
    def test_search_functionality_xss(self):
        """Test XSS protection in search functionality"""
        print("\n=== Testing Search Functionality XSS Protection ===")
        
        # Test search on various pages
        search_urls = [
            ('/products', 'Product Search'),
            ('/', 'Home Search'),
        ]
        
        for search_url, search_name in search_urls:
            for i, payload in enumerate(self.xss_payloads[:3]):  # Test first 3 payloads
                # Try GET parameter search
                encoded_payload = urllib.parse.quote(payload)
                test_url = f"{self.base_url}{search_url}?search={encoded_payload}"
                
                try:
                    response = self.session.get(test_url)
                    if response.status_code == 200:
                        xss_filtered = self.is_xss_filtered(response.text, payload)
                        
                        self.log_test(f"{search_name} XSS Protection #{i+1}", xss_filtered,
                                     f"XSS payload properly filtered" if xss_filtered 
                                     else f"XSS payload may not be filtered: {payload[:30]}...")
                    else:
                        self.log_test(f"{search_name} XSS Protection #{i+1}", True, 
                                     f"Search endpoint not accessible (status: {response.status_code})")
                except Exception as e:
                    self.log_test(f"{search_name} XSS Protection #{i+1}", False, f"Error: {e}")
    
    def test_error_message_xss(self):
        """Test XSS protection in error messages"""
        print("\n=== Testing Error Message XSS Protection ===")
        
        # Test error messages by providing invalid data
        for i, payload in enumerate(self.xss_payloads[:3]):  # Test first 3 payloads
            csrf_token = self.get_csrf_token(f"{self.base_url}/customerlogin")
            if csrf_token:
                # Try to trigger error with XSS payload in username
                login_data = {
                    'username': payload,
                    'password': 'wrongpassword',
                    'csrfmiddlewaretoken': csrf_token
                }
                
                try:
                    response = self.session.post(f"{self.base_url}/customerlogin", data=login_data)
                    xss_filtered = self.is_xss_filtered(response.text, payload)
                    
                    self.log_test(f"Error Message XSS Protection #{i+1}", xss_filtered,
                                 f"XSS payload in error properly filtered" if xss_filtered 
                                 else f"XSS payload in error may not be filtered: {payload[:30]}...")
                except Exception as e:
                    self.log_test(f"Error Message XSS Protection #{i+1}", False, f"Error: {e}")
    
    def test_content_security_policy(self):
        """Test Content Security Policy headers"""
        print("\n=== Testing Content Security Policy ===")
        
        try:
            response = self.session.get(f"{self.base_url}/")
            csp_header = response.headers.get('Content-Security-Policy')
            
            if csp_header:
                # Check for important CSP directives
                csp_checks = [
                    ("default-src", "Default source directive"),
                    ("script-src", "Script source directive"),
                    ("object-src", "Object source directive"),
                    ("style-src", "Style source directive")
                ]
                
                for directive, description in csp_checks:
                    has_directive = directive in csp_header
                    self.log_test(f"CSP {description}", has_directive,
                                 f"CSP {directive} directive present" if has_directive 
                                 else f"CSP {directive} directive missing")
                
                # Check for unsafe directives
                unsafe_patterns = ["'unsafe-inline'", "'unsafe-eval'", "*"]
                has_unsafe = any(pattern in csp_header for pattern in unsafe_patterns)
                self.log_test("CSP Safety", not has_unsafe,
                             "CSP does not contain unsafe directives" if not has_unsafe 
                             else "CSP contains potentially unsafe directives")
            else:
                self.log_test("CSP Header Present", False, "Content-Security-Policy header not found")
                
        except Exception as e:
            self.log_test("CSP Header Test", False, f"Error: {e}")
    
    def test_x_xss_protection_header(self):
        """Test X-XSS-Protection header"""
        print("\n=== Testing X-XSS-Protection Header ===")
        
        try:
            response = self.session.get(f"{self.base_url}/")
            xss_protection = response.headers.get('X-XSS-Protection')
            
            if xss_protection:
                # Check for proper XSS protection value
                proper_values = ['1; mode=block', '1']
                is_proper = xss_protection in proper_values
                self.log_test("X-XSS-Protection Header", is_proper,
                             f"X-XSS-Protection properly set: {xss_protection}" if is_proper 
                             else f"X-XSS-Protection may be improperly configured: {xss_protection}")
            else:
                self.log_test("X-XSS-Protection Header", False, "X-XSS-Protection header not found")
                
        except Exception as e:
            self.log_test("X-XSS-Protection Header", False, f"Error: {e}")
    
    def test_x_content_type_options(self):
        """Test X-Content-Type-Options header"""
        print("\n=== Testing X-Content-Type-Options Header ===")
        
        try:
            response = self.session.get(f"{self.base_url}/")
            content_type_options = response.headers.get('X-Content-Type-Options')
            
            if content_type_options:
                is_nosniff = content_type_options.lower() == 'nosniff'
                self.log_test("X-Content-Type-Options Header", is_nosniff,
                             "X-Content-Type-Options properly set to nosniff" if is_nosniff 
                             else f"X-Content-Type-Options improperly configured: {content_type_options}")
            else:
                self.log_test("X-Content-Type-Options Header", False, "X-Content-Type-Options header not found")
                
        except Exception as e:
            self.log_test("X-Content-Type-Options Header", False, f"Error: {e}")
    
    def run_all_tests(self):
        """Run all XSS security tests"""
        print("🛡️ Starting XSS Protection Security Tests...")
        print("=" * 60)
        
        self.test_registration_form_xss()
        self.test_login_form_xss()
        self.test_url_parameter_xss()
        self.test_search_functionality_xss()
        self.test_error_message_xss()
        self.test_content_security_policy()
        self.test_x_xss_protection_header()
        self.test_x_content_type_options()
        
        # Calculate results
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print("\n" + "=" * 60)
        print("📊 XSS PROTECTION TEST SUMMARY")
        print("=" * 60)
        print(f"Tests Passed: {passed_tests}/{total_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("✅ XSS protection is STRONG!")
        elif success_rate >= 60:
            print("⚠️  XSS protection needs IMPROVEMENT")
        else:
            print("❌ XSS protection is WEAK - IMMEDIATE ACTION REQUIRED!")
        
        return success_rate

if __name__ == "__main__":
    tester = XSSSecurityTester()
    tester.run_all_tests()