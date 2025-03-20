import pandas as pd
import streamlit as st
import glob

# ➤ Fiyat dönüştürücü fonksiyon
def convert_price_to_float(price_str):
    price_str = str(price_str).replace('€', '').strip().lower()

    try:
        if price_str.endswith('k'):
            return float(price_str[:-1]) * 1_000
        elif price_str.endswith('m'):
            return float(price_str[:-1]) * 1_000_000
        elif price_str.endswith('b'):
            return float(price_str[:-1]) * 1_000_000_000
        else:
            return float(price_str)
    except ValueError:
        return None

# ➤ Alış fiyatı hesaplayıcı (%4 düşerek)
def calculate_alim_fiyati(satis_fiyati):
    try:
        return round(satis_fiyati * 0.96, 2)
    except:
        return None

# Sayfa yapılandırması
st.set_page_config(page_title="Otel Raporlama Dashboard", layout="wide")

# Ana başlık
st.title("📊 Otel Stop Sale ve Fırsat Günleri Dashboard")

# ➤ SEKMELER ➤
sekme_b2c, sekme_b2b = st.tabs(["🛒 B2C (Trip.com)", "🏨 B2B (Bedsopia)"])

######################################################################################
###################################### B2C TAB #######################################
######################################################################################
with sekme_b2c:
    try:
        st.header("🛒 B2C Trip.com Verileri")

        # CSV dosyalarını bul ve sıralı liste yap
        csv_files = sorted(glob.glob("sonuc_*.csv"))

        if not csv_files:
            st.warning("Hiç CSV dosyası bulunamadı. Lütfen botu çalıştır ve tekrar dene.")
        else:
            # Tarih + saat listesini çıkar ve en yeniyi başa al
            dates_available = [
                f.replace("sonuc_", "").replace(".csv", "").replace("_", " ") for f in csv_files
            ]
            dates_available.reverse()  # En yeni başta

            # Kullanıcı tarih/saat seçiyor
            selected_datetime = st.selectbox(
                "📅 Hangi tarih/saat verisini görmek istersin?",
                dates_available,
                index=0  # Varsayılan olarak en yeni dosya seçili
            )

            # Seçilen dosya yolu
            selected_file = f"sonuc_{selected_datetime.replace(' ', '_')}.csv"

            # 🔧 Veriyi oku ➔ "-" olanlar NaN yapılır
            df = pd.read_csv(selected_file, na_values=['-', 'DOLU'])

            # Tarih formatı
            df['Tarih'] = pd.to_datetime(df['Tarih'], format='%d-%m-%Y')

            # 🔧 Dolu (Stop Sale) verilerini ayır ➔ Fiyat NaN olan satırlar
            doluluk_df = df[df['Fiyat'].isna()]

            # 🔧 Dolu olmayan verileri işle ➔ Fiyatı olanlar
            df_numeric = df[df['Fiyat'].notna()].copy()

            # ➤ Burada dönüşüm fonksiyonunu kullanıyoruz!
            df_numeric['Fiyat'] = df_numeric['Fiyat'].apply(convert_price_to_float)

            # Rapor listesi başlat
            rapor_listesi = []

            # Otel bazlı analiz
            for otel in df['Hotel Adı'].unique():
                otel_dolu = doluluk_df[doluluk_df['Hotel Adı'] == otel]
                otel_numeric = df_numeric[df_numeric['Hotel Adı'] == otel].copy()

                # Yıl-Ay bazlı gruplama
                otel_numeric['YilAy'] = otel_numeric['Tarih'].dt.to_period('M')
                ay_ortalamalari = otel_numeric.groupby('YilAy')['Fiyat'].mean()

                stop_sale_tarihler = set(otel_dolu['Tarih'].tolist())
                firsat_tarihler = set()

                for idx, row in otel_numeric.iterrows():
                    yilay = row['YilAy']
                    fiyat = row['Fiyat']
                    ortalama = ay_ortalamalari[yilay]

                    # 🔧 Fiyat ortalamanın %30 üzerindeyse ➔ Stop Sale olabilir!
                    if fiyat >= ortalama * 1.30:
                        stop_sale_tarihler.add(row['Tarih'])

                    # 🔧 Fiyat ortalamanın %15 altındaysa ➔ Fırsat günleri
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

            # TABLAR
            tab1, tab2, tab3 = st.tabs([
                "🚫 Stop Sale Olan Oteller",
                "💸 Fırsat Günleri Olan Oteller",
                "📋 Tüm Oteller Genel Rapor + Detaylar"
            ])

            # TAB 1 - STOP SALE OLAN OTELLER
            with tab1:
                st.subheader(f"🚫 Stop Sale Olan Oteller ({selected_datetime})")
                stop_sale_olanlar = rapor_df[rapor_df['Stop Sale Gün Sayısı'] > 0]

                if stop_sale_olanlar.empty:
                    st.info("Stop Sale günü olan otel bulunamadı.")
                else:
                    for index, row in stop_sale_olanlar.iterrows():
                        with st.expander(f"🛎️ {row['Otel Adı']} ({row['Stop Sale Gün Sayısı']} gün)"):
                            st.write(row['Stop Sale Tarihler'])

            # TAB 2 - FIRSAT GÜNLERİ OLAN OTELLER
            with tab2:
                st.subheader(f"💸 Fırsat Günleri Olan Oteller ({selected_datetime})")
                firsat_olanlar = rapor_df[rapor_df['Fırsat Gün Sayısı'] > 0]

                if firsat_olanlar.empty:
                    st.info("Fırsat günü olan otel bulunamadı.")
                else:
                    for index, row in firsat_olanlar.iterrows():
                        with st.expander(f"💰 {row['Otel Adı']} ({row['Fırsat Gün Sayısı']} gün)"):
                            st.write(row['Fırsat Tarihler'])

            # TAB 3 - TÜM OTELLER VE DETAYLI RAPOR
            with tab3:
                st.subheader(f"📋 Tüm Oteller Genel Raporu ({selected_datetime})")
                st.dataframe(rapor_df[['Otel Adı', 'Stop Sale Gün Sayısı', 'Fırsat Gün Sayısı']])

    except Exception as e:
        st.error(f"Hata oluştu (B2C): {e}")

######################################################################################
###################################### B2B TAB #######################################
######################################################################################
with sekme_b2b:
    try:
        st.header("🏨 B2B Bedsopia Verileri")

        # B2B CSV dosyasını oku
        df_b2b = pd.read_csv("bedsopia_prices.csv")

        # ➤ Fiyatları float'a çevir
        df_b2b['Fiyat'] = df_b2b['Fiyat'].apply(convert_price_to_float)

        # ➤ Alış fiyatını hesapla
        df_b2b['Alış Fiyatı'] = df_b2b['Fiyat'].apply(calculate_alim_fiyati)

        # ➤ Tarihleri datetime formatına çevir
        df_b2b['Tarih'] = pd.to_datetime(df_b2b['Tarih'])

        # ➤ Otel isimleri listesi
        oteller = sorted(df_b2b['Otel Adı'].unique().tolist())

        # Otel seçimi
        selected_hotel = st.selectbox("🏨 Bir Otel Seçin", oteller)

        if selected_hotel:
            hotel_df = df_b2b[df_b2b['Otel Adı'] == selected_hotel].copy()

            # ➤ Filtreler
            st.markdown("### 🔎 Filtreleme Seçenekleri")

            oda_tipleri = sorted(hotel_df['Oda Tipi'].unique().tolist())
            board_types = sorted(hotel_df['Board Type'].unique().tolist())
            iptal_politikalari = sorted(hotel_df['İptal Poliçesi'].unique().tolist())

            selected_oda = st.multiselect("🏷️ Oda Tipi", oda_tipleri, default=oda_tipleri)
            selected_board = st.multiselect("🍽️ Board Type", board_types, default=board_types)
            selected_politika = st.multiselect("⚖️ İptal Poliçesi", iptal_politikalari, default=iptal_politikalari)

            # ➤ Filtre uygula
            filtered_df = hotel_df[
                (hotel_df['Oda Tipi'].isin(selected_oda)) &
                (hotel_df['Board Type'].isin(selected_board)) &
                (hotel_df['İptal Poliçesi'].isin(selected_politika))
            ]

            # ➤ Tarihe göre sırala
            filtered_df = filtered_df.sort_values(by='Tarih')

            st.markdown(f"### 🗓️ {selected_hotel} Günlük Fiyatlar ve Alış Fiyatları")
            st.dataframe(filtered_df[['Tarih', 'Oda Tipi', 'Board Type', 'İptal Poliçesi', 'Fiyat', 'Alış Fiyatı', 'Para Birimi', 'Müsaitlik', 'Milliyet']])

            # ➤ Grafik
            st.line_chart(filtered_df.set_index('Tarih')[['Fiyat', 'Alış Fiyatı']])

    except Exception as e:
        st.error(f"Hata oluştu (B2B): {e}")
