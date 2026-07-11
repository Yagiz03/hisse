# Hisse Masası

Portföy yönetimi için fon karşılaştırma ve piyasa analiz paneli (Streamlit).

## Çalıştırma

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Modüller

- **Fon Karşılaştırma** (`pages/1_Fon_Karsilastirma.py`): Fonların KAP'ta
  yayınlanan aylık "Portföy Dağılım Raporu" PDF'lerini yükleyip varlık sınıfı
  dağılımlarını yan yana karşılaştırır. İki fon seçilirse aradaki puan farkını,
  üç veya daha fazla fon seçilirse her fonun seçili fonların ortalamasından
  sapmasını gösterir.
- **Finansal Tablolar** (`pages/2_Finansal_Tablolar.py`): BIST şirketlerinin
  bilanço/gelir tablosu kalemlerini ve rasyolarını karşılaştırır.
- **Sektör Isı Haritası** / **Portföy Simülasyonu**: BIST30 sektör
  performansı ve ağırlıklı portföy backtest'i.

## Veri kaynakları

- **Fon varlık dağılımı**: KAP'ta portföy yönetim şirketlerinin yayınladığı
  "Portföy Dağılım Raporu" PDF'leri, kullanıcı tarafından manuel yüklenir
  (`data/kap.py`). TEFAS Nisan 2026'da API'sini Akamai bot korumasıyla
  kapattığı için otomatik çekim yerine bu yol seçildi. Parser, SPK'nın
  standart aylık fon bildirim formundaki "Aylık Ortalama Portföydeki Menkul
  Kıymetler Yüzdesi" bölümünü satır (Y-koordinat) bazlı eşleştirmeyle okur -
  şirketten şirkete görsel yerleşim değişse de veri alanları standart olduğu
  için farklı formatlarda (AK Portföy, İş Portföy, QNB Portföy, Yapı Kredi
  Portföy) doğrulandı.
- **Hisse fiyat/finansal veri**: `isyatirimhisse` paketi (`data/financials.py`,
  `data/prices.py`).

## Notlar

- Renk paleti ve koyu tema `ui/theme.py` içinde tanımlıdır; tüm grafiklerde
  fon/şirket kimliği sabit bir renk sırasıyla eşlenir.
- `data/kap.py` içindeki `parse_holdings` (hisse bazlı ağırlık çıkarımı) henüz
  üretime hazır değil - bazı raporlarda birden fazla "%" sütunu olduğu için
  doğru sütunu ayırt etmek güvenilir değil.
