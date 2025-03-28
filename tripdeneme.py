from seleniumwire.undetected_chromedriver.v2 import Chrome, ChromeOptions
from selenium.webdriver.chrome.service import Service
import requests
import time
import csv
from datetime import datetime, timedelta
import pandas as pd
import os

# 📌 Otel listesini oku
df = pd.read_csv("otel_listesi.csv")

# 📅 Tarih ayarları
checkin_date = datetime.today()
checkout_date = checkin_date + timedelta(days=1)
checkin_str = checkin_date.strftime("%Y%m%d")
checkout_str = checkout_date.strftime("%Y%m%d")

# 📌 Token + Cookie çek
def get_token_and_cookie_from_request(hotel_id, city_id):
    options = ChromeOptions()
    options.binary_location = "/Applications/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--allow-insecure-localhost')
    options.add_argument('--allow-running-insecure-content')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    # options.add_argument('--headless=new')  # Görünmez çalıştırmak istersen aç

    service = Service('/usr/local/bin/chromedriver/chromedriver')
    driver = Chrome(service=service, options=options)
    driver.set_window_size(1200, 800)

    try:
        print("🌐 Otel detay sayfası açılıyor ve request'ler izleniyor...")
        url = f"https://www.trip.com/hotels/detail/?cityId={city_id}&hotelId={hotel_id}&checkIn={checkin_str}&checkOut={checkout_str}&adult=2&children=0"
        driver.get(url)
        print("⏳ Sayfa yükleniyor... 15 saniye bekleniyor.")
        time.sleep(15)

        token = None
        for request in driver.requests:
            if request.method == "POST" and "ctGetHotelPriceCalendar" in request.url:
                token = request.headers.get("phantom-token")
                if token:
                    print("✅ Token başarıyla yakalandı.")
                    break

        cookies = {cookie['name']: cookie['value'] for cookie in driver.get_cookies()}
        return token, cookies

    finally:
        driver.quit()

# 📌 Fiyat verisi çekme
def get_prices(token, cookies_dict):
    headers = {
        "accept": "application/json",
        "accept-language": "tr-TR,tr;q=0.9",
        "content-type": "application/json",
        "origin": "https://www.trip.com",
        "referer": "https://www.trip.com/hotels/detail/",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        "phantom-token": token
    }

    # 📁 Dosya adını oluştur
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"sonuc_{timestamp}.csv"

    with open(filename, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["otel_adi", "tarih", "fiyat"])  # ✅ otel_id kaldırıldı

        for _, row in df.iterrows():
            otel_id = int(row["Otel_ID"])
            otel_adi = row["Otel_Adi"]
            city_id = int(row["City_ID"])

            payload = {
                "search": {
                    "checkIn": checkin_str,
                    "checkOut": checkout_str,
                    "filters": [
                        {"filterId": "17|1", "type": "17", "value": "1"},
                        {"filterId": "29|1", "value": "1|2", "type": "29"},
                        {"filterId": "80|0|1", "value": "0", "type": "80"}
                    ],
                    "pageCode": 10320668147,
                    "hotelIds": [{"id": otel_id}],
                    "roomQuantity": 1,
                    "location": {
                        "geo": {
                            "cityID": city_id,
                            "oversea": True
                        }
                    }
                },
                "meta": {
                    "fgt": -1,
                    "roomkey": "",
                    "minCurr": "",
                    "minPrice": ""
                },
                "extension": {
                    "calendarMode": "1"
                },
                "head": {
                    "platform": "PC",
                    "cver": "0",
                    "cid": cookies_dict.get("UBT_VID", ""),
                    "bu": "IBU",
                    "group": "trip",
                    "aid": "",
                    "sid": "",
                    "ouid": "",
                    "locale": "en-XX",
                    "timezone": "3",
                    "currency": "EUR",
                    "pageId": "10320668147",
                    "vid": cookies_dict.get("UBT_VID", ""),
                    "guid": "",
                    "isSSR": False
                }
            }

            try:
                res = requests.post(
                    "https://www.trip.com/restapi/soa2/28820/ctGetHotelPriceCalendar",
                    headers=headers,
                    json=payload,
                    cookies=cookies_dict,
                    timeout=10
                )
                if res.status_code == 200:
                    data = res.json()
                    calendar = data.get("data", {}).get("priceCalendarInfos", [])
                    for day in calendar:
                        writer.writerow([otel_adi, day["date"], day["minPrice"]])
                    print(f"✅ {otel_adi} işlendi.")
                else:
                    print(f"❌ {otel_adi} - Hata kodu: {res.status_code}")
            except Exception as e:
                print(f"💥 {otel_adi} - HATA: {e}")
            time.sleep(1)

    print(f"\n📁 Sonuç dosyası oluşturuldu: {filename}")

    # ✅ Git push işlemi
    print("🚀 Git'e push ediliyor...")
    os.system(f"git add {filename}")
    os.system(f'git commit -m "Trip fiyat güncellemesi: {timestamp}"')
    os.system("git push")
    print("✅ Push tamamlandı.")

# 🔁 Ana akış
if __name__ == "__main__":
    first_hotel_id = int(df.iloc[0]["Otel_ID"])
    first_city_id = int(df.iloc[0]["City_ID"])
    token, cookies = get_token_and_cookie_from_request(first_hotel_id, first_city_id)

    if token and cookies:
        get_prices(token, cookies)
    else:
        print("❗ Token veya cookie alınamadığı için işlem durduruldu.")
