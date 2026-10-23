"""Ayrıştırıcı testleri. Çalıştırma: python -m unittest tarayici/test_tara.py

Örnek metinler Basın İlan Kurumu ihale ilanlarının standart düzenini taklit eden
deneme metinleridir; gerçek bir ilandan kopyalanmamıştır.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import tara  # noqa: E402

KIRALAMA = """ARAÇ KİRALAMA HİZMETİ ALINACAKTIR
ÖRNEK İL SAĞLIK MÜDÜRLÜĞÜ
Araç Kiralama Hizmet Alımı hizmet alımı 4734 sayılı Kamu İhale Kanununun 19 uncu maddesine göre açık ihale usulü ile ihale edilecektir.
İhale Kayıt Numarası : 2026/1234567
1-İdarenin
a) Adı : ÇANKIRI ÖRNEK İL SAĞLIK MÜDÜRLÜĞÜ
b) Adresi : Örnek Mah. Örnek Cad. No:1 MERKEZ/ÇANKIRI
2-İhale konusu hizmet alımının
a) Niteliği, türü ve miktarı : 12 Ay Süreli 25 Adet Araç Kiralama (8 Sürücülü, 17 Sürücüsüz)
3- İhalenin
a) İhale usulü : Açık İhale
b) İhale (son teklif verme) tarih ve saati : 20.11.2026 - 10:00
"""

HTA_ALIM = """ARAÇ SATIN ALINACAKTIR
1 Adet Hafif Ticari Araç (Camlı Van) Alımı mal alımı 4734 sayılı Kamu İhale Kanununun 19 uncu maddesine göre açık ihale usulü ile ihale edilecektir.
İKN : 2026/7330640
1-İdarenin
a) Adı : ÖRNEK BELEDİYE BAŞKANLIĞI GELİRLER MÜDÜRLÜĞÜ
b) Adresi : Merkez/YOZGAT
2-İhale konusu malın
a) Niteliği, türü ve miktarı : 1 Adet Hafif Ticari Araç (Camlı Van)
3- İhalenin
b) İhale (son teklif verme) tarih ve saati : 11.12.2026 - 10:00
"""

OTOBUS = HTA_ALIM.replace("Hafif Ticari Araç (Camlı Van)", "Dizel Şehir İçi Otobüs")

SATIS = """ARAÇ SATIŞ İHALE İLANI
İhale Kayıt Numarası : 2026/5555555
a) Adı : ÖRNEK BELEDİYESİ
Niteliği, türü ve miktarı : 37 adet ikinci el binek otomobil ihale ile satılacaktır
tarih ve saati : 05.12.2026 - 14:00
"""


class Ayristirma(unittest.TestCase):
    def test_kiralama(self):
        k = tara.ayristir(KIRALAMA, "https://ornek.example/ilan", "2026-10-23")
        self.assertEqual(k["ikn"], "2026/1234567")
        self.assertEqual(k["segment"], "Kiralama")
        self.assertEqual(k["ihaleTarihi"], "2026-11-20")
        self.assertEqual(k["saat"], "10:00")
        self.assertEqual(k["adet"], 25)
        self.assertEqual(k["sure"], "12 ay")
        self.assertEqual(k["surucu"], "Karma")
        self.assertEqual(k["il"], "Çankırı")
        self.assertIn("SAĞLIK", k["kurum"])

    def test_hta_alim(self):
        k = tara.ayristir(HTA_ALIM, "https://ornek.example/2", "2026-10-23")
        self.assertEqual(k["segment"], "HTA alım")
        self.assertEqual(k["ikn"], "2026/7330640")
        self.assertEqual(k["il"], "Yozgat")
        self.assertEqual(k["adet"], 1)

    def test_otobus_elenir(self):
        self.assertIsNone(tara.ayristir(OTOBUS, "https://ornek.example/3", "2026-10-23"))

    def test_satis_elenir(self):
        self.assertIsNone(tara.ayristir(SATIS, "https://ornek.example/4", "2026-10-23"))

    def test_html_metne(self):
        m = tara.html_metne("<p>a) Adı : X<br>b) Adresi : Y</p><script>z()</script>")
        self.assertEqual(m, "a) Adı : X\nb) Adresi : Y")

    def test_turkce_kucuk(self):
        self.assertEqual(tara.kucuk("İHALE IŞIK"), "ihale ışık")


if __name__ == "__main__":
    unittest.main()
