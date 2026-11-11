# Müzakere Tarzı Testi

**Sürüm: v1 — 2026-11-11 15:04**

**Sürüm notları**

- v1 — İlk sürüm.

30 soruluk A/B çatışma tarzı testini çözdüren, beş müzakere tarzını (Rekabetçi, İşbirlikçi, Uzlaşmacı, Kaçınmacı, İltifatkar) puanlayan ve profile göre yorum gösteren küçük bir web sitesi. Katılımcılar takma ad ve 4 haneli PIN ile anonim kayıt olur; yönetici `/yonetici` adresinden sonuçları görür.

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
