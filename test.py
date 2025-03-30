import json
import os
# JSON dosyasını okuma
with open('Untitled-1.json', 'r') as file:
    # Dosyadaki veriyi string olarak okuyun
    data = file.read()

# Tek tırnakları çift tırnaklarla değiştirme
data = data.replace("'", '"')

data_list=json.loads(data)
print(data_list["rooms"][0]["roomType"])