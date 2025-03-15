import pandas as pd
import streamlit as st

st.title("Otel Stop Sale ve Fırsat Günleri Dashboard")

# CSV verisini oku
try:
    df = pd.read_csv('sonuc.csv')

    # Tarih formatını düzelt!
    df['Tarih'] = pd.to_datetime(df['Tarih'], format='%d-%m-%Y')

    # Doluluk ve fiyat verilerini ayır
    doluluk_df = df[df['Fiyat'].astype(str).str.strip().str.upper() == 'DOLU']
    df_numeric = df[df['Fiyat'].astype(str).str.strip().str.upper() != 'DOLU'].copy()
    df_numeric['Fiyat'] = df_numeric['Fiyat'].replace('[€]', '', regex=True).astype(float)

    # Otel seçimi
    otel_secimi = st.selectbox("Otel Seç:", df['Hotel Adı'].unique())

    # Seçilen otelin verisini filtrele
    otel_df = df_numeric[df_numeric['Hotel Adı'] == otel_secimi].copy()
    otel_df['YilAy'] = otel_df['Tarih'].dt.to_period('M')
    ay_ortalamalari = otel_df.groupby('YilAy')['Fiyat'].mean()

    # Stop sale ve fırsat günleri hesaplama
    stop_sale_tarihler = set(doluluk_df[doluluk_df['Hotel Adı'] == otel_secimi]['Tarih'].tolist())
    firsat_tarihler = set()

    for idx, row in otel_df.iterrows():
        yilay = row['YilAy']
        fiyat = row['Fiyat']
        ortalama = ay_ortalamalari[yilay]

        if fiyat >= ortalama * 1.30:
            stop_sale_tarihler.add(row['Tarih'])

        if fiyat <= ortalama * 0.85:
            firsat_tarihler.add(row['Tarih'])

    # Dashboard çıktıları
    st.header(f"{otel_secimi} - Stop Sale Günleri")
    if stop_sale_tarihler:
        st.write(sorted([t.strftime('%d-%m-%Y') for t in stop_sale_tarihler]))
    else:
        st.write("Stop Sale günü yok.")

    st.header(f"{otel_secimi} - Fırsat Günleri")
    if firsat_tarihler:
        st.write(sorted([t.strftime('%d-%m-%Y') for t in firsat_tarihler]))
    else:
        st.write("Fırsat günü yok.")

    # Tüm fiyatları tablo halinde göster
    st.header(f"{otel_secimi} - Tüm Fiyat Verisi")
    st.dataframe(otel_df[['Tarih', 'Fiyat']].sort_values(by='Tarih'))

except Exception as e:
    st.error(f"Hata oluştu: {e}")
