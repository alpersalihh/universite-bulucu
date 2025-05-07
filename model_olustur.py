import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder
import joblib

# Genişletilmiş veri seti oluşturma
data = {
    'sayisal_yatkinlik': [1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1],  # 1: Evet, 0: Hayır
    'sozel_yatkinlik':   [0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 1, 0, 1, 0],  # 1: Evet, 0: Hayır
    'sanat_ilgisi':     [0, 0, 1, 0, 1, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1],  # 1: Evet, 0: Hayır
    'sosyal_yatkinlik': [0, 1, 1, 1, 0, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0],  # 1: Evet, 0: Hayır
    'yaratici_yatkinlik': [0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 1, 0, 1],  # 1: Evet, 0: Hayır
    'bolum_onerisi':    ['Mühendislik', 'Hukuk', 'Güzel Sanatlar', 'İşletme', 
                         'İletişim', 'Mimarlık', 'Tıp', 'Psikoloji', 
                         'Endüstriyel Tasarım', 'Sosyoloji', 'Diş Hekimliği',
                         'Grafik Tasarım', 'Eğitim Bilimleri', 'Uluslararası İlişkiler',
                         'Müzik']
}

df = pd.DataFrame(data)

# Özellikler (X) ve hedef değişken (y)
X = df[['sayisal_yatkinlik', 'sozel_yatkinlik', 'sanat_ilgisi', 'sosyal_yatkinlik', 'yaratici_yatkinlik']]
y = df['bolum_onerisi']

# Hedef değişkeni (bölüm isimlerini) sayısala çevirme
le = LabelEncoder()
y_encoded = le.fit_transform(y)

# Karar Ağacı Modelini Oluşturma ve Eğitme
# max_depth: Ağacın karmaşıklığını sınırlar, aşırı öğrenmeyi (overfitting) azaltır.
# random_state: Modelin her çalıştırıldığında aynı sonuçları vermesi için (tekrarlanabilirlik).
model = DecisionTreeClassifier(max_depth=4, random_state=42)
model.fit(X, y_encoded)

# Eğitilmiş modeli ve label encoder'ı kaydetme
joblib.dump(model, 'bolum_oneri_model.joblib')
joblib.dump(le, 'bolum_label_encoder.joblib')

print("Model ve Label Encoder başarıyla kaydedildi: 'bolum_oneri_model.joblib' ve 'bolum_label_encoder.joblib'")

# İsteğe bağlı: Modelin basit bir testini yapabilirsiniz
# Örnek bir girdi için tahmin
test_input_data = pd.DataFrame([[1, 0, 1, 1, 1]], 
                              columns=['sayisal_yatkinlik', 'sozel_yatkinlik', 'sanat_ilgisi', 
                                      'sosyal_yatkinlik', 'yaratici_yatkinlik'])
prediction_encoded = model.predict(test_input_data)
prediction_decoded = le.inverse_transform(prediction_encoded)
print(f"Örnek girdi için tahmin edilen bölüm: {prediction_decoded[0]}")