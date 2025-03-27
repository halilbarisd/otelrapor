import csv
#from selenium import webdriver
import undetected_chromedriver as uc
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
import random
from datetime import datetime
import os
import glob
import subprocess  # Git işlemleri için ekledik
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# Klasörü sabitle (değiştirmezsen hep sorun çıkar)
os.chdir('/Users/halilbarisduman/Desktop/otelrapor')

def mail_gonder(konu, mesaj):
    # SMTP Ayarları ➔ Bunları kendine göre doldur!
    smtp_server = 'mail.kurumsaleposta.com'     # SMTP sunucun
    smtp_port = 587                        # Genelde 587 (TLS), 465 (SSL)
    gonderici_email = 'admin@hifourstravel.com' # Gönderen mail
    gonderici_sifre = 'V_NWK-CbqMd:47s'        # Mail şifresi

    # Alıcı ➔ Liste şeklinde yazabilirsin
    alici_email = ['contract@hifourstravel.com']

    # Mail içeriği ➔ HTML Gönderiyoruz
    msg = MIMEMultipart()
    msg['From'] = gonderici_email
    msg['To'] = ", ".join(alici_email)
    msg['Subject'] = konu

    icerik = f"""
    <html>
    <body>
        <p>Merhaba,</p>
        <p><strong>Stop Sale Botu çalıştı.</strong> 5 dakika sonra kontrol edebilirsiniz.</p>
        <p>Uygulama Linki: <a href="https://otelrapor-hifourstravel.streamlit.app">Otel Dashboard'a Git</a></p>
        <br>
        <p>İyi çalışmalar.</p>
    </body>
    </html>
    """

    msg.attach(MIMEText(icerik, 'html'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(gonderici_email, gonderici_sifre)
        server.sendmail(gonderici_email, alici_email, msg.as_string())
        server.quit()
        print("✅ Mail başarıyla gönderildi!")
    except Exception as e:
        print(f"❌ Mail gönderim hatası: {e}")

# İnsan benzeri davranış için rastgele bekleme fonksiyonu
def human_like_wait(min_time=0.5, max_time=2):
    time.sleep(random.uniform(min_time, max_time))

# Fare hareketlerini simüle etme fonksiyonu
def simulate_mouse_movement(driver, element):
    actions = ActionChains(driver)
    actions.move_to_element(element).perform()
    human_like_wait(0.2, 0.8)  # Hareket sonrası bekleme süresi kısaltıldı


# CSV'den otel listesini oku
def read_hotel_list(file_path):
    with open(file_path, newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        return [row[0] for row in reader]  # Otel adlarını liste olarak döndür

# Sonuçları CSV'ye yaz
def write_results_to_csv(results, output_file):
    with open(output_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Hotel Adı", "Tarih", "Fiyat"])  # Başlıklar
        writer.writerows(results)

# Trip.com üzerinde bir otelin tarih ve fiyat bilgilerini al
def scrape_hotel_data(driver, hotel_name):
    results = []
    try:
        # Trip.com ana sayfasına git
        driver.get("https://us.trip.com/?locale=en-US&curr=EUR")
        print(f"Trip.com ana sayfasına gidildi ({hotel_name}).")
        human_like_wait()

        # Otel arama
        search_box = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "destinationInput"))
        )
        simulate_mouse_movement(driver, search_box)
        search_box.click()

        # Klavye simülasyonu ile otel ismini yaz
        for char in hotel_name:
            search_box.send_keys(char)
            time.sleep(random.uniform(0.1, 0.3))  # Her harf için bekleme
        print(f"Otel araması yapıldı: {hotel_name}")
        human_like_wait()

        # Önerilen oteli seç
        suggested_hotel = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".xNA4LozTCRNX8kIscFcs"))
        )
        simulate_mouse_movement(driver, suggested_hotel)
        suggested_hotel.click()
        print(f"Önerilen otel seçildi: {hotel_name}")
        human_like_wait()

        # "Search" butonuna tıkla
        search_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".tripui-online-btn-large"))
        )
        simulate_mouse_movement(driver, search_button)
        search_button.click()
        print("Arama yapıldı.")
        human_like_wait()

        # Otel detay bağlantısını bul ve tıkla
        # Otel detay bağlantısını bul ve tıkla
        hotel_link = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/div[3]/section/article/div/section/ul/li[2]/div/div/div/div/div[2]/div[1]/div[1]/div[1]/div/a"))
        )

        simulate_mouse_movement(driver, hotel_link)
        hotel_link.click()
        print(f"Otel detay sayfasına gidildi: {hotel_name}")
        human_like_wait()

        # Yeni sekmeye geçiş yap
        WebDriverWait(driver, 20).until(lambda d: len(d.window_handles) > 1)
        driver.switch_to.window(driver.window_handles[-1])
        print(f"Yeni sekmeye geçildi: {hotel_name}")
        human_like_wait()

        # Gerçek otel adını detay sayfasından çekiyoruz
        otel_adi_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1.headInit_headInit-title_nameA__EE_LB"))
        )
        gercek_otel_adi = otel_adi_element.text.strip()
        print(f"✅ Gerçek otel adı bulundu: {gercek_otel_adi}")
        human_like_wait()

        # Takvimi aç
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "checkInInput"))
        ).click()
        print("Otel detaylarında takvim açıldı.")
        time.sleep(2)

        # Bugünün tam tarihini alıyoruz
        bugun = datetime.today()

        # Takvimdeki tüm günleri çekiyoruz
        days = driver.find_elements(By.CSS_SELECTOR, "ul > li.has-price > div")

        # İlk gün ay ve yıl bilgileri
        current_month = bugun.month
        current_year = bugun.year
        previous_day = 0

        for day in days:
            try:
                date_text = day.find_element(By.CSS_SELECTOR, "span.day").text.strip()

                if not date_text.isdigit():
                    continue

                day_num = int(date_text)

                # Ay geçişini anlamak için: gün sayısı düşerse ay artır
                if previous_day != 0 and day_num < previous_day:
                    current_month += 1
                    if current_month > 12:
                        current_month = 1
                        current_year += 1

                previous_day = day_num

                full_date = datetime(current_year, current_month, day_num)

                # Geçmiş tarihleri atla
                if full_date < bugun:
                    print(f"{full_date.strftime('%d-%m-%Y')} bugünden önce, atlanıyor.")
                    continue

                price_element = day.find_element(By.CSS_SELECTOR, "span.price")
                price = price_element.text.strip() if price_element else ""

                if price == "":
                    price = "DOLU"

                results.append([gercek_otel_adi, full_date.strftime('%d-%m-%Y'), price])
                print(f"Tarih: {full_date.strftime('%d-%m-%Y')}, Fiyat: {price}")

            except Exception as e:
                print("Bilgi alınamadı:", e)

    except Exception as e:
        print(f"Hata oluştu ({hotel_name}): {e}")

    finally:
        # Detay sekmesini kapat
        if len(driver.window_handles) > 1:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])

    return results
# Git push fonksiyonu eklendi!
def git_push():
    try:
        print("🔄 Git işlemi başlıyor...")

        env = os.environ.copy()

        # 0 - Genel durum
        print("🔍 [Durum] Çalışılan dizin:", os.getcwd())
        subprocess.run(['git', 'status'], check=False, env=env)
        subprocess.run(['git', 'log', '-1', '--oneline'], check=False, env=env)

        # 1 - Değişiklikleri ekle
        print("🔧 Adım 1: git add .")
        subprocess.run(['git', 'add', '.'], check=True, env=env)
        print("✅ Değişiklikler eklendi.")

        # 2 - Commit oluştur
        commit_message = "Otomatik veri güncellemesi ve rapor push"
        print(f"🔧 Adım 2: git commit -m \"{commit_message}\"")
        subprocess.run(['git', 'commit', '-m', commit_message], check=True, env=env)
        print("✅ Commit işlemi tamamlandı.")

        # 3 - (Opsiyonel Rebase - kaldırdık!)
        # print("🔧 Adım 3: git pull --rebase origin main")
        # subprocess.run(['git', 'pull', '--rebase', 'origin', 'main'], check=True, env=env)
        # print("✅ Rebase tamamlandı.")

        # 4 - Push işlemi
        print("🔧 Adım 4: git push origin main")
        subprocess.run(['git', 'push', 'origin', 'main'], check=True, env=env)
        print("🚀 Push işlemi başarılı!")

    except subprocess.CalledProcessError as e:
        print(f"❌ Git işlemi sırasında hata oluştu!\n⛔️ Komut: {e.cmd}\n⚠️ Hata Kodu: {e.returncode}")

# En fazla X dosya tut, eski dosyaları sil
def temizle_max_kayit(limit=10):
    dosyalar = sorted(glob.glob("sonuc_*.csv"))
    if len(dosyalar) > limit:
        silinecekler = dosyalar[:len(dosyalar) - limit]
        for dosya in silinecekler:
            os.remove(dosya)
            print(f"{dosya} silindi (limit aşıldı).")
            
# Ana işlem
def main(hotel_list_file):
        # Bot başladığında bildirim gönder
    #mail_gonder(
    #    "🚀 Stop Sale Botu Çalıştı!",
    #    "Stop Sale Botu az önce çalıştı, 5 dakika sonra Streamlit Dashboard kontrol edebilirsiniz.\n\nUygulama Linki: https://otelrapor-hifourstravel.streamlit.app"
    #)

    now = datetime.now().strftime('%Y-%m-%d_%H-%M')
    output_file = f"sonuc_{now}.csv"
    
    #options = uc.ChromeOptions()
    #options.add_argument("--start-maximized")
    #options.add_argument("--window-size=1920,1080")
    # Headless istersen aç/kapat ➔ şimdilik kapatalım çünkü test ediyoruz!
    #options.add_argument("--headless=new")
    #driver = uc.Chrome(options=options)
    # ChromeOptions ile özelleştirme (isteğe bağlı)
  

    options = uc.ChromeOptions()
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-software-rasterizer')
    options.add_argument('--disable-plugins')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")

    options.binary_location = "/Applications/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
    service = Service('/usr/local/bin/chromedriver/chromedriver')

    # GUI açık çalıştırıyoruz → headless=False
    driver = uc.Chrome(service=service, options=options, headless=False)

    # (İsteğe bağlı) Stealth destek olsun diye bir de user-agent dışında şu tanımı da yapabilirsin:
    driver.execute_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)



    # Başlangıçta Google aç ➔ ısındırma
    print("🌐 Tarayıcı ısınıyor...")
    driver.get("https://www.google.com")
    time.sleep(5)


    #burdan başlar Chrome Profilini Kullanarak Tarayıcı Başlatma
    #options = webdriver.ChromeOptions()

    # Kullanıcı profili ➔ Bunu bırakabilirsin ama bazen headless ile çakışır, test et!
    #options.add_argument("--user-data-dir=/Users/halilbarisduman/Library/Application Support/Google/Chrome/User Data")
    #options.add_argument("--profile-directory=Default")

    # Başlangıç ayarları
    #options.add_argument("--start-maximized")
    #options.add_argument("--window-size=1920,1080")

    # Headless mod
    #options.add_argument("--headless")  # "new" yerine klasik kullanıyoruz
    # options.add_argument("--headless=chrome")  # Alternatif test edilebilir

    # Stealth ayarlar
    #options.add_argument("--disable-blink-features=AutomationControlled")
    #options.add_argument("--disable-infobars")
    #options.add_argument("--disable-gpu")
    #options.add_argument("--no-sandbox")
    #options.add_argument("--disable-dev-shm-usage")
    #options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    #options.add_experimental_option("useAutomationExtension", False)


    #driver = webdriver.Chrome(options=options)

    # `navigator.webdriver` özelliğini gizle
    #driver.execute_script("""
        #Object.defineProperty(navigator, 'webdriver', {
            #get: () => undefined
        #})
    #""") burda biter denemeler

    try:
        hotel_list = read_hotel_list(hotel_list_file)
        all_results = []

        for hotel_name in hotel_list:
            print(f"{hotel_name} için veri çekiliyor...")
            hotel_results = scrape_hotel_data(driver, hotel_name)
            all_results.extend(hotel_results)

        write_results_to_csv(all_results, output_file)
        print(f"Tüm sonuçlar {output_file} dosyasına kaydedildi.")

    except Exception as e:
        print(f"Genel bir hata oluştu: {e}")

    finally:
        driver.quit()
        print("Tarayıcı kapatıldı.")
        # Maksimum kayıt kontrolü, eski dosyaları siler
        temizle_max_kayit(limit=10)

# Dosya yolları
hotel_list_file = "otel_listesi.csv"  # Otel isimlerinin olduğu CSV dosyası


# Ana işlemi başlat + otomatik push ekle!
if __name__ == "__main__":
    main(hotel_list_file)
    git_push()