# Proje Bilgisi — Müzakere Tarzı Testi

**Sürüm: v4 — 2026-11-11 16:17**

**Sürüm notları**

- v4 — Barındırma Render yerine Vercel (Render'a giriş yapılamadı); `api/index.py`, `vercel.json`, `.vercelignore` eklendi.
- v3 — Kaynaklı yorumlar kullanıcı tarafından onaylandı; PIN 4 karakter harf/rakam; yönetici ana formdan girer; Kişiselleştir kutusu kapalı.
- v2 — Son inceleme düzeltmeleri: atomik PIN deneme sayacı, Türkiye saati, Docker logs klasörü.
- v1 — İlk sürüm: amaç, komutlar, klasör haritası, ayar anahtarları, kararlar.

## Amaç

Ümit Anıl'ın (Tribün) müzakere eğitimindeki 30 soruluk çatışma tarzı testini web'e taşıyan, kullanıcının portföy ve öğrenme projesi. Link yalnızca ekip arkadaşları ve birkaç tanıdıkla paylaşılır; site arama motorlarına kapalıdır.

**Canlı site:** https://ikna-muzakere.vercel.app · Kod: https://github.com/AhmettUsta/ikna_muzakere

## Komutlar

| İş | Komut |
|---|---|
| Paketleri kur | `python3 -m pip install -r requirements.txt` |
| Şemayı güncelle | `python3 -m alembic upgrade head` |
| Yerelde çalıştır | `PYTHONPATH=src python3 -m uvicorn main:app --reload` |
| Testler | `python3 -m pytest` |
| Veritabanı testleri | `RUN_DB_TESTS=1 python3 -m pytest` |
| Docker (isteğe bağlı) | `docker build -t ikna-muzakere .` · `docker run --env-file .env -p 8000:8000 ikna-muzakere` |
| Yayın | GitHub'a push → Vercel otomatik yayınlar. Şema değişirse migration yerelden çalıştırılır: `python3 -m alembic upgrade head` |

## Klasör haritası

| Yol | İçerik |
|---|---|
| `src/main.py` | Uygulama kurulumu (`create_app`), `uvicorn main:app` giriş noktası |
| `src/service.py` | `TestService` orkestratörü: kayıt, giriş, test, sonuç, canlı yorum, yönetici |
| `src/step_content.py` | `src/content/` içeriğini yükler ve doğrular |
| `src/step_database.py`, `src/db_models.py` | Neon PostgreSQL erişimi |
| `src/step_gemini.py` | İsteğe bağlı canlı Gemini yorumu |
| `src/scoring.py`, `src/presentation.py`, `src/chart.py`, `src/security.py` | Puanlama, sunum gösterim kuralı, SVG grafik, PIN ve takma ad |
| `src/web/` | Route'lar, şablonlar, CSS ve JS |
| `src/content/` | Sorular, cevap anahtarı, eşikler, sunum metinleri, kaynaklı yorumlar |
| `migrations/` | Alembic migration'ları |
| `docs/` | Soru fotoğrafları ve eğitim sunumu (kaynak malzeme) |
| `plans/` | Tasarım, mimari, uygulama planı |

## Ayarlar

Tüm ayarlar `.env` içindeki tek `ikna_muzakere_secrets` değişkeninde JSON olarak durur. Alanlar:

`LOG_LEVEL`, `LOG_TO_FILE`, `PG_USER`, `PG_PASSWORD`, `PG_HOST`, `PG_PORT`, `PG_DATABASE`, `PG_SCHEMA`, `PG_SSLMODE`, `SESSION_SECRET`, `ADMIN_PASSWORD`, `COOKIE_SECURE`, `GEMINI_API_KEY`, `GEMINI_MODEL`

- `PG_HOST` Neon'un havuzlu (`-pooler`) adresidir; migration'lar otomatik olarak havuzsuz adresi kullanır.
- `GEMINI_API_KEY` ya da `GEMINI_MODEL` boşsa canlı yorum düğmesi görünmez.
- Yerelde `COOKIE_SECURE=false`, yayında `true`.

## Alınmış kararlar

- Orijinal sorular, anahtar, eşikler ve sunum metinleri kullanılır; telif riski kullanıcıya aittir. Bu yüzden site `noindex` ve `robots.txt` ile kapalıdır.
- Kaçınmacı tarzında sunumdaki iki "uygun" slaytı olduğu gibi gösterilir; "uygun olmadığı" bölümü yoktur.
- Kaynaklı yorumlar önceden hazırlanmıştır (15 tarz–seviye bloğu, 20 profil metni, 10 doğrulanmış kaynak) ve 2026-11-11 tarihinde kullanıcı tarafından onaylanmıştır. Canlı Gemini yorumu yalnızca istek üzerine üretilir ve kaydedilir.
- Veritabanı Neon (Frankfurt, `neondb`, şema `ikna_muzakere`); barındırma Vercel Hobby (ücretsiz) — giriş `api/index.py`, tüm istekler `vercel.json` `routes` ile uygulamaya gider (repo dosyaları statik sunulmaz). Render'a giriş yapılamadığı için vazgeçildi; Dockerfile yerel/alternatif kullanım için durur.
- Kod GitHub'da: `AhmettUsta/ikna_muzakere` (gizli).
- PIN denemeleri doğrulamadan önce veritabanında tek bir UPDATE ile sayılır; eşzamanlı isteklerle 15 dakikada 5'ten fazla deneme yapılamaz.
- Tarihler Türkiye saatiyle (UTC+3) gösterilir.
- Commit ve push yalnızca kullanıcı isteyince yapılır.
