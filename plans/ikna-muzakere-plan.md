# Müzakere Tarzı Testi — Uygulama Planı

**Sürüm: v1 — 2026-11-11 14:36**

**Sürüm notları**

- v1 — İlk plan: 12 görev, ön koşullar, genel kısıtlar, gözden geçirme odakları.

> **Uygulayıcı için:** Görevler sırayla, `superpowers:subagent-driven-development` ya da `superpowers:executing-plans` ile uygulanır. Adımlar `- [ ]` kutularıyla takip edilir.

**Amaç:** Eğitimdeki 30 soruluk çatışma tarzı testini çözdüren, puanlayan, profiline göre yorum gösteren; takma ad ve PIN ile anonim çalışan, yönetici görünümü olan ücretsiz bir web sitesi.

**Mimari:** Tek FastAPI uygulaması; sayfalar Jinja2 ile sunucuda üretilir. İş mantığı step sınıflarında, akışlar `TestService` orkestratöründe. İçerik `src/content/` altında JSON ve Markdown dosyaları olarak durur. Veritabanı Neon PostgreSQL; barındırma Render'da Docker.

**Teknoloji:** Python 3.11, FastAPI, Jinja2, SQLAlchemy 2.0, psycopg 3, Alembic, google-genai, pytest.

**Dayandığı dokümanlar:** [Tasarım](ikna-muzakere-tasarim.md) · [Mimari](ikna-muzakere-mimari.md). Uygulayıcı her ikisini de okur.

## Ön koşullar (kod yazmadan önce)

- [ ] **Paket onayı:** Aşağıdaki paketler için kullanıcıdan onay alınır (AGENTS.md P9):
  - jinja2, python-multipart, itsdangerous
  - sqlalchemy, psycopg[binary], alembic
  - google-genai
  - pytest, httpx

  Onaydan sonra `python3 -m pip install ...` ile kurulur. Kurulan sürümler `pip show` ile okunur ve `requirements.txt`'ye `==` ile yazılır; mevcut `fastapi==0.116.1` ve `uvicorn==0.38.0` de eklenir.
- [x] **Neon:** Bağlantı bilgileri `.env`'ye `PG_*` alanları olarak yazıldı: `neondb` veritabanı, `ikna_muzakere` şeması, Frankfurt. Şirket RDS bilgileri silindi; 5432 portuna erişim doğrulandı.
- [ ] **Gizli değerler:** `SESSION_SECRET`, `secrets.token_urlsafe(32)` ile üretilip `.env`'ye yazılır. `ADMIN_PASSWORD` kullanıcıya sorulur. `GEMINI_API_KEY`'i kullanıcı Google AI Studio'dan alır; bu yalnızca Görev 7'deki gerçek deneme için gerekir.

## Genel kısıtlar

- **Commit, push, dal ve worktree yok** (AGENTS.md §5–6). Her görevin son adımı "testleri çalıştır ve rapor ver"dir.
- **Testler:** Tüm testler `python3 -m pytest` ile çalışır. Görev 1'de eklenen `pytest.ini` dosyası `pythonpath = src` ayarını yapar.
- **Config yalnızca iki yerde import edilir:** `src/config.py` sadece `src/main.py` ve `src/step_database.py: build_engine` tarafından import edilir. Diğer modüller değerleri parametre olarak alır; böylece testler `.env` olmadan çalışır.
- **Tarz anahtarları ve sırası sabittir:** `rekabet`, `isbirligi`, `uzlasma`, `kacinma`, `iltifat`. Eşitlik durumlarında da bu sıra kullanılır.
- **Seviye adları:** `yuksek`, `orta`, `dusuk`.
- **Eşikler:**

  | Tarz | Yüksek (≥) | Düşük (≤) |
  |---|---|---|
  | rekabet | 8 | 3 |
  | isbirligi | 10 | 5 |
  | uzlasma | 9 | 4 |
  | kacinma | 8 | 4 |
  | iltifat | 7 | 3 |

- **Göreli puan:** `(puan − düşük) / (yüksek − düşük)`.
- **Cevap anahtarı:** Tasarım Ek A'daki tablo, değiştirilmeden kullanılır.
- **Sunum metinleri birebir aktarılır.** Yazım hataları dahil hiçbir kelime değiştirilmez; yalnızca satır sonları ve fazla boşluklar temizlenir.
- **Kullanıcıya görünen bütün metinler Türkçedir.** Her sayfada `<meta name="robots" content="noindex, nofollow">` bulunur.
- **Loglara** PIN, şifre, API anahtarı ve oturum çerezi yazılmaz.
- **Kod standartları:** AGENTS.md B kısmı (tipler, `logging`, spesifik istisnalar, `with`).

## Gözden geçirme odakları

Tasarımın açıkça yazmadığı ama gerçek kullanıcının karşılaşacağı durumlar. Her biri sorumlu görevde testle sabitlenir.

1. **Takma ad benzersizliği.** "Ali", " ali ", "ALİ" ve "ali" aynı kişi sayılır. Türkçe harfler kabul edilir. Boş ya da 30 karakterden uzun ad, anlamlı bir mesajla reddedilir → Görev 5.
2. **Eksik ya da bozuk test gönderimi.** 29 ya da 31 cevap, A/B dışında bir değer, formun iki kez gönderilmesi gibi durumlarda 500 hatası verilmez. Kişiye "Testi eksiksiz doldurun" mesajı gösterilir ve test sayfasına geri dönülür → Görev 2 ve 9.
3. **Yetkisiz erişim.** Başkasının `/sonuc/...` adresi, oturumu olmayan biri ve yönetici olmayan biri `/yonetici/...` adresine girerse 404 ya da giriş sayfası görür; veri sızmaz → Görev 9 ve 10.
4. **Canlı yorumun kullanılamaması.** Gemini anahtarı yoksa düğme görünmez. Kota dolar ya da hata olursa kişiye mesaj gösterilir ve sayfanın geri kalanı çalışır. İkinci basışta kayıtlı yorum döner, yeni istek gitmez → Görev 7 ve 8.
5. **Veritabanının uykuda ya da erişilemez olması.** Neon uyandığı sırada ilk istek yavaş gelebilir; bu kabul edilir. Bağlantı tamamen koparsa kişiye "Şu anda hizmet veremiyoruz" sayfası gösterilir, stack trace gösterilmez → Görev 6 ve 9.

---

### Görev 1: Sorular, cevap anahtarı ve içerik yükleyici

**Dosyalar:**
- Oluştur: `pytest.ini`, `src/content/questions.json`, `src/content/scoring.json`, `src/content_types.py`, `src/step_content.py`
- Test: `tests/test_step_content.py`

**Arayüzler:**
- Üretir (`src/content_types.py`):
  - `StyleKey = Literal["rekabet","isbirligi","uzlasma","kacinma","iltifat"]`
  - `STYLE_ORDER: Final[tuple[StyleKey, ...]]`
  - `Level = Literal["yuksek","orta","dusuk"]`
  - `@dataclass(frozen=True) Question(no: int, a: str, b: str)`
  - `@dataclass(frozen=True) StyleDef(key: StyleKey, name: str, high: int, low: int, x: int, y: int)` — `x`, `y`: grafikte 0–100 arası konum.
  - `@dataclass Content(questions: list[Question], styles: list[StyleDef], answer_key: dict[int, dict[str, StyleKey]])`. Görev 3 ve 4 bu sınıfa alan ekler.
  - `class ContentError(ValueError)`
- Üretir (`src/step_content.py`): `class ContentStep(root: Path)` ve `load() -> Content`. Doğrulama hatasında `ContentError` fırlatır; mesaj dosyayı ve sorunu söyler.

**İçerik formatları:**
- `questions.json`: `[{"no": 1, "a": "...", "b": "..."}, ...]`. Metinler `docs/Image.jpeg`, `Image (1).jpeg` ve `Image (2).jpeg` fotoğraflarından harfi harfine aktarılır.
- `scoring.json`:
  - `styles`: `{key, name, high, low, x, y}` listesi, `STYLE_ORDER` sırasıyla.
  - `key`: `{"1": {"A": "kacinma", "B": "iltifat"}, ...}`.
  - Tarz adları ve grafik konumları:

    | Anahtar | Ad | x | y |
    |---|---|---|---|
    | rekabet | Rekabetçi | 20 | 80 |
    | isbirligi | İşbirlikçi | 80 | 80 |
    | uzlasma | Uzlaşmacı | 50 | 50 |
    | kacinma | Kaçınmacı | 20 | 20 |
    | iltifat | İltifatkar | 80 | 20 |

- [ ] **Adım 1: Başarısız testleri yaz**
  - `test_load_real_content_passes`: Gerçek `src/content` yüklenir.
    - `len(questions) == 30`, `questions[0].a == "Problemin çözümünde sorumluluğu başkasının almasına izin verdiğim zamanlar vardır."`
    - `questions[29].b == "Problemi daima onunla paylaşırım, böylece üzerinde çalışabiliriz."`
    - `[s.key for s in styles] == list(STYLE_ORDER)`
    - Eşikler, genel kısıtlardaki tabloyla aynı.
  - `test_load_answer_key_each_style_twelve_times`: Anahtardaki 60 şıkta her tarz tam olarak 12 kez geçer. `answer_key[1] == {"A": "kacinma", "B": "iltifat"}`, `answer_key[30] == {"A": "iltifat", "B": "isbirligi"}`.
  - `test_load_missing_question_raises`: `tmp_path` altında 29 soruluk bir kopya → `ContentError`.
  - `test_load_unknown_style_in_key_raises`: Anahtarda `"X"` tarzı → `ContentError`.
  - `test_load_invalid_json_raises`: Bozuk JSON → `ContentError`. Mesajda dosya adı geçer.
- [ ] **Adım 2:** `python3 -m pytest tests/test_step_content.py -v` → FAIL (modül yok).
- [ ] **Adım 3:** `pytest.ini`, içerik dosyaları, `content_types.py` ve `ContentStep.load` yazılır. JSON `json.load` ile okunur ve `json.JSONDecodeError` ile `OSError` `ContentError`'a çevrilir. Soru numaraları 1–30 aralığında, eksiksiz ve tekrarsız olmalıdır.
- [ ] **Adım 4:** Aynı komut → PASS.
- [ ] **Adım 5:** `python3 -m pytest` tamamı yeşil. Rapor: aktarılan soru sayısı ve fotoğrafta okunması zor olan yerler, varsa.

### Görev 2: Puanlama

**Dosyalar:**
- Oluştur: `src/scoring.py`
- Test: `tests/test_scoring.py`

**Arayüzler:**
- Kullanır: `Content`, `StyleDef`, `StyleKey`, `Level`, `STYLE_ORDER` (Görev 1).
- Üretir:
  - `@dataclass(frozen=True) StyleResult(style: StyleKey, score: int, level: Level, relative: float)`
  - `@dataclass(frozen=True) ScoreResult(results: list[StyleResult], dominant: StyleKey, least: StyleKey)`. `results` listesi `STYLE_ORDER` sırasındadır.
  - `class Scorer(styles: list[StyleDef], answer_key: dict[int, dict[str, StyleKey]])`:
    - `count(answers: str) -> dict[StyleKey, int]`. `answers`, `"A"` ve `"B"` harflerinden oluşan 30 karakterlik metindir. Uzunluk ya da harf hatalıysa `ValueError` fırlatır.
    - `from_scores(scores: dict[StyleKey, int]) -> ScoreResult`
    - `score(answers: str) -> ScoreResult`, yani `from_scores(count(answers))`.

- **Baskın ve en az kullanılan tarz:**
  - `dominant`: En yüksek `relative` değerine sahip tarz. Eşitlikte `STYLE_ORDER`'da önce gelen seçilir.
  - `least`: `dominant` dışındaki tarzlar arasında en düşük `relative` değerine sahip olan. Eşitlikte yine `STYLE_ORDER`'da önce gelen seçilir.
  - Böylece `dominant` ile `least` hiçbir zaman aynı olmaz.

- [ ] **Adım 1: Başarısız testleri yaz**
  - `test_score_design_example`: `"ABBABBBBBBBBBBABAAABBBABABBABB"` şu sonucu verir:
    - Puanlar: rekabet 9, isbirligi 7, uzlasma 6, kacinma 3, iltifat 5.
    - Seviyeler: yuksek, orta, orta, dusuk, orta.
    - `dominant == "rekabet"`, `least == "kacinma"`.
  - `test_level_boundaries`: Rekabet için 8 → yuksek, 7 → orta, 4 → orta, 3 → dusuk. İşbirliği için 10 → yuksek, 5 → dusuk.
  - `test_relative_tie_uses_style_order`: Tüm göreli puanları eşit olan bir `from_scores` girdisinde `dominant == "rekabet"` ve `least == "isbirligi"`.
  - `test_count_rejects_bad_input`: `"A"*29`, `"A"*31`, `"A"*29 + "C"` ve küçük harfle `"a"*30` girdileri `pytest.raises(ValueError)` ile reddedilir. (Gözden geçirme odağı 2.)
  - `test_scores_always_sum_to_30`: `"A"*30` ve `"B"*30` için puanların toplamı 30.
- [ ] **Adım 2:** `python3 -m pytest tests/test_scoring.py -v` → FAIL.
- [ ] **Adım 3:** `scoring.py` yazılır.
- [ ] **Adım 4:** → PASS. **Adım 5:** Tüm testler yeşil; rapor verilir.

### Görev 3: Sunum metinleri

**Dosyalar:**
- Oluştur: `src/content/sunum/<tarz>.json` (5 dosya), `src/presentation.py`
- Değiştir: `src/content_types.py` (yeni tipler ve `Content.sunum` alanı), `src/step_content.py` (yükleme ve doğrulama)
- Test: `tests/test_step_content.py` (ek testler), `tests/test_presentation.py`

**Arayüzler:**
- Üretir:
  - `SectionType = Literal["davranis","uygun","uygun_degil","siz_iseniz","karsi_taraf"]`
  - `@dataclass(frozen=True) Section(tur: SectionType, baslik: str, maddeler: list[str])`
  - `Content.sunum: dict[StyleKey, list[Section]]`
  - `src/presentation.py`:
    - `@dataclass(frozen=True) SunumView(style: StyleKey, level: Level, acik: bool, not_metni: str | None, bolumler: list[Section])`
    - `sunum_view(result: StyleResult, sections: list[Section]) -> SunumView`

- **Metnin çıkarılması:** Sunum metni, `.ppt` dosyasındaki `TextCharsAtom` ve `TextBytesAtom` kayıtları okunarak çıkarılır. Bu oturumda kullanılan tek seferlik okuma betiği scratchpad'de çalıştırılır; repoya girmez. Bölüm başlıkları sunumdaki gibi yazılır:

  | Tarz | davranis | uygun | uygun_degil | karsi_taraf | siz_iseniz |
  |---|---|---|---|---|---|
  | rekabet | REKABETÇİ MÜCADELECİ DAVRANIŞ | Rekabetçi Yaklaşımın Uygun Olduğu Koşullar | Şu koşullarda uygun değildir | Rekabetçilerle ile başa çıkabilmek için | SİZ REKABETÇİ İSENİZ |
  | isbirligi | İŞBİRLİKÇİ | İşbirlikçi Yaklaşımın Uygun Olduğu Koşullar | Şu durumlarda uygun olmayacaktır | Onlarla uyum sağlayabilmek için | Siz işbirlikçi iseniz |
  | uzlasma | UZLAŞMACI | Uzlaşmacı Yaklaşımın Uygun Olduğu Koşullar | Şu durumlarda etkili olamayacaktır | Uzlaşmacı ile başa çıkabilmek için | Eğer siz uzlaşmacı iseniz |
  | kacinma | KAÇINMACI | (1) Kaçınmacı yaklaşımın gerekli olduğu durumlar, (2) Kaçınmacı Yaklaşımın Uygun Olduğu Koşullar | — | Karşı taraf kaçınmacı ise | Siz Kaçınmacı İseniz |
  | iltifat | DÜZELTMECİ İLTİFATKAR-TAVİZKÂR | Tavizkâr Yaklaşımın Uygun Olduğu Koşullar | Şu durumlarda uygun olmayacaktır | Karşı taraf iltifatkar ise Yararlanma yolları | Eğer siz iltifatkar iseniz |

- **`sunum_view` gösterim kuralı:**
  - `yuksek`: `acik=True`, tüm bölümler gösterilir. `siz_iseniz` bölümü listenin başına alınır; diğerleri sunumdaki sırayla gelir.
  - `dusuk`: `acik=True`, `not_metni="Bu tarzı az kullanıyorsunuz. Şu durumlarda işe yarayabilir:"`. Yalnızca `uygun` türündeki bölümler gösterilir.
  - `orta`: `acik=False`, tüm bölümler sunumdaki sırayla gösterilir.

- [ ] **Adım 1: Başarısız testleri yaz**
  - `test_sunum_section_types_per_style`: Kaçınma tarzında `uygun` türünden 2 bölüm ve hiç `uygun_degil` bölümü bulunur. Diğer dört tarzda her türden tam olarak 1 bölüm bulunur.
  - `test_sunum_spot_text`: Rekabet `davranis` bölümünün ilk maddesi `"Diğer tarafın ne hissettiğiyle ilgilenmezler"`. Kaçınma `siz_iseniz` bölümünün ilk maddesi `"Yutkunmayın,"`.
  - `test_sunum_missing_type_raises`: Rekabet dosyasından `uygun_degil` bölümü çıkarılınca `ContentError` fırlatılır.
  - `test_sunum_view_high_puts_siz_iseniz_first`, `test_sunum_view_low_shows_only_uygun` (kaçınma için 2 bölüm), `test_sunum_view_mid_collapsed`.
- [ ] **Adım 2:** → FAIL. **Adım 3:** Dosyalar ve kod yazılır. **Adım 4:** → PASS. **Adım 5:** Tüm testler yeşil; rapor verilir.

### Görev 4: Kaynak paketi ve kaynaklı yorumlar (kullanıcı onayı ile biter)

**Dosyalar:**
- Oluştur: `src/content/kaynakli/kaynaklar.json`, `src/content/kaynakli/bloklar.json`, `src/content/kaynakli/profiller.json`
- Değiştir: `src/content_types.py`, `src/step_content.py`
- Test: `tests/test_step_content.py` (ek testler)

**Arayüzler:**
- Üretir:
  - `@dataclass(frozen=True) Source(id: str, kaynakca: str, ozet: str)`
  - `@dataclass(frozen=True) Block(metin: str, kaynaklar: list[str])` — `metin` Markdown'dır; `kaynaklar` listesi `Source.id` değerlerinden oluşur.
  - `@dataclass(frozen=True) ProfileText(baslik: str, metin: str, kaynaklar: list[str])`
  - `Content.sources: list[Source]`
  - `Content.blocks: dict[tuple[StyleKey, Level], Block]`
  - `Content.profiles: dict[tuple[StyleKey, StyleKey], ProfileText]` — anahtar `(dominant, least)` biçimindedir.
- **JSON anahtarları:**
  - `bloklar.json`: `{"rekabet": {"yuksek": {...}, "orta": {...}, "dusuk": {...}}, ...}`
  - `profiller.json`: `{"rekabet__kacinma": {...}, ...}` — 20 anahtar; her biri birbirinden farklı iki tarzın sıralı ikilisidir.

- [ ] **Adım 1: Araştır.** Tasarım 7.2'deki aday kaynaklar web aramasıyla doğrulanır:
  - Ölçüt: eser gerçekten var ve kaynakça bilgisi doğru (yazar, yıl, başlık, yayıncı ya da dergi, varsa DOI).
  - Her kaynak için 3–6 cümlelik bir özet yazılır.
  - Doğrulanamayan kaynak pakete girmez; raporda bunlar listelenir.
- [ ] **Adım 2: Başarısız testleri yaz**
  - `test_blocks_complete`: 15 blok var ve her bloğun `kaynaklar` listesi en az 1 eleman içerir.
  - `test_profiles_complete`: 20 profil var ve `dominant != least`.
  - `test_unknown_source_id_raises`: Tanımsız bir kaynak kimliği `ContentError` verir.
  - `test_sources_have_citation`: Her `Source.kaynakca` alanı bir 4 haneli yıl içerir.
- [ ] **Adım 3:** → FAIL.
- [ ] **Adım 4: Metinleri yaz.**
  - Bloklar 120–200 kelime olur ve tarzın akademik tanımını, güçlü ve riskli yönlerini, gelişim önerilerini içerir.
  - Profil metinleri 100–180 kelime olur.
  - Metinlerde kaynakta açıkça yer almayan sayısal iddia ya da alıntı bulunmaz. Kişilik tanısı dili kullanılmaz ("siz şusunuz" değil, "bu profil çoğunlukla şunu tercih eder").
- [ ] **Adım 5:** → PASS. Tüm testler yeşil.
- [ ] **Adım 6: DUR — kullanıcı onayı.** Kaynak listesi, 15 blok ve 20 profil metni okunabilir bir özet halinde kullanıcıya sunulur. Kullanıcının istediği düzeltmeler yapılır. Onay gelmeden Görev 9'daki kaynaklı yorum sekmesi yayına alınmaz; diğer görevlere devam edilebilir.

### Görev 5: PIN güvenliği ve takma ad

**Dosyalar:**
- Oluştur: `src/security.py`
- Test: `tests/test_security.py`

**Arayüzler:**
- Üretir:
  - `normalize_nickname(raw: str) -> tuple[str, str]` → `(gösterim, anahtar)`.
    - Baştaki ve sondaki boşluklar silinir; içteki ardışık boşluklar tek boşluğa indirilir.
    - Uzunluk 2–30 karakter olmalıdır.
    - İzin verilen karakterler: harfler (Türkçe dahil), rakamlar, boşluk, `_`, `-`, `.`
    - Anahtar, `unicodedata.normalize("NFC", ...)` sonrası Türkçe kurala göre küçültülür: önce `I` → `ı` ve `İ` → `i`, sonra `.lower()`.
    - Kurallara uymayan girdide Türkçe mesajlı `ValueError` fırlatılır.
  - `validate_pin(pin: str) -> None`: PIN tam 4 rakam olmalıdır; değilse `ValueError`.
  - `class PinHasher`:
    - `hash(pin: str) -> tuple[bytes, bytes]` → `(özet, tuz)`. `hashlib.scrypt` ile `n=2**14, r=8, p=1, dklen=32`; tuz `os.urandom(16)`.
    - `verify(pin: str, digest: bytes, salt: bytes) -> bool`. Karşılaştırma `hmac.compare_digest` ile yapılır.
  - `@dataclass(frozen=True) LockoutPolicy(max_failures: int = 5, lock_minutes: int = 15)`:
    - `is_locked(locked_until: datetime | None, now: datetime) -> bool`
    - `after_failure(failed: int, now: datetime) -> tuple[int, datetime | None]`. 5. hatada `(0, now + 15 dk)` döner, yani sayaç sıfırlanır ve kilit başlar.

- [ ] **Adım 1: Başarısız testleri yaz**
  - `test_normalize_nickname_same_key` (gözden geçirme odağı 1): `"Ali"`, `" ali "`, `"ALİ"` ve `"ali"` aynı anahtarı üretir. `"Işık"` girdisinin anahtarı `"ışık"` olur.
  - `test_normalize_nickname_rejects`: `""`, `"a"`, 31 karakterlik bir ad ve `"ali<script>"` → `ValueError`.
  - `test_validate_pin_rejects`: `"123"`, `"12345"` ve `"12a4"` → `ValueError`.
  - `test_pin_hash_verify`: Doğru PIN `True`, yanlış PIN `False` döner. Aynı PIN iki kez özetlenince farklı tuz üretilir.
  - `test_lockout_after_five_failures` ve `test_lock_expires`.
- [ ] **Adım 2:** → FAIL. **Adım 3:** Kod yazılır. **Adım 4:** → PASS. **Adım 5:** Tüm testler yeşil; rapor verilir.

### Görev 6: Config, veritabanı modelleri, migration ve DatabaseStep

**Ön koşul:** Neon bağlantısı `.env`'de.

**Dosyalar:**
- Değiştir: `src/config.py` — mimari §6'daki alanlar eklenir.
- Değiştir: `.env.example` — yeni alanlar yer tutucu değerlerle eklenir.
- Oluştur: `src/db_models.py`, `src/step_database.py`, `alembic.ini`, `migrations/env.py`, `migrations/versions/0001_ilk_sema.py`
- Test: `tests/test_step_database.py` (yalnızca `RUN_DB_TESTS=1` ile çalışır)

**Arayüzler:**
- Üretir:
  - `build_engine(direct: bool = False) -> Engine`. Config'den `postgresql+psycopg://` adresi kurulur; `sslmode`, `pool_size=2`, `max_overflow=2`, `pool_pre_ping=True` ayarlanır. Şema `PG_SCHEMA`'dan gelir.
    - **Neon havuzu:** `PG_HOST` Neon'un havuzlu adresidir (`-pooler`). Bu yüzden `connect_args` içinde `prepare_threshold=None` verilir; havuzlayıcı (PgBouncer transaction modu) hazır sorgularla sorun çıkarmasın diye.
    - **Migration:** Neon, şema değişikliklerinin havuzsuz adresle yapılmasını önerir. Bu yüzden `direct=True` iken adresteki `-pooler` kısmı çıkarılır. Alembic `migrations/env.py` içinde `build_engine(direct=True)` kullanır.
  - Kayıt tipleri:
    - `@dataclass ParticipantRow(id, nickname, pin_hash, pin_salt, failed_pins, locked_until)`
    - `@dataclass AttemptRow(id, public_id: UUID, participant_id, answers: str, scores: dict[StyleKey, int], created_at)`
    - `@dataclass ParticipantSummary(id, nickname, attempt_count, last_attempt_at)`
  - `class NicknameTaken(Exception)`, `class DatabaseUnavailable(Exception)`
  - `class DatabaseStep(engine: Engine)`:
    - `create_participant(nickname, nickname_key, pin_hash, pin_salt) -> int`. Takma ad alınmışsa `NicknameTaken` fırlatır.
    - `get_participant_by_key(key) -> ParticipantRow | None`
    - `get_participant(participant_id) -> ParticipantRow | None`
    - `update_pin_state(participant_id, failed_pins, locked_until) -> None`
    - `create_attempt(participant_id, answers, scores) -> UUID`
    - `get_attempt(public_id: UUID) -> AttemptRow | None`
    - `list_attempts(participant_id) -> list[AttemptRow]` — en yeni deneme başta.
    - `get_ai_comment(attempt_id) -> str | None`
    - `save_ai_comment(attempt_id, model, text) -> None` — kayıt zaten varsa dokunmaz (`ON CONFLICT DO NOTHING`).
    - `list_participant_summaries() -> list[ParticipantSummary]`
  - `sqlalchemy.exc.OperationalError` tüm metotlarda `DatabaseUnavailable`'a çevrilir.

- **Veri modeli:** Tablolar ve indeksler mimari §4'teki gibidir. Migration önce `CREATE SCHEMA IF NOT EXISTS` çalıştırır.

- [ ] **Adım 1: Başarısız testleri yaz.** Her test kendi benzersiz takma adını üretir ve sonunda oluşturduğu satırları siler.
  - `test_create_and_get_participant`
  - `test_duplicate_nickname_raises`
  - `test_attempt_roundtrip`: Puanlar ve cevaplar aynen geri gelir; `list_attempts` en yeniyi başta verir.
  - `test_ai_comment_saved_once`: İkinci `save_ai_comment` ilk metni değiştirmez.
  - `test_summaries_count_attempts`
- [ ] **Adım 2:** `RUN_DB_TESTS=1 python3 -m pytest tests/test_step_database.py -v` → FAIL.
- [ ] **Adım 3:** Kod ve migration yazılır. `PYTHONPATH=src alembic upgrade head` Neon'da çalıştırılır. Bu, veritabanına yazan bir işlemdir; hedef Neon olduğu ve kullanıcının onayladığı plan kapsamında yapıldığı raporda belirtilir.
- [ ] **Adım 4:** → PASS. `RUN_DB_TESTS` olmadan `python3 -m pytest` bu dosyayı atlar ve diğer testler yeşil kalır.
- [ ] **Adım 5:** Rapor verilir.

### Görev 7: Gemini canlı yorumu

**Dosyalar:**
- Oluştur: `src/step_gemini.py`
- Test: `tests/test_step_gemini.py`

**Arayüzler:**
- Kullanır: `ScoreResult` (Görev 2), `Content` (Görev 1, 3, 4).
- Üretir:
  - `class LiveCommentUnavailable(Exception)`
  - `build_prompt(score: ScoreResult, content: Content) -> str` — saf fonksiyon. Prompt şunları içerir:
    - Beş tarzın adı, puanı ve seviyesi.
    - Baskın ve en az kullanılan tarz.
    - Tüm `Source` kayıtları; her biri kimliği, kaynakçası ve özetiyle.
    - Talimatlar: yalnızca verilen kaynakları kullan, her tespitin sonuna `[kaynak-id]` yaz, 250–400 kelime yaz, Türkçe yaz, kişilik tanısı koyma, son satıra kullanılan kaynakların listesini ekle.
  - `class GeminiStep(api_key: str, model: str, client: object | None = None)`:
    - `generate(prompt: str) -> str`. `google.genai` istemcisi kullanılır, zaman aşımı 30 saniyedir. Herhangi bir API, ağ ya da kota hatası ve boş cevap `LiveCommentUnavailable`'a çevrilir. Gerçek istisna loglanır.
  - Model adı: Uygulama sırasında Google'ın güncel dokümanından, ücretsiz katmanda kullanılabilen bir "Flash" modeli seçilir ve `GEMINI_MODEL` alanına yazılır. Seçilen model raporda belirtilir.

- [ ] **Adım 1: Başarısız testleri yaz**
  - `test_build_prompt_contains_scores_and_sources`: Tasarım örneğinin puanları `"Rekabetçi: 9 (yüksek)"` biçiminde geçer. Her `Source.id` prompt'ta yer alır. Takma ad hiçbir yerde geçmez.
  - `test_generate_returns_text`: `client` mock'u metin döndürür.
  - `test_generate_maps_errors` (gözden geçirme odağı 4): Mock istisna fırlatınca ya da boş metin döndürünce `LiveCommentUnavailable` fırlatılır.
- [ ] **Adım 2:** → FAIL. **Adım 3:** Kod yazılır. **Adım 4:** → PASS.
- [ ] **Adım 5: Gerçek deneme** (yalnızca anahtar varsa). Tek bir gerçek istek gönderilir ve çıktı kullanıcıya gösterilir. Ücretsiz katman kullanıldığı için maliyet yoktur; yine de tek istekle sınırlı kalınır. Rapor verilir.

### Görev 8: TestService (orkestratör)

**Dosyalar:**
- Oluştur: `src/service.py`
- Test: `tests/test_service.py` — `DatabaseStep` ve `GeminiStep` `unittest.mock` ile taklit edilir; saat dışarıdan verilir.

**Arayüzler:**
- Kullanır: Görev 1–7'deki her şey.
- Üretir:
  - `@dataclass(frozen=True) Viewer(participant_id: int | None, is_admin: bool)`
  - `@dataclass ResultView(nickname: str, created_at: datetime, public_id: UUID, score: ScoreResult, sunum: list[SunumView], blocks: list[tuple[StyleKey, Block]], profile: ProfileText, answers: list[tuple[Question, str, StyleKey]], ai_comment: str | None, live_enabled: bool, can_request_live: bool)`
  - `@dataclass HistoryView(nickname: str, attempts: list[AttemptRow])`
  - İstisnalar: `class RegistrationError(ValueError)`, `class LoginError(ValueError)`, `class AccountLocked(LoginError)` (`until: datetime` alanıyla). Mesajlar Türkçedir.
  - `class TestService(content, scorer, db, hasher, lockout, gemini: GeminiStep | None, gemini_model: str | None, admin_password: str, clock: Callable[[], datetime])`:
    - `register(nickname: str, pin: str, pin_again: str) -> int`. PIN'ler uyuşmazsa, takma ad kurala uymazsa ya da alınmışsa `RegistrationError` fırlatır.
    - `login(nickname: str, pin: str) -> int`:
      - Takma ad yoksa ya da PIN yanlışsa aynı mesajla `LoginError` fırlatılır: "Takma ad veya PIN hatalı". Böylece bir takma adın var olup olmadığı anlaşılamaz.
      - Kilitliyken `AccountLocked` fırlatılır.
      - Başarılı girişte hata sayacı sıfırlanır.
    - `submit(participant_id: int, answers: str) -> UUID`. Hatalı cevap girdisinde `ValueError`'ı olduğu gibi iletir.
    - `result_view(public_id: UUID, viewer: Viewer) -> ResultView | None`. Deneme yoksa ya da izleyici sahibi veya yönetici değilse `None` döner.
      - `can_request_live` yalnızca sahip için ve `live_enabled` açıkken `True` olur.
      - `live_enabled`, `gemini` verilmişse `True` olur.
    - `history_view(participant_id: int) -> HistoryView | None`
    - `live_comment(public_id: UUID, participant_id: int) -> str | None`:
      - Sahip değilse `None` döner.
      - Kayıtlı yorum varsa onu döner ve Gemini'yi çağırmaz.
      - Yoksa Gemini'yi çağırır, sonucu kaydeder ve döner.
      - `LiveCommentUnavailable` istisnasını olduğu gibi iletir.
    - `check_admin(password: str) -> bool` — `hmac.compare_digest` ile.
    - `admin_participants() -> list[ParticipantSummary]`
  - Her akış adımı `logger.info` ile loglanır; PIN loglanmaz.

- [ ] **Adım 1: Başarısız testleri yaz**
  - `test_register_pin_mismatch`, `test_register_nickname_taken` (`NicknameTaken` → `RegistrationError`)
  - `test_login_wrong_pin_increments_and_locks` (5. hatada `AccountLocked`), `test_login_success_resets_counter`, `test_login_unknown_nickname_same_message`
  - `test_result_view_other_participant_none`, `test_result_view_admin_sees` (gözden geçirme odağı 3)
  - `test_live_comment_cached_no_second_call`, `test_live_comment_disabled_when_no_gemini` (gözden geçirme odağı 4)
  - `test_result_view_uses_profile_of_dominant_least`: Tasarım örneğinde `profiles[("rekabet", "kacinma")]` seçilir.
- [ ] **Adım 2:** → FAIL. **Adım 3:** Kod yazılır. **Adım 4:** → PASS. **Adım 5:** Tüm testler yeşil; rapor verilir.

### Görev 9: Aday sayfaları

**Dosyalar:**
- Oluştur: `src/main.py`, `src/chart.py`, `src/web/__init__.py`, `src/web/deps.py`, `src/web/routes_aday.py`
- Oluştur: `src/web/templates/` altında `base.html`, `giris.html`, `test.html`, `sonuc.html`, `gecmis.html`, `hata.html`
- Oluştur: `src/web/static/style.css`, `src/web/static/test.js`
- Test: `tests/test_routes_aday.py`, `tests/test_chart.py`

**Arayüzler:**
- Kullanır: `TestService` ve görünüm sınıfları (Görev 8).
- Üretir:
  - `create_app(service: TestService, session_secret: str, cookie_secure: bool) -> FastAPI`. Testler bu fonksiyonu sahte bir servisle çağırır.
  - Modül seviyesinde `app`: Gerçek nesneler config'den kurulur ve başlangıçta `setup_logging()` çağrılır. Bu kurulum bir `build_default_app()` fonksiyonuyla yapılır; modül yalnızca uvicorn tarafından içe aktarıldığında çalışır.
  - `chart_svg(score: ScoreResult, styles: list[StyleDef]) -> str`:
    - 400×400'lük bir SVG üretir. Eksen etiketleri "Kendi ilgisini tatmin" (dikey) ve "Karşı tarafın ilgisini tatmin" (yatay).
    - Her tarz `(x, y)` konumunda bir daire olarak çizilir; yarıçap `10 + puan * 2`.
    - Dairenin rengi seviyeye göre üç sınıftan birini alır.
    - Etiket "Tarz adı · puan" biçimindedir.
  - Oturum anahtarları: `participant_id` (int) ve `is_admin` (bool).

- **Route'lar ve davranışlar:** Mimari §5'teki aday route'ları uygulanır. Ek kurallar:
  - **Test gönderimi:** `POST /test` sırasıyla `q1`…`q30` form alanlarını okur ve bunları 30 karakterlik cevap metnine çevirir.
    - Eksik ya da hatalı bir cevapta `test.html` 400 koduyla yeniden gösterilir. Mesaj: "Lütfen 30 sorunun hepsini cevaplayın." (gözden geçirme odağı 2)
  - **Test sayfası:**
    - JavaScript açıkken her ekranda bir soru gösterilir. A ya da B'ye basınca sonraki soruya geçilir. "Geri" düğmesi ve "n / 30" göstergesi bulunur. Son soruda "Bitir" düğmesi çıkar.
    - JavaScript kapalıyken tüm sorular tek sayfada listelenir.
  - **Sonuç sayfası:**
    - Puan tablosu, `chart_svg` grafiği, "kişilik testi değildir" notu.
    - "Sunum yorumları" ve "Kaynaklarla genişletilmiş yorum" sekmeleri. İkinci sekmenin başında tasarım 7.2'deki uyarı yer alır.
    - Katlanabilir bir "Cevaplarım" bölümü.
    - En altta, `can_request_live` açıksa küçük canlı yorum düğmesi bulunur. Düğmeye basınca tasarım 7.3'teki uyarıyı gösteren bir onay penceresi açılır (`<dialog>`). Onaydan sonra `POST /sonuc/{id}/canli-yorum` çağrılır ve sayfa yorumla birlikte yeniden yüklenir.
    - `LiveCommentUnavailable` olursa sonuç sayfası "Şu anda canlı yorum üretilemiyor, daha sonra tekrar deneyin." mesajıyla gösterilir.
  - **Hata durumları:**
    - Oturumu olmayan biri `/test` ya da `/gecmis`'e girerse `/`'a yönlendirilir.
    - `result_view` `None` dönerse 404 verilir.
    - `DatabaseUnavailable` olursa `hata.html` 503 koduyla gösterilir. Mesaj: "Şu anda hizmet veremiyoruz, biraz sonra tekrar deneyin." (gözden geçirme odağı 5)
    - Beklenmeyen bir hata olursa `hata.html` 500 koduyla gösterilir ve hata loglanır; stack trace gösterilmez.
  - **Geçmiş sayfası:** `gecmis.html` en son sonuca bir bağlantı, önceki denemelerin tarih listesi ve "Testi tekrar çöz" düğmesi (`/test`) içerir. Her sayfanın üst kısmında, oturum açıksa "Çıkış" düğmesi (`POST /cikis`) bulunur.
  - **Diğer:** `GET /robots.txt` ve `GET /saglik` route'ları vardır. Tüm şablonlar `base.html`'den türer ve `noindex` etiketini oradan alır.

- [ ] **Adım 1: Başarısız testleri yaz.** `TestClient` kullanılır ve servis `MagicMock` ile taklit edilir.
  - `test_robots_and_noindex`: `/robots.txt` → `Disallow: /`. `/` sayfasının HTML'inde `noindex` geçer.
  - `test_register_then_redirect_test`
  - `test_test_requires_session`: Oturumsuz `GET /test` → `/`'a yönlendirme.
  - `test_submit_incomplete_shows_message`: 29 alanla gönderim → 400 kodu ve mesaj metni.
  - `test_result_other_user_404`
  - `test_live_button_hidden_when_disabled`
  - `test_live_unavailable_message`
  - `test_db_unavailable_503`
  - `test_chart_svg_contains_all_styles`: SVG'de beş tarz adı ve `"Rekabetçi · 9"` geçer.
- [ ] **Adım 2:** → FAIL. **Adım 3:** Kod, şablonlar ve statik dosyalar yazılır. **Adım 4:** → PASS.
- [ ] **Adım 5: Yerelde uçtan uca deneme.** `PYTHONPATH=src uvicorn main:app --reload` ile Neon'a bağlı olarak başlatılır.
  - Akış elle denenir: kayıt → 30 soru (tasarım örneği cevaplarıyla) → sonuç 9-7-6-3-5 → çıkış → giriş → geçmiş.
  - Telefon genişliğinde (375 px) görünüm kontrol edilir.
  - Ekran görüntüleri kullanıcıya gösterilir; rapor verilir.

### Görev 10: Yönetici sayfaları

**Dosyalar:**
- Oluştur: `src/web/routes_yonetici.py`
- Oluştur: `src/web/templates/yonetici_giris.html`, `src/web/templates/yonetici_adaylar.html`
- Değiştir: `src/main.py` — router kaydı.
- Test: `tests/test_routes_yonetici.py`

**Arayüzler:**
- Kullanır: `TestService.check_admin`, `admin_participants`, `history_view`, `result_view(Viewer(None, True))`.

- **Davranış:**
  - `/yonetici`: Şifre formu. Doğru şifrede oturuma `is_admin=True` yazılır.
  - `/yonetici/adaylar`: Takma ad, deneme sayısı ve son tarih listelenir.
  - `/yonetici/aday/{id}`: `gecmis.html` aynen gösterilir. Sonuç bağlantıları `/sonuc/{public_id}`'ye gider; `result_view` yöneticiyi kabul ettiği için açılır. Yönetici görünümünde canlı yorum düğmesi gösterilmez.
  - Yanlış şifrede formda "Şifre hatalı" mesajı gösterilir.
  - Yönetici girişi de `LockoutPolicy` kuralına tabidir: 5 yanlış denemede 15 dakika kilit. Sayaç bellekte tutulur.

- [ ] **Adım 1: Başarısız testleri yaz**
  - `test_admin_pages_require_login`: Oturumsuz `/yonetici/adaylar` → `/yonetici`'ye yönlendirme. (Gözden geçirme odağı 3.)
  - `test_admin_login_wrong_password`
  - `test_admin_sees_candidate_result`
  - `test_admin_no_live_button`
- [ ] **Adım 2:** → FAIL. **Adım 3:** Kod yazılır. **Adım 4:** → PASS. **Adım 5:** Tüm testler yeşil; rapor verilir.

### Görev 11: Docker, dokümanlar ve yerel paket doğrulaması

**Dosyalar:**
- Oluştur: `Dockerfile`, `.dockerignore`, `README.md`, `PROJE.md`

- **Dockerfile:**
  - `python:3.11-slim` tabanlı.
  - Önce `requirements.txt` kopyalanıp `pip install --no-cache-dir` çalıştırılır; ardından `src/`, `migrations/` ve `alembic.ini` kopyalanır.
  - Non-root kullanıcı `app` oluşturulur; `ENV PYTHONPATH=src` ayarlanır.
  - `CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]`
- **`.dockerignore`:** AGENTS.md P11'deki liste.
- **README.md:** Kısa özet, yerelde çalıştırma ve test komutları.
- **PROJE.md:** Amaç, komutlar, klasör haritası, `ikna_muzakere_secrets` alan adları (değerler değil), alınmış kararlar ve plan dokümanlarına bağlantılar.

- [ ] **Adım 1:** Docker kullanılabiliyorsa `docker build -t ikna-muzakere .` → başarılı. Ardından `docker run --env-file .env -p 8000:8000 ikna-muzakere` çalıştırılır ve `/saglik` adresinden `ok` alınır.
  - Docker komut satırı kapalıysa kullanıcıdan Docker.app'i açması istenir. Açılamıyorsa bu adım "doğrulanmadı" olarak raporlanır ve yayında Render derlemesi doğrulama yerine geçer.
- [ ] **Adım 2:** `python3 -m pytest` tamamı yeşil; rapor verilir.

### Görev 12: Yayına alma (kullanıcıyla birlikte)

- [ ] **Adım 1:** Kullanıcı GitHub'da gizli bir depo açar. Push'u kullanıcı yapar ya da açıkça ister.
  - Push öncesinde `git status` ile `.env`, `data/` ve `logs/` klasörlerinin depoya girmediği gösterilir.
- [ ] **Adım 2:** Render'da ücretsiz bir web servisi kurulur: Docker ortamı, Frankfurt bölgesi, sağlık kontrolü `/saglik`.
  - Ortam değişkeni olarak `ikna_muzakere_secrets` tek satırlık JSON olarak girilir. Yayında `COOKIE_SECURE` açık olur.
  - Adımları kullanıcı uygular; asistan her ekranda ne seçileceğini söyler.
- [ ] **Adım 3: Yayın doğrulaması.**
  - Canlı adreste Görev 9 Adım 5'teki akış tekrarlanır.
  - `/robots.txt` kontrol edilir; yönetici girişi denenir.
  - İsteğe bağlı olarak tek bir canlı Gemini yorumu denenir.
  - Sonuç kullanıcıya bildirilir.
