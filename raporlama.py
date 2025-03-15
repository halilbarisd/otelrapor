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

            st.divider()  # Görsel ayırıcı

            st.subheader("📝 Detaylı Otel Raporları")

            # Her otelin detayları
            for index, row in rapor_df.iterrows():
                otel_adi = row['Otel Adı']

                with st.expander(f"🔍 {otel_adi} Detaylı Rapor"):
                    st.write(f"**Stop Sale Günleri ({len(row['Stop Sale Tarihler'])}):**")
                    st.write(row['Stop Sale Tarihler'])

                    st.write(f"**Fırsat Günleri ({len(row['Fırsat Tarihler'])}):**")
                    st.write(row['Fırsat Tarihler'])

                    # Detaylı fiyat listesi
                    st.write("**Günlük Fiyat Listesi:**")
                    otel_fiyat_df = df_numeric[df_numeric['Hotel Adı'] == otel_adi][['Tarih', 'Fiyat']].sort_values(by='Tarih')
                    st.dataframe(otel_fiyat_df)

                    # (Opsiyonel) Fiyat grafiği
                    st.line_chart(otel_fiyat_df.set_index('Tarih'))

                        # Karşılaştırmalı analiz alanı
    st.divider()
    st.subheader("🔄 İki Zaman Dilimi Arasında Karşılaştırmalı Analiz")

    # Kullanıcı iki zaman dilimi seçiyor
    compare_datetimes = st.multiselect(
        "Karşılaştırmak istediğin iki tarih/saat kaydını seç (ilk → önceki, ikinci → yeni):",
        dates_available,
        max_selections=2
    )

    # İki kayıt seçildiğinde
    if len(compare_datetimes) == 2:
        file1 = f"sonuc_{compare_datetimes[0].replace(' ', '_')}.csv"
        file2 = f"sonuc_{compare_datetimes[1].replace(' ', '_')}.csv"

        st.info(f"Karşılaştırılıyor:\n➡️ {compare_datetimes[0]}\n➡️ {compare_datetimes[1]}")

        df1 = pd.read_csv(file1)
        df2 = pd.read_csv(file2)

        # Verileri hazırlıyoruz
        df1['Fiyat'] = df1['Fiyat'].replace('DOLU', 0).replace('[€]', '', regex=True).astype(float)
        df2['Fiyat'] = df2['Fiyat'].replace('DOLU', 0).replace('[€]', '', regex=True).astype(float)

        df1['Tarih'] = pd.to_datetime(df1['Tarih'], format='%d-%m-%Y')
        df2['Tarih'] = pd.to_datetime(df2['Tarih'], format='%d-%m-%Y')

        # İki dataframe'i birleştiriyoruz (Hotel Adı + Tarih bazlı)
        merged = pd.merge(
            df1,
            df2,
            on=['Hotel Adı', 'Tarih'],
            suffixes=('_ilk', '_son')
        )

        # Fiyat farkı hesapla
        merged['Fiyat Farkı'] = merged['Fiyat_son'] - merged['Fiyat_ilk']

        # Değişim durumlarını filtrele
        fiyat_artanlar = merged[merged['Fiyat Farkı'] > 0]
        fiyat_azalanlar = merged[merged['Fiyat Farkı'] < 0]

        st.subheader("📈 Fiyat Artışları")
        if fiyat_artanlar.empty:
            st.success("Fiyat artışı yok!")
        else:
            st.dataframe(fiyat_artanlar[['Hotel Adı', 'Tarih', 'Fiyat_ilk', 'Fiyat_son', 'Fiyat Farkı']])

        st.subheader("📉 Fiyat Düşüşleri (Fırsat Olabilir!)")
        if fiyat_azalanlar.empty:
            st.success("Fiyat düşüşü yok!")
        else:
            st.dataframe(fiyat_azalanlar[['Hotel Adı', 'Tarih', 'Fiyat_ilk', 'Fiyat_son', 'Fiyat Farkı']])

        # Stop sale / doluluk durum farklarını göstermek istersen ekleriz!

    elif len(compare_datetimes) == 1:
        st.info("Lütfen iki farklı zaman dilimi seçin.")

    else:
        st.info("Karşılaştırma için iki kayıt seçiniz.")


except Exception as e:
    st.error(f"Hata oluştu: {e}")
