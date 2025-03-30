import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import csv
import os
import time
import pandas as pd

username = 'HiFoursTravel'
password = 'HiFoursTravel24*'
session = requests.Session()

def login():
    token_response = session.get("https://www.bedsopia.com/")
    soup = BeautifulSoup(token_response.text, 'html.parser')
    token = soup.find('input', {'name': 'csrf_token'})['value']

    data = {
        'action': 'login',
        'user': username,
        'password': password,
        'login-box-terms-and-conditions': 'true',
        'csrf_token': token
    }

    login_response = session.post('https://www.bedsopia.com/users/handlers/login.ashx', data=data)

def searchHotel(jpCode, startDate, endDate):
    params = {
        'accion': 'searchhotels',
        'null': 'null',
        'secondarySearch': 'true',
        'prov_secondary': 'EXP',
        'rates_secondary': 'packagesOnly',
        'hotelID': jpCode,
        'startDate': startDate,
        'endDate': endDate,
        'nationality': 'TN',
        'paxs': '20',
        'hashParams': '',
        '_': '1743190492928',
    }

    search_response = session.get('https://www.bedsopia.com/handlers/searcher.ashx', params=params)

    try:
        sessionID = json.loads(search_response.text)['searchSessionID']
        print(f"Search Session ID: {sessionID}")
    except KeyError:
        print("⛔ Search session ID bulunamadı.")
        return None

    params = {
        'idioma': 'tr',
        '_': '',
        'searchSessionID': sessionID,
        'page': '1',
        'order': 'etiqueta',
        'presearch': 'false',
    }

    response = session.get('https://www.bedsopia.com/hotels/ashx/results.ashx', params=params)

    with open('raw_response.json', 'w', encoding='utf-8') as f:
        f.write(response.text)

    try:
        result_list = json.loads(response.text).get("results", [])
        if not result_list:
            print("⚠️ results listesi boş döndü.")
            return None
        return result_list[0]
    except Exception as e:
        print(f"⛔ JSON parse hatası: {e}")
        return None

def parse_and_append_to_csv(data, startDate, endDate):
    output_file = 'bedsopia_prices.csv'
    checkin_date = datetime.strptime(startDate, '%Y-%m-%d')
    checkout_date = datetime.strptime(endDate, '%Y-%m-%d')
    write_header = not os.path.exists(output_file)
    header = ["Tarih", "Otel Adı", "Oda Tipi", "Board Type", "İptal Poliçesi", "Fiyat", "Para Birimi", "Müsaitlik", "Milliyet"]
    lowest_prices = {}

    hotel_name = data.get("hotel", {}).get("name", "N/A")
    options = data.get('availability', {}).get('options', [])
    if not options:
        print(f"⚠️ {hotel_name} için uygun seçenek bulunamadı.")
        return

    for option in options:
        room_name = option.get('roomList', [{}])[0].get('name', 'N/A')
        board_type = option.get("boardTypeName", "N/A")

        non_refundable = option.get("nonRefundable", None)
        cancellation_policy_raw = option.get("cancellationPolicy", {})
        cancellation_policy = "Non-refundable"

        if non_refundable is False:
            cancellation_policy = "Refundable"
        elif non_refundable is True:
            cancellation_policy = "Non-refundable"
        else:
            deadline_date_str = cancellation_policy_raw.get("deadlineDate", "")
            if deadline_date_str and not deadline_date_str.startswith("0001"):
                try:
                    deadline_date = datetime.strptime(deadline_date_str, '%Y-%m-%dT%H:%M:%S')
                    if deadline_date >= datetime.now():
                        cancellation_policy = "Refundable"
                except:
                    pass

        currency = option.get("priceDetail", {}).get("currency", "EUR")
        availability = option.get("breakdownByRoom", [])

        for room in availability:
            weeks = room.get("breakdown", {}).get("weeks", [])

            start = datetime.strptime(data.get('availability', {}).get('startDate', '').split('T')[0], '%Y-%m-%d')
            shift_days = (start.weekday() + 1) % 7
            week_start_date = start - timedelta(days=shift_days)

            for week_index, week in enumerate(weeks):
                for day_index, day in enumerate(week):
                    if not day:
                        continue

                    current_date = week_start_date + timedelta(days=(week_index * 7) + day_index)
                    if not (checkin_date <= current_date < checkout_date):
                        continue

                    price = day.get("price", 0)
                    availability_status = "Stop Sale" if day.get("onRequest", False) else "Available"

                    key = (
                        current_date.strftime('%Y-%m-%d'),
                        hotel_name,
                        board_type.lower().strip(),
                        cancellation_policy
                    )

                    if key not in lowest_prices or price < lowest_prices[key]["Fiyat"]:
                        lowest_prices[key] = {
                            "Tarih": key[0],
                            "Otel Adı": key[1],
                            "Oda Tipi": room_name,
                            "Board Type": board_type,
                            "İptal Poliçesi": cancellation_policy,
                            "Fiyat": price,
                            "Para Birimi": currency,
                            "Müsaitlik": availability_status,
                            "Milliyet": "TN"
                        }

    with open(output_file, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=header)
        if write_header:
            writer.writeheader()
        for row in lowest_prices.values():
            writer.writerow(row)

    print(f"✅ {hotel_name} için en düşük fiyatlı kombinasyonlar CSV'ye yazıldı.")

def generate_date_blocks(days_after_today=3, total_days=30, block_length=7):
    today = datetime.today().date()
    start_date = today + timedelta(days=days_after_today)
    blocks = []
    while total_days > 0:
        block_days = min(block_length, total_days)
        end_date = start_date + timedelta(days=block_days)
        blocks.append((start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
        start_date = end_date
        total_days -= block_days
    return blocks

# 🔁 Ana Akış
with open('bedsopia_prices.csv', mode='w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=["Tarih", "Otel Adı", "Oda Tipi", "Board Type", "İptal Poliçesi", "Fiyat", "Para Birimi", "Müsaitlik", "Milliyet"])
    writer.writeheader()
login()
df = pd.read_csv('hotel_list.csv')
hotel_uids = df['hotel_uid'].astype(str).tolist()

date_blocks = generate_date_blocks()

for hotel_uid in hotel_uids:
    print(f"\n🏨 Otel işleniyor: {hotel_uid}")
    for start_date, end_date in date_blocks:
        print(f"🔍 Tarih aralığı: {start_date} - {end_date}")
        response = searchHotel(hotel_uid, start_date, end_date)
        if response:
            parse_and_append_to_csv(response, start_date, end_date)
        else:
            print("❌ Sonuç alınamadı, atlanıyor.")
        time.sleep(1.5)  # sistem yavaşlamasın diye bekleme süresi
