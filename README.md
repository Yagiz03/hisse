# Hisse Masası

Portföy yönetimi için fon karşılaştırma ve piyasa analiz paneli (Streamlit).

## Çalıştırma

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Modüller

- **Fon Karşılaştırma** (`pages/1_Fon_Karsilastirma.py`): TEFAS'tan çekilen fon
  içi varlık dağılımlarını yan yana karşılaştırır. İki fon seçilirse aradaki
  puan farkını, üç veya daha fazla fon seçilirse her fonun seçili fonların
  ortalamasından sapmasını gösterir.

## Veri kaynakları

- **Fon verisi**: TEFAS'ın resmi olmayan (topluluk tarafından tespit edilmiş)
  `tefas.gov.tr/api/DB/BindHistoryAllocation` ve `BindHistoryInfo` uç noktaları
  (`data/tefas.py`). TEFAS bu uç noktaları önceden haber vermeden
  değiştirebilir; hata alınırsa tarayıcı geliştirici araçlarından güncel
  istek/yanıt şekli doğrulanmalı.
- **Finansal tablolar** (yakında): `isyatirimhisse` paketi, eksik kalemler için
  KAP fallback.

## Notlar

- TEFAS istekleri `data/cache.py` üzerinden 6 saat TTL ile önbelleklenir.
- Renk paleti ve koyu tema `ui/theme.py` içinde tanımlıdır; tüm grafiklerde
  fon kimliği sabit bir renk sırasıyla eşlenir.
