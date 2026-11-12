# Müzakere Tarzı Testi — Mimari

**Sürüm: v7 — 2026-11-12 15:05**

**Sürüm notları**

- v7 — `sunum/tavsiyeler.json`: düşük ve orta seviye tavsiye maddeleri (`Content.sunum_tavsiye`), bölüm başına en fazla 4 madde denetimi.
- v6 — Yönetici için ad değiştirme ve silme route'ları; `DatabaseStep.rename_participant`, `delete_participant`, `ParticipantMissing`.
- v5 — `kaynakli/bolumler.json` (tarz başına uygun / uygun değil / karşı taraf düz yazısı); profil alanları giriş / güçlü / zayıf / öneri; AI destekli sekme için ayrı kart modeli (`AiCard`).
- v4 — Kaçınmacı istisnası kalktı: her tarzda her bölüm türünden tam bir tane; bölüm başına en fazla 4 madde denetimi.
- v3 — Barındırma Render yerine Vercel (Render'a giriş yapılamadı); canlıda doğrulandı.
- v2 — İçerik doğrulaması tür bazlı bölüm listesine göre güncellendi (Kaçınmacı istisnası); geliştirme veritabanı da Neon.
- v1 — İlk mimari: bileşenler, klasör yapısı, veri modeli, sayfalar, dağıtım, test stratejisi.

İlgili dokümanlar: [Tasarım](ikna-muzakere-tasarim.md) · [Uygulama planı](ikna-muzakere-plan.md)

---

## 1. Genel görünüm

```
 Tarayıcı (telefon / bilgisayar)
        │  HTML sayfalar + az JavaScript, imzalı oturum çerezi
        ▼
 Vercel Hobby (ücretsiz) ── Python sunucusuz fonksiyon api/index.py (Frankfurt, fra1)
 ┌──────────────────────────────────────────────────────────┐
 │ FastAPI uygulaması (src/main.py)                         │
 │   web katmanı: aday ve yönetici route'ları, Jinja2       │
 │        │                                                  │
 │   TestService (orkestratör)                               │
 │     ├─ ContentStep   → src/content/*.json, *.md (repoda)  │
 │     ├─ Scorer        → saf puanlama mantığı               │
 │     ├─ PinSecurity   → scrypt özeti, kilitleme kuralı     │
 │     ├─ DatabaseStep  → SQLAlchemy ─────────┐              │
 │     └─ GeminiStep    → google-genai ──┐    │              │
 └───────────────────────────────────────┼────┼─────────────┘
                                         │    ▼
                       Google Gemini API ┘   Neon PostgreSQL (ücretsiz)
                       (yalnızca istek üzerine)  şema: ikna_muzakere
```

- **Tek süreç, tek imaj.** Arka planda iş yok; her şey istek–cevap şeklinde çalışır.
- **İçerik koddan ayrı.** Sorular, anahtar, eşikler ve metinler `src/content/` altında veri dosyası olarak durur.
  - `data/` klasörü `.gitignore`'da olduğu ve Render repodan yayın aldığı için içerik `data/` altına konmaz.
  - Kod yalnızca bu dosyaları okur. İçerik değişince kod değişmez.

## 2. Klasör yapısı

```
src/
  config.py            # mevcut şablon + yeni alanlar (§6)
  logger.py            # mevcut şablon, değişmez
  main.py              # ince giriş noktası: setup_logging, app kurulumu, route kaydı
  service.py           # TestService: step'leri __init__'te alır (DI), akışları yönetir
  scoring.py           # Scorer: puan, seviye, göreli sıralama (DB'siz, saf)
  security.py          # PinSecurity: scrypt hash/verify, kilitleme kuralı
  step_content.py      # ContentStep: src/content dosyalarını yükler ve doğrular
  step_database.py     # DatabaseStep: katılımcı / deneme / AI yorumu kayıtları
  step_gemini.py       # GeminiStep: canlı yorum isteği
  db_models.py         # SQLAlchemy 2.0 deklaratif modeller
  web/
    routes_aday.py
    routes_yonetici.py
    templates/         # Jinja2: base, giris, test, sonuc, gecmis, yonetici_*
    static/            # style.css, test.js (soru geçişi), robots.txt
  content/
    questions.json     # 30 soru: {no, a, b}
    scoring.json       # anahtar (soru→A/B→tarz), eşikler, tarz adları, grafik konumları
    sunum/             # tarz başına sunum metinleri (1. seçenek): sıralı bölüm listesi {tur, baslik, maddeler}
    kaynakli/          # 15 tarz–seviye bloğu, 15 tarz bölümü (bolumler.json), 20 profil yorumu (2. seçenek)
    kaynaklar.md       # kaynak paketi: özetler + tam kaynakça
migrations/            # Alembic
tests/                 # pytest
Dockerfile, .dockerignore, alembic.ini
```

## 3. Bileşenler

| Bileşen | Sorumluluk | Bağımlılık |
|---|---|---|
| `ContentStep` | İçerik dosyalarını açılışta bir kez yükler; doğrular: 30 soru var, her soruda A ve B var, anahtar her şıkkı bir tarza bağlıyor, her tarz 12 şıkta geçiyor. Sunum bölümleri tür bazlı kontrol edilir: her tarzda her türden tam olarak bir bölüm bulunur ve her bölümde 1–4 madde olur. 15 blok ve 20 profil yorumu eksiksiz olmalıdır. Doğrulama hatasında uygulama açılmaz. | dosya sistemi |
| `Scorer` | 30 cevaptan beş puanı, seviyeleri, göreli puanları, baskın ve en az kullanılan tarzı hesaplar. Geçersiz girdide (eksik ya da fazla cevap, A/B dışı değer) `ValueError` verir. | `scoring.json` içeriği (parametre olarak alır) |
| `PinSecurity` | PIN'i `hashlib.scrypt` ile tuz ekleyerek özetler ve doğrular (sabit süreli karşılaştırma). Kilitleme kuralı: 5 yanlış denemede 15 dakika kilit. | standart kütüphane |
| `DatabaseStep` | Katılımcı oluşturma ve bulma, yanlış deneme sayacı, deneme kaydı, deneme listeleri, AI yorumu kaydı ve okuma, yönetici listesi. Her yazma işlemi tek transaction içinde yapılır. | SQLAlchemy, psycopg |
| `GeminiStep` | Puanları, seviyeleri ve kaynak paketini içeren prompt'u gönderir, metni döndürür. Zaman aşımı ve kota hatalarını tek bir `LiveCommentUnavailable` istisnasına çevirir. | google-genai |
| `TestService` | Akışları yönetir: kayıt, giriş, testi bitirme, sonuç görünümü, canlı yorum, yönetici görünümü. Step'leri parametre olarak alır, verilmezse kendisi kurar. Her adım loglanır. | yukarıdakiler |
| web katmanı | Formu okur, `TestService`'i çağırır, şablonu döndürür. İş mantığı içermez. | FastAPI, Jinja2 |

## 4. Veri modeli (şema `ikna_muzakere`)

```
participants
  id              serial PK
  nickname        varchar(30)  NOT NULL
  nickname_key    varchar(30)  NOT NULL UNIQUE   -- küçük harfe çevrilmiş, kırpılmış (benzersizlik buradan)
  pin_hash        bytea        NOT NULL
  pin_salt        bytea        NOT NULL
  failed_pins     smallint     NOT NULL DEFAULT 0
  locked_until    timestamptz  NULL
  created_at      timestamptz  NOT NULL DEFAULT now()

attempts
  id              serial PK
  public_id       uuid         NOT NULL UNIQUE   -- URL'de bu kullanılır, sıralı id değil
  participant_id  int          NOT NULL FK → participants.id
  answers         char(30)     NOT NULL          -- ör. "ABBAB…"; i. karakter i. sorunun cevabı
  score_rekabet, score_isbirligi, score_uzlasma, score_kacinma, score_iltifat  smallint NOT NULL
  created_at      timestamptz  NOT NULL DEFAULT now()
  INDEX (participant_id, created_at DESC)

ai_comments
  attempt_id      int PK FK → attempts.id
  model           varchar(60)  NOT NULL
  text            text         NOT NULL
  created_at      timestamptz  NOT NULL DEFAULT now()
```

- **Puanlar ayrıca saklanır.** Puanlar cevaplardan yeniden hesaplanabilir, ama ayrıca saklanır. Böylece yönetici listesi hızlı açılır ve içerik dosyası ileride değişse bile eski sonuçlar korunur.
- **Seviyeler saklanmaz.** Gösterim anında eşiklerden hesaplanır.
- **Bağlantı havuzu küçük tutulur:** `pool_size=2`, `max_overflow=2`, `pool_pre_ping=True`. Neon'un ücretsiz planında bağlantı sayısı sınırlı. Bağlantı `sslmode=require` ile kurulur.

## 5. Sayfalar ve route'lar

| Yöntem | Yol | Ne yapar | Erişim |
|---|---|---|---|
| GET | `/` | Tanıtım; "Teste başla" ve "Sonucuma bak" | herkes |
| POST | `/kayit` | Takma ad + PIN (iki kez) → katılımcı oluşturur, oturum açar, `/test`'e yönlendirir | herkes |
| POST | `/giris` | Takma ad + PIN → doğrular (kilit kuralıyla), `/gecmis`'e yönlendirir | herkes |
| GET | `/test` | 30 soruluk form; JavaScript her ekranda bir soru gösterir. JavaScript yoksa hepsi listelenir. | oturumlu aday |
| POST | `/test` | Cevapları puanlar ve kaydeder, `/sonuc/{public_id}`'ye yönlendirir | oturumlu aday |
| GET | `/sonuc/{public_id}` | Puan tablosu, SVG grafik, yorum sekmeleri, cevaplar, canlı yorum düğmesi | denemenin sahibi ya da yönetici |
| POST | `/sonuc/{public_id}/canli-yorum` | Onaylanmışsa Gemini'den yorum alır ve kaydeder; zaten varsa kayıtlıyı döndürür | yalnızca denemenin sahibi |
| GET | `/gecmis` | En son sonuç bağlantısı, önceki denemeler, "Testi tekrar çöz" | oturumlu aday |
| POST | `/cikis` | Oturumu kapatır | herkes |
| GET/POST | `/yonetici` | Şifre ile giriş | herkes |
| GET | `/yonetici/adaylar` | Takma ad, deneme sayısı, son tarih | yönetici |
| GET | `/yonetici/aday/{participant_id}` | Adayın `/gecmis` görünümü; sonuçlara tıklanır | yönetici |
| POST | `/yonetici/aday/{participant_id}/ad` | Takma adı değiştirir (`nickname`); hata 400, aday yoksa 404 | yönetici |
| POST | `/yonetici/aday/{participant_id}/sil` | Adayı denemeleri ve AI yorumlarıyla tek işlemde siler; aday yoksa 404 | yönetici |
| GET | `/robots.txt` | `Disallow: /` | herkes |
| GET | `/saglik` | `ok` döner; Render sağlık kontrolü için | herkes |

- **Oturum:** Starlette `SessionMiddleware` ile imzalı çerez kullanılır. İçinde `participant_id` ya da `is_admin` tutulur. Çerez `HttpOnly`, `SameSite=Lax`; üretimde `Secure`.
- **Yetki kontrolü:** Tek bir yardımcı fonksiyonda yapılır. Başkasının `public_id`'sine erişimde 404 döner (403 değil). Böyle bir denemenin var olduğu bile belli olmaz.
- **Arama motorları:** Her sayfanın `<head>` kısmında `<meta name="robots" content="noindex, nofollow">` bulunur.

## 6. Konfigürasyon

`src/config.py` şablonuna eklenecek alanlar. Değerler `ikna_muzakere_secrets` JSON'ından gelir.

| Grup | Alan | Not |
|---|---|---|
| Postgres | `PG_USER`, `PG_PASSWORD`, `PG_HOST`, `PG_PORT`, `PG_DATABASE`, `PG_SCHEMA` (mevcut) + `PG_SSLMODE: str = "require"` | Neon bilgileri girilince şirket RDS bilgileri `.env`'den çıkarılır |
| Web | `SESSION_SECRET: str`, `ADMIN_PASSWORD: str`, `COOKIE_SECURE: bool = True` | yerelde `COOKIE_SECURE=false` |
| Gemini | `GEMINI_API_KEY: Optional[str] = None`, `GEMINI_MODEL: str` | anahtar yoksa canlı yorum düğmesi gizlenir; model adı uygulama sırasında güncel ücretsiz modelden seçilir |

## 7. Bağımlılıklar (eklemeden önce onay gerekir)

| Paket | Neden | Durum |
|---|---|---|
| `fastapi`, `uvicorn` | web sunucusu | kurulu (0.116.1 / 0.38.0) |
| `jinja2` | şablonlar | yeni |
| `python-multipart` | form verisi | yeni |
| `itsdangerous` | `SessionMiddleware` imzası | yeni |
| `sqlalchemy`, `psycopg[binary]`, `alembic` | veritabanı, migration | yeni |
| `google-genai` | Gemini | yeni |
| `pytest`, `httpx` | test ve `TestClient` | yeni (yalnızca geliştirme) |

Sürümler kurulum anında tam sürümle (`==`) yazılır.

## 8. Dağıtım

- **Vercel Hobby (ücretsiz):** GitHub'daki gizli `AhmettUsta/ikna_muzakere` reposuna bağlı; `main`'e her push otomatik yayınlanır. Adres: `https://ikna-muzakere.vercel.app`.
  - `api/index.py`: `src/`'yi yola ekler, çalışma klasörünü geçici klasöre alır (proje klasörü salt okunur; logger `logs/` oluşturur) ve `build_default_app()` ile uygulamayı kurar.
  - `vercel.json`: `routes` ile tüm istekler fonksiyona gider; dosya sisteminden önce işlendiği için repo dosyaları (içerik JSON'ları vb.) statik sunulmaz. Fonksiyon bölgesi `fra1` (Neon ile aynı bölge).
  - `.vercelignore`: `docs/`, `plans/`, `tests/`, `migrations/` vb. yayına girmez.
  - Ortam değişkeni yalnızca `ikna_muzakere_secrets` (tek satırlık JSON, "Secret" türünde). Değişince **Redeploy** gerekir.
- **Migration:** Vercel'de çalışmaz; şema değiştiğinde yerelden `python3 -m alembic upgrade head` çalıştırılır (havuzsuz adresi otomatik kullanır).
- **Neon:** Ücretsiz proje, `neondb` veritabanı, `ikna_muzakere` şeması.
- **Soğuk başlangıç:** Bir süre istek gelmezse fonksiyon ve Neon uyur; ilk istek birkaç saniye sürebilir.
- **Docker:** `Dockerfile` yerel ya da başka bir barındırma için durur; Vercel kullanmaz.
- **Yerelde çalıştırma:** `PYTHONPATH=src python3 -m uvicorn main:app --reload` ve `.env`. Geliştirme de aynı Neon veritabanını kullanır.

## 9. Test stratejisi

| Katman | Ne test edilir | Dış bağımlılık |
|---|---|---|
| `Scorer` | Tasarım Ek A'daki örnek (9-7-6-3-5); seviye sınırları (eşiğe eşit, bir altı, bir üstü); göreli sıralama ve eşitlik kuralı; eksik, fazla ve geçersiz cevap | yok |
| `ContentStep` | Gerçek içerik dosyalarının doğrulamadan geçmesi; bozuk örnek dosyalarda anlamlı hata | geçici dosyalar (`tmp_path`) |
| `PinSecurity` | Doğru ve yanlış PIN; aynı PIN için farklı tuz; kilitleme süresi ve sayaç sıfırlanması | yok |
| `TestService` | Kayıt (alınmış takma ad), giriş (kilit), testi bitirme, canlı yorumun bir kez üretilmesi, Gemini hatasında anlamlı sonuç | `DatabaseStep` ve `GeminiStep` mock |
| web | Route'ların yetki kuralları: başkasının sonucu 404, yönetici erişimi, `noindex` ve `robots.txt` | `TestService` mock, `TestClient` |
| `DatabaseStep` | Gerçek bir veritabanına karşı küçük duman testi; yalnızca bayrakla çalışır, varsayılan test koşusunda atlanır | Neon (isteğe bağlı) |
