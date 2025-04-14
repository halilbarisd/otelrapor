from selenium.webdriver.chrome.service import Service
import requests
import time
import csv
from datetime import datetime, timedelta
import pandas as pd
import os
import glob  # Eksik import eklendi

# 📌 Otel listesini oku
df = pd.read_csv('/Users/halilbarisduman/Desktop/otelrapor/otel_listesi.csv')

# 📅 Tarih ayarları
checkin_date = datetime.today()
checkout_date = checkin_date + timedelta(days=1)
checkin_str = checkin_date.strftime("%Y%m%d")
checkout_str = checkout_date.strftime("%Y%m%d")

# 📌 Fiyat verisi çekme
def get_prices():
    headers = {
        "accept": "application/json",
        "accept-language": "tr-TR,tr;q=0.9",
        "content-type": "application/json",
        "origin": "https://www.trip.com",
        "referer": "https://www.trip.com/hotels/detail/",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    }

    # 📁 Dosya adını oluştur
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"sonuc_{timestamp}.csv"

    with open(filename, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Hotel Adı", "Tarih", "Fiyat"])  # ✅ otel_id kaldırıldı

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
                    "bu": "IBU",
                    "group": "trip",
                    "aid": "",
                    "sid": "",
                    "ouid": "",
                    "locale": "en-XX",
                    "timezone": "3",
                    "currency": "EUR",
                    "pageId": "10320668147",
                    "guid": "",
                    "isSSR": False
                }
            }

            try:
                res = requests.post(
                    "https://www.trip.com/restapi/soa2/28820/ctGetHotelPriceCalendar",
                    headers=headers,
                    json=payload,
                    timeout=10
                )
                if res.status_code == 200:
                    data = res.json()
                    calendar = data.get("data", {}).get("priceCalendarInfos", [])
                    for day in calendar:
                        # Tarihi gün-ay-yıl formatına çevir
                        date_obj = datetime.strptime(day["date"], "%Y-%m-%d")
                        formatted_date = date_obj.strftime("%d-%m-%Y")  # Gün-Ay-Yıl formatı
                        writer.writerow([otel_adi, formatted_date, day["minPrice"]])
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

    # Eski dosyaları temizle (son 10 dosyayı tut)
    temizle_max_kayit(limit=10)

# Eski dosyaları temizleme fonksiyonu
def temizle_max_kayit(limit=10):
    dosyalar = sorted(glob.glob("sonuc_*.csv"))
    if len(dosyalar) > limit:
        silinecekler = dosyalar[:len(dosyalar) - limit]
        for dosya in silinecekler:
            os.remove(dosya)
            print(f"{dosya} silindi (limit aşıldı).")

# 🔁 Ana akış
if __name__ == "__main__":
    first_hotel_id = int(df.iloc[0]["Otel_ID"])
    first_city_id = int(df.iloc[0]["City_ID"])

    get_prices()
