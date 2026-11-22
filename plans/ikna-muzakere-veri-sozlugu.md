# Müzakere Tarzı Testi — Veri Sözlüğü

**Sürüm: v2 — 2026-11-22 19:40**

**Sürüm notları**

- v2 — `POST /yonetici` kaldırıldı; yönetici `POST /giris` ile girer.
- v1 — İlk veri sözlüğü: veritabanı tabloları (mimari §4'ten taşındı), içerik dosyaları, form alanları, oturum, config alanları.

**İlgili dokümanlar:** [Tasarım](ikna-muzakere-tasarim.md) · [Mimari](ikna-muzakere-mimari.md) · [Plan](ikna-muzakere-plan.md)

Projenin okuduğu ve yazdığı her verinin alan düzeyindeki tanımı. Şema ya da alan değişince güncellenir.

## 1. Adlandırma kuralları

- **Tarz anahtarları** (`StyleKey`), bu sırayla: `rekabet`, `isbirligi`, `uzlasma`, `kacinma`, `iltifat`. Eşitliklerde de bu sıra kullanılır (`STYLE_ORDER`).
- **Seviyeler** (`Level`): `yuksek`, `orta`, `dusuk`.
- **Takma ad anahtarı** (`nickname_key`): görünen ad kırpılır, Türkçe `I → ı`, `İ → i` elle eşlenir, sonra küçük harfe çevrilir. "Ali", " ali ", "ALİ" aynı kişidir (`security.normalize_nickname`).
- **Deneme adresi:** URL'de sıralı `id` değil `public_id` (UUID) kullanılır.
- **Profil anahtarı:** `<baskın>__<en az>` (ör. `rekabet__kacinma`).

## 2. Kaynak veriler (okunan)

Tüm içerik `src/content/` altında, repoda durur; `ContentStep` açılışta yükler ve doğrular. Değişince kod değişmez.

### 2.1 `questions.json` — 30 soru

Liste, her eleman:

| Alan | Tip | Açıklama |
|---|---|---|
| `no` | int | Soru numarası, 1–30 |
| `a` | str | A seçeneğinin metni |
| `b` | str | B seçeneğinin metni |

### 2.2 `scoring.json` — tarzlar, eşikler, cevap anahtarı

| Alan | Tip | Açıklama |
|---|---|---|
| `styles[].key` | StyleKey | Tarz anahtarı |
| `styles[].name` | str | Görünen ad (ör. "Rekabetçi") |
| `styles[].high` | int | Bu puan ve üstü `yuksek` |
| `styles[].low` | int | Bu puan ve altı `dusuk`; arası `orta` |
| `styles[].x`, `styles[].y` | int | SVG grafikteki konum |
| `key["<no>"]["A" \| "B"]` | StyleKey | Hangi cevabın hangi tarza puan verdiği (tasarım Ek A) |

### 2.3 `sunum/<tarz>.json` — eğitim sunumu metinleri

| Alan | Tip | Açıklama |
|---|---|---|
| `style` | StyleKey | Tarz |
| `bolumler[].tur` | SectionType | `davranis`, `uygun`, `uygun_degil`, `siz_iseniz`, `karsi_taraf` |
| `bolumler[].baslik` | str | Kart başlığı |
| `bolumler[].maddeler` | list[str] | Sunumdan birebir maddeler |

### 2.4 `sunum/tavsiyeler.json` — seviyeye özel tavsiyeler

`<tarz>.<dusuk | orta>` → `list[str]`; bölüm başına en fazla 4 madde (`Content.sunum_tavsiye`).

### 2.5 `kaynakli/` — AI destekli (kaynaklı) yorumlar

| Dosya | Yapı | Açıklama |
|---|---|---|
| `kaynaklar.json` | liste: `id`, `kaynakca`, `ozet` | 10 doğrulanmış kaynak (ör. `thomas-kilmann-1974`) |
| `bloklar.json` | `<tarz>.<seviye>` → `metin`, `kaynaklar` | 15 tarz–seviye bloğu |
| `bolumler.json` | `<tarz>.<uygun \| uygun_degil \| karsi_taraf>` → `metin`, `kaynaklar` | AI sekmesindeki düz yazı bölümleri |
| `profiller.json` | `<baskın>__<en az>` → `baslik`, `giris`, `guclu`, `zayif`, `oneri`, `kaynaklar` | 20 profil metni |

`kaynaklar` alanları `kaynaklar.json`'daki `id`'lere atıf yapar.

## 3. Hedef veriler (yazılan)

Neon PostgreSQL, şema `ikna_muzakere` (`PG_SCHEMA`). Tablolar şemasız tanımlanır, şema `build_engine` içinde `schema_translate_map` ile verilir. Migration: `migrations/versions/0001_ilk_sema.py`.

### 3.1 `participants` — adaylar

| Sütun | Tip | Kısıt | Açıklama |
|---|---|---|---|
| `id` | serial | PK | |
| `nickname` | varchar(30) | NOT NULL | Görünen takma ad, 2–30 karakter |
| `nickname_key` | varchar(30) | NOT NULL, UNIQUE | Benzersizlik anahtarı (§1) |
| `pin_hash` | bytea | NOT NULL | scrypt özeti (N=2^14, r=8, p=1, 32 bayt) |
| `pin_salt` | bytea | NOT NULL | 16 baytlık tuz |
| `failed_pins` | smallint | NOT NULL, varsayılan 0 | Art arda hatalı PIN sayısı |
| `locked_until` | timestamptz | NULL | 5 hatalı denemede 15 dakika kilit |
| `created_at` | timestamptz | NOT NULL, varsayılan now() | |

### 3.2 `attempts` — test denemeleri

| Sütun | Tip | Kısıt | Açıklama |
|---|---|---|---|
| `id` | serial | PK | |
| `public_id` | uuid | NOT NULL, UNIQUE | URL'de kullanılan kimlik |
| `participant_id` | int | NOT NULL, FK → `participants.id` | |
| `answers` | char(30) | NOT NULL | Ör. `ABBAB…`; i. karakter i. sorunun cevabı |
| `score_rekabet` | smallint | NOT NULL | |
| `score_isbirligi` | smallint | NOT NULL | |
| `score_uzlasma` | smallint | NOT NULL | |
| `score_kacinma` | smallint | NOT NULL | |
| `score_iltifat` | smallint | NOT NULL | |
| `created_at` | timestamptz | NOT NULL, varsayılan now() | |

İndeks: `ix_attempts_participant_created (participant_id, created_at)`.

Puanlar cevaplardan yeniden hesaplanabilir ama ayrıca saklanır: yönetici listesi hızlı açılır, içerik ileride değişse bile eski sonuçlar korunur. Seviyeler saklanmaz, gösterimde eşiklerden hesaplanır.

### 3.3 `ai_comments` — canlı Gemini yorumları

| Sütun | Tip | Kısıt | Açıklama |
|---|---|---|---|
| `attempt_id` | int | PK, FK → `attempts.id` | Deneme başına en fazla bir yorum |
| `model` | varchar(60) | NOT NULL | Kullanılan Gemini modeli |
| `text` | text | NOT NULL | Üretilen yorum |
| `created_at` | timestamptz | NOT NULL, varsayılan now() | |

Aday silinince denemeleri ve yorumları tek işlemde silinir.

## 4. Türetilmiş alanlar

| Alan | Kural | Kod |
|---|---|---|
| Tarz puanı | Cevap anahtarına göre her tarzın aldığı cevap sayısı; toplam her zaman 30 | `Scorer.count` |
| Seviye | `puan ≥ high` → `yuksek`, `puan ≤ low` → `dusuk`, arası `orta` | `scoring.py` |
| Göreli puan | `(puan − low) / (high − low)` | `scoring.py` |
| Baskın tarz | En yüksek göreli puan; eşitlikte `STYLE_ORDER` | `ScoreResult.dominant` |
| En az kullanılan | Baskın dışındaki en düşük göreli puan; eşitlikte `STYLE_ORDER` | `ScoreResult.least` |
| Tarih gösterimi | UTC saklanır, Türkiye saatiyle (UTC+3) gösterilir | web katmanı |

## 5. Form ve oturum alanları

| Route | Alan | Kural |
|---|---|---|
| `POST /kayit` | `nickname`, `pin`, `pin_again` | Takma ad §1; PIN tam 4 karakter harf / rakam (`[A-Za-z0-9]{4}`), iki PIN aynı |
| `POST /giris` | `nickname`, `pin` | Kilit kuralı: 5 hatada 15 dakika. `nickname` = `ADMIN_USERNAME` ise `pin` alanı yönetici şifresi olarak denetlenir (yönetici kilidiyle ortak) |
| `POST /test` | `q1` … `q30` | Her biri `A` ya da `B`; eksikse form doldurulmuş cevaplarla geri gelir |
| `POST /yonetici/aday/{id}/ad` | `nickname` | Takma ad kuralları; çakışmada 400 |

Oturum (imzalı çerez, `SessionMiddleware`): `participant_id` (aday) ya da `is_admin` (yönetici).

## 6. Durum ve kod değerleri

| Değer | Anlamı |
|---|---|
| `SectionType` | `davranis`, `uygun`, `uygun_degil`, `siz_iseniz`, `karsi_taraf` |
| `AiSectionType` | `uygun`, `uygun_degil`, `karsi_taraf` (AI sekmesinde düz yazı) |
| 404 (sonuç) | Başkasının denemesi ya da olmayan deneme; varlığı belli edilmez |

## 7. Konfigürasyon sözlüğü (`ikna_muzakere_secrets`)

| Alan | Tip | Zorunlu | Açıklama |
|---|---|---|---|
| `VERSION` | str | hayır | Varsayılan `1.0.0` |
| `DEBUG_MODE` | bool | hayır | Varsayılan `false` |
| `LOG_LEVEL` | DEBUG / INFO / WARNING / ERROR / CRITICAL | evet | |
| `LOG_TO_FILE` | bool | hayır | `logs/log.log`; Vercel'de kapalı kalmalı (salt okunur) |
| `PG_USER`, `PG_PASSWORD`, `PG_HOST`, `PG_DATABASE`, `PG_SCHEMA` | str | evet | `PG_HOST` Neon'un havuzlu (`-pooler`) adresi |
| `PG_PORT` | int | hayır | Varsayılan `5432` |
| `PG_SSLMODE` | str | hayır | Varsayılan `require` |
| `SESSION_SECRET` | str | evet | Oturum çerezi imzası |
| `ADMIN_USERNAME` | str | evet | Yönetici adı |
| `ADMIN_PASSWORD` | str | evet | Yönetici şifresi |
| `COOKIE_SECURE` | bool | hayır | Varsayılan `true`; yerelde `false` |
| `LIVE_COMMENT_ENABLED` | bool | hayır | Varsayılan `false`; kapalıysa kişiselleştir kutusu tıklanamaz |
| `GEMINI_API_KEY`, `GEMINI_MODEL` | str \| null | hayır | Biri boşsa canlı yorum kapalı |

## 8. Veri kalitesi kontrolleri

`ContentStep` açılışta içeriği doğrular, hata varsa uygulama başlamaz (`ContentError`):

- `questions.json`: 1–30 arası sorular eksiksiz, boş şık yok.
- `scoring.json`: tarzlar `STYLE_ORDER` sırasında; her tarzda `low < high`; her soru için A ve B var ve bilinen bir tarza işaret ediyor.
- `sunum/<tarz>.json`: yalnızca bilinen bölüm türleri, her tür beklenen sayıda (`EXPECTED_SECTION_COUNTS`); her bölümde en az bir, en fazla 4 madde.
- `tavsiyeler.json`: her tarz için `dusuk` ve `orta` var; boş madde yok, en fazla 4 madde.
- `kaynaklar.json`: boş değil, kimlikler tekrar etmiyor.
- `bloklar.json`: her tarz–seviye var ve tam bir "Gelişim için" paragrafı içeriyor.
- `bolumler.json` ve `profiller.json`: her kayıt var, metin boş değil, en az bir kaynağa dayanıyor ve tanımsız kaynak kullanmıyor.
