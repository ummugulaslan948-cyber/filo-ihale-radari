# Filo İhale Radarı

Kamu kurumlarının araç kiralama, binek ve hafif ticari araç alımı ihalelerini resmî ilanlardan otomatik toplayan, tarayıcıda çalışan bir uygulama.

- **Uygulama:** `index.html`. Bir web adresinden veya bilgisayardan doğrudan açılır.
- **Tarama:** `tarayici/tara.py`. Hafta içi her sabah 07:40'ta GitHub'ın sunucusunda çalışır, yeni ihaleleri `data/` klasörüne ekler.
- Yapay zekâ servisi, ücretli lisans veya sunucu gerekmez. Ücretsiz bir GitHub hesabı yeterlidir.

## Kurulum (yaklaşık 15 dakika)

1. **GitHub hesabı açın:** github.com adresinden ücretsiz hesap oluşturun. Şirket e-postanızı kullanabilirsiniz.
2. **Depo oluşturun:** Sağ üstteki **+** → **New repository**. Adı örneğin `filo-ihale-radari` olsun. **Public** seçin (nedeni aşağıda). **Create repository** deyin.
3. **Dosyaları yükleyin:** Açılan sayfada **uploading an existing file** bağlantısına tıklayın. Zip'ten çıkardığınız klasörün **içindeki** her şeyi sürükleyip bırakın. `.github` klasörü gizli olabilir; görünmüyorsa 3a'ya bakın. **Commit changes** deyin.
   - 3a. `.github/workflows/tara.yml` yüklenmediyse: depoda **Add file → Create new file** deyin. Dosya adına `.github/workflows/tara.yml` yazın ve dosyanın içeriğini yapıştırın.
4. **Taramaya yazma izni verin:** **Settings → Actions → General**. En alttaki **Workflow permissions** bölümünde **Read and write permissions** seçip kaydedin.
5. **Web adresini açın:** **Settings → Pages**. **Source: Deploy from a branch**, **Branch: main**, klasör **/ (root)** seçip kaydedin. 1–2 dakika sonra sayfanın üstünde adres görünür: `https://<kullanıcı-adınız>.github.io/filo-ihale-radari/`
6. **İlk taramayı elle deneyin:** **Actions** sekmesi → **Günlük ihale taraması** → **Run workflow**. Birkaç dakika sürer. Yeşil tik çıkarsa tamamdır. Kırmızı çarpı çıkarsa adımın kaydını açın.

Bundan sonra tarama hafta içi her sabah kendiliğinden çalışır. Uygulama adresini ekiple paylaşabilir, telefonda **Ana ekrana ekle** ile uygulama simgesi gibi kullanabilirsiniz.

## Bilmeniz gerekenler

- **Public depo:** Ücretsiz planda GitHub Pages yalnız public depolarda çalışır. Depodaki bilgiler, yani zaten herkese açık resmî ihale ilanları, herkes tarafından görülebilir. Koordinatörlerin girdiği durum, sorumlu ve notlar depoya **gitmez**; her kişinin kendi tarayıcısında kalır. Gizli bir depo isterseniz GitHub'ın ücretli planı veya şirket içi bir sunucu gerekir.
- **Durumlar kişiseldir:** Herkes kendi tarayıcısında kendi durumlarını görür. Ekip olarak ortak takip için **Excel'e aktar** ile dosya alıp paylaşabilirsiniz. Tam ortak kullanım için BT'nin bir veritabanı sağlaması gerekir.
- **Kaynak:** EKAP ve ilan.gov.tr otomatik taramaya kapalıdır. Program, Bing Haber aramasıyla resmî ilanları yayımlayan haber sitelerini bulur ve ilan metnini kurallarla okur. Her ilanı yakalamayabilir. İKN'si, ihale tarihi veya idare adı okunamayan ilanlar atlanır, araç adedi tek bir sayı değilse boş bırakılır.
- **Kontrol:** Program yeni bir site düzeniyle karşılaşırsa yanlış okuma yapabilir. İlk haftalarda yeni eklenen kayıtları "İlan metni" bağlantısından kontrol edin.

## Ayarlar

- **Arama sorguları:** `tarayici/tara.py` içindeki `SORGULAR` listesi.
- **Dışlanan konular** (otobüs, iş makinesi, satış ihaleleri vb.): aynı dosyada `DISLA_K`.
- **Çalışma saati:** `.github/workflows/tara.yml` içindeki `cron` satırı. Saat UTC'dir, Türkiye saatinden 3 saat geridir.
- **Bir kaydı silmek:** GitHub'da `data/ihaleler.json` dosyasını düzenleyip ilgili bloğu silin. `data/ihaleler.js` bir sonraki taramada yeniden oluşturulur.

## Bilgisayarda denemek

Klasördeki `index.html` dosyasına çift tıklayın; uygulama mevcut veriyle açılır. Taramayı bilgisayarda çalıştırmak için Python 3.10 veya üstü gerekir: `python tarayici/tara.py`
