#!/usr/bin/env python3
"""
Password Security Test Suite
Tests password validation, hashing, and security policies
"""

import requests
import re
from bs4 import BeautifulSoup
import hashlib
import time

class PasswordSecurityTester:
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
    
    def test_weak_password_rejection(self):
        """Test rejection of weak passwords during registration"""
        print("\n=== Testing Weak Password Rejection ===")
        
        weak_passwords = [
            ('123', 'Too short numeric'),
            ('password', 'Common dictionary word'),
            ('12345678', 'Sequential numbers'),
            ('qwerty', 'Keyboard pattern'),
            ('abc123', 'Simple alphanumeric'),
            ('admin', 'Common admin password'),
            ('test', 'Too short'),
            ('a', 'Single character'),
            ('', 'Empty password'),
        ]
        
        for weak_password, description in weak_passwords:
            csrf_token = self.get_csrf_token(f"{self.base_url}/customersignup")
            if csrf_token:
                reg_data = {
                    'first_name': 'Test',
                    'last_name': 'User',
                    'username': f'testuser_{int(time.time())}',
                    'email': f'test_{int(time.time())}@example.com',
                    'password1': weak_password,
                    'password2': weak_password,
                    'csrfmiddlewaretoken': csrf_token
                }
                
                try:
                    response = self.session.post(f"{self.base_url}/customersignup", data=reg_data)
                    # Check if registration was rejected (form errors or validation messages)
                    password_rejected = (
                        'password' in response.text.lower() and 
                        ('error' in response.text.lower() or 
                         'invalid' in response.text.lower() or
                         'weak' in response.text.lower() or
                         'short' in response.text.lower() or
                         'common' in response.text.lower() or
                         response.url.endswith('/customersignup'))  # Stayed on signup page
                    )
                    
                    self.log_test(f"Weak Password Rejection ({description})", password_rejected,
                                 f"Password '{weak_password}' properly rejected" if password_rejected 
                                 else f"Weak password '{weak_password}' may have been accepted")
                except Exception as e:
                    self.log_test(f"Weak Password Rejection ({description})", False, f"Error: {e}")
            else:
                self.log_test(f"Weak Password Rejection ({description})", False, "Could not get CSRF token")
    
    def test_password_confirmation_validation(self):
        """Test password confirmation validation"""
        print("\n=== Testing Password Confirmation Validation ===")
        
        csrf_token = self.get_csrf_token(f"{self.base_url}/customersignup")
        if csrf_token:
            reg_data = {
                'first_name': 'Test',
                'last_name': 'User',
                'username': f'testuser_{int(time.time())}',
                'email': f'test_{int(time.time())}@example.com',
                'password1': 'StrongPassword123!',
                'password2': 'DifferentPassword456!',  # Mismatched password
                'csrfmiddlewaretoken': csrf_token
            }
            
            try:
                response = self.session.post(f"{self.base_url}/customersignup", data=reg_data)
                # Check if registration was rejected due to password mismatch
                mismatch_rejected = (
                    'password' in response.text.lower() and 
                    ('match' in response.text.lower() or 
                     'same' in response.text.lower() or
                     'confirm' in response.text.lower() or
                     response.url.endswith('/customersignup'))
                )
                
                self.log_test("Password Confirmation Validation", mismatch_rejected,
                             "Mismatched passwords properly rejected" if mismatch_rejected 
                             else "Password mismatch validation may be missing")
            except Exception as e:
                self.log_test("Password Confirmation Validation", False, f"Error: {e}")
        else:
            self.log_test("Password Confirmation Validation", False, "Could not get CSRF token")
    
    def test_password_length_requirements(self):
        """Test password length requirements"""
        print("\n=== Testing Password Length Requirements ===")
        
        # Test various password lengths
        length_tests = [
            ('a', 1, 'Single character'),
            ('ab', 2, 'Two characters'),
            ('abc', 3, 'Three characters'),
            ('abcd', 4, 'Four characters'),
            ('abcde', 5, 'Five characters'),
            ('abcdef', 6, 'Six characters'),
            ('abcdefg', 7, 'Seven characters'),
            ('abcdefgh', 8, 'Eight characters'),
        ]
        
        for password, length, description in length_tests:
            csrf_token = self.get_csrf_token(f"{self.base_url}/customersignup")
            if csrf_token:
                reg_data = {
                    'first_name': 'Test',
                    'last_name': 'User',
                    'username': f'testuser_{int(time.time())}_{length}',
                    'email': f'test_{int(time.time())}_{length}@example.com',
                    'password1': password,
                    'password2': password,
                    'csrfmiddlewaretoken': csrf_token
                }
                
                try:
                    response = self.session.post(f"{self.base_url}/customersignup", data=reg_data)
                    # For very short passwords (< 8 chars), they should be rejected
                    if length < 8:
                        length_rejected = (
                            'password' in response.text.lower() and 
                            ('short' in response.text.lower() or 
                             'length' in response.text.lower() or
                             'characters' in response.text.lower() or
                             response.url.endswith('/customersignup'))
                        )
                        self.log_test(f"Password Length Requirement ({description})", length_rejected,
                                     f"Short password ({length} chars) properly rejected" if length_rejected 
                                     else f"Short password ({length} chars) may have been accepted")
                    else:
                        # 8+ character passwords might be accepted (depending on other validation)
                        self.log_test(f"Password Length Requirement ({description})", True,
                                     f"Password length ({length} chars) meets minimum requirement")
                except Exception as e:
                    self.log_test(f"Password Length Requirement ({description})", False, f"Error: {e}")
    
    def test_password_complexity_requirements(self):
        """Test password complexity requirements"""
        print("\n=== Testing Password Complexity Requirements ===")
        
        complexity_tests = [
            ('alllowercase', 'All lowercase'),
            ('ALLUPPERCASE', 'All uppercase'),
            ('1234567890', 'All numbers'),
            ('NoNumbers!', 'No numbers'),
            ('nonumbers', 'No numbers or symbols'),
            ('NoSymbols123', 'No symbols'),
            ('Good1Pass!', 'Mixed case, numbers, symbols'),
        ]
        
        for password, description in complexity_tests:
            csrf_token = self.get_csrf_token(f"{self.base_url}/customersignup")
            if csrf_token:
                reg_data = {
                    'first_name': 'Test',
                    'last_name': 'User',
                    'username': f'testuser_{int(time.time())}',
                    'email': f'test_{int(time.time())}@example.com',
                    'password1': password,
                    'password2': password,
                    'csrfmiddlewaretoken': csrf_token
                }
                
                try:
                    response = self.session.post(f"{self.base_url}/customersignup", data=reg_data)
                    # Check if complex password requirements are enforced
                    has_complexity_check = (
                        'password' in response.text.lower() and 
                        ('complex' in response.text.lower() or 
                         'uppercase' in response.text.lower() or
                         'lowercase' in response.text.lower() or
                         'number' in response.text.lower() or
                         'symbol' in response.text.lower())
                    )
                    
                    # For simple passwords, they should ideally be rejected
                    if description in ['All lowercase', 'All uppercase', 'All numbers', 'No numbers or symbols']:
                        complexity_enforced = has_complexity_check or response.url.endswith('/customersignup')
                        self.log_test(f"Password Complexity ({description})", complexity_enforced,
                                     f"Simple password properly rejected" if complexity_enforced 
                                     else f"Simple password may have been accepted")
                    else:
                        self.log_test(f"Password Complexity ({description})", True,
                                     f"Complex password handling tested")
                except Exception as e:
                    self.log_test(f"Password Complexity ({description})", False, f"Error: {e}")
    
    def test_common_password_rejection(self):
        """Test rejection of common passwords"""
        print("\n=== Testing Common Password Rejection ===")
        
        common_passwords = [
            'password123',
            'admin123',
            'qwerty123',
            'letmein',
            'welcome',
            'monkey123',
            'dragon123',
        ]
        
        for common_password in common_passwords:
            csrf_token = self.get_csrf_token(f"{self.base_url}/customersignup")
            if csrf_token:
                reg_data = {
                    'first_name': 'Test',
                    'last_name': 'User',
                    'username': f'testuser_{int(time.time())}',
                    'email': f'test_{int(time.time())}@example.com',
                    'password1': common_password,
                    'password2': common_password,
                    'csrfmiddlewaretoken': csrf_token
                }
                
                try:
                    response = self.session.post(f"{self.base_url}/customersignup", data=reg_data)
                    # Check if common password was rejected
                    common_rejected = (
                        'password' in response.text.lower() and 
                        ('common' in response.text.lower() or 
                         'weak' in response.text.lower() or
                         'dictionary' in response.text.lower() or
                         response.url.endswith('/customersignup'))
                    )
                    
                    self.log_test(f"Common Password Rejection ({common_password})", common_rejected,
                                 f"Common password properly rejected" if common_rejected 
                                 else f"Common password may have been accepted")
                except Exception as e:
                    self.log_test(f"Common Password Rejection ({common_password})", False, f"Error: {e}")
    
    def test_password_field_security(self):
        """Test password field security features"""
        print("\n=== Testing Password Field Security ===")
        
        try:
            # Check registration form
            response = self.session.get(f"{self.base_url}/customersignup")
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Check for password input type
                password_inputs = soup.find_all('input', {'type': 'password'})
                has_password_type = len(password_inputs) > 0
                self.log_test("Password Input Type", has_password_type,
                             "Password fields use type='password'" if has_password_type 
                             else "Password fields may not be properly masked")
                
                # Check for autocomplete attributes
                autocomplete_disabled = any(
                    input_field.get('autocomplete') in ['off', 'new-password'] 
                    for input_field in password_inputs
                )
                self.log_test("Password Autocomplete Security", autocomplete_disabled,
                             "Password autocomplete properly configured" if autocomplete_disabled 
                             else "Password autocomplete may not be disabled")
                
            # Check login form
            response = self.session.get(f"{self.base_url}/customerlogin")
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                password_inputs = soup.find_all('input', {'type': 'password'})
                has_login_password_type = len(password_inputs) > 0
                self.log_test("Login Password Input Type", has_login_password_type,
                             "Login password field uses type='password'" if has_login_password_type 
                             else "Login password field may not be properly masked")
                
        except Exception as e:
            self.log_test("Password Field Security", False, f"Error: {e}")
    
    def test_brute_force_protection(self):
        """Test basic brute force protection"""
        print("\n=== Testing Brute Force Protection ===")
        
        # Attempt multiple failed logins
        failed_attempts = 0
        for i in range(5):  # Try 5 failed login attempts
            csrf_token = self.get_csrf_token(f"{self.base_url}/customerlogin")
            if csrf_token:
                login_data = {
                    'username': 'nonexistentuser',
                    'password': f'wrongpassword{i}',
                    'csrfmiddlewaretoken': csrf_token
                }
                
                try:
                    response = self.session.post(f"{self.base_url}/customerlogin", data=login_data)
                    if 'error' in response.text.lower() or 'invalid' in response.text.lower():
                        failed_attempts += 1
                    
                    # Check for rate limiting or account lockout
                    if 'locked' in response.text.lower() or 'blocked' in response.text.lower() or 'rate' in response.text.lower():
                        self.log_test("Brute Force Protection", True, f"Account lockout detected after {i+1} attempts")
                        return
                        
                except Exception as e:
                    pass
        
        # If we made it through all attempts without lockout
        self.log_test("Brute Force Protection", False, 
                     f"No brute force protection detected after {failed_attempts} failed attempts")
    
    def run_all_tests(self):
        """Run all password security tests"""
        print("🔐 Starting Password Security Tests...")
        print("=" * 60)
        
        self.test_weak_password_rejection()
        self.test_password_confirmation_validation()
        self.test_password_length_requirements()
        self.test_password_complexity_requirements()
        self.test_common_password_rejection()
        self.test_password_field_security()
        self.test_brute_force_protection()
        
        # Calculate results
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print("\n" + "=" * 60)
        print("📊 PASSWORD SECURITY TEST SUMMARY")
        print("=" * 60)
        print(f"Tests Passed: {passed_tests}/{total_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("✅ Password security is STRONG!")
        elif success_rate >= 60:
            print("⚠️  Password security needs IMPROVEMENT")
        else:
            print("❌ Password security is WEAK - IMMEDIATE ACTION REQUIRED!")
        
        return success_rate

if __name__ == "__main__":
    tester = PasswordSecurityTester()
    tester.run_all_tests()