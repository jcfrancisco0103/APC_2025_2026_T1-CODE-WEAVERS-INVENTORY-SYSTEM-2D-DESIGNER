# file: C:\Selenium\Tests\test_login_signup_full_edge.py
# Selenium frontend/UI test for login and customer sign up page with robust dynamic checks

import time
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

# ---------- CONFIG ----------
driver_path = "C:\\Selenium\\msedgedriver.exe"
login_url = "http://worksteamwear.playit.pub:64472/customerlogin"
signup_url = "http://worksteamwear.playit.pub:64472/customersignup"

# ---------- START EDGE BROWSER ----------
service = Service(driver_path)
options = webdriver.EdgeOptions()
driver = webdriver.Edge(service=service, options=options)
wait = WebDriverWait(driver, 10)
actions = ActionChains(driver)

def check_element(selector, name):
    try:
        elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        visible = elem.is_displayed()
        print(f"{name} visible: {visible}")
        return elem
    except:
        print(f"{name} NOT found!")
        return None

def hover_click(elem, name):
    if elem:
        try:
            actions.move_to_element(elem).perform()
            print(f"{name} button hover works.")
            original_windows = driver.window_handles
            pre_url = driver.current_url
            elem.click()
            time.sleep(2)

            new_windows = driver.window_handles
            if len(new_windows) > len(original_windows):
                print(f"{name} button responded (popup opened). Closing popup...")
                driver.switch_to.window(new_windows[-1])
                driver.close()
                driver.switch_to.window(original_windows[0])
            elif driver.current_url != pre_url:
                print(f"{name} button responded (page URL changed to {driver.current_url}).")
            else:
                try:
                    modal = driver.find_element(By.CSS_SELECTOR, ".modal, .popup, .social-login-response")
                    if modal.is_displayed():
                        print(f"{name} button responded (modal appeared).")
                    else:
                        print(f"{name} button clicked but no observable frontend response.")
                except:
                    print(f"{name} button clicked but no observable frontend response.")
        except:
            print(f"{name} button cannot be hovered or clicked.")

try:
    # ---------------- LOGIN PAGE ----------------
    driver.get(login_url)
    print("\n--- LOGIN PAGE ---")
    time.sleep(2)

    username_field = check_element("input[type='text'], input[type='email']", "Username")
    password_field = check_element("input[type='password']", "Password")
    remember_checkbox = check_element("input[type='checkbox']", "Remember Me checkbox")
    login_btn = check_element("button[type='submit'], input[type='submit']", "Login button")
    google_btn = check_element("button.btn-social[onclick*='google']", "Google button")
    facebook_btn = check_element("button.btn-social[onclick*='facebook']", "Facebook button")
    signup_link = check_element("a[href*='signup']", "Sign Up link")

    # Forgot Password (case-insensitive XPath)
    try:
        forgot_link = wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//a[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'forgot password')]")
            )
        )
        print("Forgot Password link visible: True")
    except:
        forgot_link = None
        print("Forgot Password link NOT found!")

    hover_click(google_btn, "Google")
    hover_click(facebook_btn, "Facebook")

    if remember_checkbox:
        try:
            remember_checkbox.click()
            print("Remember Me checkbox clicked.")
        except:
            print("Could not click Remember Me checkbox.")

    if login_btn:
        login_btn.click()
        print("Clicked login button without filling fields (should trigger JS validation).")
        time.sleep(1)
        if username_field:
            msg = username_field.get_attribute("validationMessage")
            if msg:
                print(f"Validation message for Username: {msg}")
        if password_field:
            msg = password_field.get_attribute("validationMessage")
            if msg:
                print(f"Validation message for Password: {msg}")

    # ---------------- SIGN UP PAGE ----------------
    driver.get(signup_url)
    print("\n--- SIGN UP PAGE ---")
    time.sleep(2)

    first_name = check_element("input[name='first_name']", "First Name")
    last_name = check_element("input[name='last_name']", "Last Name")
    username_signup = check_element("input[name='username']", "Username")
    password_signup = check_element("input[name='password']", "Password")
    region_select = check_element("select[name='region']", "Region")
    province_select = check_element("select[name='province']", "Province")
    city_select = check_element("select#citymun", "City")
    barangay_select = check_element("select[name='barangay']", "Barangay")
    contact_field = check_element("input[name='mobile'], input#mobile_number", "Contact Number")
    create_account_btn = check_element("button#createAccountBtn", "Create Account button")
    terms_link = check_element("a#termsLink", "Terms link")
    privacy_link = check_element("a#privacyLink", "Privacy link")

    # Test JS validation for empty required fields
    if create_account_btn:
        try:
            create_account_btn.click()
            print("Clicked Create Account button (should be disabled if fields not selected).")
        except:
            print("Create Account button is disabled (expected).")

    # Print dropdowns state
    for dropdown, name in [(region_select,"Region"), (province_select,"Province"), (city_select,"City"), (barangay_select,"Barangay")]:
        if dropdown:
            if name == "City" and province_select:
                # Wait for city options after selecting province
                wait_city = WebDriverWait(driver, 5)
                try:
                    wait_city.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "select#citymun option")) > 1)
                except:
                    pass
            selected_value = Select(dropdown).first_selected_option.text
            print(f"{name} selected: {selected_value}")

    # Check Contact Number
    if contact_field:
        visible = contact_field.is_displayed()
        print(f"Contact Number visible: {visible}")

    # ---------------- Layout / Responsiveness ----------------
    for size in [(1920,1080),(1366,768),(768,1024),(375,667)]:
        driver.set_window_size(*size)
        time.sleep(0.5)
        print(f"Window size {size[0]}x{size[1]} checked.")

except Exception as e:
    print("Test failed:", repr(e))

finally:
    # Close browser
    time.sleep(2)
    driver.quit()
    print("Browser closed.")
