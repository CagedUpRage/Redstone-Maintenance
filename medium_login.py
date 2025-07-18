# medium_login.py
import sys
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

parser = argparse.ArgumentParser()
parser.add_argument('--email', required=True)
parser.add_argument('--password', required=True)
args = parser.parse_args()

driver = webdriver.Chrome()  # Make sure chromedriver is in PATH

try:
    driver.get('https://medium.com/m/signin')
    time.sleep(2)

    # Click "Sign in with email"
    email_button = driver.find_element(By.XPATH, "//button[contains(., 'Sign in with email')]")
    email_button.click()
    time.sleep(2)

    # Enter email
    email_input = driver.find_element(By.NAME, 'email')
    email_input.send_keys(args.email)
    email_input.send_keys(Keys.RETURN)
    time.sleep(2)

    # Enter password
    password_input = driver.find_element(By.NAME, 'password')
    password_input.send_keys(args.password)
    password_input.send_keys(Keys.RETURN)
    time.sleep(5)  # Wait for login to complete

    # Check if login was successful
    if "stories" in driver.page_source or "Write" in driver.page_source:
        print("Login successful!")
    else:
        print("Login may have failed. Please check credentials or for CAPTCHA.")

finally:
    driver.quit()
    