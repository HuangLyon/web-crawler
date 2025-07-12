from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
import random
import time
import csv
import re
import json

# --- Set up Chrome options ---
chrome_options = Options()
# chrome_options.add_argument("--headless=new")  # Run in headless mode
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--log-level=3")  # Suppress warnings

# ✅ Initialize driver AFTER setting options
driver = webdriver.Chrome(options=chrome_options)

# --- Visit the YouTube video ---
video_url = 'https://www.youtube.com/watch?v=I8u-y8EiD74'
driver.get(video_url)
time.sleep(5)

# --- Scroll to the comment section ---
element = driver.find_element(By.XPATH, '//*[@id="comments"]')
driver.execute_script("arguments[0].scrollIntoView(true);", element)
time.sleep(3)

# --- Scroll to load comments ---
old_position = 0
new_position = None
while new_position != old_position:
    old_position = driver.execute_script("return document.documentElement.scrollHeight")
    driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
    time.sleep(5)
    new_position = driver.execute_script("return document.documentElement.scrollHeight")

driver.find_element('xpath', '//body').send_keys(Keys.HOME)
time.sleep(3)


# --- Expand all replies ---
def expand_replies():
    wait = WebDriverWait(driver, 10)
    last_count = 0
    while True:
        # Find all "View replies" buttons that are visible and clickable
        more_replies_buttons = driver.find_elements(By.ID, 'more-replies')
        # Alternative xpath if some buttons have text like "View 2 replies"
        more_replies_buttons = driver.find_elements(By.ID, 'more-replies')

        # Remove duplicates by using a set or convert list to unique list by id
        more_replies_buttons = list(set(more_replies_buttons))

        if len(more_replies_buttons) == 0 or len(more_replies_buttons) == last_count:
            # No new buttons or no change after last iteration, break
            break
        last_count = len(more_replies_buttons)

        for button in more_replies_buttons:
            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", button)
                # Click only if visible and enabled
                if button.is_displayed() and button.is_enabled():
                    driver.execute_script("arguments[0].click();", button)
                    time.sleep(1)  # wait to load replies
            except Exception as e:
                # Continue if any clicking error occurs
                print(f"Error clicking reply button: {e}")
                continue

expand_replies()

def expand_more_replies():
    driver.execute_script('window.scrollTo(0, 1000)')
    time.sleep(3)
    try:
        while True:
            more_replies_buttons = driver.find_elements(By.XPATH, '//*[@id="button"]/ytd-button-renderer/yt-button-shape/button/yt-touch-feedback-shape/div/div[2]')
            time.sleep(2)
            if not more_replies_buttons:
                break
            for more_btn in more_replies_buttons:
                try:
                    driver.execute_script("arguments[0].scrollIntoView(true);",more_btn)
                    driver.execute_script("arguments[0].click();", more_btn)
                    time.sleep(2)
                except Exception as e:
                    print("Error clicking a 'more replies' button:", e)
    except Exception as e:
        print("Replies expansion loop error:", e)

expand_more_replies()

# --- Get the comment count (for verification) ---
try:
    comment_count_text = driver.find_element(By.XPATH, '//h2[@id="count"]/yt-formatted-string/span').text
    comment_count = int(comment_count_text.replace(",", "").split()[0])
except:
    comment_count = None

# --- Retry to expand replies if comments are missing ---
retries = 0
while comment_count and retries < 5:
    driver.execute_script('window.scrollTo(0, 1000)')
    comment_elements = driver.find_elements(By.XPATH, '//*[@id="content-text"]/span')
    time.sleep(60)
    if len(comment_elements) >= comment_count:
        break
    print(f"🔄 Loading more comments: {len(comment_elements)}/{comment_count}")
    driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
    time.sleep(2)
    expand_replies()
    expand_more_replies()
    retries += 1



# --- Final data extraction ---
comment_elements = driver.find_elements(By.XPATH, '//*[@id="content-text"]/span')
author_elements = driver.find_elements(By.ID, 'author-text')
time_elements = driver.find_elements(By.ID, 'published-time-text')

comments = [c.text for c in comment_elements]
authors = [a.text.strip() for a in author_elements]
timestamps = [t.text for t in time_elements]

# --- Get video title ---
try:
    title_elem = driver.find_element(By.ID, "title")
    title = title_elem.text.strip()
except:
    title = "youtube_comments"

safe_title = re.sub(r'[\\/*?:"<>|]', "", title)
filename_csv = safe_title + ".csv"
filename_json = safe_title + ".json"

# --- Save to CSV ---
with open(filename_csv, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(["Username", "Comment", "Comment Time"])
    for user, comment, time_ in zip(authors, comments, timestamps):
        writer.writerow([user, comment, time_])

# --- Save to JSON ---
data = [{"username": user, "comment": comment, "time": time_}
        for user, comment, time_ in zip(authors, comments, timestamps)]

with open(filename_json, mode='w', encoding='utf-8') as fjson:
    json.dump(data, fjson, ensure_ascii=False, indent=2)

# ✅ Final report
print(f"\n✅ Done! Extracted {len(data)} comments.")
print(f"📄 Saved to: {filename_csv} and {filename_json}")

# --- Close the driver ---
driver.quit()

