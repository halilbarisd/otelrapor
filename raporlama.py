import pandas as pd
import os

# ------------------------------
# 1. Veriyi Yükleme ve Hazırlık
# ------------------------------

df = pd.read_csv('sonuc.csv')
df['Tarih'] = pd.to_datetime(df['Tarih'], format='%d-%m-%Y')

# Doluluk verisi: "DOLU" olan günler
doluluk_df = df[df['Fiyat'].astype(str).str.strip().str.upper() == 'DOLU']

# Fiyat verilerini al, "DOLU" olanları hariç tut
df_numeric = df[df['Fiyat'].astype(str).str.strip().str.upper() != 'DOLU'].copy()
df_numeric['Fiyat'] = df_numeric['Fiyat'].replace('[€]', '', regex=True).astype(float)

# ------------------------------
# 2. Stop Sale + Fırsat Günleri Raporları
# ------------------------------

print("\n[Stop Sale ve Fırsat Günleri Raporu (Ortalama Bazlı)]\n")

for otel_adi in df['Hotel Adı'].unique():
    print(f"\nOtel: {otel_adi}")

    # Otelin DOLU olan günleri
    otel_dolu_df = doluluk_df[doluluk_df['Hotel Adı'] == otel_adi]
    otel_dolu_tarihler = set(otel_dolu_df['Tarih'].tolist())

    # Fiyat analizi için veriyi sırala
    otel_numeric_df = df_numeric[df_numeric['Hotel Adı'] == otel_adi].copy()

    # Ay bilgisini ekle
    otel_numeric_df['YilAy'] = otel_numeric_df['Tarih'].dt.to_period('M')

    # Her ay için ortalama fiyat hesapla
    ay_ortalamalari = otel_numeric_df.groupby('YilAy')['Fiyat'].mean()

    # Stop sale ve fırsat günleri
    stop_sale_tarihler = set(otel_dolu_tarihler)
    firsat_tarihler = set()

    # Günlük fiyat kontrolü
    for idx, row in otel_numeric_df.iterrows():
        yilay = row['YilAy']
        fiyat = row['Fiyat']
        ortalama = ay_ortalamalari[yilay]

        # Stop sale → fiyat ortalamanın %30 üstündeyse
        if fiyat >= ortalama * 1.40:
            stop_sale_tarihler.add(row['Tarih'])

        # Fırsat günü → fiyat ortalamanın %15 altındaysa
        if fiyat <= ortalama * 0.85:
            firsat_tarihler.add(row['Tarih'])

    # Stop sale yazdır
    if not stop_sale_tarihler:
        print("Stop sale günü bulunamadı.")
    else:
        print("Stop Sale Günleri:")
        for tarih in sorted(stop_sale_tarihler):
            print(f" - {tarih.strftime('%d-%m-%Y')}")

    # Fırsat günleri yazdır
    if not firsat_tarihler:
        print("Fırsat günü bulunamadı.")
    else:
        print("Fırsat Günleri:")
        for tarih in sorted(firsat_tarihler):
            print(f" - {tarih.strftime('%d-%m-%Y')}")
