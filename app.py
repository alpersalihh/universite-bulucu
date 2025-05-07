import os
import pandas as pd
from flask import Flask, render_template, request, send_file
import google.generativeai as genai
import json
from io import BytesIO
from datetime import datetime

app = Flask(__name__)

# --- Gemini API Yapılandırması Başlangıç ---
API_KEY = "AIzaSyAota_W3SpUKSO3SPxeFG9NlXu1OgdJ_HQ"
model_gemini = None

if API_KEY:
    try:
        genai.configure(api_key=API_KEY)
        # Doğrudan gemini-1.5-flash modelini kullan
        model_gemini = genai.GenerativeModel('gemini-1.5-flash')
        print("Gemini API başarıyla yapılandırıldı. Kullanılan model: gemini-1.5-flash")
    except Exception as e:
        print(f"Gemini API yapılandırma hatası: {e}")
        print("Lütfen API anahtarınızın doğru olduğundan ve Gemini API'ye erişim izniniz olduğundan emin olun.")
else:
    print("UYARI: GOOGLE_API_KEY ortam değişkeni ayarlanmamış. Gemini API özellikleri kullanılamayacak.")
    print("Lütfen GOOGLE_API_KEY ortam değişkenini ayarlayın.")

def get_bolum_details_from_gemini(responses):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Eğitim seviyesi bilgisini al
        egitim_seviyesi = responses.get('egitim_seviyesi', 'kararsiz')
        egitim_bilgisi = ""
        if egitim_seviyesi == 'lisans':
            egitim_bilgisi = "Lisans (4 yıllık) programlar için"
        elif egitim_seviyesi == 'onlisans':
            egitim_bilgisi = "Ön lisans (2 yıllık) programlar için"
        else:
            egitim_bilgisi = "Hem lisans hem de ön lisans programları için"

        prompt = f"""
        Aşağıdaki bilgilere göre {egitim_bilgisi} en uygun 3 bölüm önerisi yap.
        Her bölüm için detaylı açıklama, iş imkanları ve önerilen üniversiteleri listele.
        
        Kullanıcı Bilgileri:
        - Bölge: {responses.get('bolge', 'Belirtilmemiş')}
        - Kişisel Tanıtım: {responses.get('kendini_tanit', 'Belirtilmemiş')}
        - Sayısal Yetenek: {'Var' if responses.get('sayisal_yatkinlik') == '1' else 'Yok'}
        - Sözel Yetenek: {'Var' if responses.get('sozel_yatkinlik') == '1' else 'Yok'}
        - Sanat İlgisi: {'Var' if responses.get('sanat_ilgisi') == '1' else 'Yok'}
        - Sosyal İlişkiler: {'Var' if responses.get('sosyal_yatkinlik') == '1' else 'Yok'}
        - Yaratıcı Düşünme: {'Var' if responses.get('yaratici_yatkinlik') == '1' else 'Yok'}
        - Teknoloji İlgisi: {'Var' if responses.get('teknoloji_ilgisi') == '1' else 'Yok'}
        - Dil Yeteneği: {'Var' if responses.get('dil_yetenegi') == '1' else 'Yok'}
        - Liderlik: {'Var' if responses.get('liderlik') == '1' else 'Yok'}
        
        Lütfen aşağıdaki JSON formatında yanıt ver. Yanıtını sadece JSON olarak ver, başka açıklama ekleme:
        {{
            "bolumler": [
                {{
                    "bolum_adi": "Bölüm Adı",
                    "aciklama": "Bölüm hakkında detaylı açıklama",
                    "is_imkanlari": ["İş imkanı 1", "İş imkanı 2", "..."],
                    "universiteler": ["Üniversite 1", "Üniversite 2", "..."]
                }}
            ],
            "analiz": "Kullanıcının profiline göre genel analiz"
        }}
        """

        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # JSON formatını temizle
        if response_text.startswith("```json"):
            response_text = response_text[len("```json"):].strip()
        if response_text.endswith("```"):
            response_text = response_text[:-len("```")].strip()
            
        # JSON'ı parse et
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            print(f"Geçersiz JSON yanıtı: {response_text}")
            return {
                "bolumler": [
                    {
                        "bolum_adi": "Hata",
                        "aciklama": "API yanıtı işlenirken bir hata oluştu.",
                        "is_imkanlari": ["Lütfen tekrar deneyin"],
                        "universiteler": ["Lütfen tekrar deneyin"]
                    }
                ],
                "analiz": "API yanıtı işlenirken bir hata oluştu. Lütfen tekrar deneyin."
            }
            
    except Exception as e:
        print(f"Gemini API Hatası: {str(e)}")
        return {
            "bolumler": [
                {
                    "bolum_adi": "Hata",
                    "aciklama": "API'ye erişim sağlanamadı.",
                    "is_imkanlari": ["Lütfen tekrar deneyin"],
                    "universiteler": ["Lütfen tekrar deneyin"]
                }
            ],
            "analiz": "API'ye erişim sağlanamadı. Lütfen tekrar deneyin."
        }

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            # Form verilerini al
            form_inputs = {
                'bolge': request.form.get('bolge'),
                'kendini_tanit': request.form.get('kendini_tanit'),
                'sayisal_yatkinlik': request.form.get('sayisal_yatkinlik'),
                'sozel_yatkinlik': request.form.get('sozel_yatkinlik'),
                'sanat_ilgisi': request.form.get('sanat_ilgisi'),
                'sosyal_yatkinlik': request.form.get('sosyal_yatkinlik'),
                'yaratici_yatkinlik': request.form.get('yaratici_yatkinlik'),
                'teknoloji_ilgisi': request.form.get('teknoloji_ilgisi'),
                'dil_yetenegi': request.form.get('dil_yetenegi'),
                'liderlik': request.form.get('liderlik'),
                'egitim_seviyesi': request.form.get('egitim_seviyesi')
            }

            # Form validasyonu
            if not all(form_inputs.values()):
                return render_template('index.html', error_dt="Lütfen tüm alanları doldurun.")

            # Gemini API'den önerileri al
            response_data = get_bolum_details_from_gemini(form_inputs)
            if not response_data:
                return render_template('index.html', error_dt="API erişimi sağlanamadı.")
            
            # Sonuçları hazırla
            prediction_dt = [bolum['bolum_adi'] for bolum in response_data['bolumler']]
            aciklama_api = [bolum['aciklama'] for bolum in response_data['bolumler']]
            is_imkanlari_api = [bolum['is_imkanlari'] for bolum in response_data['bolumler']]
            universiteler_api = [bolum['universiteler'] for bolum in response_data['bolumler']]
            analiz_api = response_data['analiz']

            # Excel verisi hazırla
            excel_data = []
            for i in range(len(prediction_dt)):
                excel_data.append({
                    'Bölüm': prediction_dt[i],
                    'Açıklama': aciklama_api[i],
                    'İş İmkanları': ', '.join(is_imkanlari_api[i]),
                    'Önerilen Üniversiteler': ', '.join(universiteler_api[i])
                })

            return render_template('index.html',
                                prediction_dt=prediction_dt,
                                aciklama_api=aciklama_api,
                                is_imkanlari_api=is_imkanlari_api,
                                universiteler_api=universiteler_api,
                                analiz_api=analiz_api,
                                excel_data=excel_data,
                                form_inputs=form_inputs)

        except Exception as e:
            print(f"Hata: {str(e)}")
            return render_template('index.html', error_dt="Bir hata oluştu. Lütfen tekrar deneyin.")

    return render_template('index.html')

@app.route('/download_excel')
def download_excel():
    if not hasattr(app, 'excel_data'):
        return "Excel verisi bulunamadı.", 404

    # Excel dosyası oluştur
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Üniversiteler
        universities_data = []
        for i, unis in enumerate(app.excel_data.get('universiteler_api', [])):
            for uni in unis:
                universities_data.append({
                    'Bölüm': app.excel_data['Bölümler'][i],
                    'Üniversite': uni
                })
        
        pd.DataFrame(universities_data).to_excel(writer, sheet_name='Üniversiteler', index=False)

    output.seek(0)
    
    # Dosya adını oluştur
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'universiteler_{timestamp}.xlsx'
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)