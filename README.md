# Müzakere Tarzı Testi

**Sürüm: v2 — 2026-11-11 16:34**

**Sürüm notları**

- v2 — Canlı site ve yönetim panelleri bağlantıları eklendi.
- v1 — İlk sürüm.

## Bağlantılar

| | |
|---|---|
| **Canlı site** | https://ikna-muzakere.vercel.app |
| Yönetici girişi | Ana sayfada "Sonucuma bak" → takma ad: yönetici adı, PIN: yönetici şifresi |
| Kod (GitHub) | https://github.com/AhmettUsta/ikna_muzakere |
| Yayın paneli (Vercel) | https://vercel.com/dashboard → `ikna-muzakere` |
| Veritabanı (Neon) | https://console.neon.tech → `ikna_muzakere` |

`main` dalına her push, Vercel'de otomatik yeni yayın başlatır.

30 soruluk A/B çatışma tarzı testini çözdüren, beş müzakere tarzını (Rekabetçi, İşbirlikçi, Uzlaşmacı, Kaçınmacı, İltifatkar) puanlayan ve profile göre yorum gösteren küçük bir web sitesi. Katılımcılar takma ad ve 4 karakterli PIN (harf/rakam) ile anonim kayıt olur; yönetici ana sayfadaki giriş formundan ya da `/yonetici` adresinden sonuçları görür.

## Hızlı başlangıç

```bash
python3 -m pip install -r requirements.txt
cp .env.example .env            # değerleri doldurun
python3 -m alembic upgrade head # şemayı oluşturur
PYTHONPATH=src python3 -m uvicorn main:app --reload
```

Site `http://localhost:8000` adresinde açılır.

## Testler

```bash
python3 -m pytest                          # veritabanı gerektirmeyen testler
RUN_DB_TESTS=1 python3 -m pytest           # Neon'a karşı veritabanı testleri dahil
```

## Teknoloji

FastAPI · Jinja2 · SQLAlchemy 2.0 · Alembic · PostgreSQL (Neon) · Google Gemini (isteğe bağlı) · Vercel

Ayrıntılar: [plans/](plans/) altındaki tasarım, mimari ve uygulama planı.
