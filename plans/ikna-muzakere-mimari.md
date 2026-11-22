# Müzakere Tarzı Testi — Mimari

**Sürüm: v11 — 2026-11-22 19:40**

**Kod commit'i: `4d6ee0a` — 2026-11-22** _(dokümanların en son eşitlendiği commit; AGENTS.md §6)_

**Sürüm notları**

- v11 — Ayrı giriş ekranı (tasarım v15): `/` giriş yapmış kişiyi yönlendirir, `/yonetici` yalnızca yönlendirme yapar (`POST /yonetici` ve `yonetici_giris.html` kaldırıldı); yönetici sayfaları oturumsuz istekte `/`'a yönlenir.
- v10 — Teknik mimari PDF'i sade, kutulu akış diyagramı olarak yeniden çizildi.
- v9 — Topoloji ikiye ayrıldı: teknik mimari PDF'i (geliştirici) ve ürün tanıtımı PDF'i (sunum); Mermaid, draw.io ve PNG kaldırıldı.
- v8 — Yeni şablon düzeni: topoloji (Mermaid + draw.io / PNG / PDF) ve numaralı akış adımları; kod içi akış; tablo sütunları ve config alanları veri sözlüğüne taşındı; riskler bölümü. Koda göre düzeltmeler: `PinHasher` / `LockoutPolicy` adları, `kaynaklar.md` ve `static/robots.txt` yok, Render atıfları kaldırıldı, `api/index.py` artık çalışma klasörünü değiştirmiyor (logger log yolunu proje köküne sabitliyor).
- v7 — `sunum/tavsiyeler.json`: düşük ve orta seviye tavsiye maddeleri (`Content.sunum_tavsiye`), bölüm başına en fazla 4 madde denetimi.
- v6 — Yönetici için ad değiştirme ve silme route'ları; `DatabaseStep.rename_participant`, `delete_participant`, `ParticipantMissing`.
- v5 — `kaynakli/bolumler.json` (tarz başına uygun / uygun değil / karşı taraf düz yazısı); profil alanları giriş / güçlü / zayıf / öneri; AI destekli sekme için ayrı kart modeli (`AiCard`).
- v4 — Kaçınmacı istisnası kalktı: her tarzda her bölüm türünden tam bir tane; bölüm başına en fazla 4 madde denetimi.
- v3 — Barındırma Render yerine Vercel (Render'a giriş yapılamadı); canlıda doğrulandı.
- v2 — İçerik doğrulaması tür bazlı bölüm listesine göre güncellendi (Kaçınmacı istisnası); geliştirme veritabanı da Neon.
- v1 — İlk mimari: bileşenler, klasör yapısı, veri modeli, sayfalar, dağıtım, test stratejisi.

**İlgili dokümanlar:** [Tasarım](ikna-muzakere-tasarim.md) · [Veri sözlüğü](ikna-muzakere-veri-sozlugu.md) · [Plan](ikna-muzakere-plan.md)

---

## 1. Genel görünüm

Aday tarayıcıdan testi çözer, sonucunu ve yorumlarını görür; yönetici adayları yönetir. Uygulama Vercel'de tek bir Python sunucusuz fonksiyonu olarak çalışan bir FastAPI uygulamasıdır. Veriler Neon PostgreSQL'de, içerik (sorular, anahtar, metinler) repodaki JSON dosyalarında durur; canlı yorum için isteğe bağlı olarak Google Gemini çağrılır.

- **Tek süreç.** Arka planda iş yok; her şey istek–cevap şeklinde çalışır.
- **İçerik koddan ayrı.** Sorular, anahtar, eşikler ve metinler `src/content/` altında veri dosyası olarak durur; içerik değişince kod değişmez. `data/` `.gitignore`'da olduğu ve Vercel repodan yayın aldığı için içerik oraya konmaz.

### 1.1 Görseller

| Belge | Kime | Ne gösterir |
|---|---|---|
| [Teknik mimari (PDF)](ikna-muzakere-teknik-mimari.pdf) | geliştirici | Kutulu akış diyagramı: aday / yönetici → Vercel → route'lar → TestService → step'ler → içerik, Neon, Gemini; altta GitHub yayını ve Alembic migration. İstek akışları ve hata davranışı §1.2'de |
| [Ürün tanıtımı (PDF)](ikna-muzakere-urun-tanitimi.pdf) | yönetici, sunum | 6 sayfa: problem, kullanıcı yolculuğu, sade çalışma şeması, güven ve maliyet, rakamlar |

Kaynaklar aynı adlı `.html` dosyalarıdır; PDF `python3 ~/Desktop/YH/agents-md/araclar/pdf_yap.py plans/ikna-muzakere-teknik-mimari.html plans/ikna-muzakere-urun-tanitimi.html` ile üretilir.

### 1.2 Akış adımları

| # | Ne olur | Kod | Veri / protokol | Hata olursa |
|---|---|---|---|---|
| 0 | Aday siteye girer | tarayıcı | HTTPS; imzalı oturum çerezi (`HttpOnly`, `SameSite=Lax`, üretimde `Secure`) | — |
| 1 | Vercel her isteği fonksiyona verir, uygulama kurulur | `api/index.py`, `main.build_default_app()` | `vercel.json` `routes` (repo dosyaları statik sunulmaz) | İçerik doğrulanamazsa uygulama açılmaz |
| 2 | Kayıt / giriş: takma ad + 4 karakter PIN; yönetici aynı formdan da girebilir | `routes_aday.register` / `login`, `TestService.register` / `login`, `PinHasher`, `LockoutPolicy` | `participants` (scrypt özeti, hatalı deneme sayacı) | 5 hatada 15 dk kilit (429); alınmış takma ad 400 |
| 3 | Sorular, anahtar ve metinler açılışta yüklenip doğrulanır | `ContentStep.load` | `src/content/*.json` | `ContentError` → uygulama açılmaz |
| 4 | Test gönderimi: 30 cevap puanlanır, deneme kaydedilir | `routes_aday` `POST /test`, `TestService.submit`, `Scorer.count`, `DatabaseStep.create_attempt` | form `q1`…`q30` → `attempts` | Eksik / hatalı cevapta form cevaplarla geri gelir |
| 5 | Sonuç sayfası: puan, seviye, SVG grafik, sunum ve kaynaklı yorum sekmeleri | `TestService.result_view`, `presentation.py`, `chart.py` | `attempts` | Başkasının ya da olmayan deneme → 404 |
| 6 | Canlı yorum (isteğe bağlı) Gemini'den istenir | `TestService.live_comment`, `GeminiStep.generate` | HTTPS; puan + seviye + kaynak paketiyle prompt | `LiveCommentUnavailable` → kişiye mesaj, sayfanın geri kalanı çalışır |
| 7 | Yorum kaydedilir; sonraki isteklerde kayıtlı yorum döner | `DatabaseStep.save_ai_comment` / `get_ai_comment` | `ai_comments` | Eşzamanlı iki istekte ilk kaydedilen geçerli |
| 8 | Yönetici: aday listesi, aday geçmişi, ad değiştirme, silme | `routes_yonetici`, `TestService.admin_*` | `participants`, `attempts`, `ai_comments` | Aday yoksa 404; ad çakışmasında 400 |
| 9 | Yayın: GitHub'a push, Vercel otomatik yayınlar | — | `main` dalı | — |
| 10 | Şema değişikliği yerelden uygulanır | `alembic upgrade head` | Neon'un havuzsuz adresi | Vercel'de migration çalışmaz |

Veritabanına her erişimde bağlantı TLS (`sslmode=require`) ve Neon'un havuzlu (`-pooler`) adresiyle kurulur. Veritabanına ulaşılamazsa (`DatabaseUnavailable`) kişiye 503 ile "Şu anda hizmet veremiyoruz" sayfası gösterilir.

## 2. Klasör yapısı

```
api/
  index.py             # Vercel giriş noktası: src/'yi yola ekler, build_default_app()
src/
  config.py            # şablon + Postgres / Web / Gemini alanları (veri sözlüğü §7)
  logger.py            # şablon; log yolu proje kökü, yalnızca LOG_TO_FILE açıkken logs/ oluşturur
  main.py              # create_app, build_default_app, hata sayfaları; uvicorn main:app
  service.py           # TestService: step'leri __init__'te alır (DI), akışları yönetir
  scoring.py           # Scorer: puan, seviye, göreli sıralama (DB'siz, saf)
  presentation.py      # sonuç sayfası kartları (sunum ve AI destekli sekmeler)
  chart.py             # SVG grafik
  security.py          # PinHasher (scrypt), LockoutPolicy, takma ad ve PIN kuralları
  content_types.py     # içerik dataclass'ları ve sabit anahtarlar (StyleKey, Level …)
  step_content.py      # ContentStep: src/content dosyalarını yükler ve doğrular
  step_database.py     # DatabaseStep: katılımcı / deneme / AI yorumu kayıtları, build_engine
  step_gemini.py       # GeminiStep: canlı yorum isteği
  db_models.py         # SQLAlchemy 2.0 deklaratif modeller
  web/
    deps.py            # servis erişimi, oturum / yetki yardımcıları, render, Markdown, tarih biçimi
    routes_aday.py
    routes_yonetici.py
    templates/         # Jinja2: base, giris, test, sonuc, gecmis, hata, _kart, yonetici_adaylar
    static/            # style.css, test.js (soru geçişi)
  content/
    questions.json     # 30 soru
    scoring.json       # tarzlar, eşikler, grafik konumları, cevap anahtarı
    sunum/             # tarz başına sunum metinleri + tavsiyeler.json
    kaynakli/          # kaynaklar, bloklar, bölümler, profiller
migrations/            # Alembic
tests/                 # pytest
plans/                 # tasarım, mimari, veri sözlüğü, plan; teknik mimari ve ürün tanıtımı (html + pdf)
docs/                  # soru fotoğrafları ve eğitim sunumu (kaynak malzeme)
Dockerfile, .dockerignore, alembic.ini, vercel.json, .vercelignore
```

## 3. Bileşenler

| Bileşen | Dosya | Sorumluluk | Dış sistem |
|---|---|---|---|
| `ContentStep` | `step_content.py` | İçerik dosyalarını açılışta bir kez yükler ve doğrular (kurallar: veri sözlüğü §8). Doğrulama hatasında uygulama açılmaz. | dosya sistemi |
| `Scorer` | `scoring.py` | 30 cevaptan beş puanı, seviyeleri, göreli puanları, baskın ve en az kullanılan tarzı hesaplar. Geçersiz girdide `ValueError`. | — |
| `PinHasher` | `security.py` | PIN'i `hashlib.scrypt` ile tuz ekleyerek özetler ve sabit süreli karşılaştırmayla doğrular. | — |
| `LockoutPolicy` | `security.py` | 5 yanlış denemede 15 dakika kilit. | — |
| `DatabaseStep` | `step_database.py` | Katılımcı oluşturma ve bulma, hatalı deneme sayacı (tek UPDATE ile atomik), deneme kaydı ve listeleri, AI yorumu, yönetici işlemleri. Her yazma tek transaction. | Neon PostgreSQL |
| `GeminiStep` | `step_gemini.py` | Prompt'u gönderir, metni döndürür; zaman aşımı ve kota hatalarını `LiveCommentUnavailable`'a çevirir. | Google Gemini API |
| `TestService` | `service.py` | Orkestratör: kayıt, giriş, test, sonuç, geçmiş, canlı yorum, yönetici. Step'leri parametre olarak alır. | yukarıdakiler |
| web katmanı | `web/` | Formu okur, `TestService`'i çağırır, şablonu döndürür; iş mantığı içermez. | — |

## 4. Kod içi akış

`TestService` metodları (§1.2'deki sistem adımlarının kod karşılığı):

1. `register(nickname, pin, pin_again)` → takma ad ve PIN kuralları → `PinHasher.hash` → `DatabaseStep` katılımcı oluşturur → `participant_id`.
2. `login(nickname, pin)` → kilit kontrolü (`LockoutPolicy.is_locked`) → `PinHasher.verify` → hatalıysa sayaç artar (`after_failure`).
3. `submit(participant_id, answers)` → `Scorer.count` → `DatabaseStep.create_attempt` → `public_id`.
4. `result_view(public_id, viewer)` → deneme okunur, yetki denetlenir → `Scorer.from_scores` → `presentation` kartları ve `chart` SVG.
5. `history_view(participant_id)` → katılımcının denemeleri.
6. `live_comment(public_id, participant_id)` → kayıtlı yorum varsa döner; yoksa `GeminiStep.generate` → `save_ai_comment`.
7. Yönetici: `is_admin_name`, `check_admin`, `admin_participants`, `admin_rename`, `admin_delete`.

## 5. Veri modeli

Şema `ikna_muzakere`: `participants` 1 — n `attempts` 1 — 0..1 `ai_comments`. Sütunlar ve kısıtlar: [veri sözlüğü §3](ikna-muzakere-veri-sozlugu.md#3-hedef-veriler-yazılan).

- **Puanlar ayrıca saklanır.** Yönetici listesi hızlı açılır; içerik ileride değişse bile eski sonuçlar korunur. Seviyeler saklanmaz, gösterimde eşiklerden hesaplanır.
- **Bağlantı havuzu küçük tutulur:** `pool_size=2`, `max_overflow=2`, `pool_pre_ping=True`; Neon'un ücretsiz planında bağlantı sayısı sınırlı.
- **Şema adı koddan bağımsız:** modeller şemasız; şema `build_engine` içinde `schema_translate_map` ile verilir.

## 6. Arayüzler

| Yöntem | Yol | Ne yapar | Erişim |
|---|---|---|---|
| GET | `/` | Giriş ekranı: giriş formu açık, "Kayıt ol" ile kayıt formu. Giriş yapmış aday `/gecmis`'e, yönetici `/yonetici/adaylar`'a yönlenir | herkes |
| POST | `/kayit` | Takma ad + PIN (iki kez) → katılımcı oluşturur, oturum açar, `/test`'e yönlendirir | herkes |
| POST | `/giris` | Takma ad + PIN → doğrular (kilit kuralıyla), `/gecmis`'e yönlendirir; yönetici adıyla girilirse `/yonetici/adaylar` | herkes |
| GET | `/test` | 30 soruluk form; JavaScript her ekranda bir soru gösterir. JavaScript yoksa hepsi listelenir. | oturumlu aday |
| POST | `/test` | Cevapları puanlar ve kaydeder, `/sonuc/{public_id}`'ye yönlendirir | oturumlu aday |
| GET | `/sonuc/{public_id}` | Puan tablosu, SVG grafik, yorum sekmeleri, cevaplar, canlı yorum düğmesi | denemenin sahibi ya da yönetici |
| POST | `/sonuc/{public_id}/canli-yorum` | Gemini'den yorum alır ve kaydeder; zaten varsa kayıtlıyı döndürür | yalnızca denemenin sahibi |
| GET | `/gecmis` | En son sonuç bağlantısı, önceki denemeler, "Testi tekrar çöz" | oturumlu aday |
| POST | `/cikis` | Oturumu kapatır | herkes |
| GET | `/yonetici` | Yalnızca yönlendirme: yöneticiyse `/yonetici/adaylar`, değilse `/` (tek giriş kapısı ana formdur). Diğer yönetici adresleri de oturumsuz istekte `/`'a yönlenir | herkes |
| GET | `/yonetici/adaylar` | Takma ad, deneme sayısı, son tarih | yönetici |
| GET | `/yonetici/aday/{participant_id}` | Adayın `/gecmis` görünümü | yönetici |
| POST | `/yonetici/aday/{participant_id}/ad` | Takma adı değiştirir; hata 400, aday yoksa 404 | yönetici |
| POST | `/yonetici/aday/{participant_id}/sil` | Adayı denemeleri ve AI yorumlarıyla tek işlemde siler; aday yoksa 404 | yönetici |
| GET | `/robots.txt` | `Disallow: /` | herkes |
| GET | `/saglik` | `ok` döner (sağlık kontrolü) | herkes |

- **Oturum:** Starlette `SessionMiddleware` ile imzalı çerez; içinde `participant_id` ya da `is_admin`.
- **Yetki kontrolü:** tek bir yardımcı fonksiyonda. Başkasının `public_id`'sine erişimde 404 döner (403 değil); denemenin var olduğu belli olmaz.
- **Arama motorları:** her sayfada `<meta name="robots" content="noindex, nofollow">`.
- Form alanları: [veri sözlüğü §5](ikna-muzakere-veri-sozlugu.md#5-form-ve-oturum-alanları).

## 7. Konfigürasyon

Değerler `ikna_muzakere_secrets` JSON'ından gelir (tam alan listesi: [veri sözlüğü §7](ikna-muzakere-veri-sozlugu.md#7-konfigürasyon-sözlüğü-ikna_muzakere_secrets)).

| Grup | Kullanan |
|---|---|
| `# Logging` | `logger.setup_logging` |
| `# Postgres` | `step_database.build_engine`, Alembic |
| `# Web` | `main.create_app` (oturum, çerez), yönetici girişi |
| `# Gemini` | `main.build_default_app` (`GeminiStep` yalnızca `LIVE_COMMENT_ENABLED` ve anahtar + model doluysa kurulur) |

Config yalnızca `main.py`, `step_database.py` ve `logger.py` tarafından import edilir; diğer modüller değerleri parametre olarak alır.

## 8. Bağımlılıklar

| Paket | Neden |
|---|---|
| `fastapi`, `uvicorn` | web sunucusu |
| `jinja2` | şablonlar |
| `python-multipart` | form verisi |
| `itsdangerous` | `SessionMiddleware` imzası |
| `sqlalchemy`, `psycopg[binary]`, `alembic` | veritabanı, migration |
| `google-genai`, `httpx2` | Gemini ve hata türleri (`step_gemini.py` doğrudan import eder) |
| `pydantic`, `python-dotenv` | config |
| `pytest`, `httpx` | test ve `TestClient` |

Sürümler `requirements.txt`'te tam sürümle (`==`).

## 9. Dağıtım ve işletim

- **Vercel Hobby (ücretsiz):** gizli GitHub reposuna bağlı; `main`'e her push otomatik yayınlanır. Adres: `https://ikna-muzakere.vercel.app`.
  - `api/index.py`: `src/`'yi yola ekler ve `build_default_app()` ile uygulamayı kurar.
  - `vercel.json`: `routes` ile tüm istekler fonksiyona gider; repo dosyaları statik sunulmaz. Fonksiyon bölgesi `fra1` (Neon ile aynı bölge).
  - `.vercelignore`: `docs/`, `plans/`, `tests/`, `migrations/`, `logs/` vb. yayına girmez.
  - Ortam değişkeni yalnızca `ikna_muzakere_secrets` ("Secret" türünde). Değişince **Redeploy** gerekir. Proje klasörü salt okunur olduğu için `LOG_TO_FILE` kapalı kalmalıdır.
- **Migration:** Vercel'de çalışmaz; şema değiştiğinde yerelden `python3 -m alembic upgrade head` (havuzsuz adresi otomatik kullanır).
- **Neon:** ücretsiz proje, Frankfurt, `neondb` veritabanı, `ikna_muzakere` şeması. Geliştirme de aynı veritabanını kullanır.
- **Loglama:** konsola (Vercel fonksiyon logları); dosyaya yazma yalnızca yerelde / Docker'da `LOG_TO_FILE` ile.
- **Docker:** `Dockerfile` yerel ya da başka bir barındırma için durur (`/app/logs` non-root kullanıcıya açık); Vercel kullanmaz.
- **Yerelde çalıştırma:** `PYTHONPATH=src python3 -m uvicorn main:app --reload` ve `.env`.

## 10. Test stratejisi

| Katman | Ne test edilir | Dış bağımlılık |
|---|---|---|
| `Scorer` | Tasarım Ek A'daki örnek (9-7-6-3-5); seviye sınırları; göreli sıralama ve eşitlik kuralı; eksik, fazla ve geçersiz cevap | yok |
| `ContentStep` | Gerçek içerik dosyalarının doğrulamadan geçmesi; bozuk örnek dosyalarda anlamlı hata | geçici dosyalar (`tmp_path`) |
| `PinHasher`, `LockoutPolicy` | Doğru ve yanlış PIN; aynı PIN için farklı tuz; kilit süresi ve sayaç sıfırlanması | yok |
| `TestService` | Kayıt, giriş (kilit), testi bitirme, canlı yorumun bir kez üretilmesi, Gemini hatasında anlamlı sonuç | `DatabaseStep` ve `GeminiStep` mock |
| web | Yetki kuralları: başkasının sonucu 404, yönetici erişimi, `noindex` ve `robots.txt` | `TestService` mock, `TestClient` |
| `logger` | `LOG_TO_FILE` kapalıyken log klasörü oluşmaz; açıkken `logs/log.log`'a yazar | geçici klasör |
| Dağıtım dosyaları | Vercel girişi uygulamayı kurar ve proje klasörüne yazmaz; `vercel.json` routes; Dockerfile `logs` izni | alt süreç |
| `DatabaseStep` | Gerçek veritabanına karşı duman testi; yalnızca `RUN_DB_TESTS=1` ile, varsayılan koşuda atlanır | Neon (isteğe bağlı) |

Komut: `python3 -m pytest` (`pytest.ini`: `pythonpath = src`).

## 11. Riskler ve bilinen sınırlar

- **Soğuk başlangıç:** bir süre istek gelmezse fonksiyon ve Neon uyur; ilk istek birkaç saniye sürebilir.
- **Ücretsiz plan sınırları:** Neon bağlantı ve depolama, Vercel Hobby fonksiyon süresi, Gemini kotası. Gemini kotası dolarsa yalnızca canlı yorum çalışmaz.
- **Salt okunur yayın ortamı:** Vercel'de `LOG_TO_FILE` açılırsa uygulama açılmaz.
- **Telif:** orijinal sorular ve sunum metinleri kullanılır; site `noindex` ve `robots.txt` ile arama motorlarına kapalıdır, link yalnızca tanıdıklarla paylaşılır.
- **Tek yönetici:** yönetici hesabı config'teki tek ad / şifredir; şifre değişikliği Vercel'de secret güncellemesi + Redeploy ister.
