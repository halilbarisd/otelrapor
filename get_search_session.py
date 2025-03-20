import time
import random
import re
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
from selenium.webdriver.common.action_chains import ActionChains

def select_date_from_calendar(driver, wait, target_date):
    print(f"📅 Tarih seçiliyor: {target_date.strftime('%m/%d/%Y')}")
    day_target = target_date.day
    day_xpath = f"//a[@class='ui-state-default' and @data-date='{day_target}']"
    day_element = wait.until(EC.element_to_be_clickable((By.XPATH, day_xpath)))
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();", day_element)
    human_wait(0.5, 1)

def human_wait(min_sec=0.5, max_sec=1.5):
    time.sleep(random.uniform(min_sec, max_sec))

def human_typing(element, text):
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.1, 0.3))

def simulate_mouse_move(driver, element):
    actions = ActionChains(driver)
    actions.move_to_element(element).perform()
    human_wait(0.3, 0.8)

driver = None

try:
    options = Options()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=Service(), options=options)
    wait = WebDriverWait(driver, 30)

    print("⏳ Sayfa yükleniyor...")
    driver.get("https://www.bedsopia.com/")
    human_wait(3, 4)

    # ➡️ Giriş Yapılıyor
    print("➡️ Giriş yapılıyor...")
    login_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.upper-menu__login-button.js-login-box-modal")))
    driver.execute_script("arguments[0].click();", login_btn)
    human_wait(2, 3)

    username_input = wait.until(EC.presence_of_element_located((By.ID, "login-box-user")))
    simulate_mouse_move(driver, username_input)
    username_input.click()
    human_typing(username_input, "HiFoursTravel")

    password_input = wait.until(EC.presence_of_element_located((By.ID, "login-box-password")))
    simulate_mouse_move(driver, password_input)
    password_input.click()
    human_typing(password_input, "HiFoursTravel24*")

    terms_checkbox = wait.until(EC.element_to_be_clickable((By.ID, "login-box-terms-and-conditions")))
    driver.execute_script("arguments[0].click();", terms_checkbox)

    login_submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.js-auto-form-submit")))
    simulate_mouse_move(driver, login_submit)
    driver.execute_script("arguments[0].click();", login_submit)
    print("✅ Giriş başarılı!")
    human_wait(3, 5)

    # ➡️ Destination Seçimi
    destination_input = wait.until(EC.presence_of_element_located((By.ID, "hotels-searcher-_ctl1__ctl1__ctl1_pageBody_pageBody_searcher_ctlMultiSearcher__ctl1_ctlZoneSelector-input")))
    driver.execute_script("arguments[0].click(); arguments[0].focus();", destination_input)
    human_wait(1, 2)

    driver.execute_script("arguments[0].value='istanbul';", destination_input)
    driver.execute_script("arguments[0].dispatchEvent(new Event('input'));", destination_input)
    human_wait(4, 5)

    first_suggestion = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.tt-suggestion.tt-selectable")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", first_suggestion)
    first_suggestion.click()
    human_wait(2, 3)

    # ➡️ Tarih Seçimi
    today = datetime.today()
    checkin_date = today + timedelta(days=3)
    checkout_date = today + timedelta(days=18)

    checkin_input = wait.until(EC.element_to_be_clickable((By.ID, "hotels-searcher-_ctl1__ctl1__ctl1_pageBody_pageBody_searcher_ctlMultiSearcher__ctl1_ctlDateSelector-start-date-input")))
    checkin_input.click()
    select_date_from_calendar(driver, wait, checkin_date)

    checkout_input = wait.until(EC.element_to_be_clickable((By.ID, "hotels-searcher-_ctl1__ctl1__ctl1_pageBody_pageBody_searcher_ctlMultiSearcher__ctl1_ctlDateSelector-end-date-input")))
    checkout_input.click()
    select_date_from_calendar(driver, wait, checkout_date)

    # ➡️ Nationality Seçimi
    nationality_text = "Irlanda"
    nationality_code = "IE"

    nationality_dropdown = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[@id='select2-hotels-searcher-nationality-container']")))
    nationality_dropdown.click()
    human_wait(1, 2)

    nationality_option = wait.until(EC.element_to_be_clickable((By.XPATH, f"//li[contains(text(),'{nationality_text}')]")))
    nationality_option.click()
    human_wait(2, 3)

    # ➡️ Search butonuna tıklama
    search_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="hotels-searcher"]/div[7]/div[2]/button')))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", search_button)
    human_wait(8, 12)

    # ➡️ Session ID çekimi
    current_url = driver.current_url
    print(f"🌐 Son URL: {current_url}")

    match = re.search(r"searchSessionID=(\d+)", current_url)
    if match:
        search_session_id = match.group(1)
        print(f"✅ searchSessionID bulundu: {search_session_id}")

        # ➕ Session ID kaydet
        with open("session_id.txt", "w") as f:
            f.write(search_session_id)

        # ➕ Tarihleri kaydet
        with open("search_dates.txt", "w") as f:
            f.write(checkin_date.strftime('%Y-%m-%d') + '\n')
            f.write(checkout_date.strftime('%Y-%m-%d'))

        # ➕ Milliyet kaydet
        with open("nationality.txt", "w") as f:
            f.write(nationality_code)

        # ➕ Cookie çekimi ve kaydı
        cookies = driver.get_cookies()
        cookie_string = "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])

        with open("cookies.txt", "w") as f:
            f.write(cookie_string)

        print("💾 Bütün veriler kaydedildi! (session_id, dates, nationality, cookies)")
    else:
        print("❌ searchSessionID bulunamadı!")

except Exception as e:
    print(f"❌ Genel hata oluştu: {e}")

finally:
    if driver:
        driver.quit()
        print("🟣 Tarayıcı kapatıldı.")
