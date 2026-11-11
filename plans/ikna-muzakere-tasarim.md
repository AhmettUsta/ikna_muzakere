# Müzakere Tarzı Testi — Tasarım

**Sürüm: v5 — 2026-11-11 23:02**

**Sürüm notları**

- v5 — "Cevaplarım" bölümü iki sekme: sorulara verilen cevaplar ve eğitimdeki kâğıt gibi 5 sütunlu cevap anahtarı.
- v4 — Sonuç kartları: sabit bölüm sırası (davranış → uygun → uygun değil → tavsiye → karşı taraf); tavsiye kaynağı sekmeye göre.
- v3 — Kullanıcı kararları: PIN 4 karakter, yalnızca İngilizce harf ve rakam; yönetici ana giriş formundan `ustaoglu` adıyla girer; canlı yorum, kaynaklı yorum sekmesinde "Kişiselleştir" kutusu olarak durur ve şimdilik kapalıdır.
- v2 — Gözden geçirme sonrası: Kaçınmacı slaytlarının sunumdaki haliyle gösterilmesi (7.1), kaynak doğrulama ölçütü ve kullanıcı onay adımı (7.2), Neon'un ilk adım olması (10).
- v1 — İlk tasarım: kapsam, kararlar, yaklaşımlar, içerik ve kullanıcı akışları.

İlgili dokümanlar: [Mimari](ikna-muzakere-mimari.md) · [Uygulama planı](ikna-muzakere-plan.md)

---

## 1. Amaç ve neden

Ümit Anıl'ın (Tribün) "Müzakere" eğitiminde, 30 soruluk A/B formatında bir çatışma tarzı testi çözülüyor. Cevaplar, beş müzakere tarzına puan olarak dağıtılıyor: Rekabetçi, İşbirlikçi, Uzlaşmacı, Kaçınmacı ve İltifatkar. Eğitim sunumu her tarz için yorum ve tavsiyeler içeriyor.

Bu proje, testi bir web sitesine taşır. Kişi soruları çözer, puanlarını ve tarz profilini görür, profiline göre yorum ve tavsiye okur.

- **Neden:** Kullanıcının **portföy ve öğrenme projesi**. Kullanıcılar, linki doğrudan paylaşılan ekip arkadaşları ve birkaç tanıdık.
- **Başarı:** Linki alan biri testi telefondan ya da bilgisayardan zahmetsizce çözer, sonucunu anlaşılır bir grafikle görür, tarzına uygun somut tavsiyeler okur. Sonradan takma adı ve PIN'iyle dönüp sonucuna tekrar bakabilir. Site sahibi tüm sonuçları sitedeki basit bir yönetici ekranından görür.

## 2. Hedefler, kapsam dışı olanlar, istenmeyenler

**Hedefler**

- 30 soruyu adım adım sormak; cevaplara göre beş tarzın puanını hesaplamak.
- Puanları yüksek / orta / düşük olarak sınıflandırmak ve iki eksenli grafikte göstermek.
- İki katmanlı yorum sunmak: sunum metinleri ve kaynaklarla genişletilmiş, önceden hazırlanmış yorumlar. İsteyene ayrıca canlı yapay zekâ yorumu.
- Takma ad ve PIN ile anonim kayıt; aynı kişinin geri dönüp geçmiş sonuçlarını görmesi.
- Site sahibine basit bir yönetici görünümü.
- Tamamen ücretsiz barındırma.

**Kapsam dışı (şimdilik)**

- Gerçek ad, e-posta, telefon gibi kimlik bilgisi toplamak.
- Ekip karşılaştırması, istatistik paneli, dışa aktarma, PDF; yöneticide "kişi gibi görmek" dışında ek özellik.
- Çoklu dil (yalnızca Türkçe).
- Sunumdaki "masa taktikleri", "itiraz karşılama" gibi bölümler; yalnızca beş tarzla ilgili içerik kullanılır.

**İstenmeyenler** (teknik olarak çalışsa bile başarısızlık sayılır)

- Sitenin arama motorlarında çıkması ya da içeriğin yaygınlaşması.
- Bir kişinin başkasının sonucunu görebilmesi (yönetici hariç).
- Testin psikolojik tanı ya da kişilik analizi gibi sunulması. Test, çatışma anındaki davranış tercihini gösterir.
- Yapay zekânın kaynakta olmayan bilgiyi kaynaklıymış gibi sunması.
- Kişinin haberi olmadan verisinin üçüncü bir tarafa (Google) gönderilmesi.

## 3. Kısıtlar

- **Telif:** Sorular, cevap anahtarı ve eşikler, Thomas–Kilmann Çatışma Tarzları Envanteri (TKI) ile aynı yapıda. Sunum metinleri "Copyright Tribün" ibaresi taşıyor. Kullanıcı orijinal içeriği kullanmayı ve bu riski bilerek üstlendi. Bu yüzden site arama motorlarına kapalı tutulur; yalnızca linkle paylaşılır.
- **Maliyet:** Sıfır. Barındırma, veritabanı ve yapay zekâ ücretsiz katmanlarla karşılanır.
- **Proje kuralları:** AGENTS.md'deki Python standartları geçerlidir: `src/config.py`, `src/logger.py`, step sınıfları ve orkestratör, `pytest`, tam sürümlü bağımlılıklar.
- **Commit ve push yok:** Kullanıcı istemedikçe yapılmaz. Render, GitHub'daki depodan yayın alır. Depoyu kullanıcı oluşturur, push'u kullanıcı yapar ya da açıkça ister.

## 4. Değerlendirilen yaklaşımlar

| Yaklaşım | Artı | Eksi | Karar |
|---|---|---|---|
| **Tek Python uygulaması** (FastAPI + sunucuda üretilen sayfalar + az JavaScript) | Tek kod tabanı, tek Docker imajı; AGENTS.md kurallarına tam uyar; Render'a doğrudan uyar | Arayüz, tek sayfa uygulamalar kadar akıcı değil | **Seçildi** |
| FastAPI API + React arayüz | En modern görünüm; portföyde frontend de gösterilir | İki proje, iki dil; kabaca iki kat iş | Elendi |
| Streamlit | En hızlı | Özelleştirmesi zor; PIN, yönetici ve adım adım akış zorlama olur; portföyde zayıf | Elendi |

**Barındırma:** Render ücretsiz web servisi seçildi. Kredi kartı istemiyor. Servis 15 dakika boşta kalınca uyur ve ilk istek yaklaşık 1 dakika bekler; bu kabul edildi. Elenen seçenekler:

- Şirketin AWS hesabı: ücretli ve şirket onayı gerekir.
- Kullanıcının kendi bilgisayarı ve tünel: bilgisayar kapalıyken site de kapalı olur.
- Fly.io, Koyeb ve Vercel: ücretsiz değil ya da FastAPI'ye uygun değil.

**Veritabanı:** Neon ücretsiz PostgreSQL seçildi. Süre sınırı yok ve 1 GB yer veriyor. Kullanıcının verdiği şirket RDS'i iki nedenle elendi: şirket kuralları ve dışarıdan erişim izni belirsiz, ayrıca test sunucusu sıfırlanabilir. Render'ın ücretsiz veritabanı da 30 günde silindiği için elendi.

**Yorum üretimi:** Önceden hazırlanmış yorumlar ve isteğe bağlı canlı Gemini yorumu seçildi. Elenen seçenekler:

- Yalnızca canlı yapay zekâ: ücretli ya da ücretsiz katmanın sınırlarına takılır.
- Yalnızca sunum metinleri: kişinin profiline özel hiçbir yorum sunmaz.

## 5. Kullanıcının verdiği kararlar

1. Orijinal sorular, cevap anahtarı, eşikler ve sunum metinleri kullanılır.
2. Kişi gerçek adını değil, bir **takma ad** girer. Takma ad ve **4 karakterli PIN** ile kayıt olur ve tekrar giriş yapar. PIN yalnızca İngilizce harf ve rakam içerebilir (Türkçe karakter, sembol ve boşluk yok; büyük-küçük harf ayrımı var).
3. Sonuçlar veritabanında saklanır. Herkes yalnızca kendi cevaplarını ve sonuçlarını görür.
4. **Yönetici ekranı:** Site sahibi, ana sayfadaki giriş formuna takma ad olarak yönetici adını (`ustaoglu`) ve yönetici şifresini yazınca doğrudan yönetici ekranına girer; `/yonetici` adresi de çalışır. Yönetici adı aday olarak kaydedilemez. Site sahibi adayların takma ad listesinden birini seçer ve onun gördüğü sonuç ekranını aynen görür. Şimdilik ek bir özellik yoktur.
5. **Yorumlar** (sonuç sayfasında iki seçenek):
   1. **Sunum metinleri:** Varsayılan seçenek. Eğitimdeki hazır metinler gösterilir.
   2. **Kaynaklarla genişletilmiş yorum:** Önceden hazırlanmış, akademik kaynaklara dayalı ve kaynakçalı yorumlar. "Yapay zekâ yardımıyla hazırlanmıştır" uyarısı taşır.
   3. Kaynaklı yorumların altında bir **"Kişiselleştir"** kutusu bulunur. Açıkken, uyarı onaylandıktan sonra Gemini'den profile özel yorum ister; üretilen yorum kaydedilir. **Şimdilik kapalıdır ve tıklanamaz**; `LIVE_COMMENT_ENABLED` ayarıyla açılır.
6. Barındırma Render (ücretsiz), veritabanı Neon (ücretsiz), mimari tek Python uygulaması.

## 6. Puanlama

- **Sorular:** 30 soru vardır; her soruda iki ifade (A ve B) bulunur. Kişi kendine daha yakın olanı seçer. Sorular `docs/` altındaki üç fotoğraftan metne aktarılır: `Image.jpeg` 1–10. sorular, `Image (1).jpeg` 11–20, `Image (2).jpeg` 21–30.
- **Cevap anahtarı:** Her cevap, tam olarak bir tarza 1 puan verir (Ek A). Beş puanın toplamı her zaman 30'dur.
- **Seviyeler:** Eşikler sunumdan alınmıştır. Puan, "yüksek" eşiğine eşit ya da üstündeyse **yüksek**, "düşük" eşiğine eşit ya da altındaysa **düşük**, arada kalırsa **orta** sayılır.

| Tarz | Yüksek (≥) | Düşük (≤) |
|---|---|---|
| Rekabetçi | 8 | 3 |
| İşbirlikçi | 10 | 5 |
| Uzlaşmacı | 9 | 4 |
| Kaçınmacı | 8 | 4 |
| İltifatkar | 7 | 3 |

- **Grafik:** Dikey eksen "kendi ilgisini tatmin" (iddialılık), yatay eksen "karşı tarafın ilgisini tatmin" (işbirliği) olan iki eksenli diyagramda beş tarz klasik konumlarında durur:
  - sol üst: Rekabetçi
  - sağ üst: İşbirlikçi
  - orta: Uzlaşmacı
  - sol alt: Kaçınmacı
  - sağ alt: İltifatkar

  Her tarzın balonu ya da etiketi, kişinin puanını ve seviyesini gösterir. Bu düzen sunumdaki "Müzakerede durumsallık" diyagramının ve kullanıcının el çizimi notunun karşılığıdır.
- **Doğrulama:** Kullanıcının kendi cevap kâğıdı (Ek A'nın altında) bu anahtarla 9-7-6-3-5 sonucunu verir; elle hesaplanan sonuçla aynıdır.

## 7. Yorum içeriği

### 7.1 Sunum metinleri (1. seçenek)

Sunumdan her tarz için şu bölümler alınır; metin değiştirilmez:

- **Davranış özellikleri:** Örneğin "Rekabetçi — mücadeleci davranış".
- **Uygun olduğu koşullar.**
- **Uygun olmadığı koşullar.**
- **"Siz bu tarzdaysanız"** tavsiyeleri.
- **"Karşı taraf bu tarzdaysa"** tavsiyeleri: başa çıkma ya da yararlanma yolları.

**Kaçınmacı istisnası (kullanıcının kararı):** Sunumda bu tarzın "Uygun olmadığı koşullar" slaytı yok. Onun yerine iki ayrı slayt var: "Kaçınmacı yaklaşımın gerekli olduğu durumlar" ve "Kaçınmacı Yaklaşımın Uygun Olduğu Koşullar". İkincisinin içeriği İltifatkar tarzına ait gibi görünse de iki slayt da **kendi başlıklarıyla, olduğu gibi** gösterilir. "Uygun olmadığı koşullar" bölümü bu tarzda yer almaz.

Buna göre içerik, sabit beş bölüm yerine **sunumdaki başlıklarıyla sıralı bir bölüm listesi** olarak tutulur. Her bölümün bir türü vardır: `davranis`, `uygun`, `uygun_degil`, `siz_iseniz`, `karsi_taraf`. Kaçınmacı tarzında `uygun` türünde iki bölüm bulunur, `uygun_degil` türünde bölüm bulunmaz. Diğer dört tarzda her türden tam olarak bir bölüm vardır.

Gösterim kuralı (kullanıcı kararı, v4): Her tarz bir kart olarak gösterilir; bölümler sunumdaki sıradan bağımsız olarak şu **sabit sırayla** gelir:

1. **Nasıl davranır** (`davranis`)
2. **Uygun olduğu koşullar** (`uygun`; Kaçınmacı'da iki slayt kendi başlıklarıyla)
3. **Uygun olmadığı koşullar** (`uygun_degil`; Kaçınmacı'da "sunumda ayrı bölüm yok" notu)
4. **Size tavsiyeler** — kaynağı sekmeye göre değişir:
   - *Sunum yorumları* sekmesi: yüksek seviyede "Siz … iseniz" maddeleri; orta ve düşükte kısa bir not ("Bu tarzı az / orta düzeyde kullanıyorsunuz…") ve "Bu tarzı kullandığınızda dikkat edin" başlığıyla aynı maddeler.
   - *Kaynaklarla genişletilmiş yorum* sekmesi: o tarz ve seviyeye ait kaynaklı bloğun "Gelişim için" paragrafı ("kaynaklı öneri" etiketiyle).
5. **Karşınızda bu tarzda biri varsa** (`karsi_taraf`)

Yüksek seviyedeki kartlar açık, diğerleri kapalı başlar. Kaynaklı sekmede ayrıca en üstte profil yorumu, "Nasıl davranır" altında "Kaynaklara göre" açıklaması ve en altta kaynakça bulunur.

### 7.2 Kaynaklarla genişletilmiş yorum (2. seçenek)

- **Kaynak paketi:** Uygulamadan önce, çatışma tarzları üzerine güvenilir kaynaklar araştırılır ve doğrulanır. Adaylar:
  - Thomas & Kilmann (1974) TKI ve Thomas (1976/1992) çatışma modeli,
  - Blake & Mouton (1964) Yönetim Izgarası,
  - Pruitt & Rubin (1986) ve Pruitt & Carnevale (1993) iki yönlü ilgi kuramı,
  - Rahim (1983) ROCI-II,
  - Fisher & Ury (1981) *Getting to Yes*,
  - De Dreu ve arkadaşlarının (2001) çatışma yönetimi çalışmaları.

  Her kaynak için kısa bir özet ve tam kaynakça yazılır.
- **Doğrulama ölçütü** (benim kararım): Eserin gerçekten var olduğu ve kaynakça bilgisinin doğru olduğu yayıncı, kütüphane ya da akademik dizin kayıtlarından kontrol edilir. Kaynakça bilgisi; yazar, yıl, başlık, yayıncı ya da dergi ve DOI'dir (varsa). Bu şekilde doğrulanamayan kaynak kullanılmaz.
  - Kitapların ve kılavuzların tam metni çoğunlukla erişilebilir değildir. Bu yüzden metinler, bu eserlerin akademik literatürde yaygın olarak aktarılan içeriğini özetler: modelin iki ekseni, beş tarzın tanımı, tarzların uygun olduğu durumlar. Kaynakta açıkça yer almayan sayısal iddia ya da alıntı yazılmaz.
- **Kullanıcı onayı:** Kaynak paketi, 15 blok ve 20 profil yorumu yayına girmeden önce kullanıcı tarafından okunur ve onaylanır. Bu, uygulama planında ayrı bir adımdır.
- **Metinler:**
  - **Tarz–seviye blokları:** 5 tarz × 3 seviye = 15 blok. Her blokta tarzın akademik tanımı, güçlü ve riskli yönleri, gelişim önerileri ve kaynak atıfları bulunur.
  - **Profil yorumları:** Kişinin **en baskın** tarzı ile **en az kullandığı** tarzın birleşimine göre yazılır; 5 × 4 = 20 metin. Profil yorumu, bu ikisinin birlikte ne anlama geldiğini ve hangi durumlarda zorluk çıkarabileceğini anlatır.
- **Baskın ve en az kullanılan tarzın belirlenmesi** (benim kararım): Eşikler tarzlar arasında farklı olduğu için ham puan değil, göreli puan karşılaştırılır:

  `göreli = (puan − düşük eşik) / (yüksek eşik − düşük eşik)`

  En yüksek göreli puan baskın tarz, en düşük göreli puan en az kullanılan tarzdır. Eşitlikte sabit sıra uygulanır: Rekabetçi, İşbirlikçi, Uzlaşmacı, Kaçınmacı, İltifatkar.
- **Uyarı:** Bölümün başında şu metin yer alır: "Bu yorumlar akademik kaynaklardan yararlanılarak yapay zekâ yardımıyla hazırlanmıştır; profilinize göre seçilir, size özel yazılmamıştır. Psikolojik değerlendirme yerine geçmez."

### 7.3 Canlı yapay zekâ yorumu (isteğe bağlı)

- **Görünüm:** Sonuç sayfasının en altında küçük, ikincil bir düğme olarak durur.
- **Onay penceresi:** Düğmeye basılınca bir onay penceresi açılır:
  - Yorumu Google Gemini yazacaktır ve hata içerebilir.
  - Google'a yalnızca beş puan ve seviyeler gönderilir; takma ad gönderilmez.
  - Ücretsiz katmanda Google, gönderilen veriyi ürün geliştirmek için kullanabilir ve insanlar okuyabilir.
- **Kişi onaylarsa:** Gemini'ye puanlar, seviyeler ve 7.2'deki kaynak paketi gönderilir. Yapay zekâya yalnızca bu paketi kullanması ve her tespit için kaynak belirtmesi söylenir.
- **Sonuç:**
  - Yorum o denemeye bağlı olarak kaydedilir. Aynı denemede düğme bir daha çalışmaz; kayıtlı yorum gösterilir.
  - Kota dolarsa ya da hata olursa "Şu anda canlı yorum üretilemiyor, daha sonra tekrar deneyin" mesajı gösterilir. Sayfanın geri kalanı etkilenmez.

## 8. Kullanıcı akışları

**Aday**

1. **Giriş sayfası:** Testin ne olduğu iki cümleyle anlatılır ve "kişilik testi değildir" notu yer alır. Kişi "Teste başla" ya da "Sonucuma bak" seçeneklerinden birini seçer.
2. **Teste başla:** Kişi bir takma ad ve 4 haneli PIN girer (PIN iki kez yazılır). Takma ad alınmışsa başka bir ad istenir.
3. **Test:** Her ekranda bir soru gösterilir. A ya da B'ye dokununca sonraki soruya geçilir. İlerleme çubuğu (ör. "12 / 30") ve "geri" düğmesi bulunur. Son soruda "Bitir" düğmesi çıkar.
4. **Sonuç sayfası:**
   - Puan tablosu ve seviyeler.
   - İki eksenli grafik.
   - Yorum sekmeleri: "Sunum yorumları" ve "Kaynaklarla genişletilmiş yorum".
   - En altta canlı yapay zekâ düğmesi.
   - Katlanabilir "Cevaplarım" bölümü, iki sekme:
     - "Sorulara cevaplarım": her soruda A ve B şıkkı, seçilen işaretli.
     - "Cevap anahtarım": eğitimdeki kâğıt gibi 30 satır × 5 tarz sütunu; A ve B kendi tarzının sütununda, seçilen hücre taralı, altta sütun toplamları (puanlar).
5. **Sonucuma bak:** Kişi takma adını ve PIN'ini girer. En son sonucu açılır; önceki denemeleri tarih listesi olarak görür ve "Testi tekrar çöz" diyebilir.

**Yönetici**

1. `/yonetici` adresinden şifreyle girer.
2. Takma ad listesini görür: takma ad, deneme sayısı, son deneme tarihi.
3. Bir takma adı seçince o kişinin "Sonucuma bak" ekranını aynen görür. Yönetici kendi oturumundan çıkmaz, yalnızca görüntüler; adayın verisi değişmez.

## 9. Güvenlik ve gizlilik (benim kararlarım)

- PIN düz metin olarak saklanmaz; standart kütüphanedeki `hashlib.scrypt` ile tuzlanmış özet olarak tutulur.
- Aynı takma adla art arda 5 yanlış PIN girilirse o takma ad 15 dakika kilitlenir. 4 haneli bir PIN'in deneme yoluyla bulunmasını engellemek için.
- Yönetici şifresi ve oturum anahtarı `.env` → `Config` üzerinden okunur. Oturum, imzalı bir çerezle tutulur.
- Bütün sayfalarda `noindex` etiketi bulunur; `robots.txt` her şeyi kapatır.
- Loglara PIN, şifre ve API anahtarı yazılmaz.
- Takma ad dışında hiçbir kişisel veri alınmaz; IP adresi veritabanına yazılmaz.

## 10. Kurulum için kullanıcıdan gerekenler

Bunları yalnızca kullanıcı yapabilir; plan bu adımları kullanıcıya yönlendirir:

1. **İlk iş olarak** Neon hesabı açıp veritabanı bağlantı bilgilerini vermek. Geliştirme, test ve yayın aynı Neon veritabanını kullanır. Şirket RDS'i hiçbir aşamada kullanılmaz ve bilgileri `.env`'den çıkarılır. Neon hazır olana kadar yalnızca veritabanı gerektirmeyen işler yapılır: puanlama, içerik, sayfalar.
2. Google AI Studio'dan Gemini API anahtarı almak.
3. Bir GitHub hesabı ve gizli (private) depo açmak; kodu push etmek ya da push'u açıkça istemek.
4. Render hesabı açıp depoyu bağlamak ve ortam değişkenini Render'a girmek.
5. Yönetici şifresini belirlemek.

## 11. Uygulayıcıya bırakılanlar

- Sayfa tasarımının ayrıntıları: renkler, yazı tipleri, boşluklar. Sade, telefonda okunur ve sunumun tonuna uygun olmalı.
- Grafiğin çizim yöntemi (sunucuda üretilen SVG önerilir) ve balon boyutlarının ölçeği.
- Kaynak paketinin ve yorum metinlerinin tam metni. 7.2'deki kurallar ve kaynak doğrulaması şartıyla.
- Hata sayfalarının metinleri.

---

## Ek A — Cevap anahtarı

Her soruda A ve B'nin puan verdiği tarz. Kısaltmalar: R = Rekabetçi, İ = İşbirlikçi, U = Uzlaşmacı, K = Kaçınmacı, D = İltifatkar (düzeltmeci).

| Soru | A | B | | Soru | A | B | | Soru | A | B |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | K | D | | 11 | İ | D | | 21 | D | İ |
| 2 | U | İ | | 12 | K | U | | 22 | U | R |
| 3 | R | D | | 13 | U | R | | 23 | İ | K |
| 4 | U | D | | 14 | İ | R | | 24 | D | U |
| 5 | İ | K | | 15 | D | K | | 25 | R | D |
| 6 | K | R | | 16 | D | R | | 26 | U | İ |
| 7 | K | U | | 17 | R | K | | 27 | K | D |
| 8 | R | İ | | 18 | D | U | | 28 | R | İ |
| 9 | K | R | | 19 | İ | K | | 29 | U | K |
| 10 | R | U | | 20 | İ | U | | 30 | D | İ |

Kaynak: `docs/Image (3).jpeg`. Anahtar, yayımlanmış TKI anahtarıyla da karşılaştırıldı ve tutarlı çıktı.

**Doğrulama örneği:** Kullanıcının cevapları şöyle:

1A 2B 3B 4A 5B 6B 7B 8B 9B 10B 11B 12B 13B 14B 15A 16B 17A 18A 19A 20B 21B 22B 23A 24B 25A 26B 27B 28A 29B 30B

Bu cevaplar anahtara göre şu sonucu verir:

| Tarz | Puan | Seviye |
|---|---|---|
| Rekabetçi | 9 | yüksek |
| İşbirlikçi | 7 | orta |
| Uzlaşmacı | 6 | orta |
| Kaçınmacı | 3 | düşük |
| İltifatkar | 5 | orta |

Bu örnek, puanlama testinde sabit bir test vakası olarak kullanılır.
