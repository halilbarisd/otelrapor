import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import csv

username = 'HiFoursTravel'
password = 'HiFoursTravel24*'
session = requests.Session()

def login():
    token_response = session.get("https://www.bedsopia.com/")  
    soup = BeautifulSoup(token_response.text, 'html.parser')
    token = soup.find('input', {'name': 'csrf_token'})['value']

    token_response = session.get("https://www.bedsopia.com/")  

    data = {
        'action': 'login',
        'user': username,
        'password': password,
        'login-box-terms-and-conditions': 'true',
        'csrf_token': token
    }

    login_response = session.post('https://www.bedsopia.com/users/handlers/login.ashx', data=data)

def searchHotel(jpCode,startDate,endDate):
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
        print("Search session ID bulunamadı.")

    params = {
        'idioma': 'tr',
        '_': '',
        'searchSessionID': sessionID,
        'page': '1',
        'order': 'etiqueta',
        'presearch': 'false',
    }

    response = session.get('https://www.bedsopia.com/hotels/ashx/results.ashx', params=params)

    with open('Untitled-1.json', 'w') as file:
        data = file.write(response.text)
    return (json.loads(response.text))["results"][0]


def addDataToCsv(data,startDate):
    header = ["Tarih", "Otel Adı", "Oda Tipi", "Board Type", "İptal Poliçesi", "DeadlineDate", "Fiyat", "Para Birimi", "hotelCode"]
    with open('hotel_datatest.csv', mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=header)
        writer.writeheader()  # Başlıkları yaz
        hotelName = data["hotel"]["name"]
        for room in data["availability"]["options"]:
            room = data.get('availability', {}).get('options', [])
            for index in room:
                priceDate = startDate
                roomType = index["roomList"][0]["name"],
                boardType= index["boardTypeName"],
                print(roomType)
                deadlineDate = index["cancellationPolicy"]["deadlineDate"],
                currency =  index["priceDetail"]["currency"],
                hotelCode = index["hotelCode"]
                for dailyPrice in index["breakdownByRoom"][0]["breakdown"]["weeks"]:
                    for priceIndex in dailyPrice:
                        if priceIndex is not None:
                            row = {
                                'Otel Adı': hotelName,
                                'Tarih' : priceDate,
                                'Oda Tipi': roomType,
                                'Board Type': boardType,
                                'Fiyat' : priceIndex["price"],
                                'DeadlineDate': deadlineDate,
                                'Para Birimi': currency,
                                'hotelCode': hotelCode
                                }
                            writer.writerow(row)
                            priceDate = datetime.strptime(priceDate, '%Y-%m-%d')
                            priceDate = priceDate + timedelta(days=1)
                            priceDate = priceDate.strftime('%Y-%m-%d')
                    
login()
response=searchHotel('JP757855','2025-04-04','2025-04-08')
addDataToCsv(response,'2025-03-30')

