import os
import json
import re
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tab_opener import process_courses_in_new_tabs
import smtplib
from email.message import EmailMessage

def send_email(subject, body, to_email):
    sender_email = "ahmadarshad01972@gmail.com"
    app_password = "xumu djkm hhna unas"  # App Password

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email
    msg.set_content(body)

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, app_password)
            server.send_message(msg)
        print(f"📧 Email sent to {to_email}")
    except Exception as e:
        print(f"❌ Email failed: {e}")

def scrape_user(user, i):
    email = user["ucp_email"]
    password = user["password"]
    notify_email = user["notify_email"]

    direct_login_url = (
        "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id=4a6562df-f309-48d2-94c2-16d03a5c3644"
        "&response_type=code"
        "&redirect_uri=https%3A%2F%2Fhorizon.ucp.edu.pk%2Fauth_oauth%2Fmicrosoft%2Fsignin"
        "&prompt=select_account"
        "&scope=User.Read+Mail.Read+User.ReadWrite.All+Contacts.ReadWrite"
        "&sso_reload=true"
    )

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    #user_data_dir = f"/tmp/selenium_profile_{i}"
    #options.add_argument(f"--user-data-dir={user_data_dir}")
    options.add_argument("--profile-directory=Default")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 30)

    def safe_click(selector, by=By.CSS_SELECTOR, retries=3):
        for attempt in range(retries):
            try:
                elem = wait.until(EC.element_to_be_clickable((by, selector)))
                elem.click()
                return
            except Exception as e:
                print(f"Retrying click due to {e}... Attempt {attempt + 1}/{retries}")
                time.sleep(2)
        raise Exception(f"Failed to click element after {retries} attempts.")

    def handle_stay_signed_in():
        try:
        # If password field is still present, enter password and click sign in
            if driver.find_elements(By.CSS_SELECTOR, "#i0118"):
                print("🔑 Password input still visible — entering password and signing in.")
                password_input = driver.find_element(By.CSS_SELECTOR, "#i0118")
                password_input.clear()
                password_input.send_keys(password)
                safe_click("#idSIButton9")
                time.sleep(1)  # short delay to let next prompt appear
                return  # Exit early — handled password input!

            # Otherwise: handle stay signed in prompt
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#idSIButton9")))
            try:
                checkbox = driver.find_element(By.CSS_SELECTOR, "#KmsiCheckboxField")
                if not checkbox.is_selected():
                    checkbox.click()
                    print("✅ Ticked 'Don't show this again'.")
            except:
                print("⚠️ Checkbox not found or already ticked.")

            safe_click("#idSIButton9")
            print("✅ Clicked 'Stay Signed In'.")
        except:
            print("✅ Stay signed in prompt not shown — proceeding.")


    def handle_account_selection_by_aria_label():
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@aria-label, 'Sign in with')]")))
            accounts = driver.find_elements(By.XPATH, "//div[contains(@aria-label, 'Sign in with')]")
            for acc in accounts:
                label = acc.get_attribute("aria-label")
                if email.lower() in label.lower():
                    acc.click()
                    print(f"✅ Clicked account with aria-label: {label}")
                    return True
            print("⚠ Account not found. Clicking 'Use another account' instead.")
            try:
                other_tile = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@id='otherTile']")))
                other_tile.click()
            except:
                print("❌ 'Other account' not clickable.")
        except:
            print("No account selection screen detected.")
        return False

    try:
        driver.get(direct_login_url)
        print("🌐 Current URL:", driver.current_url)
        print("🕵️ Page title:", driver.title)
        
        screenshot_name = f"screenshot1_{email.split('@')[0]}.png"
        driver.save_screenshot(screenshot_name)
        print(f"📸 Screenshot saved as {screenshot_name}")

        if "login.microsoftonline.com" in driver.current_url:
            if handle_account_selection_by_aria_label():
                try:
                    password_input = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "#i0118"))
                    )
                    password_input.send_keys(password)
                    safe_click("#idSIButton9")
                    handle_stay_signed_in()
                except:
                    print("✅ Password not prompted — proceeding.")
                    handle_stay_signed_in()
            else:
                print("Manual login fallback...")
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#i0116"))).send_keys(email)
                safe_click("#idSIButton9")
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#i0118"))).send_keys(password)
                safe_click("#idSIButton9")
                handle_stay_signed_in()

        time.sleep(5)  # Let UCP load
        for attempt in range(3):
            try:
                icon = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "i.material-icons.md-24")))
                print("✅ Login successful, dashboard loaded!")
                break
            except:
                print(f"🔁 Retrying dashboard load ({attempt + 1})")
                time.sleep(3)
        else:
            raise Exception("❌ Dashboard failed to load.")
        screenshot_name = f"screenshot4_{email.split('@')[0]}.png"
        driver.save_screenshot(screenshot_name)
        print(f"📸 Screenshot saved as {screenshot_name}")

        # Student info
        roll_num = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.uk-width-large-3-10 span:nth-child(2)")))
        number_text = roll_num.get_attribute("textContent").strip()
        st_name = wait.until(EC.presence_of_element_located((By.XPATH, "//span[@class='uk-text-truncate']")))
        student = st_name.get_attribute("textContent").strip()
        grade_box = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(),'Academic Standings:')]")))
        grade = grade_box.get_attribute("textContent").strip()
        clean_grade = re.sub(r'\s+', ' ', grade).strip()

        print(f"👤 {student} | {number_text} | Grade: {clean_grade}")

        has_changes, messages = process_courses_in_new_tabs(driver, number_text)
        if has_changes:
            final_message = "\n\n".join(messages)
            send_email("📢 UCP Portal Update Detected", final_message, notify_email)
        else:
            print("📭 No updates found.")
        return has_changes

    except Exception as e:
        print(f"❌ Error for {email}: {e}")
        # 📸 Take screenshot for debugging
        screenshot_name = f"screenshot5_{email.split('@')[0]}.png"
        driver.save_screenshot(screenshot_name)
        print(f"📸 Screenshot saved as {screenshot_name}")
        return False

    finally:
        print("Closing browser.")
        driver.quit()
