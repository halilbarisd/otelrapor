import pandas as pd
import streamlit as st
import glob

# Sayfa yapılandırması
st.set_page_config(page_title="Otel Raporlama Dashboard", layout="wide")

# Başlık
st.title("📊 Otel Stop Sale ve Fırsat Günleri Dashboard")

try:
    # CSV dosyalarını bul
    csv_files = sorted(glob.glob("sonuc_*.csv"))

    if not csv_files:
        st.warning("Hiç CSV dosyası bulunamadı. Lütfen botu çalıştır ve tekrar dene.")
    else:
        # Tarih + saat listesini çıkar
        dates_available = [
            f.replace("sonuc_", "").replace(".csv", "").replace("_", " ") for f in csv_files
        ]

        # Kullanıcı tarih/saat seçiyor
        selected_datetime = st.selectbox("📅 Hangi tarih/saat verisini görmek istersin?", dates_available)

        # Seçilen dosya yolu
        selected_file = f"sonuc_{selected_datetime.replace(' ', '_')}.csv"

        # Veriyi oku
        df = pd.read_csv(selected_file)

        # Tarih formatı
        df['Tarih'] = pd.to_datetime(df['Tarih'], format='%d-%m-%Y')

        # Dolu ve fiyat verilerini ayır
        doluluk_df = df[df['Fiyat'].astype(str).str.strip().str.upper() == 'DOLU']
        df_numeric = df[df['Fiyat'].astype(str).str.strip().str.upper() != 'DOLU'].copy()
        df_numeric['Fiyat'] = df_numeric['Fiyat'].replace('[€]', '', regex=True).astype(float)

        # Rapor listesi başlat
        rapor_listesi = []

        # Otel bazlı analiz
        for otel in df['Hotel Adı'].unique():
            otel_dolu = doluluk_df[doluluk_df['Hotel Adı'] == otel]
            otel_numeric = df_numeric[df_numeric['Hotel Adı'] == otel].copy()

            otel_numeric['YilAy'] = otel_numeric['Tarih'].dt.to_period('M')
            ay_ortalamalari = otel_numeric.groupby('YilAy')['Fiyat'].mean()

            stop_sale_tarihler = set(otel_dolu['Tarih'].tolist())
            firsat_tarihler = set()

            for idx, row in otel_numeric.iterrows():
                yilay = row['YilAy']
                fiyat = row['Fiyat']
                ortalama = ay_ortalamalari[yilay]

                if fiyat >= ortalama * 1.30:
                    stop_sale_tarihler.add(row['Tarih'])

                if fiyat <= ortalama * 0.85:
                    firsat_tarihler.add(row['Tarih'])

            rapor_listesi.append({
                'Otel Adı': otel,
                'Stop Sale Gün Sayısı': len(stop_sale_tarihler),
                'Fırsat Gün Sayısı': len(firsat_tarihler),
                'Stop Sale Tarihler': sorted([t.strftime('%d-%m-%Y') for t in stop_sale_tarihler]),
                'Fırsat Tarihler': sorted([t.strftime('%d-%m-%Y') for t in firsat_tarihler])
            })

        # Veriyi DataFrame'e dönüştür
        rapor_df = pd.DataFrame(rapor_listesi)

        # Dashboard Sekmeleri
        tab1, tab2, tab3 = st.tabs(["🚫 Stop Sale Olan Oteller", "💸 Fırsat Günleri Olan Oteller", "📋 Tüm Oteller Raporu"])

        with tab1:
            st.subheader(f"Stop Sale Olan Oteller ({selected_datetime})")
            stop_sale_olanlar = rapor_df[rapor_df['Stop Sale Gün Sayısı'] > 0]

            if stop_sale_olanlar.empty:
                st.info("Stop Sale günü olan otel bulunamadı.")
            else:
                for index, row in stop_sale_olanlar.iterrows():
                    with st.expander(f"🛎️ {row['Otel Adı']} ({row['Stop Sale Gün Sayısı']} gün)"):
                        st.write(row['Stop Sale Tarihler'])

        with tab2:
            st.subheader(f"Fırsat Günleri Olan Oteller ({selected_datetime})")
            firsat_olanlar = rapor_df[rapor_df['Fırsat Gün Sayısı'] > 0]

            if firsat_olanlar.empty:
                st.info("Fırsat günü olan otel bulunamadı.")
            else:
                for index, row in firsat_olanlar.iterrows():
                    with st.expander(f"💰 {row['Otel Adı']} ({row['Fırsat Gün Sayısı']} gün)"):
                        st.write(row['Fırsat Tarihler'])

        with tab3:
            st.subheader(f"Tüm Oteller Genel Raporu ({selected_datetime})")
            st.dataframe(rapor_df[['Otel Adı', 'Stop Sale Gün Sayısı', 'Fırsat Gün Sayısı']])

except Exception as e:
    st.error(f"Hata oluştu: {e}")
