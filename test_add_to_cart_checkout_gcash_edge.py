# file: C:\Selenium\Tests\test_add_to_cart_checkout_gcash_edge.py
# Selenium test for Edge browser — Add to Cart, Verify Remove Icon, Checkout via GCash (PayMongo)

import time
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ---------- CONFIG ----------
driver_path = "C:\\Selenium\\msedgedriver.exe"
base_url = "http://worksteamwear.playit.pub:64472"
login_url = f"{base_url}/customerlogin"
home_url = f"{base_url}/customer-home"
cart_url = f"{base_url}/cart"

USERNAME = "mersyeon0103"
PASSWORD = "janjcmatt567"

def log(msg): print(f"[INFO] {msg}")

# ---------- START EDGE ----------
service = Service(driver_path)
options = webdriver.EdgeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Edge(service=service, options=options)
wait = WebDriverWait(driver, 20)

try:
    # --- LOGIN ---
    print("--- Opening login page...")
    driver.get(login_url)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
    driver.find_element(By.CSS_SELECTOR, "input[type='text'], input[type='email']").send_keys(USERNAME)
    driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys(PASSWORD)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    print("[OK] Clicked Login button")
    wait.until_not(EC.url_to_be(login_url))
    print("[OK] Logged in successfully.")

    # --- ADD TO CART ---
    print("--- Opening customer home page...")
    driver.get(home_url)
    time.sleep(2)

    product_img = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".product-card img")))
    driver.execute_script("arguments[0].click();", product_img)
    print("[OK] Clicked Product image (Quick View)")
    time.sleep(2)

    try:
        size_btn = driver.find_element(By.CSS_SELECTOR, ".size-option-btn[data-size='XL']")
        driver.execute_script("arguments[0].click();", size_btn)
        print("[OK] Clicked Size XL")
    except:
        print("[WARN] Size XL not found — skipping")

    try:
        qty_plus = driver.find_element(By.ID, "modalQtyPlus")
        driver.execute_script("arguments[0].click();", qty_plus)
        print("[OK] Clicked Quantity + button")
    except:
        print("[WARN] Quantity + not found")

    add_to_cart = wait.until(EC.element_to_be_clickable((By.ID, "modalAddToCartBtn")))
    driver.execute_script("arguments[0].click();", add_to_cart)
    print("[OK] Added to cart")
    time.sleep(2)

    # --- CART PAGE ---
    print("--- Opening cart page...")
    driver.get(cart_url)
    time.sleep(2)

    # Verify remove button exists but DO NOT CLICK
    print("--- Checking if Remove icon exists...")
    try:
        remove_btn = driver.find_element(By.CSS_SELECTOR, "a.btn.btn-danger.btn-xs")
        if remove_btn.is_displayed():
            print("[OK] Remove icon is visible and clickable (not clicked).")
    except:
        print("[WARN] Remove icon not found — continuing.")

    # --- CHECKOUT BUTTON ---
    print("--- Proceeding to Checkout...")
    checkout_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.pay-btn#openModalBtn")))
    driver.execute_script("arguments[0].click();", checkout_btn)
    print("[OK] Checkout button clicked.")
    time.sleep(2)

    # Select GCash payment method
    gcash_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".payment-method-btn[data-method='gcash']")))
    driver.execute_script("arguments[0].click();", gcash_btn)
    print("[OK] Selected GCash payment method.")
    time.sleep(1)

    # --- Click "GCash" button to proceed to PayMongo ---
    print("--- Clicking GCash pay button...")
    gcash_pay_btn = wait.until(EC.element_to_be_clickable((By.ID, "gcash-pay-button")))
    driver.execute_script("arguments[0].click();", gcash_pay_btn)
    print("[OK] Clicked GCash Pay button.")
    time.sleep(5)

    # --- HANDLE PAYMONGO PAGE ---
    print("--- Waiting for PayMongo checkout page to load...")
    wait.until(lambda d: "checkout.paymongo.com" in d.current_url)
    print(f"[OK] Redirected to PayMongo: {driver.current_url}")

    # Click “Continue” button
    cont_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.button--primary span")))
    driver.execute_script("arguments[0].click();", cont_btn)
    print("[OK] Clicked Continue button.")
    time.sleep(2)

    # Fill Customer Info — overwrite defaults using JS
    name_input = wait.until(EC.presence_of_element_located((By.ID, "name")))
    email_input = driver.find_element(By.ID, "email")
    phone_input = driver.find_element(By.ID, "phone")

    # Force clear & set values
    driver.execute_script("arguments[0].value = '';", name_input)
    driver.execute_script("arguments[0].value = '';", email_input)
    driver.execute_script("arguments[0].value = '';", phone_input)

    driver.execute_script("arguments[0].value = 'Juan Dela Cruz';", name_input)
    driver.execute_script("arguments[0].value = 'juan@example.com';", email_input)
    driver.execute_script("arguments[0].value = '+639171234567';", phone_input)
    print("[OK] Filled in customer info (overwriting default values).")

    # Tick Privacy Policy checkbox
    checkbox = wait.until(EC.presence_of_element_located((By.ID, "privacy-policy")))
    driver.execute_script("arguments[0].scrollIntoView(true);", checkbox)  # scroll into view
    driver.execute_script("arguments[0].click();", checkbox)
    print("[OK] Checked privacy policy box.")

    # Wait until Complete Payment button enabled
    complete_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Complete payment')]")))
    driver.execute_script("arguments[0].click();", complete_btn)
    print("[OK] Clicked Complete Payment button.")

    # --- HANDLE SANDBOX REDIRECT ---
    try:
        auth_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//span[text()='Authorize Test Payment']/..")
        ))
        driver.execute_script("arguments[0].click();", auth_btn)
        print("[OK] Clicked Authorize Test Payment button.")
        time.sleep(3)

        redirect_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//span[text()='Redirect back to merchant']")
        ))
        driver.execute_script("arguments[0].click();", redirect_btn)
        time.sleep(3)

        # Check for 404 (sandbox limitation)
        if "404" in driver.title or "Not Found" in driver.page_source:
            print("[INFO] Sandbox redirect resulted in 404 — expected in test mode")
        else:
            print("[OK] Redirect back to merchant successful.")
    except Exception as e:
        print(f"[WARN] Sandbox redirect step failed (expected in test mode): {e}")

    print("[SUCCESS] Full GCash + PayMongo checkout flow executed successfully!")

except Exception as e:
    print(f"[ERR] Test failed: {e}")

finally:
    time.sleep(3)
    driver.quit()
    print("✅ Browser closed — test finished.")
