import requests
import pandas as pd
import os
import json
import urllib.parse
from datetime import datetime, timedelta

# 📌 Sabit Dosya Adları
hotel_csv = 'hotel_list.csv'
output_file = 'bedsopia_prices.csv'
cookie_file = 'cookies.txt'
session_file = 'session_id.txt'

# ✅ RAW JSON KAYIT FONKSİYONU
def save_raw_response(hotel_name, hotel_uid, response_data):
    folder = "raw_responses"
    if not os.path.exists(folder):
        os.makedirs(folder)

    filename = f"{folder}/{hotel_name.replace(' ', '_')}_{hotel_uid}.json"

    with open(filename, "w", encoding='utf-8') as f:
        json.dump(response_data, f, ensure_ascii=False, indent=4)

    print(f"📁 RAW veri kaydedildi: {filename}")

# 🔐 Cookie Yükle
with open(cookie_file, "r") as f:
    cookie_string = f.read().strip()

# 📝 CSV'den Otelleri Yükle
df_hotels = pd.read_csv(hotel_csv)
hotel_uid_list = df_hotels['hotel_uid'].astype(str).tolist()

# 🔎 Session ID
with open(session_file, "r") as f:
    searchSessionID = f.read().strip()

# 📅 Tarihleri search_dates.txt dosyasından al
with open('search_dates.txt', 'r') as f:
    dates = f.readlines()
    checkin_date_str = dates[0].strip()
    checkout_date_str = dates[1].strip()

checkin_date = datetime.strptime(checkin_date_str, '%Y-%m-%d')
checkout_date = datetime.strptime(checkout_date_str, '%Y-%m-%d')

print(f"🔎 Check-in: {checkin_date.strftime('%Y-%m-%d')} | Check-out: {checkout_date.strftime('%Y-%m-%d')}")
print(f"🌍 Nationality (Kod): IE\n")

# 🌐 Header Ayarları
headers = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest",
    "cookie": cookie_string
}

# 🔄 Sonuçları Topla
result_list = []

for hotel_uid in hotel_uid_list:
    hotel_name = df_hotels[df_hotels['hotel_uid'] == hotel_uid]['hotel_name'].values[0]
    uid_param = urllib.parse.quote(f"GHU@{hotel_uid}")

    # ✅ DÜZGÜN PARAMETRELERLE URL (Sadece searchSessionID ve UID gönderiyoruz)
    url = (
        f"https://www.bedsopia.com/hotels/ashx/availability.ashx"
        f"?_="
        f"&searchSessionID={searchSessionID}"
        f"&UID={uid_param}"
        f"&presearch="
    )

    print(f"\n🔎 Sorgulanıyor: {hotel_name} ({hotel_uid})")
    print(f"➡️ URL: {url}")

    # ✅ API Request
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"❌ {hotel_name} için hata! Status Code: {response.status_code}")
        continue

    data = response.json()

    # ✅ RAW JSON'u Kaydet!
    save_raw_response(hotel_name, hotel_uid, data)

    # ✅ startDate kontrolü
    api_start_date_str = data.get('availability', {}).get('startDate', '').split('T')[0]

    if not api_start_date_str:
        print(f"⚠️ {hotel_name} için startDate bulunamadı!")
        continue

    try:
        api_start_date = datetime.strptime(api_start_date_str, '%Y-%m-%d')
    except ValueError as e:
        print(f"⚠️ {hotel_name} için tarih format hatası: {e}")
        continue

    options = data.get('availability', {}).get('options', [])
    if not options:
        print(f"⚠️ {hotel_name} için seçenek bulunamadı!")
        continue

    seen_combinations = set()  # Tekrar edilen fiyat kombinasyonlarını kontrol etmek için set

    for option in options:
        breakdown_rooms = option.get('breakdownByRoom', [])

        for room in breakdown_rooms:
            room_name = room.get('name', 'N/A')

            # Dinamik boardType kontrolü: Eğer 'Room' ile başlıyorsa 'Room Only', diğerlerini 'Bed & Breakfast'
            board_type = 'Room Only' if 'room' in option.get('boardTypeName', '').lower() else 'Bed & Breakfast'
            
                        # İptal Poliçesi Kontrolü
            non_refundable = option.get('nonRefundable', None)
            cancellation_policy_raw = option.get('cancellationPolicy', {})

            # Öncelikli kontrol: nonRefundable alanı
            if non_refundable is not None:
                if non_refundable:
                    cancellation_policy = 'Non-refundable'
                else:
                    cancellation_policy = 'Refundable'

            # Eğer nonRefundable bilgisi eksikse, cancellationPolicy'den kontrol ederiz
            else:
                deadline_date_str = cancellation_policy_raw.get('deadlineDate')
                
                # deadlineDate boş mu, veya default tarih mi?
                if not deadline_date_str or deadline_date_str == "0001-01-01T00:00:00":
                    cancellation_policy = 'Non-refundable'
                else:
                    try:
                        deadline_date = datetime.strptime(deadline_date_str, '%Y-%m-%dT%H:%M:%S')
                        now = datetime.now()
                        
                        if deadline_date >= now:
                            cancellation_policy = 'Refundable'
                        else:
                            cancellation_policy = 'Non-refundable'
                    
                    except ValueError:
                        print(f"⚠️ Hatalı tarih formatı: {deadline_date_str}")
                        cancellation_policy = 'Non-refundable'  # Hata varsa güvenli varsayılan

            # Sonucu yazdıralım
            print(f"Cancellation Policy: {cancellation_policy}")
            
            weeks = room.get('breakdown', {}).get('weeks', [])

            # Haftanın Başlangıç Tarihi Hesaplanıyor (PAZARTESİ)
            week_start_date = api_start_date - timedelta(days=api_start_date.weekday())

            for week_index, week in enumerate(weeks):
                if not week:
                    continue

                for day_index, day in enumerate(week):
                    if not day:
                        continue

                    # Doğru Tarih Hesaplaması
                    current_date = week_start_date + timedelta(days=(week_index * 7) + day_index)

                    if not (checkin_date <= current_date < checkout_date):
                        continue

                    # Kombinasyonları Kontrol Et ve Fiyatı Yaz
                    combination = (board_type, cancellation_policy, current_date)

                    # Eğer bu kombinasyon daha önce işlendi ise, aynı fiyatı tekrar yazmıyoruz
                    if combination in seen_combinations:
                        continue
                    seen_combinations.add(combination)

                    result_list.append({
                        'Tarih': current_date.strftime('%Y-%m-%d'),
                        'Otel Adı': hotel_name,
                        'Oda Tipi': room_name,
                        'Board Type': board_type,
                        'İptal Poliçesi': cancellation_policy,
                        'Fiyat': day.get('price', 0),
                        'Para Birimi': option.get('currency', 'EUR'),
                        'Müsaitlik': 'Stop Sale' if day.get('onRequest', False) else 'Available',
                        'Milliyet': 'IE'
                    })

        print(f"✅ {hotel_name} için veri işlendi!")

# 💾 CSV Kaydet
df_result = pd.DataFrame(result_list)

# Eğer dosya mevcutsa, yeni veriyi dosyanın sonuna ekleyelim
if os.path.exists(output_file):
    df_existing = pd.read_csv(output_file)
    df_result = pd.concat([df_existing, df_result])

# 💾 CSV Kaydet
df_result.to_csv(output_file, index=False)

print(f"\n✅ {len(result_list)} kayıt {output_file} dosyasına yazıldı.")
print("🎉 İşlem tamamlandı!")
