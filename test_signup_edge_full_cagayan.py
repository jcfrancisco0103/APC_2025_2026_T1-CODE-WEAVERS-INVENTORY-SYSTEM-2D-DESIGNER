# Full robust Edge signup script with exact location selection
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

# ---------- CONFIG ----------
driver_path = "C:\\Selenium\\msedgedriver.exe"
signup_url = "http://worksteamwear.playit.pub:64472/customersignup"

# ---------- UNIQUE TEST DATA ----------
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
first_name = "TestFirst"
last_name = "TestLast"
username = f"testuser{timestamp}"
password = "TestPass123!"
region_text = "Cagayan Valley"
province_text = "Batanes"
city_text = "Basco"
barangay_text = "San Antonio"
street_address = "123 Test St"
postal_code = "1000"
mobile_number = f"956{timestamp[-7:]}"  # unique last 7 digits

# ---------- START EDGE ----------
service = Service(driver_path)
options = webdriver.EdgeOptions()
driver = webdriver.Edge(service=service, options=options)
wait = WebDriverWait(driver, 60)  # increased wait

try:
    driver.get(signup_url)
    print("Opened signup URL")

    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(2)

    # ---------- Fill Personal Info ----------
    print("Filling First Name...")
    wait.until(EC.element_to_be_clickable((By.ID, "id_first_name"))).send_keys(first_name)

    print("Filling Last Name...")
    wait.until(EC.element_to_be_clickable((By.ID, "id_last_name"))).send_keys(last_name)

    print("Filling Username...")
    wait.until(EC.element_to_be_clickable((By.ID, "id_username"))).send_keys(username)

    print("Filling Password...")
    wait.until(EC.element_to_be_clickable((By.ID, "id_password"))).send_keys(password)
    wait.until(EC.element_to_be_clickable((By.ID, "id_confirm_password"))).send_keys(password)

    # ---------- Shipping Address ----------
    # REGION
    print(f"Selecting Region: {region_text}")
    region_elem = wait.until(EC.presence_of_element_located((By.ID, "region")))
    driver.execute_script("arguments[0].scrollIntoView(true); arguments[0].focus();", region_elem)
    Select(region_elem).select_by_visible_text(region_text)
    time.sleep(2)

    # PROVINCE
    print(f"Selecting Province: {province_text}")
    province_elem = wait.until(EC.presence_of_element_located((By.ID, "province")))
    driver.execute_script("arguments[0].scrollIntoView(true); arguments[0].focus();", province_elem)
    Select(province_elem).select_by_visible_text(province_text)
    time.sleep(2)

    # CITY
    print(f"Selecting City: {city_text}")
    city_elem = wait.until(EC.presence_of_element_located((By.ID, "citymun")))
    for i in range(20):
        options = city_elem.find_elements(By.TAG_NAME, "option")
        if any(opt.text.strip() == city_text for opt in options):
            break
        time.sleep(0.5)
    else:
        raise Exception("City options never loaded")
    Select(city_elem).select_by_visible_text(city_text)
    time.sleep(1)

    # BARANGAY
    print(f"Selecting Barangay: {barangay_text}")
    barangay_elem = wait.until(EC.presence_of_element_located((By.ID, "barangay")))
    for i in range(20):
        options = barangay_elem.find_elements(By.TAG_NAME, "option")
        if any(opt.text.strip() == barangay_text for opt in options):
            break
        time.sleep(0.5)
    else:
        raise Exception("Barangay options never loaded")
    Select(barangay_elem).select_by_visible_text(barangay_text)
    time.sleep(1)

    # STREET ADDRESS, POSTAL, MOBILE
    print("Filling Street Address...")
    wait.until(EC.element_to_be_clickable((By.ID, "id_street_address"))).send_keys(street_address)

    print("Filling Postal Code...")
    driver.find_element(By.ID, "id_postal_code").send_keys(postal_code)

    print("Filling Mobile Number...")
    driver.find_element(By.ID, "mobile_number").send_keys(mobile_number)

    # TERMS CHECKBOX
    print("Checking Terms checkbox...")
    checkbox = wait.until(EC.element_to_be_clickable((By.ID, "terms")))
    if not checkbox.is_selected():
        checkbox.click()

    # CREATE ACCOUNT
    print("Waiting for Create Account button to be enabled...")
    create_btn = wait.until(EC.element_to_be_clickable((By.ID, "createAccountBtn")))
    create_btn.click()
    print(f"Signup submitted! Username: {username}, Mobile: {mobile_number}")

    time.sleep(5)  # observe result

except Exception as e:
    print("Test failed at step:", repr(e))

finally:
    driver.quit()
    print("Browser closed.")
