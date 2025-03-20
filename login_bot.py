import random
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

# İnsan benzeri bekleme
def human_wait(min_sec=0.5, max_sec=1.5):
    time.sleep(random.uniform(min_sec, max_sec))

# Harf harf yazma efekti
def human_typing(element, text):
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.1, 0.3))

# Fare hareketi simülasyonu
def simulate_mouse_move(driver, element):
    actions = ActionChains(driver)
    actions.move_to_element(element).perform()
    human_wait(0.3, 0.8)

# Başlangıç ayarları
options = Options()
options.add_argument("--start-maximized")

driver = webdriver.Chrome(service=Service(), options=options)

driver.get("https://www.bedsopia.com/")
wait = WebDriverWait(driver, 30)

try:
    print("⏳ Sayfa yükleniyor...")
    human_wait(3, 4)

    # 1️⃣ Giriş butonunu bul ve tıkla
    print("🟢 Giriş butonuna JS ile tıklanacak...")
    giris_butonu = wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, "button.upper-menu__login-button.js-login-box-modal")
    ))

    driver.execute_script("arguments[0].click();", giris_butonu)
    print("✅ Giriş popup açıldı!")
    
    # Popup'ın tam yüklenmesini bekle (ekstra garanti)
    human_wait(2, 3)

    # 2️⃣ Kullanıcı adı gir
    print("🟢 Kullanıcı adı yazılıyor...")
    username_input = wait.until(EC.presence_of_element_located((By.ID, "login-box-user")))
    simulate_mouse_move(driver, username_input)
    username_input.click()
    human_wait(0.5, 1)
    human_typing(username_input, "HiFoursTravel")  # ➡️ Kendi kullanıcı adını gir!

    # 3️⃣ Şifre gir
    print("🟢 Şifre yazılıyor...")
    password_input = wait.until(EC.presence_of_element_located((By.ID, "login-box-password")))
    simulate_mouse_move(driver, password_input)
    password_input.click()
    human_wait(0.5, 1)
    human_typing(password_input, "HiFoursTravel24*")  # ➡️ Kendi şifreni gir!

    # 4️⃣ Şartlar kutusuna tıkla
    print("🟢 Şartlar ve koşullar kutusu işaretleniyor...")
    terms_checkbox = wait.until(EC.element_to_be_clickable((By.ID, "login-box-terms-and-conditions")))
    driver.execute_script("arguments[0].click();", terms_checkbox)
    human_wait(0.5, 1)

    # 5️⃣ Giriş yap butonuna tıkla
    print("🟢 Giriş yap butonuna tıklanıyor...")
    giris_yap_butonu = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.js-auto-form-submit")))
    simulate_mouse_move(driver, giris_yap_butonu)
    driver.execute_script("arguments[0].click();", giris_yap_butonu)

    print("✅ Giriş başarılı, bekleniyor...")
    human_wait(3, 5)

    # Çerezleri alıyoruz
    cookies = driver.get_cookies()
    cookie_string = "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])

    print("✅ Cookie Başarıyla Alındı:")
    print(cookie_string)

    # Cookie'leri txt dosyasına yaz
    with open("cookies.txt", "w") as f:
        f.write(cookie_string)

    print("✅ Cookie dosyaya kaydedildi.")


except Exception as e:
    print(f"❌ Hata oluştu: {e}")

finally:
    driver.quit()
    print("🟣 Tarayıcı kapatıldı.")
