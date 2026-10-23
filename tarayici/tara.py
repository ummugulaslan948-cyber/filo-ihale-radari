"""Filo İhale Radarı – günlük tarama programı.

Haber arama RSS beslemelerinden resmî ihale ilanı sayfalarını bulur,
Basın İlan Kurumu ilan metnini kurallarla ayrıştırır ve yeni İKN'leri
data/ihaleler.json ile data/ihaleler.js dosyalarına ekler.

Yalnızca Python standart kütüphanesi kullanılır; yapay zekâ servisi yoktur.
Çalıştırma:  python tarayici/tara.py
"""
from __future__ import annotations

import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
VERI_JSON = KOK / "data" / "ihaleler.json"
VERI_JS = KOK / "data" / "ihaleler.js"
TR = timezone(timedelta(hours=3))

SORGULAR = [
    '"araç kiralama hizmeti alınacaktır"',
    '"araç kiralama hizmet alımı" ihale',
    '"sürücüsüz araç kiralama"',
    '"şoförsüz araç kiralama"',
    '"taşıt kiralanması" ihale',
    '"binek otomobil" alımı ihale',
    '"hafif ticari araç" alımı ihale',
    '"araç satın alınacaktır"',
]

UA = "Mozilla/5.0 (FiloIhaleRadari; +https://github.com)"
ATLA_ALAN = ("ekap.kik.gov.tr", "ilan.gov.tr", "news.google.com", "bing.com", "msn.com")

ILLER = ["Adana", "Adıyaman", "Afyonkarahisar", "Ağrı", "Aksaray", "Amasya", "Ankara", "Antalya",
    "Ardahan", "Artvin", "Aydın", "Balıkesir", "Bartın", "Batman", "Bayburt", "Bilecik", "Bingöl",
    "Bitlis", "Bolu", "Burdur", "Bursa", "Çanakkale", "Çankırı", "Çorum", "Denizli", "Diyarbakır",
    "Düzce", "Edirne", "Elazığ", "Erzincan", "Erzurum", "Eskişehir", "Gaziantep", "Giresun",
    "Gümüşhane", "Hakkari", "Hatay", "Iğdır", "Isparta", "İstanbul", "İzmir", "Kahramanmaraş",
    "Karabük", "Karaman", "Kars", "Kastamonu", "Kayseri", "Kilis", "Kırıkkale", "Kırklareli",
    "Kırşehir", "Kocaeli", "Konya", "Kütahya", "Malatya", "Manisa", "Mardin", "Mersin", "Muğla",
    "Muş", "Nevşehir", "Niğde", "Ordu", "Osmaniye", "Rize", "Sakarya", "Samsun", "Siirt", "Sinop",
    "Sivas", "Şanlıurfa", "Şırnak", "Tekirdağ", "Tokat", "Trabzon", "Tunceli", "Uşak", "Van",
    "Yalova", "Yozgat", "Zonguldak"]


def kucuk(s: str) -> str:
    """Türkçe kurallarıyla küçük harfe çevirir (İ→i, I→ı)."""
    return s.replace("İ", "i").replace("I", "ı").lower()


# ---------------------------------------------------------------- ağ işlemleri
def getir(url: str, zaman: int = 20) -> tuple[str, str]:
    """Sayfayı indirir; (son adres, metin) döner."""
    istek = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "tr-TR,tr"})
    with urllib.request.urlopen(istek, timeout=zaman) as yanit:
        ham = yanit.read(3_000_000)
        kod = yanit.headers.get_content_charset()
        son = yanit.geturl()
    for k in [kod, "utf-8", "windows-1254", "iso-8859-9"]:
        if not k:
            continue
        try:
            return son, ham.decode(k)
        except (LookupError, UnicodeDecodeError):
            continue
    return son, ham.decode("utf-8", "replace")


def rss_linkleri(sorgu: str) -> list[str]:
    """Bing Haber RSS'inden haber linklerini çıkarır."""
    adres = "https://www.bing.com/news/search?" + urllib.parse.urlencode(
        {"q": sorgu, "format": "rss", "setlang": "tr-TR", "cc": "TR"})
    try:
        _, xml = getir(adres)
        kok = ET.fromstring(xml)
    except Exception as hata:  # ağ veya XML hatası: bu sorguyu atla
        print(f"  ! RSS alınamadı ({sorgu}): {hata}")
        return []
    linkler = []
    for item in kok.iter("item"):
        link = (item.findtext("link") or "").strip()
        q = urllib.parse.parse_qs(urllib.parse.urlparse(link).query)
        if "url" in q:  # Bing yönlendirme linki
            link = q["url"][0]
        if link.startswith("http"):
            linkler.append(link)
    return linkler


def html_metne(h: str) -> str:
    h = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", h)
    h = re.sub(r"(?i)<br\s*/?>|</(p|div|li|tr|h\d|td|th)>", "\n", h)
    h = re.sub(r"<[^>]+>", " ", h)
    h = html.unescape(h).replace("\xa0", " ")
    satirlar = [re.sub(r"[ \t]+", " ", s).strip() for s in h.split("\n")]
    return "\n".join(s for s in satirlar if s)


# ---------------------------------------------------------------- ayrıştırma
IKN_RE = re.compile(r"(?:İ\s*K\s*N|İhale\s+Kayıt\s+(?:No|Numarası)|IKN)\s*[:：.]?\s*(20\d\d\s*/\s*\d{5,8})", re.I)
IKN_GENEL_RE = re.compile(r"\b(20\d\d/\d{6,8})\b")
TARIH_RE = re.compile(
    r"(?:tarih\s+ve\s+saati|tarihi\s+ve\s+saati|son\s+teklif\s+verme\s+tarih[ie]?\s+ve\s+saati)[^:\n]{0,40}:\s*"
    r"(\d{1,2})[./](\d{1,2})[./](20\d\d)\s*[-–,]?\s*(?:saat\s*)?(\d{1,2}[:.]\d{2})?", re.I)
ADI_RE = re.compile(r"(?:^|\n)\s*(?:a\)\s*)?Adı\s*:\s*([^\n]{4,200})", re.I)
KONU_RE = re.compile(r"Niteliği,?\s*türü\s*ve\s*miktarı\s*:\s*([^\n]{4,400})", re.I)
BASLIK_RE = re.compile(r"(?:^|\n)([^\n]{8,250}?)\s+4734\s+sayılı", re.I)
ADRES_RE = re.compile(r"Adresi\s*:\s*([^\n]{4,250})", re.I)
ADET_RE = re.compile(r"(\d{1,4})\s*(?:\([^)]{1,15}\)\s*)?adet", re.I)
SURE_RE = re.compile(r"(\d{1,3})\s*(ay|gün|yıl)\b", re.I)

ARAC_K = ("araç", "taşıt", "otomobil", "binek", "panelvan", "kamyonet", "pick-up", "pikap", "van ", "hafif ticari", "minibüs")
DISLA_K = ("otobüs", "iş makinesi", "iş makinası", "çöp", "kepçe", "greyder", "ekskavatör", "vidanjör",
           "satış ihale", "satılacaktır", "satışı", "kiraya verilecek", "ihale ile satılacak", "hurda", "lastik", "akaryakıt")


def ilgili_mi(metin: str) -> str | None:
    """İlanın filo kapsamında olup olmadığına karar verir, segmenti döner."""
    m = kucuk(metin)
    if any(k in m for k in DISLA_K):
        return None
    if re.search(r"\bkamyon\b|\bkamyonlar", m) and "kamyonet" not in m:
        return None
    if not any(k in m for k in ARAC_K):
        return None
    if re.search(r"kirala|kiralanma", m):
        return "Kiralama"
    if re.search(r"alım|satın al|alınacaktır|temin", m):
        if any(k in m for k in ("hafif ticari", "panelvan", "kamyonet", "pick-up", "pikap", "van ")):
            return "HTA alım"
        if any(k in m for k in ("binek", "otomobil", "sedan")):
            return "Binek alım"
    return None


def surucu_bul(m: str) -> str:
    var = bool(re.search(r"sürücülü|şoförlü", m))
    yok = bool(re.search(r"sürücüsüz|şoförsüz|sürücü\s+(?:ve\s+yakıt\s+)?hariç", m))
    return "Karma" if var and yok else "Sürücülü" if var else "Sürücüsüz" if yok else ""


def il_bul(*metinler: str) -> str:
    for metin in metinler:
        km = kucuk(metin or "")
        for il in sorted(ILLER, key=len, reverse=True):
            if re.search(r"(?<![a-zçğıöşü])" + re.escape(kucuk(il)) + r"(?![a-zçğıöşü])", km):
                return il
    return ""


def kisalt(s: str, n: int = 220) -> str:
    s = re.sub(r"\s+", " ", s).strip(" .:-")
    return s if len(s) <= n else s[: n - 1].rsplit(" ", 1)[0] + "…"


def ayristir(metin: str, kaynak: str, bugun: str) -> dict | None:
    """Bir ilan sayfasının metninden kayıt üretir; uygun değilse None."""
    m_ikn = IKN_RE.search(metin)
    if m_ikn:
        ikn = re.sub(r"\s", "", m_ikn.group(1))
    else:
        tum = set(IKN_GENEL_RE.findall(metin))
        if len(tum) != 1:  # birden fazla veya hiç yoksa yanlış eşleşme riskli
            return None
        ikn = tum.pop()

    m_t = TARIH_RE.search(metin)
    if not m_t:
        return None
    g, a, y, saat = m_t.groups()
    ihale_tarihi = f"{y}-{int(a):02d}-{int(g):02d}"
    saat = (saat or "").replace(".", ":")
    if saat and len(saat) == 4:
        saat = "0" + saat

    m_adi = ADI_RE.search(metin)
    kurum = kisalt(m_adi.group(1), 160) if m_adi else ""
    m_konu = KONU_RE.search(metin)
    m_bas = BASLIK_RE.search(metin)
    konu = kisalt(m_konu.group(1) if m_konu else (m_bas.group(1) if m_bas else ""))
    baslik = m_bas.group(1) if m_bas else ""

    segment = ilgili_mi(f"{baslik} {konu}") or ilgili_mi(metin[:4000])
    if not segment or not kurum:
        return None

    adetler = ADET_RE.findall(konu)
    adet = int(adetler[0]) if len(adetler) == 1 else None
    m_sure = SURE_RE.search(konu) or SURE_RE.search(baslik)
    sure = f"{m_sure.group(1)} {m_sure.group(2).lower()}" if m_sure else ""
    m_adres = ADRES_RE.search(metin)

    return {
        "ikn": ikn,
        "kurum": kurum,
        "il": il_bul(m_adres.group(1) if m_adres else "", kurum),
        "konu": konu,
        "segment": segment,
        "adet": adet,
        "sure": sure,
        "surucu": surucu_bul(kucuk(f"{baslik} {konu}")),
        "ihaleTarihi": ihale_tarihi,
        "saat": saat,
        "yayinTarihi": "",
        "kaynak": kaynak,
        "kaynakAd": urllib.parse.urlparse(kaynak).netloc.removeprefix("www."),
        "eklenme": bugun,
    }


# ---------------------------------------------------------------- veri dosyası
def oku() -> dict:
    if VERI_JSON.exists():
        return json.loads(VERI_JSON.read_text(encoding="utf-8"))
    return {"sonTarama": None, "ihaleler": []}


def yaz(veri: dict) -> None:
    VERI_JSON.parent.mkdir(parents=True, exist_ok=True)
    metin = json.dumps(veri, ensure_ascii=False, indent=1)
    VERI_JSON.write_text(metin + "\n", encoding="utf-8")
    VERI_JS.write_text("window.IHALE_VERISI = " + metin + ";\n", encoding="utf-8")


def main() -> int:
    bugun = datetime.now(TR).date().isoformat()
    veri = oku()
    mevcut = {k["ikn"] for k in veri["ihaleler"]}
    goruldu: set[str] = set()
    yeni: list[dict] = []

    for sorgu in SORGULAR:
        print(f"Sorgu: {sorgu}")
        for link in rss_linkleri(sorgu):
            alan = urllib.parse.urlparse(link).netloc
            if link in goruldu or any(a in alan for a in ATLA_ALAN):
                continue
            goruldu.add(link)
            try:
                son, h = getir(link)
            except Exception as hata:
                print(f"  ! açılamadı: {link} ({hata})")
                continue
            kayit = ayristir(html_metne(h), son, bugun)
            time.sleep(1)  # sitelere nazik davran
            if not kayit:
                continue
            if kayit["ikn"] in mevcut or kayit["ihaleTarihi"] < bugun:
                continue
            mevcut.add(kayit["ikn"])
            yeni.append(kayit)
            print(f"  + {kayit['ikn']} {kayit['kurum']} ({kayit['ihaleTarihi']})")

    veri["ihaleler"].extend(yeni)
    veri["sonTarama"] = {"tarih": bugun, "eklenen": len(yeni)}
    yaz(veri)
    print(f"Bitti: {len(yeni)} yeni ihale, toplam {len(veri['ihaleler'])}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
