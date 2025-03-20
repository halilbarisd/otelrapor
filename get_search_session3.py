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

def select_date_from_calendar(driver, wait, target_date):
    print(f"📅 Tarih seçiliyor: {target_date.strftime('%d/%m/%Y')}")

    # Türkçe aylar sıralı (site dili değişirse düzenle!)
    months_tr = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
                 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']

    # Ay/Yıl doğru mu? Değilse ileri butonuyla gez
    while True:
        month_element = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "ui-datepicker-month")))
        year_element = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "ui-datepicker-year")))

        current_month_name = month_element.text.strip()
        current_year_text = year_element.text.strip()

        print(f"[DEBUG] Ay elementi: '{current_month_name}'")
        print(f"[DEBUG] Yıl elementi: '{current_year_text}'")

        if not current_year_text:
            raise Exception("❌ Yıl elementi boş geldi! Takvim açılmamış olabilir.")

        current_year = int(current_year_text)
        current_month = months_tr.index(current_month_name) + 1

        if current_month == target_date.month and current_year == target_date.year:
            break

        next_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "ui-icon-circle-triangle-e")))
        simulate_mouse_move(driver, next_button)
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
        driver.execute_script("arguments[0].click();", next_button)
        print("➡️ Sonraki aya geçildi.")
        human_wait(0.5, 1.2)

    # Gün seçimi
    day_xpath = f"//a[@class='ui-state-default' and text()='{target_date.day}']"
    day_element = wait.until(EC.element_to_be_clickable((By.XPATH, day_xpath)))

    simulate_mouse_move(driver, day_element)
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", day_element)
    driver.execute_script("arguments[0].click();", day_element)
    print(f"✅ Tarih seçildi: {target_date.strftime('%d/%m/%Y')}")
    human_wait(0.5, 1.5)

# Ana driver başlatma
driver = None

try:
    options = Options()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=Service(), options=options)
    wait = WebDriverWait(driver, 30)

    print("⏳ Sayfa yükleniyor...")
    driver.get("https://www.bedsopia.com/")
    human_wait(3, 4)

    # ➡️ Giriş İşlemi
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
    checkin_date = today + timedelta(days=33)
    checkout_date = today + timedelta(days=48)

    # Check-in tarihi seçimi
    checkin_input = wait.until(EC.element_to_be_clickable((By.ID, "hotels-searcher-_ctl1__ctl1__ctl1_pageBody_pageBody_searcher_ctlMultiSearcher__ctl1_ctlDateSelector-start-date-input")))
    simulate_mouse_move(driver, checkin_input)
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkin_input)
    driver.execute_script("arguments[0].click();", checkin_input)
    human_wait(0.5, 1)
    wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "ui-datepicker-calendar")))

    select_date_from_calendar(driver, wait, checkin_date)

    # Checkout tarihi seçimi
    checkout_input = wait.until(EC.element_to_be_clickable((By.ID, "hotels-searcher-_ctl1__ctl1__ctl1_pageBody_pageBody_searcher_ctlMultiSearcher__ctl1_ctlDateSelector-end-date-input")))
    simulate_mouse_move(driver, checkout_input)
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkout_input)
    driver.execute_script("arguments[0].click();", checkout_input)
    human_wait(0.5, 1)
    wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "ui-datepicker-calendar")))

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

    # ➡️ Search Butonuna Tıklama
    search_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="hotels-searcher"]/div[7]/div[2]/button')))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", search_button)
    human_wait(8, 12)

    # ➡️ Session ID Çekimi
    current_url = driver.current_url
    print(f"🌐 Son URL: {current_url}")

    match = re.search(r"searchSessionID=(\d+)", current_url)
    if match:
        search_session_id = match.group(1)
        print(f"✅ searchSessionID bulundu: {search_session_id}")

        # ➕ Session ID Kaydet
        with open("session_id.txt", "w") as f:
            f.write(search_session_id)

        # ➕ Tarihleri Kaydet
        with open("search_dates.txt", "w") as f:
            f.write(checkin_date.strftime('%Y-%m-%d') + '\n')
            f.write(checkout_date.strftime('%Y-%m-%d'))

        # ➕ Milliyet Kaydet
        with open("nationality.txt", "w") as f:
            f.write(nationality_code)

        # ➕ Cookie Çekimi ve Kaydı
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
