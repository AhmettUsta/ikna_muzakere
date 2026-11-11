# Asistan Çalışma Kuralları

**Sürüm: v8 — 2026-11-11 14:29**

Bu dosya projeden bağımsızdır; her projeye olduğu gibi kopyalanabilir. Yapay zekâ asistanları (Claude, Codex, Copilot, Cursor…) için yazılmıştır.

- Projeye özel bilgi, komut ve kurallar **`PROJE.md`**'dedir: işe başlamadan önce ikisini de oku. Çelişki varsa `PROJE.md` kazanır. `PROJE.md` yoksa ilk büyük işte oluşturmayı öner.
- `PROJE.md`'de olması beklenenler: projenin amacı (2–3 cümle), kurulum / çalıştırma / test komutları, klasör ve akış haritası, dış sistemler (DB, API) ve `.env` anahtar adları, alınmış kararlar, projeye özel istisnalar.
- **Öncelik sırası:** kullanıcının o anki açık talimatı > `PROJE.md` > bu dosya > skill / eklenti iş akışları (ör. Superpowers) > aracın varsayılan davranışı. Bir talimat bu dosyayla çelişiyorsa uygulamadan önce bunu açıkça söyle.
- Claude Code için projede yalnızca `@AGENTS.md` satırını içeren bir `CLAUDE.md` bulunur; kurallar yalnızca bu dosyada tutulur.

**Sürüm notları**

- v8 — `plans/` doküman adlarından tarih kaldırıldı (`<konu>-tasarim.md` vb.); tarih sürüm satırında.
- v7 — `plans/` için üç doküman düzeni (tasarım, mimari, plan) §6 ve P10'a yazıldı.
- v6 — P0 "Yeni proje kurulumu" eklendi: adım listesi ve `config.py`, `logger.py`, `.env.example`, `requirements.txt`, `.gitignore` şablonlarının tam içeriği; P10'a kurulum dosyaları eklendi.
- v5 — Sorular tıklanabilir şıklarla (`AskUserQuestion` vb.) sorulur, seçildikçe ilerlenir; metin içi a/b listesi kullanılmaz.
- v4 — Standart `config.py` (pydantic `Config`, tek JSON ortam değişkeni) ve `logger.py` (`setup_logging()`, konsol + günlük dönen dosya) formatı P4 ve P5'e yazıldı.
- v3 — Dizin yapısına sunumlar için `presentations/` klasörü eklendi.
- v2 — Tasarım ve plan dokümanları `docs/plans/` yerine kök dizindeki ayrı `plans/` klasörüne taşındı.
- v1 — Eski `AGENTS.md` (çalışma süreci, v5) ve `CLAUDE.md` (Python standartları) tek dosyada birleştirildi; Superpowers gibi iş akışı eklentileriyle uyum kuralları (§6) eklendi.

---

# A. Çalışma Süreci

## 0. Genel

- Yanıt dili Türkçe; yerleşik teknik terimler İngilizce kalabilir.
- Kısa ve net yaz. Cevapta **ne yapıldığını**, **test / doğrulama sonucunu** ve **kullanıcıdan beklenen kararı** ayrı ayrı belirt.
- Yalnızca istenen görevi yap, sorulan soruyu yanıtla. İstenmeyen alternatif, "şunu da yapabilirsiniz", "best practice olarak" türü yönlendirme ya da gelecek iyileştirme önerisi sunma; görev kapsamını genişletme.
- **İstisnalar** (bunları her zaman söyle): güvenlik açığı; hata, veri kaybı ya da beklenmeyen davranış riski; istenen çözümün bu dosyayla ya da `PROJE.md` ile çelişmesi.
- İstenmedikçe koda "kullanım örneği" ya da test amaçlı `if __name__ == "__main__":` bloğu ekleme.
- Teknik olarak yanlış bulduğun bir talimatı ya da inceleme yorumunu körü körüne uygulama; gerekçesiyle söyle.

## 1. Önce seçenekli sor

- Önce bağlamı topla: ilgili dosyaları ve `PROJE.md`'yi oku. Koddan öğrenilebilecek bir şeyi sorma.
- Bir istekte karar gerektiren nokta varsa (yöntem, parametre, kapsam, isimlendirme, silme / tutma…) işe başlamadan önce **seçenekli sorular** sor. Her soruda 2–4 seçenek ve kısa açıklama olsun; önerdiğin seçeneği başa koy ve "(Önerilen)" diye işaretle.
- **Sorular tıklanabilir şıklarla sorulur.** Araç destekliyorsa etkileşimli seçim aracı kullanılır (ör. Claude Code'da `AskUserQuestion`); soruları metin içinde "a) … b) …" listesi olarak yazma. Araç yoksa metin içinde numaralı seçenekle sor.
- **Seçildikçe ilerle.** Kullanıcı bir şık seçince hemen uygula, sonucu kısaca bildir; sonraki karar noktasında yeni soruyu yine şıklı sor. Cevabı bekleyen işe başlama.
- Birbirinden bağımsız sorular tek seferde (en fazla 4) sorulabilir; birinin cevabı diğerini değiştiriyorsa tek tek sor.
- Cevabın sonunda bekleyen bir karar varsa onu metin olarak bırakma; şıklı soru olarak sor.
- Cevaplara göre uygula. Cevaplarda istenmeyen bir şeyi kendiliğinden ekleme.
- Konvansiyonu belli olan ya da koddan doğrulanabilen konularda soru sorma; makul varsayılanı seç ve bunu söyle.
- Analizde yöntem, parametre ve grafik kararı koddan önce verilir. Seçenekleri sade dille, mümkünse tek bir örnek üzerinden sayısal olarak anlat. Parametre sayısını en aza indir; her parametrenin bir gerekçesi olsun.
- Kullanıcı "neden?" diye sorarsa ya da açıklama isterse önce açıkla, sonra öner. **Açıklama isteğini onay sayma.**

## 2. Sürüm ve tarih

- Güncellediğin her notebook ve dokümanın en başına, başlığın hemen altına `**Sürüm: vN — YYYY-AA-GG SS:DD**` satırını koy.
- Her değişiklikte N'i bir artır, tarihi güncelle ve "Sürüm notları" listesinin **en üstüne** tek satırlık bir not ekle.
- Cevabında yeni sürümü söyle ("v7 yazdım"). Kullanıcı editördeki sürümle karşılaştırıp eski bir kopyaya bakıp bakmadığını buradan anlar.
- Kod dosyalarında (`.py` vb.) sürüm satırı olmaz.

## 3. Plan → adım → test

- Birden fazla adımlı işlerde önce kısa bir plan sun: adımlar ve her adımın nasıl test edileceği. Onay al.
- Adım adım uygula. Her adımın sonunda test et, kısa bir rapor ver, sonra sıradakine geç.
- Plan gerçekle uyuşmuyorsa ya da bir varsayım yanlış çıktıysa tahminle devam etme; dur, raporla, sor.
- Test: kod için birim testleri; notebook için temiz bir kernel'de baştan sona çalıştırma. Çalıştırılmış kopya geçici bir klasöre yazılır, repodaki notebook çıktısız kalır.
- **Test cache'i yalnızca asistan için.** Tekrar tekrar çalıştırırken ağır sorgular cache'lenebilir, ama cache yalnızca asistanın açtığı bir bayrakla (ör. ortam değişkeni) devreye girer; kullanıcı kodu normal çalıştırdığında veri her zaman kaynaktan taze gelir. Cache günlüktür ve **birikmez**: aynı gün tekrar kullanılır, yeni gün yazılınca önceki günlerinki silinir; her zaman yalnızca en son çalıştırmanın cache'i durur. Cache klasörü gitignore'dadır.
- Sonuçları dürüstçe raporla. Hata varsa çıktısıyla söyle, atlanan adımı söyle; çalıştırıp çıktısını görmediğin bir şeye "tamam" deme. Doğrulayamadığın şeyi "doğrulanmadı" diye yaz.
- Hata ayıklarken kök nedeni bulmadan düzeltme yapma; belirtiyi bastıran yama düzeltme değildir.
- Yeni veriyle sayılar değiştiyse eski ve yeni değeri yan yana göster. Dokümandaki sabit rakamları kullanıcıya sormadan değiştirme.
- Veriye göre sırası değişebilen şeylere (küme numarası, sıra numarası) numarayla atıf yapma; içerikle atıf yap.
- İş sırasında bulduğun hataları (kırık hücre, tanımsız değişken, silinmiş dosyaya atıf) raporla ve düzelt. Kapsam dışı büyük bir değişikliği önce sor.

## 4. Kapsam sınırı

- Yalnızca açıkça istenen ya da üzerinde çalışılan kod bloklarını değiştir; ilgisiz fonksiyon ve dosyaları yeniden yapılandırma.
- Yeni bir özellik ya da hata düzeltmesi gerektirmiyorsa mevcut, çalışan koda dokunma.
- Kodun geri kalanındaki stil hatalarını (PEP 8 uyumsuzlukları dahil) görev kapsamında değilse düzeltme; mevcut yapıyı koru.

## 5. Görünür ve geri alınabilir değişiklik

- Dosyaları kullanıcının diff görebileceği araçlarla değiştir. Script ile dışarıdan değiştirmen gerekiyorsa (örneğin çok büyük bir notebook), önce kullanıcıdan dosyayı editörde **kaydetmeden kapatmasını** iste, yedek al ve değişiklikten sonra kaynak diff'ini göster. Açık kalan bir editör, bellekteki eski kopyayı kaydedip değişikliği silebilir.
- Silme, üzerine yazma, DB'ye yazma, ücretli ya da kotalı API çağrısı ve dışarıya gönderimden önce hedefe bak ve onay al. Geri getirilemeyecek bir veriyi (tek kopya yedek vb.) silmeden önce bunu açıkça söyle.
- Maliyet ya da kota tüketen işlerde (ücretli API, uzun hesaplama, toplu yazım) önce maliyetsiz bir deneme yap (kuru çalışma, küçük örnek), sonucu göster, sonra büyüt.
- **Git: commit, push, merge, dal açma ve worktree oluşturma yalnızca kullanıcı açıkça isteyince yapılır.** Değişiklikler çalışma klasöründe, commit'lenmemiş halde bırakılır; kullanıcı diff'i inceleyip kendisi commit'ler. Notebook'lar çıktısız commit edilir.
- Gizli bilgiler (`.env`, anahtar, şifre, token) koda, loga, çıktıya ya da dokümana yazılmaz; dokümanda yalnızca anahtar adları geçer.

## 6. İş akışı eklentileriyle çalışma (Superpowers vb.)

Bu kurallar, skill / eklenti iş akışlarının bu dosyayla çakıştığı yerlerde geçerlidir. Çakışmayan yerlerde eklentinin akışı (beyin fırtınası, plan, TDD, sistematik hata ayıklama, doğrulama, kod incelemesi) olduğu gibi kullanılır.

- **Commit yok.** Planlardaki "commit" adımları atlanır; yerine o adımın testleri çalıştırılır ve kısa rapor verilir. Commit ve push yalnızca kullanıcı isteyince (§5).
- **Worktree ve dal yok.** `using-git-worktrees` ve `finishing-a-development-branch` akışları kullanıcı istemedikçe uygulanmaz; iş mevcut klasörde yapılır. Proje git reposu değilse git adımları tamamen atlanır.
- **Test kapsamı:** TDD (önce başarısız test, sonra kod) davranış değişikliği, hata düzeltmesi ve kritik akışlar için uygulanır. Yalnızca yapılandırma, doküman, keşif notebook'u ve tek seferlik script için zorunlu değildir; bunlarda da sonuç doğrulanır.
- **Kod silme yok.** "Testten önce yazılan kodu sil" türü adımlar kullanıcının mevcut koduna uygulanmaz; yalnızca asistanın aynı iş sırasında yazdığı kod için geçerlidir.
- **Sorular:** eklentinin soru akışında da §1 geçerlidir (seçenekli, önerilen başta).
- **Dokümanlar:** her proje ya da büyük iş için `plans/` altında üç doküman yazılır; birbirine bağlantı verir. Dosya adında tarih olmaz; tarih ve sürüm dosyanın başındaki sürüm satırındadır (§2):
  - `<konu>-tasarim.md` — **ne ve neden:** amaç, hedefler / kapsam dışı / istenmeyenler, kısıtlar, değerlendirilen yaklaşımlar ve seçilen, kullanıcının kararları, akışlar, uygulayıcıya bırakılanlar.
  - `<konu>-mimari.md` — **nasıl kurulur:** genel şema, klasör yapısı, bileşenler ve sorumlulukları, veri modeli, arayüzler / route'lar, konfigürasyon alanları, bağımlılıklar, dağıtım, test stratejisi.
  - `<konu>-plan.md` — **hangi sırayla:** tasarım ve mimari onaylandıktan sonra yazılan uygulama adımları (§3, §4).
  - Küçük işlerde tasarım ve mimari tek kısa dokümanda birleşebilir.
- **Alt ajanlar:** paralel alt ajan kullanılırsa aynı dosyalara dokunan görevler paralel yürütülmez; dönen iş kabul edilmeden önce incelenir ve testleri çalıştırılır.

## 7. Dokümanlar

- Projeye özel bir bilgi değişince (yeni komut, tablo, karar, sonuç) `PROJE.md`'yi güncelle; sürüm ve tarihiyle.
- Kullanıcının kalıcı bir tercihini öğrenirsen ("bundan sonra hep…"), bu tercih her projede geçerliyse `AGENTS.md`'ye, yalnızca bu projeye özelse `PROJE.md`'ye eklemeyi öner.

---

# B. Python Standartları

Python projelerinde A kısmına ek olarak geçerlidir. Çevredeki mevcut kodun adlandırma diline, yorum yoğunluğuna ve kalıplarına uy.

## P0. Yeni proje kurulumu

Yeni bir Python projesi açılırken (ya da bu yapıya sahip olmayan bir projeye ilk kez girilirken) aşağıdaki adımlar sırayla uygulanır. Var olan dosyanın üzerine yazılmaz; farklıysa kullanıcıya sorulur. `<proje>` yer tutucusu, projenin küçük harfli ve alt çizgili adıdır (ör. `ikna_muzakere`).

1. **Klasörler:** `src/`, `tests/`, `docs/`, `plans/`, `presentations/`, `data/`, `logs/`. `data/` ve `logs/` içine boş bir `.gitkeep` konur.
2. **`.gitignore`**, **`.env.example`**, **`requirements.txt`**: aşağıdaki şablonlarla.
3. **`src/config.py`** ve **`src/logger.py`**: aşağıdaki şablonlar **birebir** kopyalanır; yalnızca `<proje>` değiştirilir. `Config`'e projenin ihtiyacı olan alanlar zamanla eklenir (P4).
4. **Doğrulama:** `.env.example` geçici olarak `.env`'ye kopyalanır, proje kökünden `PYTHONPATH=src python3 -c "from config import config; from logger import setup_logging; import logging; setup_logging(); logging.getLogger(__name__).info('test')"` çalıştırılır, log satırı görülür, geçici `.env` silinir.
5. `README.md` ve `PROJE.md` projenin amacı belli olunca yazılır.

Config'e başka ihtiyaç olmasa da logger `LOG_LEVEL`'i okuduğu için `<proje>_secrets` değişkeni en az `{"LOG_LEVEL": "INFO"}` ile tanımlı olmalıdır.

**`src/config.py`**

```python
import os
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class Config(BaseModel):
    VERSION: str = "1.0.0"
    DEBUG_MODE: Optional[bool] = False

    # Logging
    LOG_LEVEL: str
    LOG_TO_FILE: Optional[bool] = False

config = Config.model_validate_json(os.environ["<proje>_secrets"])
```

**`src/logger.py`**

```python
"""
Logging configuration and setup utilities
"""

import logging
import os
from logging.handlers import TimedRotatingFileHandler
from config import config


def setup_logging():
    """
    Set up comprehensive logging with both time and size rotation
    """
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    log_level = config.LOG_LEVEL
    root_logger.setLevel(getattr(logging, log_level))

    # Clear any existing handlers
    root_logger.handlers.clear()

    # Console formatter
    log_format = "%(asctime)s - %(levelname)s [PID %(process)d - TID %(thread)d]: %(filename)s:%(lineno)d - %(message)s"
    log_formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level))
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)

    # Silence verbose Azure SDK HTTP request/response logs.
    for azure_logger_name in [
        "azure",
        "azure.core",
        "azure.storage",
        "azure.core.pipeline.policies.http_logging_policy",
        "httpx",
        "openai",
        "openai._base_client",
    ]:
        logging.getLogger(azure_logger_name).setLevel(logging.WARNING)

    # Single unified log file with both time and size rotation
    if config.LOG_TO_FILE:
        # File handler
        unified_handler = TimedRotatingFileHandler(
            filename=os.path.join(log_dir, "log.log"),
            when="midnight",
            interval=1,
            backupCount=30,  # Keep 30 days of logs
            encoding="utf-8",
        )

        unified_handler.setFormatter(log_formatter)
        unified_handler.suffix = "%Y-%m-%d"
        root_logger.addHandler(unified_handler)
```

**`.env.example`**

```bash
# Bu dosyayı .env olarak kopyalayıp gerçek değerleri girin.
# Tüm ayarlar tek bir değişkende JSON olarak tutulur; yalnızca yer tutucu değerler yazılır.
<proje>_secrets='{"LOG_LEVEL": "INFO", "LOG_TO_FILE": false}'
```

**`requirements.txt`** (sürümler kurulumdaki güncel sürümle `==` olarak yazılır)

```text
pydantic==2.9.2
python-dotenv==1.1.1
```

**`.gitignore`**

```gitignore
# Ortam ve gizli bilgiler
.env
.env.*
!.env.example

# Python
__pycache__/
*.py[cod]
*.egg-info/
build/
dist/

# Sanal ortam
.venv/
venv/
env/

# Test ve araç cache'leri
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/
.cache/

# Jupyter
.ipynb_checkpoints/

# Loglar ve veri (klasörler kalır, içerik takip edilmez)
logs/*
!logs/.gitkeep
data/*
!data/.gitkeep

# Editör ve işletim sistemi
.vscode/
.idea/
.DS_Store
Thumbs.db
```

## P1. Dil ve stil

- Python 3.11+; PEP 8.
- Okunabilirlik ve sadelik (Zen of Python) karmaşık optimizasyondan önce gelir.
- Döngü içinde string birleştirmede `+` yerine `"".join()` ya da f-string.
- Kaynaklar (dosya, DB bağlantısı, HTTP client) her zaman `with` bloğuyla yönetilir.
- Yorumlar kodun **ne** yaptığını değil, karmaşık yerlerde **neden** böyle yapıldığını anlatır.
- Kullanılmayan kod, ölü değişken ve eski dosya atıfları bırakılmaz.

## P2. Tipler

- Tüm fonksiyon ve metodlarda parametre ve dönüş tipleri açıkça yazılır.
- Yerleşik generic'ler ve `|` sözdizimi kullanılır: `list[str]`, `dict[str, int]`, `str | None`.
- `typing`'den gerektiğinde: `Final` (sabitler), `Literal` (sınırlı değerler), `Protocol` (bağımlılık arayüzleri), `TypedDict`, `Self`.

## P3. Kod organizasyonu — nesne yönelimli, katmanlı

- **Ortak kısa fonksiyonlar** (DB bağlantısı, sorgu çalıştırma, küçük dönüşümler) tek bir ortak modülde (`common` / `tools`) fonksiyon olarak durur; notebook'lar ve akışlar bunları import eder, kopyalamaz.
- **Akışı olan Python kodu** (job, servis, pipeline) sınıflara bölünür:
  - Her dış sistem ya da süreç adımı kendi sınıfında, kendi dosyasında: `step_<ad>.py` → `class ...` (ör. DB tablosu, harici API, veri kaynağı). Sınıf yalnızca kendi sistemini bilir.
  - Akışı bir **orkestratör sınıfı** yönetir: step sınıflarını `__init__`'te parametre olarak alır, verilmezse kendisi kurar (testte sahte step verilebilsin diye — bağımlılık enjeksiyonu). Ana metodunda adımları numaralı yorumlarla sırayla çağırır. Hangi adımda hata olduğu loglarda ve istisnada görünür.
  - Giriş noktası (`main.py`, CLI) incedir: parametreleri okur, orkestratörü kurar, çalıştırır.
  - Normalde `src/` tek bir akışa aittir; step dosyaları doğrudan `src/` altında durur. Bir repoda birden fazla akış varsa her akış kendi alt klasöründe olur (`PROJE.md`'de belirtilir).
  - Dış sisteme ulaşılamıyorsa (art arda birkaç hata) akış durur; kalan işleri tek tek deneyip zaman harcamaz.
  - Uzun fonksiyonlar bölünür; her metod tek iş yapar (Tek Sorumluluk). DB ve API'ye dokunmayan mantık (seçim, ayrıştırma, hizalama) ayrı metod / fonksiyon olur ki DB'siz test edilebilsin.
- Veri modelleri için `dataclasses` ya da `pydantic`.
- **Notebook'lar** ön çalışma ve keşif içindir; akışı sınıfa taşımak zorunlu değil. Ama tekrar eden parçalar (bağlantı, veri çekme, ortak sabitler) ortak modülden gelir.

## P4. Konfigürasyon

Tüm ayarlar tek bir `src/config.py` dosyasından gelir; başlangıç şablonu P0'dadır.

- `Config`, `pydantic.BaseModel`'den türer. Modülün sonunda tek bir `config` örneği oluşturulur; kod her yerde `from config import config` ile kullanır. `os.getenv` / `os.environ` yalnızca `config.py` içinde geçer.
- Tüm değerler **tek bir ortam değişkeninde JSON** olarak gelir ve `Config.model_validate_json(...)` ile doğrulanır. Yerelde bu değişken `.env`'den `load_dotenv()` ile yüklenir. Değişkenin adı `<proje>_secrets` biçimindedir ve `PROJE.md`'de yazılır.
- Alanlar `# Logging`, `# Postgres`, `# Azure` gibi yorum başlıklarıyla gruplanır; alan adları `BÜYÜK_HARF`.
- Gizli ya da ortama özel alanların (anahtar, şifre, adres) varsayılanı olmaz; eksikse uygulama başlarken hata verir. Diğer alanların makul bir varsayılanı olur.
- `Config` yalnızca projenin gerçekten kullandığı alanları içerir; başka projeden kalan alan bırakılmaz.
- Yeni bir ayar gerektiğinde önce `Config`'e alan eklenir, sonra `.env`'deki JSON'a değer yazılır; `PROJE.md`'ye yalnızca alan adı eklenir.
- `.env.example` aynı değişkeni, tüm alanlarıyla ve yalnızca yer tutucu değerlerle içerir; yeni alan eklendiğinde buraya da eklenir.
- Gerekli paketler: `pydantic`, `python-dotenv`.

## P5. Hata yönetimi ve loglama

- Çıplak `except:` kullanılmaz; spesifik hata sınıfları yakalanır (`ValueError`, `KeyError`…).
- Hata yutulmaz: ya ele alınır ya loglanıp yeniden fırlatılır (`raise ... from e`).
- Beklenmeyen durumlarda anlamlı mesajlı `raise` kullanılır; mesaj hangi değerin neden geçersiz olduğunu söyler.
- Çıktı ve hatalar için `print()` değil, `logging`. Gizli bilgi loglanmaz.

**Logger formatı** — loglama tek bir `src/logger.py` dosyasındaki `setup_logging()` fonksiyonuyla kurulur; kodu P0'daki şablonun birebir aynısıdır:

- `setup_logging()` giriş noktasında (`main.py`, CLI, API başlangıcı) **bir kez** çağrılır. Root logger'ı kurar; önceki handler'ları temizler.
- Diğer modüller kendi handler'ını eklemez; yalnızca `logger = logging.getLogger(__name__)` kullanır.
- Seviye `config.LOG_LEVEL`'den gelir. Dosyaya yazma `config.LOG_TO_FILE` ile açılır.
- Format: `%(asctime)s - %(levelname)s [PID %(process)d - TID %(thread)d]: %(filename)s:%(lineno)d - %(message)s`, tarih biçimi `%Y-%m-%d %H:%M:%S`.
- Konsol handler'ı her zaman vardır. Dosya handler'ı `TimedRotatingFileHandler`'dır: `logs/log.log`, gece yarısı döner, dosya eki `%Y-%m-%d`, 30 gün saklanır, `utf-8`.
- Gürültülü üçüncü parti logger'lar (`azure`, `httpx`, `openai` vb.) `WARNING` seviyesine çekilir; projeye yeni bir gürültülü kütüphane girerse bu listeye eklenir.

## P6. Test

- Ne zaman test yazılacağı §6'daki test kapsamına göre belirlenir; kullanıcı açıkça isterse her zaman yazılır.
- `pytest` (`unittest` değil); testler `tests/` altında, dosyalar `test_*.py`.
- İsimlendirme: `test_<fonksiyon_adi>_<senaryo>`.
- Yalnızca başarılı senaryo değil; hatalı girdi, sınır değerler ve istisnalar da test edilir (`pytest.raises`).
- Dış bağımlılıklar (API, DB, dosya sistemi) `unittest.mock` ya da `pytest-mock` ile izole edilir; mock sınırı step sınıflarıdır.

## P7. Güvenlik

- Kullanıcı girdisi doğrudan SQL sorgusuna ya da sistem komutuna eklenmez; parametreli sorgu ve argüman listesi kullanılır (`shell=True` yok).
- Hassas veri (şifre, API anahtarı) koda gömülmez; `.env` → `Config` üzerinden okunur.

## P8. Veritabanı

- Bağlantı adresi `DATABASE_URL` ile `.env`'den, `Config` üzerinden okunur.
- Bağlantı havuzu (connection pooling) kullanılır; bağlantılar `with` bloğunda açılır ve her durumda kapanır.
- Yazma işlemleri açık transaction içinde: başarılıysa `COMMIT`, hata olursa `ROLLBACK`.
- Zaman aşımı, sınırlı sayıda yeniden deneme ve kopan bağlantı için hata yönetimi bulunur.
- `SELECT *` yok; gereken sütunlar açıkça yazılır.
- N+1 sorgudan kaçınılır: JOIN ya da eager loading (`selectinload` / `joinedload`).
- ORM kullanılıyorsa SQLAlchemy 2.0 stili: deklaratif `Base`, `relationship`, `select()`. Şema değişiklikleri Alembic migration'ı ile versiyonlanır.
- Asenkron gerekiyorsa `asyncio` + `sqlalchemy.ext.asyncio`.

## P9. Bağımlılıklar

- Önce standart kütüphane.
- Projede yüklü olmayan yeni bir paket eklemeden önce **sor**.
- `requirements.txt`'te tam sürüm (`==`); `>=`, `~=` yok.

## P10. Dizin yapısı

| Klasör / dosya | İçerik |
|---|---|
| `src/` | Kaynak kod (yalnızca burada); `config.py` ve `logger.py` dahil |
| `tests/` | Birim testleri (`test_*.py`) |
| `docs/` | Proje dokümantasyonu |
| `plans/` | Tasarım, mimari ve uygulama planı dokümanları (tarihli, sürümlü; §6) |
| `presentations/` | Sunumlar ve sunum kaynakları (varsa) |
| `data/` | Veri dosyaları |
| `logs/` | Log dosyaları |
| `README.md` | Kısa proje özeti ve hızlı başlangıç |
| `PROJE.md` | Asistan için projeye özel bilgi |
| `.env.example` | Gerekli anahtarlar, yalnızca yer tutucularla |
| `requirements.txt` | Paketler, tam sürümle (`==`) |
| `.gitignore` | P0'daki şablon |

## P11. Docker

- `Dockerfile` ve `docker-compose.yml` kök dizinde.
- `slim` ya da `alpine` tabanlı imaj; imaj boyutu küçük tutulur.
- Konteyner non-root kullanıcıyla çalışır.
- Ortam değişkenleri `.env`'den gelir; Dockerfile'a yazılmaz.
- `.dockerignore`: `.env`, `logs/`, `data/`, `tests/`, `docs/`, `plans/`, `presentations/`, `.git/`, cache klasörleri.
