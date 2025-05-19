import os
import time
import json
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import json
import shutil


def format_changes_for_email(course_name, section, changes):
    lines = [f"📚 Course: {course_name}", f"📂 Section: {section}", "🔔 Changes:\n"]

    for change in changes:
        if change["type"] == "added":
            row = change["row"]
            lines.append(f"➕ New entry: {' | '.join(row)}")
        elif change["type"] == "modified":
            from_row = change["from"]
            to_row = change["to"]
            lines.append(f"✏️ Updated: {' | '.join(from_row)} → {' | '.join(to_row)}")

    return "\n".join(lines)


def backup_and_update_json(old_path, new_path):
    os.makedirs(os.path.dirname(old_path), exist_ok=True)
    shutil.copyfile(new_path, old_path)

def compare_json_with_diff(old_path, new_path):
    if not os.path.exists(old_path):
        with open(new_path, 'r', encoding='utf-8') as f:
            new_data = json.load(f)
        return True, [{"type": "added", "row": row} for row in new_data]

    with open(old_path, 'r', encoding='utf-8') as f1, open(new_path, 'r', encoding='utf-8') as f2:
        old_data = json.load(f1)
        new_data = json.load(f2)

    changes = []
    old_map = {json.dumps(row): row for row in old_data}
    new_map = {json.dumps(row): row for row in new_data}

    # Detect added
    for key, row in new_map.items():
        if key not in old_map:
            changes.append({"type": "added", "row": row})

    # Detect modified rows (same length, similar structure)
    for old_row in old_data:
        for new_row in new_data:
            if old_row and new_row and old_row[0] == new_row[0] and old_row != new_row:
                changes.append({
                    "type": "modified",
                    "from": old_row,
                    "to": new_row
                })

    has_changes = len(changes) > 0
    return has_changes, changes


def extract_table_data(driver):
    table_xpath = "//table[contains(@class, 'table_tree')]"
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, table_xpath))
        )
        table = driver.find_element(By.XPATH, table_xpath)
        rows = table.find_elements(By.XPATH, ".//tbody/tr")

        all_data = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            row_data = []
            for cell in cells:
                paragraphs = cell.find_elements(By.TAG_NAME, "p")
                text = "\n".join(p.text.strip() for p in paragraphs) if paragraphs else cell.text.strip()
                row_data.append(text)
            all_data.append(row_data)

        return all_data
    except Exception as e:
        print("❌ Error extracting table:", e)
        return []

def process_courses_in_new_tabs(driver, roll_number):
    wait = WebDriverWait(driver, 15)
    wait.until(EC.presence_of_element_located((By.ID, "hierarchical_show2")))
    print("✅ Course grid found.")
    course_links = driver.find_elements(By.CSS_SELECTOR, "#hierarchical_show2 > div > a")
    total_courses = len(course_links)
    print(f"Found {total_courses} courses.")

    has_changes = False
    change_messages = []

    for i in range(total_courses):
        try:
            course_links = driver.find_elements(By.CSS_SELECTOR, "#hierarchical_show2 > div > a")
            course_url = course_links[i].get_attribute("href")
            if not course_url:
                print(f"⚠️ No href found for course {i + 1}. Skipping.")
                continue

            driver.execute_script(f"window.open('{course_url}', '_blank');")
            driver.switch_to.window(driver.window_handles[-1])
            print(f"🧭 Opened course {i + 1} in new tab.")

            try:
                name = wait.until(EC.presence_of_element_located((By.XPATH, "//ul[@id='breadcrumbs']/li[2]/a")))
                course_name = name.get_attribute("textContent").strip()
                print(f"✅ Course {i + 1} loaded: {course_name}")

                base_path = f"data/{roll_number}"
                os.makedirs(f"{base_path}/current", exist_ok=True)
                os.makedirs(f"{base_path}/last", exist_ok=True)

                # ----- Announcements -----
                announce_data = extract_table_data(driver)
                announce_json_path = f"{base_path}/current/{course_name}_announcements.json"
                last_announce_path = f"{base_path}/last/{course_name}_announcements.json"
                with open(announce_json_path, "w", encoding="utf-8") as f:
                    json.dump(announce_data, f, indent=2, ensure_ascii=False)

                changed, diffs = compare_json_with_diff(last_announce_path, announce_json_path)
                if changed:
                    backup_and_update_json(last_announce_path, announce_json_path)
                    msg = format_changes_for_email(course_name, "Announcements", diffs)
                    change_messages.append(msg)
                    has_changes = True
                    print(msg)
                else:
                    print(f"✅ No changes in {course_name} - Announcements")

                # ----- Course Material -----
                wait.until(EC.presence_of_element_located((By.XPATH, "//a[text()='Course Material']"))).click()
                time.sleep(1)
                material_data = extract_table_data(driver)
                material_json_path = f"{base_path}/current/{course_name}_course_material.json"
                last_material_path = f"{base_path}/last/{course_name}_course_material.json"
                with open(material_json_path, "w", encoding="utf-8") as f:
                    json.dump(material_data, f, indent=2, ensure_ascii=False)

                changed, diffs = compare_json_with_diff(last_material_path, material_json_path)
                if changed:
                    backup_and_update_json(last_material_path, material_json_path)
                    msg = format_changes_for_email(course_name, "Course Material", diffs)
                    change_messages.append(msg)
                    has_changes = True
                    print(msg)
                else:
                    print(f"✅ No changes in {course_name} - Course Material")

                # ----- Grade Book -----
                wait.until(EC.presence_of_element_located((By.XPATH, "//a[text()='Grade Book']"))).click()
                time.sleep(1)
                grades_data = extract_table_data(driver)
                grades_json_path = f"{base_path}/current/{course_name}_grade_book.json"
                last_grades_path = f"{base_path}/last/{course_name}_grade_book.json"
                with open(grades_json_path, "w", encoding="utf-8") as f:
                    json.dump(grades_data, f, indent=2, ensure_ascii=False)

                changed, diffs = compare_json_with_diff(last_grades_path, grades_json_path)
                if changed:
                    backup_and_update_json(last_grades_path, grades_json_path)
                    msg = format_changes_for_email(course_name, "Grade Book", diffs)
                    change_messages.append(msg)
                    has_changes = True
                    print(msg)
                else:
                    print(f"✅ No changes in {course_name} - Grade Book")

            except Exception as course_page_error:
                print(f"❌ Course {i + 1} failed to load: {course_page_error}")

            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            time.sleep(1)

        except Exception as e:
            print(f"⚠️ Error in course {i + 1}: {e}")
            driver.switch_to.window(driver.window_handles[0])
            continue

    print("🎉 All courses processed.")
    return has_changes, change_messages
