import pandas as pd
from fuzzywuzzy import fuzz

# CSV dosyasını oku
df = pd.read_csv("bedsopia_prices_normalized.csv")

# Benzersiz oda ve board tiplerini al
unique_rooms = df["Oda Tipi"].unique()
unique_boards = df["Board Type"].unique()

# Dinamik gruplama fonksiyonu
def group_similar(items, threshold=85):
    groups = []
    labels = []

    for item in items:
        found = False
        for group in groups:
            if fuzz.token_set_ratio(item, group[0]) >= threshold:
                labels.append(group[1])
                found = True
                break
        if not found:
            new_label = f"Group_{len(groups) + 1}"
            groups.append((item, new_label))
            labels.append(new_label)

    return dict(zip(items, labels))

# Grupları oluştur
room_mapping = group_similar(unique_rooms)
board_mapping = group_similar(unique_boards)

# Yeni kolonları ekle
df["Room Group"] = df["Oda Tipi"].map(room_mapping)
df["Board Group"] = df["Board Type"].map(board_mapping)

# Sonuçları kaydet
output_path = "bedsopia_prices_grouped.csv"
df.to_csv(output_path, index=False)
print(f"✅ Normalize edilmiş dosya kaydedildi: {output_path}")