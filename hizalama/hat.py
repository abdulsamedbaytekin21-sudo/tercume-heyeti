#!/usr/bin/env python3
"""Mukabeleci: Konuk Fusûs şerhinden bir fassın Arapça-Türkçe hizalama hattı (sürüm hat-0.3.1, G-037).

Girdi : G-022 çıktısı temiz.jsonl (blok başına sayfa, sira, tur, dil, metin).
Çıktı : <cikti>/fass-NN.jsonl           (duzey=pasaj | cumle; kayıt başına kalıcı kimlik + sürüm)
        <cikti>/fass-NN.alinti.jsonl     (şerh içi ayet/hadis/beyit; eğitim çifti DEĞİL)
        <cikti>/fass-NN.dipnot.jsonl     (neşir dipnotları; hizalamaya karışmaz)

Katlar:
 1. Yapısal çapa  : fass başlığı -> sonraki fass başlığı (basmala) arası.
 2. Pasaj         : Arapça blok serisi + hemen ardından gelen Türkçe 'terceme' serisi = çift.
                    "Ya'ni ..." paragrafı Konuk'un îzâhıdır, çifte girmez (tr_izah).
                    Satır içi Arapçanın böldüğü Türkçe paragraf birleştirilir.
 3. Cümle/öbek    : Gale-Church tipi uzunluk DP'si + az sayıda bağlaç çapası (1-n, n-1, n-m).
                    Anlamsal doğrulama YOKTUR; güven tavanı düşüktür, eşik altı 'inceleme: insan'.
 4. Terim adayları: bu görevde kurulmadı.

Gömme modeli (LaBSE, BGE-M3) bu ortamda yok; ölçülmedi. Yöntem 'kural+uzunluk-DP'dir.
Telifli metin yalnız veri/kasa/ altına yazılır; bu dosya veri içermez.
"""
import argparse
import hashlib
import json
import math
import os
import re
import sys
import unicodedata

SURUM = "hat-0.3.1"
ESIK_INCELEME = 0.60
ESIK_BANT_ALT = 0.55   # 0.55 <= pasaj güveni < 0.60: pasaj 'kenar'; satır güveni belirleyici (G-032, Ö-eşik)
# Sözcük oranı (ln TR/AR) dağılımı: fass-1..14 havuzundan SÜRÜME SABİTLENDİ (G-032). Bir pasajın puanı başka
# pasajların metnine bağlı değildir. sd(n) = sqrt(SD0^2 + C/n): kısa pasajda oran doğal olarak daha gürültülü.
ORAN_ORT_LN = 0.24   # havuz medyanı: oran 1.27 (347 pasaj, fass 1-14; fass medyanları 1.21-1.44)
ORAN_SD0 = 0.12   # havuz MAD-sd 0.107, std 0.117
ORAN_C = 0.3         # n=7: sd 0.43, n=11: 0.20, n=22: 0.13, n>=40: ~0.10 (MAD)
# Cilt ayarları (G-032): cilt -> (girdi, çıktı, kimlik öneki, fass başlığı için en küçük PDF sayfası)
CILT_AYAR = {
    1: {"girdi": "veri/kasa/metin/konuk1/temiz.jsonl", "cikti": "veri/kasa/hizalama/fusus-konuk", "kimlik": "fusus-konuk", "min_sayfa": 40, "son_baslik": None},
}


def cilt_ayari(cilt):
    if cilt in CILT_AYAR:
        return CILT_AYAR[cilt]
    return {"girdi": "veri/kasa/metin/konuk%d/temiz.jsonl" % cilt, "cikti": "veri/kasa/hizalama/fusus-konuk-c%d" % cilt,
            "kimlik": "fusus-konuk-c%d" % cilt, "min_sayfa": 0, "son_baslik": r"^(LUGATÇE|KAYNAKÇA|ÂYET İNDEKSİ)$"}

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "metin"))
try:
    from normallestir import normalize_ar as _norm_ar
except Exception:  # pragma: no cover
    _norm_ar = None

TASHKEEL = re.compile("[ً-ْٰٓ-ٕۖ-ۭ]")
FARSI_ONLY = re.compile("[گچپژیۀہ]")
AR_LETTER = re.compile("[ء-يٱ-ەگچپژ]")
LATIN_LOWER = re.compile(r"^[a-zâîûçşğöüıé]")
PAGE_MARK = re.compile(r"\s*\[(\d+)/(\d+[a-z]?)\]\s*")
FN_REF = re.compile(r"\[\^(\d+)\]")
INLINE_AR = re.compile("[؀-ۿ]")


def norm_ar(t):
    t = unicodedata.normalize("NFC", t)
    if _norm_ar:
        t = _norm_ar(t)
    else:
        t = TASHKEEL.sub("", t).replace("ـ", "")
        t = t.translate(str.maketrans("أإآٱ", "اااا"))
    t = t.replace("ک", "ك").replace("ی", "ي").replace("ى", "ي")
    return t


# ---------------------------------------------------------------- yükleme / çapa

def yukle(yol):
    with open(yol, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def fass_sinirlari(bloklar, no=1, min_sayfa=40, son_baslik=None):
    """Fass başlığı (Arapça 'فص حكمة ...') bloğundan sonraki fass başlığının basmalasına kadar.

    Dönüş: (baslik_idx, bitis_idx_dahil_degil). no: 1 = ilk fass.
    """
    basliklar = []
    for i, b in enumerate(bloklar):
        if b["tur"] == "arapca" and norm_ar(b["metin"]).startswith("فص حكمة") and b["sayfa"] > min_sayfa:
            basliklar.append(i)
    if len(basliklar) < no:
        raise ValueError("fass başlığı bulunamadı")
    bas = basliklar[no - 1]
    bit = basliklar[no] if len(basliklar) > no else len(bloklar)
    if son_baslik and bit == len(bloklar):
        # cildin son fassı: Lugatçe/Kaynakça/dizinler Fusûs metni değildir (G-034)
        for i in range(bas, len(bloklar)):
            if bloklar[i]["tur"] == "baslik" and re.match(son_baslik, bloklar[i]["metin"].strip()):
                bit = i
                break
    # sonraki fassın başındaki basmala/numara bloklarını dışarıda bırak
    while bit > bas and bloklar[bit - 1]["tur"] in ("arapca", "serh") and len(bloklar[bit - 1]["metin"]) <= 3:
        bit -= 1
    # fass sonundaki ibtidâ/intihâ kolofonu (baslik) çıkar
    while bit > bas and bloklar[bit - 1]["tur"] in ("baslik", "baslik_sayfa") and re.match(
        r"(İbtidâ|İntihâ|\d|\[)", bloklar[bit - 1]["metin"]
    ):
        bit -= 1
    return bas, bit


# ---------------------------------------------------------------- Türkçe metin işleme

IZAFET = {"i", "ı", "yı", "yi", "u", "ü"}  # 'ât-ı', 'hikmet-i': gerçek izâfet tiresi korunur
ATIF_RE = re.compile(r"\((?:[^()]*\d+/\d+[^()]*)\)")        # "(Nisâ, 4/1)" neşir atfı
ILAVE_RE = re.compile(r"\[[^\[\]]*\]")                      # köşeli parantez = neşir heyeti ilavesi (G-025)
ARMARK_RE = re.compile(r"\{ar:[^}]*\}")


def satir_birlestir(satirlar, birlesmeler=None):
    """Fiziksel satırları birleştirir; satır sonu tireyi kaldırır (izâfet 'ât-ı' gibi kısa devamlar hariç).

    birlesmeler (liste) verilirse her tire kararı (sol, sag, birlesti_mi) olarak eklenir (bütünlük bayrağı için).
    """
    out = ""
    for s in satirlar:
        s = s.strip()
        if not s:
            continue
        if out.endswith("-") and out[-2:-1].isalpha():
            ilk = re.split(r"[\s,.;:?!”’)\]]", s, maxsplit=1)[0]
            sol = re.split(r"[\s(\[“‘]", out[:-1])[-1]
            if ilk[:1].islower() and ilk not in IZAFET:
                out = out[:-1] + s  # hece bölünmesi: 'üze-/re' -> 'üzere'
                birles = True
            else:
                out += s
                birles = False
            if birlesmeler is not None:
                birlesmeler.append((sol, ilk, birles))
            continue
        out = (out + " " + s) if out else s
    return out


def sayfa_dipnot_ayikla(tr):
    """Sayfa işaretleri ([1/64]) ve dipnot atıflarını ([^7]) çıkarır. Dönüş: (metin, sayfa_isaretleri, dipnot_ref)."""
    fn = [int(x) for x in FN_REF.findall(tr)]
    t = FN_REF.sub("", tr)
    sayfa = [m.group(0).strip() for m in PAGE_MARK.finditer(t)]
    t = PAGE_MARK.sub(" ", t)
    return re.sub(r"\s+", " ", t).strip(), sayfa, fn


def _duzelt_bosluk(t):
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"\s+([,.;:?!])", r"\1", t)
    return t.strip()


def parantezsiz(t):
    """Öğretici çiftin Türkçe tarafı: köşeli parantez (neşir ilavesi), atıf parantezi ve {ar:...} parçaları çıkarılır."""
    # Karar (G-027, Reis): satır içi Arapça ibareler Türkçe tarafta yerinde kalır; yalnız köşeli parantezli
    # neşir ilaveleri ve atıf parantezleri çıkar. Köşeli parantez içindeki Arapça ilaveyle birlikte düşer.
    t = ILAVE_RE.sub(" ", t)
    t = ATIF_RE.sub(" ", t)
    t = re.sub(r"\{ar:\s*([^}]*)\}", r" \1 ", t)
    t = re.sub(r"[\[\]]", " ", t)  # kalan tek köşeli parantez (dengesizlik) -> bayrak ayrıca
    return _duzelt_bosluk(t)


def ilave_ve_atiflar(t):
    """Parantezli metinden: (nasir_ilavesi listesi, atiflar listesi, diğer parantezler)."""
    t0 = ARMARK_RE.sub(" ", t)
    ilaveler = [m.group(0)[1:-1].strip() for m in ILAVE_RE.finditer(t0)]
    ilaveler = [x for x in ilaveler if x]
    atiflar = [m.group(0)[1:-1].strip() for m in ATIF_RE.finditer(t0)]
    paren = []
    rest = ATIF_RE.sub(" ", ILAVE_RE.sub(" ", t0))
    for m in re.finditer(r"\(([^()]{1,80})\)", rest):
        ic = m.group(1)
        if re.fullmatch(r"(?:[a-zA-Z]\.){1,4}[a-zA-Z]?\.?\)?", ic) or re.fullmatch(r"(?:r|a|s|c|k)\.[a-z.]+", ic):
            continue  # (r.a.) (a.s.) benzeri formüller
        paren.append(ic)
    return ilaveler, atiflar, paren


def ic_arapca_araliklari(parantezli, temiz):
    """Temiz Türkçe içinde satır içi Arapça ibarelerin [bas, son) karakter aralıkları."""
    sonuc, pos = [], 0
    ilave_disi = ILAVE_RE.sub(" ", parantezli)
    for m in ARMARK_RE.finditer(ilave_disi):
        f = re.sub(r"\s+", " ", m.group(0)[4:-1].strip())
        i = temiz.find(f, pos)
        if f and i >= 0:
            sonuc.append({"metin": f, "bas": i, "son": i + len(f)})
            pos = i + len(f)
    return sonuc


def arapcasiz_say(t):
    return len(re.sub("[؀-ۿ]+", " ", t).split())


def ilavesiz(t):
    return parantezsiz(t)


# --- Arapça kök iskeleti ~ Osmanlıca Türkçe ünlüsüz iskelet (Arapça kökenli sözcükler için leksik çapa)
_AR2K = {"ب": "b", "ت": "T", "ث": "S", "ج": "C", "ح": "H", "خ": "H", "د": "T", "ذ": "S", "ر": "r", "ز": "S",
         "س": "S", "ش": "S", "ص": "S", "ض": "S", "ط": "T", "ظ": "S", "غ": "K", "ف": "f", "ق": "K", "ك": "K",
         "ل": "l", "م": "m", "ن": "n", "ه": "H", "ة": "T"}
_TR2K = {"b": "b", "p": "b", "t": "T", "d": "T", "s": "S", "z": "S", "ş": "S", "c": "C", "ç": "C", "j": "C",
         "h": "H", "k": "K", "g": "K", "ğ": "K", "r": "r", "f": "f", "l": "l", "m": "m", "n": "n", "v": "v"}
_AR_ONEK = re.compile(r"^(?:ال|لل|وال|فال|بال|كال|و|ف|ب|ل|ك)(?=.{3})")
_TR_STOP = {"ve", "bir", "bu", "o", "ki", "de", "da", "ile", "için", "gibi", "her", "ise", "ya", "imdi"}


def ar_iskelet(w):
    w = AR_LETTER_ONLY.sub("", norm_ar(w))
    w = _AR_ONEK.sub("", w, count=1)
    if w.startswith("ال"):
        w = w[2:]
    for sf in ("هما", "هم", "ها", "نا", "كم", "ه", "ك"):
        if w.endswith(sf) and len(w) - len(sf) >= 3:
            w = w[: -len(sf)]
            break
    return "".join(_AR2K.get(c, "") for c in w)


def tr_iskelet(w):
    w = unicodedata.normalize("NFC", w).lower().replace("â", "a").replace("î", "i").replace("û", "u")
    w = re.sub(r"[^a-zçşğıöüj]", "", w)
    return "".join(_TR2K.get(c, "") for c in w)


AR_LETTER_ONLY = re.compile("[^ء-ي]")


def leksik_ortak(ar_metin, tr_metin):
    """Arapça içerik sözcüklerinin kaçının kök iskeleti Türkçe sözcüklerde geçiyor (0-1). Anlam yargısı değildir."""
    a = [ar_iskelet(w) for w in norm_ar(ar_metin).split()]
    a = [x for x in a if len(x) >= 3]
    if not a:
        return 0.0
    t = [tr_iskelet(w) for w in re.sub("[؀-ۿ]+", " ", ilavesiz(tr_metin)).split() if w.lower().strip("’'.,;:“”") not in _TR_STOP]
    t = [x for x in t if len(x) >= 3]
    ok = sum(any(x in y for y in t) for x in a)
    return ok / len(a)


SORU_HITAP = re.compile(r"^(?:G[öo]rmez misin|G[öo]rm[üu]yor musun|G[öo]rmedin mi|Bilmez misin|Bilmiyor musun|Anlamadın mı)\s*\?$")
def leksik_siki(ar_metin, tr_metin):
    """leksik_ortak'un katı sürümü (yalnız kısa artık denetimi için): 3 harfli iskelet ancak aynı iskeletle eşleşir
    ('HKK' ≠ 'tahkîkan' iskeleti 'THKKn'); 4+ harfli iskelet içerme ile eşleşir."""
    a = [x for x in (ar_iskelet(w) for w in norm_ar(ar_metin).split()) if len(x) >= 3]
    if not a:
        return 0.0
    t = [x for x in (tr_iskelet(w) for w in re.sub("[؀-ۿ]+", " ", ilavesiz(tr_metin)).split() if w.lower().strip("’'.,;:“”") not in _TR_STOP) if len(x) >= 3]
    ok = sum(any(x == y or (len(x) >= 4 and x in y) for y in t) for x in a)
    return ok / len(a)


ABBR = re.compile(r"(?:^|\s)(?:\w{1,2}|Hz|Bk|bk|vs|ö|yy)\.$")


def tr_cumleler(t):
    """Türkçeyi cümle/öbeğe böler: ';' her zaman, '.', '?', '!' büyük harf/tırnak öncesi.

    Köşeli parantez, atıf parantezi ve {ar:...} içindeki noktalama bölme yeri sayılmaz: bu bölgeler hiçbir
    birim sınırını kesmez (G-025: parantez iki satıra bölünmez).
    """
    maske = re.sub(r"\[[^\[\]]*\]|\{ar:[^}]*\}|" + ATIF_RE.pattern,
                   lambda m: "_" * len(m.group(0)), t)
    parcalar, bas = [], 0
    tirnak_dengeli = maske.count("“") == maske.count("”")
    for m in re.finditer(r"[.;?!]+[”’\"»)\]]*\s+", maske):
        son = m.end()
        onceki = maske[bas:m.start() + 1]
        sonraki = maske[son:son + 1]
        isaret = maske[m.start()]
        # G-032 (Ö-1): açık “ ” tırnağı içinde bölme (ayet meali iki satıra yayılmasın)
        if tirnak_dengeli and maske[:m.end()].count("“") > maske[:m.end()].count("”"):
            continue
        # "Tâ ki ..." önceki öbeğin devamıdır; "Görmez misin?" gibi kısa hitap öbeği sonrakine aittir
        if re.match(r"T[âa]\s?ki\b", maske[son:son + 6]):
            continue
        if SORU_HITAP.match(onceki.strip()):
            continue
        if sonraki == "_":
            k = son
            while k < len(maske) and maske[k] in "_ ":
                k += 1
            if k < len(maske) and maske[k].islower():
                continue  # "...yoktur.” (Şûrâ, 42/11) buyurdu." : atıf cümle sonu değildir (K-B)
        if isaret == ";":
            pass
        elif ABBR.search(onceki[-12:]):
            continue
        elif not (sonraki.isupper() or sonraki in "“\"‘[(«_"):
            continue
        parcalar.append(t[bas:son].strip())
        bas = son
    son_parca = t[bas:].strip()
    if son_parca:
        parcalar.append(son_parca)
    # parantezden ibaret (temiz hâli boş) birimleri komşuya kat
    out = []
    bekleyen = ""
    for u in parcalar:
        if not parantezsiz(bekleyen + " " + u).strip("“”\"’‘ .;,:"):
            bekleyen = (bekleyen + " " + u).strip()
            continue
        out.append((bekleyen + " " + u).strip() if bekleyen else u)
        bekleyen = ""
    if bekleyen:
        if out:
            out[-1] = out[-1] + " " + bekleyen
        else:
            out.append(bekleyen)
    return out


def ar_parantezsiz(t):
    """Arapça tarafta köşeli parantez = neşir ilavesi (G-032, K-1): parantez ve içeriği çıkar."""
    t = re.sub(r"\s+", " ", ILAVE_RE.sub(" ", t)).strip()
    return re.sub(r"([،؛])\s+[،؛]", r"\1", t)   # "،[ilave]،" -> "،،" artığını sadeleştir


def ar_cumleler_parantezli(t):
    """ar_cumleler gibi, ama köşeli parantezin içindeki noktalama bölme yeri değildir. Dönüş: parantezli birimler."""
    maske = ILAVE_RE.sub(lambda m: "_" * len(m.group(0)), t)
    parcalar, bas = [], 0
    for m in re.finditer(r"[،؛.؟﴾]+\s*", maske):
        parcalar.append(t[bas:m.end()].strip())
        bas = m.end()
    kalan = t[bas:].strip()
    if kalan:
        parcalar.append(kalan)
    return parcalar


def ar_cumleler(t):
    """Arapçayı '،' '؛' '.' '؟' ve ﴾ sonrasında böler (Konuk Arapçasında noktalama seyrektir)."""
    parcalar = ar_cumleler_parantezli(t)
    # çok kısa parçaları (ör. tek sözcük) bir sonrakiyle birleştir
    out = []
    for p in parcalar:
        if out and len(AR_LETTER.findall(norm_ar(out[-1]))) < 6:
            out[-1] = out[-1] + " " + p
        else:
            out.append(p)
    if len(out) > 1 and len(AR_LETTER.findall(norm_ar(out[-1]))) < 6:
        son = out.pop()
        out[-1] += " " + son
    return out


def ar_birimleri(t_parantezli):
    """(parantezli birimler, temiz birimler); neşir ilavesinden ibaret birim komşuya katılır."""
    pt = ar_cumleler(t_parantezli)
    birlesik = []
    for u in pt:
        if birlesik and not ar_parantezsiz(birlesik[-1]).strip(" ،؛.؟"):
            birlesik[-1] = birlesik[-1] + " " + u
        else:
            birlesik.append(u)
    if len(birlesik) > 1 and not ar_parantezsiz(birlesik[-1]).strip(" ،؛.؟"):
        son = birlesik.pop()
        birlesik[-1] += " " + son
    return birlesik, [ar_parantezsiz(u) for u in birlesik]


# ---------------------------------------------------------------- segmentleme

def segmentle(bloklar, bas, bit):
    """[bas, bit) arası blokları 'ar' / 'tr' / 'sh' / 'baslik' serilerine toplar.

    baslik_sayfa atlanır, dipnot ayrı toplanır, 'isaret' Arapça/Türkçe serisini kesmez ama kaydedilir.
    """
    segs, dipnotlar, ilk_arapca = [], [], True
    for i in range(bas, bit):
        b = bloklar[i]
        tur = b["tur"]
        if tur == "baslik_sayfa":
            continue
        if tur == "dipnot":
            dipnotlar.append(b)
            continue
        if tur == "isaret":
            if segs:
                segs[-1]["isaretler"].append(b["metin"])
            continue
        if tur == "arapca":
            k = "ar"
        elif tur == "terceme":
            k = "tr"
        elif tur == "baslik" and i - bas <= 3:
            k = "baslik"
        else:
            k = "sh"
        if k == "ar" and ilk_arapca:
            k = "baslik_ar"
            ilk_arapca = False
        if segs and segs[-1]["k"] == k:
            segs[-1]["bloklar"].append(b)
            segs[-1]["idx"].append(i)
        else:
            segs.append({"k": k, "bloklar": [b], "idx": [i], "isaretler": []})
    return segs, dipnotlar


TERMINAL = re.compile(r"[.?!;:”\"’»)]\s*$")


def _son_metin(seg):
    t = seg["bloklar"][-1]["metin"]
    t = FN_REF.sub("", t)
    t = PAGE_MARK.sub(" ", t)
    return t.rstrip()


def devam_mi(onceki, arap, sonraki, oncesi_ar=False, ar_oncesi=""):
    """tr + ar + tr üçlüsünde Arapça satır içi mi (Türkçe paragraf devam ediyor mu)?

    Sonraki Türkçe büyük harfle (ya da tırnak/[ ile) başlamıyorsa, ya da önceki Türkçe cümle bitirilmemişse
    ve araya giren Arapça kısaysa (<= 6 blok) devam sayılır.
    """
    ilk = PAGE_MARK.sub(" ", sonraki["bloklar"][0]["metin"]).lstrip()
    # G-034 (cilt 2): Türkçe, Fusûs Arapçasının parçalarını satır içi yeniden alıntılar; bu Arapça hemen öncesindeki
    # Fusûs Arapçasının içinde aynen geçiyorsa yeni pasaj değil, yankıdır (aynı Türkçe paragraf)
    if ar_oncesi:
        a = norm_ar(" ".join(b["metin"] for b in arap["bloklar"]))
        if len(a) >= 5 and a in ar_oncesi and len(arap["bloklar"]) <= 3:
            return True
    # G-032 (Y-1): "Sehl dedi:" + satır içi Arapça + "[meal]" / "(atıf)" / "Ya'ni ..." = aynı Türkçe paragraf
    # Yalnız Türkçe seri bir Fusûs Arapçasının hemen ardındaysa (yoksa "Şiir:" gibi etiketli beyit pasajı yetim kalır).
    izahli = any(IZAH_TR.match(b["metin"]) for b in onceki["bloklar"])   # îzâh paragrafından sonra gelen Arapça yeni pasajdır
    if oncesi_ar and not izahli and _son_metin(onceki).endswith(":") and len(arap["bloklar"]) <= 2 and len(_son_metin(onceki).split()) > 2:
        return True
    # Satır içi Arapçanın hemen ardından gelen köşeli parantezli Türkçe, o Arapçanın neşir mealidir (aynı paragraf)
    if oncesi_ar and ilk.startswith("[") and len(arap["bloklar"]) <= 3:
        return True
    if ilk[:1].isupper() or ilk[:1] in "“\"‘«" or ilk.startswith("["):
        # büyük harfle başlıyorsa yalnız önceki bitmemişse ve Arapça kısaysa devam say
        return (not TERMINAL.search(_son_metin(onceki))) and len(arap["bloklar"]) <= 6
    return True


def satir_ici_birlestir(segs):
    """tr + ar + tr(devam) -> tek Türkçe seri; Arapça parça 'satır içi' işaretlenir."""
    out, i = [], 0
    while i < len(segs):
        s = segs[i]
        if (
            s["k"] == "tr" and i + 2 < len(segs)
            and segs[i + 1]["k"] == "ar" and segs[i + 2]["k"] == "tr"
            and devam_mi(s, segs[i + 1], segs[i + 2], i > 0 and segs[i - 1]["k"] == "ar",
                         norm_ar(" ".join(b["metin"] for b in segs[i - 1]["bloklar"])) if i > 0 and segs[i - 1]["k"] == "ar" else "")
        ):
            oncesi_ar = i > 0 and segs[i - 1]["k"] == "ar"
            ar_oncesi = norm_ar(" ".join(b["metin"] for b in segs[i - 1]["bloklar"])) if oncesi_ar else ""
            s = dict(s)
            s["parcalar"] = s.get("parcalar") or [("tr", s["bloklar"])]
            s["isaretler"] = list(s["isaretler"])
            while (
                i + 2 < len(segs)
                and segs[i + 1]["k"] == "ar" and segs[i + 2]["k"] == "tr"
                and devam_mi(s, segs[i + 1], segs[i + 2], oncesi_ar, ar_oncesi)
            ):
                s["parcalar"].append(("ar_ic", segs[i + 1]["bloklar"]))
                s["parcalar"].append(("tr", segs[i + 2]["bloklar"]))
                s["bloklar"] = s["bloklar"] + segs[i + 1]["bloklar"] + segs[i + 2]["bloklar"]
                s["idx"] = s["idx"] + segs[i + 1]["idx"] + segs[i + 2]["idx"]
                s["isaretler"] += segs[i + 1]["isaretler"] + segs[i + 2]["isaretler"]
                i += 2
            out.append(s)
            i += 1
            continue
        out.append(s)
        i += 1
    return out


def kucuk_harfle_basliyor(seg):
    t = seg["bloklar"][0]["metin"].lstrip()
    return bool(LATIN_LOWER.match(t))


ALINTI_TR = re.compile(r"^(Tercüme|Îzâhen|Ya[’']ni\s*:)")
IZAH_TR = re.compile(r"^Ya[’']ni\b")


FARSI_YE = "ی"   # Farsça ye (U+06CC): Arapça metinde de ('تعالی') tek tük görülür (G-037, K-1)


def farsca_mi(metin):
    """Farsça'ya özgü harf (گ چ پ ژ ۀ ہ) oranı > %1; Farsça ye (ی) tek başına yeterli değildir:
    en az 3 adet ve harflerin %3'ü olmalı (Arapça içinde tek 'تعالی' Farsça sayılmaz)."""
    harf = AR_LETTER.findall(metin)
    if not harf:
        return False
    kesin = len(re.findall("[گچپژۀہ]", metin))
    ye = metin.count(FARSI_YE)
    return kesin / len(harf) > 0.01 or (ye >= 3 and ye / len(harf) > 0.03)


_FA_SOZ = {"است", "را", "که", "این", "آن", "چه", "نيست", "بود", "گر", "همي", "كز", "وز", "اي", "كي", "خود", "ز", "مي", "نه"}


def _fa_norm(w):
    return w.replace("ک", "ك").replace("ی", "ي").replace("ى", "ي")


_FA_SOZ = {_fa_norm(x) for x in _FA_SOZ}


def dil_tespit(metin):
    """Blok dili: Farsça'ya özgü harf (گ چ پ ژ ی) ya da Farsça işlev sözcüğü varsa 'fa', yoksa 'ar'."""
    if farsca_mi(metin):
        return "fa"
    kel = [_fa_norm(w) for w in re.split(r"[\s/]+", TASHKEEL.sub("", metin))]
    return "fa" if any(w in _FA_SOZ for w in kel) else "ar"


def tr_serisini_ayir(seg, birlesmeler=None):
    """Türkçe serisini (literal çeviri, îzâh) olarak ikiye ayırır. Satır içi Arapçayı {ar: ...} gömer."""
    parcalar = seg.get("parcalar") or [("tr", seg["bloklar"])]
    literal_parcalar, izah, ic_ar = [], [], []
    izahta = False
    for tur, bl in parcalar:
        if tur == "ar_ic":
            if not izahta:
                ar = " ".join(b["metin"] for b in bl)
                ic_ar.append(ar)
                literal_parcalar.append("{ar: " + ar + "}")
            continue
        satirlar = []
        for b in bl:
            if not izahta and IZAH_TR.match(b["metin"]):
                if satirlar:
                    literal_parcalar.append(satir_birlestir(satirlar, birlesmeler))
                    satirlar = []
                izahta = True
            if izahta:
                izah.append(b["metin"])
            else:
                satirlar.append(b["metin"])
        if satirlar:
            literal_parcalar.append(satir_birlestir(satirlar, birlesmeler))
    literal = " ".join(literal_parcalar)
    return literal, " ".join(izah), ic_ar


# ---------------------------------------------------------------- dipnotlar

def dipnotlari_coz(dipnot_bloklari):
    sonuc, cur = {}, None
    for b in dipnot_bloklari:
        m = re.match(r"^(\d{1,3}) (?=\S)", b["metin"])
        if m and (cur is None or cur < int(m.group(1)) <= cur + 4):
            cur = int(m.group(1))
            sonuc[cur] = {"no": cur, "sayfa": b["sayfa"], "metin": b["metin"][m.end():]}
        elif cur is not None:
            sonuc[cur]["metin"] += " " + b["metin"]
    return sonuc


# ---------------------------------------------------------------- cümle hizalama (DP)

def _nufus_cdf_iki_kuyruk(z):
    return math.erfc(z / math.sqrt(2))


ONCEL = {(1, 1): 0.89, (1, 2): 0.089, (2, 1): 0.089, (2, 2): 0.011, (1, 3): 0.006, (3, 1): 0.006,
         (2, 3): 0.003, (3, 2): 0.003, (1, 0): 0.002, (0, 1): 0.002}

# Arapça cümle başı bağlaç sınıfı -> Türkçe cümle başı karşılıkları (küçük, kasıtlı olarak kaba)
BAGLAC = [
    (re.compile(r"^(?:و|ف)?(?:ان|انه|انها|انما)\b"), re.compile(r"^(?:Zîrâ|Çünkü|Muhakkak|Hâlbuki)")),
    (re.compile(r"^(?:و|ف)?ثم\b"), re.compile(r"^(?:Ba[’']dehû|Ondan sonra|Sonra)")),
    (re.compile(r"^(?:و|ف)?(?:لما|لما)\b"), re.compile(r"^(?:Vaktâki|Vaktaki|Ne zaman|Zaman)")),
    (re.compile(r"^(?:و|ف)?لا شك\b"), re.compile(r"^(?:Ve )?[Şş]ek yoktur|^[Şş]übhe")),
    (re.compile(r"^(?:و|ف)?(?:هذا|هذه)\b"), re.compile(r"^(?:Ve )?(?:[Bb]u|[Bb]unun)")),
]


def _baglac_bonus(ar_u, tr_u):
    a = norm_ar(ar_u).strip()
    t = tr_u.strip()
    for ra, rt in BAGLAC:
        if ra.search(a) and rt.search(t):
            return 1
    return 0


def dp_hizala(ar_u, tr_u):
    """Monoton n-m hizalama. Dönüş: [(ar_idx_listesi, tr_idx_listesi, delta_z, baglac)]"""
    n, m = len(ar_u), len(tr_u)
    la = [max(1, len(AR_LETTER.findall(norm_ar(x)))) for x in ar_u]
    lt = [max(1, len(re.sub(r"[^\w]", "", re.sub("[؀-ۿ]+", "", ilavesiz(x))))) for x in tr_u]
    c = sum(lt) / sum(la)
    s2 = 8.0
    INF = float("inf")
    D = [[INF] * (m + 1) for _ in range(n + 1)]
    geri = [[None] * (m + 1) for _ in range(n + 1)]
    D[0][0] = 0.0
    for i in range(n + 1):
        for j in range(m + 1):
            if D[i][j] == INF:
                continue
            for (di, dj), p in ONCEL.items():
                ni, nj = i + di, j + dj
                if ni > n or nj > m:
                    continue
                a = sum(la[i:ni])
                t = sum(lt[j:nj])
                if di and dj:
                    z = (t - a * c) / math.sqrt(max(a, 1) * s2 * c)
                    pz = max(_nufus_cdf_iki_kuyruk(abs(z)), 1e-9)
                    maliyet = -math.log(p) - math.log(pz)
                    bon = _baglac_bonus(" ".join(ar_u[i:ni]), " ".join(tr_u[j:nj]))
                    maliyet -= 0.8 * bon
                    ov = leksik_ortak(" ".join(ar_u[i:ni]), " ".join(tr_u[j:nj]))
                    maliyet -= 4.0 * ov
                else:
                    z, bon, ov = 9.0, 0, 0.0
                    maliyet = -math.log(p) + 6.0  # atlama: pahalı
                if D[i][j] + maliyet < D[ni][nj]:
                    D[ni][nj] = D[i][j] + maliyet
                    geri[ni][nj] = (i, j, z, bon, ov)
    yol, i, j = [], n, m
    if D[n][m] == INF:
        return [(list(range(n)), list(range(m)), 9.0, 0, 0.0)]
    while (i, j) != (0, 0):
        pi, pj, z, bon, ov = geri[i][j]
        yol.append((list(range(pi, i)), list(range(pj, j)), z, bon, ov))
        i, j = pi, pj
    return yol[::-1]


def cumle_guveni(ar_idx, tr_idx, z, bon, ov, pasaj_guveni):
    """Güven = uzunluk uyumu (0.45) + leksik kök-iskelet örtüşmesi (0.55); tavan 0.9. Anlamsal doğrulama değildir."""
    if not ar_idx or not tr_idx:
        return 0.15, "atlama: karşılığı olmayan birim"
    tur = (len(ar_idx), len(tr_idx))
    uzun = math.exp(-(abs(z) ** 2) / 4.0)
    lek = min(1.0, ov / 0.5)
    g = 0.45 * uzun + 0.55 * lek
    g *= {(1, 1): 1.0, (1, 2): 0.92, (2, 1): 0.92}.get(tur, 0.8)
    if bon:
        g += 0.08
    g = min(g, 0.9, pasaj_guveni + 0.2)
    neden = "uzunluk z=%.2f, leksik örtüşme %.2f, eşleşme %d-%d%s" % (abs(z), ov, tur[0], tur[1], ", bağlaç çapası" if bon else "")
    return round(g, 3), neden


# ---------------------------------------------------------------- pasaj güveni

def oran_z(ar_kelime, tr_kelime, ort_ln=ORAN_ORT_LN, sd0=ORAN_SD0):
    if ar_kelime <= 0 or tr_kelime <= 0:
        return 9.0
    return (math.log(tr_kelime / ar_kelime) - ort_ln) / max(0.12, math.sqrt(sd0 ** 2 + ORAN_C / ar_kelime))


def _skel_sayi(metin, ar=True):
    if ar:
        return len([x for x in (ar_iskelet(w) for w in norm_ar(metin).split()) if len(x) >= 3])
    return len([x for x in (tr_iskelet(w) for w in re.sub("[؀-ۿ]+", " ", ilavesiz(metin)).split()
                            if w.lower().strip("’'.,;:“”") not in _TR_STOP) if len(x) >= 3])


FA_TR = re.compile(r"^(?:İmdi|Binâenaleyh|Böyle olunca|Şu hâlde)\b")


def _yon(j, n):
    """n birimli satırda j. birim şüpheliyse kaymanın yönü: ilk birim -> önceki satır, son birim -> sonraki satır."""
    if n >= 2 and j == 0:
        return "onceki"
    if n >= 2 and j == n - 1:
        return "sonraki"
    return "ikisi"


def artik_suphe(ar_birimler, tr_birimler):
    """G-032 (Ö-1): 1-2 / 2-1 (n-m) satırda kısa (<=3 sözcük) bir birimin karşı tarafla kök örtüşmesi sıfırsa şüphe:
    komşu satıra ait kısa artık olabilir. Anlam yargısı değil, kontrol bayrağıdır.

    G-037: dönüş değeri kaymanın yönüdür ("onceki" | "sonraki" | "ikisi"); şüphe yoksa None. Komşu bayrağı yalnız o yöne konur.
    """
    if len(ar_birimler) == 1 and len(tr_birimler) == 1:
        return None
    ar_hepsi, tr_hepsi = " ".join(ar_birimler), " ".join(tr_birimler)
    if len(tr_birimler) >= 2:
        for j, u in enumerate(tr_birimler):
            if len(re.sub("[؀-ۿ]+", " ", ilavesiz(u)).split()) <= 3 and leksik_siki(ar_hepsi, u) == 0.0:
                return _yon(j, len(tr_birimler))
    # Arapça "fe-" (ف) başlı birim sayısından fazla "İmdi/Binâenaleyh/Böyle olunca/Şu hâlde" ile başlayan Türkçe birim:
    # fazla olan, komşu Arapça birimin karşılığıdır (ör. F12 p0011-c06, F1 p0007-c03)
    if len(tr_birimler) >= 2:
        fa_ar = sum(1 for w in norm_ar(ar_hepsi).split() if w.startswith("ف") and len(w) >= 3)
        fa_idx = [j for j, u in enumerate(tr_birimler) if FA_TR.match(ilavesiz(u))]
        if len(fa_idx) > fa_ar:
            return _yon(fa_idx[-1], len(tr_birimler))   # fazla olan sondaki "fe-" birimi
    if len(ar_birimler) >= 2:
        for j, a in enumerate(ar_birimler):
            if len(a.split()) <= 4 and not re.search("[﴿﴾«»]", a) and _skel_sayi(a) >= 1 and leksik_siki(a, tr_hepsi) == 0.0:
                return _yon(j, len(ar_birimler))   # çevirisi bu satırda olmayan Arapça birim: karşılığı o yöndeki komşuda
    return None


def pasaj_guveni(ar_kelime, tr_kelime, ort_ln_oran, sd_ln, ic_ar, farsca, ov):
    """Yapı temiz (Arapça seri -> Türkçe seri bitişik) ise 0.92 taban; oran sapması ve küçüklük cezası."""
    gerekce = ["yapı: Arapça seri + bitişik 'terceme' serisi"]
    g = 0.92
    if ar_kelime == 0 or tr_kelime == 0:
        return 0.0, ["boş taraf"]
    ln = math.log(tr_kelime / ar_kelime)
    sd_eff = max(0.12, math.sqrt(sd_ln ** 2 + ORAN_C / max(ar_kelime, 1)))
    z = (ln - ort_ln_oran) / sd_eff
    g *= 0.45 + 0.55 * math.exp(-(z * z) / 2)
    gerekce.append("sözcük oranı TR/AR=%.2f (z=%.2f)" % (tr_kelime / ar_kelime, z))
    g *= 0.6 + 0.4 * min(1.0, ov / 0.4)
    gerekce.append("leksik kök örtüşmesi %.2f (yanlış pasaj çaprazında ort. 0.14, doğruda 0.61 (fass-01 ölçümü))" % ov)
    if ov < 0.2:
        g -= 0.25
    if ar_kelime < 6 or tr_kelime < 6:
        g -= 0.20
        gerekce.append("çok kısa pasaj (oran gürültülü)")
    if ic_ar:
        g -= 0.05
        gerekce.append("satır içi Arapçayla birleştirilmiş Türkçe paragraf")
    if farsca:
        g -= 0.3
        gerekce.append("Farsça işaretleri var")
    return round(max(0.0, min(g, 0.95)), 3), gerekce


# ---------------------------------------------------------------- ana hat

TOKEN_RE = re.compile(r"[^\W\d_]+(?:[’'][^\W\d_]+)*")


def sozluk_kur(bloklar):
    """Tüm ciltteki Türkçe sözcük dağarcığı (satır sonu tire kararlarını denetlemek için)."""
    v = set()
    for b in bloklar:
        if b["tur"] in ("terceme", "serh") and b["dil"] == "tr":
            for w in TOKEN_RE.findall(b["metin"].lower()):
                v.add(w)
    return v


BILGI_BAYRAKLARI = {"satir_ici_arapca"}  # karar G-027/Reis: bilgi amaçlı, tek başına öğretici uygunluğu düşürmez


def kusur(bayraklar):
    return [b for b in bayraklar if b not in BILGI_BAYRAKLARI]


def butunluk(bayraklar):
    k = kusur(bayraklar)
    return {"durum": "kontrol" if k else "temiz", "bayraklar": k, "bilgi": [b for b in bayraklar if b in BILGI_BAYRAKLARI]}


def hizala(bloklar, fass_no=1, min_sayfa=40, son_baslik=None):
    bas, bit = fass_sinirlari(bloklar, fass_no, min_sayfa, son_baslik)
    segs, dipnot_bloklari = segmentle(bloklar, bas, bit)
    segs = satir_ici_birlestir(segs)
    dipnotlar = dipnotlari_coz(dipnot_bloklari)
    sozluk = sozluk_kur(bloklar)

    adaylar, alintilar, baslik = [], [], None
    for i, s in enumerate(segs):
        if s["k"] == "baslik_ar":
            tr_bas = []
            if i + 1 < len(segs) and segs[i + 1]["k"] == "baslik":
                tr_bas = [b["metin"] for b in segs[i + 1]["bloklar"]]
            baslik = {"ar": " ".join(b["metin"] for b in s["bloklar"]), "tr": satir_birlestir(tr_bas), "blok": s["idx"] + (segs[i + 1]["idx"] if tr_bas else [])}
            continue
        if s["k"] != "ar":
            continue
        ar_metin = " ".join(b["metin"] for b in s["bloklar"])
        sonraki = segs[i + 1] if i + 1 < len(segs) else None
        if sonraki and sonraki["k"] == "tr":
            ilk = sonraki["bloklar"][0]["metin"]
            if ALINTI_TR.match(ilk) or farsca_mi(ar_metin):
                alintilar.append({"ar_seg": s, "tr_seg": sonraki, "neden": "Tercüme:/Ya'ni: ile başlayan ya da Farsça: şerh içi alıntı"})
            elif kucuk_harfle_basliyor(sonraki):
                alintilar.append({"ar_seg": s, "tr_seg": None, "neden": "küçük harfle devam eden Türkçe önünde (birleştirilemedi)"})
            else:
                adaylar.append((s, sonraki))
        else:
            alintilar.append({"ar_seg": s, "tr_seg": None, "neden": "ardından Fusûs tercümesi yok: şerh içi ayet/hadis/beyit/ibare"})

    pasajlar = []
    for s, t in adaylar:
        ar = " ".join(b["metin"] for b in s["bloklar"])
        birl = []
        literal, izah, ic_ar = tr_serisini_ayir(t, birl)
        raw, sayfa_isaret, fn = sayfa_dipnot_ayikla(literal)
        temiz = parantezsiz(raw)
        ic_aral = ic_arapca_araliklari(raw, temiz)
        ilaveler, atiflar, paren = ilave_ve_atiflar(raw)
        izah_devam = False
        if izah and not TERMINAL.search(izah.rstrip()):
            ti = next(j for j, x in enumerate(segs) if x is t)
            if ti + 1 < len(segs) and segs[ti + 1]["k"] == "sh" and kucuk_harfle_basliyor(segs[ti + 1]):
                izah = izah + " " + segs[ti + 1]["bloklar"][0]["metin"]  # îzâh şerh yazı tipine taşan paragraf
                izah_devam = True
        izah = re.sub(r"\s*(?:Şiir|Beyit|Şi’r|Rubâî|Mısra|Mesnevî)\s*:\s*$", "", izah)  # sonraki beytin başlığı
        izah_t, _, fn2 = sayfa_dipnot_ayikla(izah) if izah else ("", [], [])
        izah_t = ARMARK_RE.sub(" ", izah_t)
        if not temiz.strip():
            # G-032 (Y-1): harfî tercümesi olmayan Arapça blok (şerhteki alıntı + "Ya'ni" îzâhı) Fusûs pasajı değildir
            alintilar.append({"ar_seg": s, "tr_seg": t, "neden": "sahte pasaj: Türkçe harfî tercüme boş (şerh içi Arapça alıntı + Ya’ni îzâhı)", "sahte": True, "izah": izah_t})
            continue
        govde = ARMARK_RE.sub(" ", raw)
        bay = []
        if ic_ar:
            bay.append("satir_ici_arapca")
        belirsiz = []
        for sol, sag, birles in birl:
            if birles:
                l_, r_ = re.sub(r"[^\w’']", "", sol).lower(), re.sub(r"[^\w’']", "", sag).lower()
                # iki yarı da tek başına bilinen sözcükse (gerçek bileşik olabilir) ve birleşik biçim cilt sözlüğünde yoksa
                if len(l_) >= 3 and len(r_) >= 5 and l_ in sozluk and r_ in sozluk and (l_ + r_) not in sozluk:
                    belirsiz.append("%s-%s" % (sol, sag))
        if belirsiz:
            bay.append("tire_belirsiz")
        if govde.count("[") != govde.count("]") or govde.count("(") != govde.count(")"):
            bay.append("parantez_dengesiz")
        dil_t = [dil_tespit(b["metin"]) for b in s["bloklar"]]
        etiket = [b["dil"] for b in s["bloklar"]]
        tutarsiz = sum(1 for a, b in zip(dil_t, etiket) if a != b)
        yanlis_blok = [norm_ar(bk["metin"]) for a, e, bk in zip(dil_t, etiket, s["bloklar"]) if a != e]
        if tutarsiz or "fa" in dil_t:
            bay.append("dil_etiketi_tutarsiz")
        artik = temiz
        for a_ in sorted(ic_aral, key=lambda x: -x["bas"]):
            artik = artik[:a_["bas"]] + " " + artik[a_["son"]:]
        if re.search("[؀-ۿ]", artik):
            bay.append("tr_icinde_arapca_harf")  # bildirilmemiş Arapça harf
        if re.search("[A-Za-z0-9]|�", ar):
            bay.append("ar_icinde_latin_ya_da_bozuk")
        ar_pt = ar
        ar = ar_parantezsiz(ar_pt)
        ar_ilaveleri = [m.group(0)[1:-1].strip() for m in ILAVE_RE.finditer(ar_pt)]
        ar_kel = len(norm_ar(ar).split())
        tr_kel = arapcasiz_say(temiz)
        pasajlar.append({
            "s": s, "t": t, "ar": ar, "ar_parantezli": ar_pt, "nasir_ilavesi_ar": ar_ilaveleri, "tr": temiz, "ic_aral": ic_aral, "tr_parantezli": raw, "izah": izah_t, "ic_ar": ic_ar,
            "izah_devam": izah_devam, "izah_tamam": (not izah_t) or bool(TERMINAL.search(izah_t.rstrip())),
            "ilaveler": ilaveler, "atiflar": atiflar, "paren": paren, "belirsiz_tire": belirsiz,
            "dil_tutarsiz_blok": tutarsiz, "dil_yanlis_metin": yanlis_blok, "bayraklar": bay,
            "sayfa_isaret": sorted(set(s["isaretler"] + t["isaretler"] + sayfa_isaret)),
            "fn": sorted(set(fn + fn2 + [int(x) for bk in s["bloklar"] for x in bk.get("dipnot_ref", [])])), "ar_kel": ar_kel, "tr_kel": tr_kel,
        })
    # G-032 (Y-1): Arapçası bir önceki pasajın Arapçasında/satır içi Arapçasında aynen geçen kısa "pasaj" sahtedir
    kalan = []
    for p in pasajlar:
        a40 = norm_ar(p["ar"])[:40]
        onc = kalan[-1] if kalan else None
        if onc is not None and len(a40) >= 12 and p["ar_kel"] <= 12 and a40 in norm_ar(onc["ar"] + " " + " ".join(onc["ic_ar"]) + " " + onc["tr_parantezli"]):
            alintilar.append({"ar_seg": p["s"], "tr_seg": p["t"], "neden": "sahte pasaj: Arapçası önceki pasajın içinde geçiyor (satır içi alıntı)", "sahte": True, "izah": p["izah"]})
        else:
            kalan.append(p)
    pasajlar = kalan
    ort, sd = ORAN_ORT_LN, ORAN_SD0   # sürüme sabit: pasaj puanı başka pasajlara bağlı değil (G-032)

    # dipnot atıflarının gövdedeki yeri (şerh vb.)
    dip_ref_idx = {}
    for i in range(bas, bit):
        if bloklar[i]["tur"] not in ("dipnot", "baslik_sayfa"):
            for n_ in FN_REF.findall(bloklar[i]["metin"]) + [str(x) for x in bloklar[i].get("dipnot_ref", [])]:
                dip_ref_idx.setdefault(int(n_), i)

    # alıntı kayıtlarının dil bilgisi
    for a in alintilar:
        bl = a["ar_seg"]["bloklar"]
        dt = [dil_tespit(b["metin"]) for b in bl]
        a["dil_tespit"] = "fa" if dt.count("fa") * 2 > len(dt) else "ar"
        a["dil_tutarsiz_blok"] = sum(1 for b, d in zip(bl, dt) if b["dil"] != d)
    return {
        "bas": bas, "bit": bit, "baslik": baslik, "pasajlar": pasajlar, "alintilar": sorted(alintilar, key=lambda a: a["ar_seg"]["idx"][0]),
        "dipnotlar": dipnotlar, "ort": ort, "sd": sd, "bloklar": bloklar, "segs": segs, "dip_ref_idx": dip_ref_idx,
    }


def onceki_kayitlar(dizin, fass_no):
    """Önceki sürümün kimlik kaydı: kimlikleri korumak için (G-027)."""
    reg = {"pasaj": {}, "cumle": {}, "alinti": {}, "maks_p": 0, "maks_q": 0, "maks_c": {}}
    yol = os.path.join(dizin, "fass-%02d.jsonl" % fass_no)
    if not os.path.exists(yol):
        return reg
    with open(yol, encoding="utf-8") as f:
        satirlar = f.readlines()
    for l in satirlar:
        k = json.loads(l)
        if k["duzey"] == "pasaj":
            reg["pasaj"][norm_ar(k["ar"])[:70]] = k["id"]
            reg["maks_p"] = max(reg["maks_p"], int(k["id"].rsplit("-p", 1)[1]))
        elif k["duzey"] == "cumle":
            reg["cumle"].setdefault((k["ust"], norm_ar(k["ar"])[:30]), k["id"]); reg.setdefault("cumle_liste", {}).setdefault(k["ust"], []).append((norm_ar(k["ar"]), k["id"]))
            reg["maks_c"][k["ust"]] = max(reg["maks_c"].get(k["ust"], 0), int(k["id"].rsplit("-c", 1)[1]))
    yol = os.path.join(dizin, "fass-%02d.alinti.jsonl" % fass_no)
    if os.path.exists(yol):
        with open(yol, encoding="utf-8") as f:
            satirlar = f.readlines()
        for l in satirlar:
            k = json.loads(l)
            reg["alinti"][norm_ar(k["ar"])[:70]] = k["id"]
            reg["maks_q"] = max(reg["maks_q"], int(k["id"].rsplit("-q", 1)[1]))
    return reg


def kayitlar(sonuc, fass_no=1, eser_ar="E-006", eser_tr="E-001", onceki=None, kimlik_oneki="fusus-konuk"):
    """JSONL kayıtlarını üretir. Dönüş: (ana, alinti, dipnot). onceki: kimlik korunacak önceki sürüm dizini."""
    reg = onceki_kayitlar(onceki, fass_no) if onceki else {"pasaj": {}, "cumle": {}, "alinti": {}, "maks_p": 0, "maks_q": 0, "maks_c": {}}
    bl = sonuc["bloklar"]
    kimlik = "%s-f%02d" % (kimlik_oneki, fass_no)
    ana, alinti, dipnot = [], [], []
    kullanilan = set()

    def kaynak(idx):
        return {"ilk": {"sayfa": bl[idx[0]]["sayfa"], "basili": bl[idx[0]]["basili_sayfa"], "sira": bl[idx[0]]["sira"]},
                "son": {"sayfa": bl[idx[-1]]["sayfa"], "basili": bl[idx[-1]]["basili_sayfa"], "sira": bl[idx[-1]]["sira"]}}

    taban = {"surum": SURUM, "eser_ar": eser_ar, "eser_tr": eser_tr, "fass": fass_no}
    if sonuc["baslik"]:
        # Eser bazında dışarıda bırakma birimi: aynı Arapça fass başlığını taşıyan şerhler (Mûsâ'nın iki şerhi) tek birimdir (G-035 kararı)
        taban["dislama_birimi"] = "%s-d%s" % (kimlik_oneki, hashlib.sha1(_bosluksuz(norm_ar(sonuc["baslik"]["ar"])).encode()).hexdigest()[:6])
    if sonuc["baslik"] and re.search(r"\[(\d)\. Şerh\]", sonuc["baslik"]["tr"]):
        # Konuk bazı fassları iki kez şerh eder (cilt 2, Mûsâ): ikinci şerh aynı Arapça fassı yeniden verir
        taban["serh_no"] = int(re.search(r"\[(\d)\. Şerh\]", sonuc["baslik"]["tr"]).group(1))
    if sonuc["baslik"]:
        b = sonuc["baslik"]
        ana.append(dict(taban, id="%s-b0001" % kimlik, duzey="baslik", ar_id="%s-a-b0001" % kimlik, tr_id="%s-t-b0001" % kimlik,
                        ar=b["ar"], tr=b["tr"], esleme="1-1", guven=0.9, gerekce="fass başlığı: Arapça başlık satırı + bitişik Türkçe başlık",
                        yontem="yapi-capa", model="yok", inceleme="hayır", butunluk=butunluk([]), ogretici_uygun=False,
                        kaynak=kaynak(b["blok"])))

    # dipnot -> pasaj bağları (atıf pasajın Türkçesinde geçiyorsa)
    pasaj_idleri = []
    maks_p = reg["maks_p"]
    for p in sonuc["pasajlar"]:
        pid = reg["pasaj"].get(norm_ar(p["ar"])[:70]) or reg["pasaj"].get(norm_ar(p["ar_parantezli"])[:70])
        if not pid or pid in kullanilan:
            maks_p += 1
            pid = "%s-p%04d" % (kimlik, maks_p)
        kullanilan.add(pid)
        pasaj_idleri.append(pid)

    dip_ar = {}
    for no, d in sonuc["dipnotlar"].items():
        parcalar = [m.group(0)[5:-1].strip() for m in ARMARK_RE.finditer(d["metin"])]
        if parcalar:
            dip_ar[no] = parcalar

    for pid, p in zip(pasaj_idleri, sonuc["pasajlar"]):
        g, gerekce = pasaj_guveni(p["ar_kel"], p["tr_kel"], sonuc["ort"], sonuc["sd"], p["ic_ar"], farsca_mi(p["ar"]), leksik_ortak(p["ar"], p["tr"]))
        inc = "insan" if g < ESIK_INCELEME else "hayır"
        kenar = ESIK_BANT_ALT <= g < ESIK_INCELEME   # G-032: kenar bandı; satır güveni belirleyici
        varyantlar = []
        for no in p["fn"]:
            if no in dip_ar:
                d = sonuc["dipnotlar"][no]
                varyantlar.append({"dipnot_id": "%s-d%03d" % (kimlik, no), "no": no, "ar": dip_ar[no], "dipnot_metni": d["metin"]})
        ba = list(p["bayraklar"])
        but = butunluk(ba)
        ana.append(dict(taban, id=pid, duzey="pasaj", ar_id=pid.replace("-p", "-a"), tr_id=pid.replace("-p", "-t"),
                        ar=p["ar"], ar_parantezli=p["ar_parantezli"], nasir_ilavesi_ar=p["nasir_ilavesi_ar"], ar_norm=norm_ar(p["ar"]), tr=p["tr"], tr_parantezli=p["tr_parantezli"],
                        nasir_ilavesi=p["ilaveler"], atiflar=p["atiflar"], parantezler=p["paren"],
                        tr_izah=p["izah"], tr_izah_tamam=p["izah_tamam"], tr_izah_serhten_devam=p["izah_devam"], tr_satir_ici_arapca=p["ic_aral"], nasir_varyantlari=varyantlar,
                        dipnot_ref=p["fn"], sayfa_isaretleri=p["sayfa_isaret"], esleme="1-1", ar_kelime=p["ar_kel"], tr_kelime=p["tr_kel"],
                        guven=g, gerekce="; ".join(gerekce), yontem="yapi-capa+oran", model="yok (gömme modeli ölçülmedi)",
                        inceleme=inc, bant=("kenar" if kenar else None), butunluk=but, ogretici_uygun=(inc == "hayır" and not kusur(ba)),
                        tire_belirsiz=p["belirsiz_tire"], kaynak_ar=kaynak(p["s"]["idx"]), kaynak_tr=kaynak(p["t"]["idx"])))
        # ---- cümle düzeyi
        ar_pu, ar_u = ar_birimleri(p["ar_parantezli"])
        tr_pu = tr_cumleler(p["tr_parantezli"])          # parantezli birimler (parantez bölünmez)
        tr_u = [parantezsiz(u) for u in tr_pu]           # çiftin Türkçe tarafı
        sayac = [reg["maks_c"].get(pid, 0)]

        def cid(ar_birim, ar_birim_pt=None):
            k = reg["cumle"].get((pid, norm_ar(ar_birim)[:30])) or (reg["cumle"].get((pid, norm_ar(ar_birim_pt)[:30])) if ar_birim_pt else None)
            if not k or k in kullanilan:
                # çok birimli eski satırın ilk birimi: eski metin bu birimle başlıyorsa (ya da tersi) aynı kimlik
                ub = norm_ar(ar_birim).strip()
                k = next((i_ for (m_, i_) in reg.get("cumle_liste", {}).get(pid, []) if i_ not in kullanilan and len(ub) >= 8 and (m_.startswith(ub[:30]) or ub.startswith(m_[:30]))), None)
            if k and k not in kullanilan:
                kullanilan.add(k)
                return k
            while True:
                sayac[0] += 1
                k = "%s-c%02d" % (pid, sayac[0])
                if k not in kullanilan:
                    kullanilan.add(k)
                    return k

        def ar_satiri_etiket_yanlis(ai):
            kel = norm_ar(" ".join(ar_u[x] for x in ai)).split()
            uclu = {tuple(kel[i:i + 3]) for i in range(max(1, len(kel) - 2))}
            for m in p["dil_yanlis_metin"]:
                w = m.split()
                if any(tuple(w[i:i + 3]) in uclu for i in range(max(1, len(w) - 2))):
                    return True
            return False

        def satir_bay(ti, ai=()):
            b = [x for x in ba if x != "dil_etiketi_tutarsiz"]
            if "dil_etiketi_tutarsiz" in ba and (not p["dil_yanlis_metin"] or ar_satiri_etiket_yanlis(ai)):
                b.append("dil_etiketi_tutarsiz")
            metin = " ".join(tr_pu[x] for x in ti)
            if "{ar:" in metin and "satir_ici_arapca" not in b:
                b.append("satir_ici_arapca")
            for t in p["belirsiz_tire"]:
                if t.replace("-", "").lower() in " ".join(tr_u[x] for x in ti).lower() and "tire_belirsiz" not in b:
                    b.append("tire_belirsiz")
            # G-032 (Ö-2): neşir ilavesi çıkınca Arapçanın Türkçesi kayboluyor olabilir (ilave var, satır içi Arapça yok)
            if ilave_ve_atiflar(metin)[0] and "{ar:" not in metin and "ilave_karsiliksiz" not in b:
                b.append("ilave_karsiliksiz")
            g0 = ARMARK_RE.sub(" ", metin)
            if g0.count("[") != g0.count("]") and "parantez_siniri" not in b:
                b.append("parantez_siniri")
            # tire_belirsiz ve satir_ici_arapca yalnız satırın kendi metni için; diğer bayraklar pasajdan miras
            if "tire_belirsiz" in b and not any(t.replace("-", "").lower() in " ".join(tr_u[x] for x in ti).lower() for t in p["belirsiz_tire"]):
                b.remove("tire_belirsiz")
            if "satir_ici_arapca" in b and "{ar:" not in metin:
                b.remove("satir_ici_arapca")
            return b

        def satir(ai, ti, **ek):
            return dict(taban, ust=pid, ar_ids=["%s-c%02d" % (pid.replace("-p", "-a"), x + 1) for x in ai],
                        tr_ids=["%s-c%02d" % (pid.replace("-p", "-t"), x + 1) for x in ti],
                        ar=" ".join(ar_u[x] for x in ai), ar_parantezli=" ".join(ar_pu[x] for x in ai), tr=" ".join(tr_u[x] for x in ti),
                        tr_parantezli=" ".join(tr_pu[x] for x in ti),
                        nasir_ilavesi=ilave_ve_atiflar(" ".join(tr_pu[x] for x in ti))[0],
                        atiflar=ilave_ve_atiflar(" ".join(tr_pu[x] for x in ti))[1],
                        tr_satir_ici_arapca=ic_arapca_araliklari(" ".join(tr_pu[x] for x in ti), " ".join(tr_u[x] for x in ti)), **ek)

        if len(ar_u) <= 1 or len(tr_u) <= 1:
            bb = satir_bay(range(len(tr_u)), range(len(ar_u)))
            # tek birimlik pasaj kuralı (G-032): satır pasajın kendisidir. Kenar bandında (0.55-0.60) satır güveni
            # (uzunluk + leksik) belirleyici; altında pasaj kararı geçerli.
            gt, inc = g, inc
            if kenar and ar_u and tr_u:
                gt, _n = cumle_guveni(list(range(len(ar_u))), list(range(len(tr_u))), oran_z(p["ar_kel"], p["tr_kel"], ort_ln=sonuc["ort"], sd0=sonuc["sd"]),
                                      0, leksik_ortak(p["ar"], p["tr"]), g)
                inc = "insan" if gt < ESIK_INCELEME else "hayır"
            ana.append(satir(list(range(len(ar_u))), list(range(len(tr_u))), id=cid(ar_u[0] if ar_u else p["ar"], ar_pu[0] if ar_pu else None), duzey="cumle",
                             esleme="%d-%d" % (len(ar_u) or 1, len(tr_u) or 1), guven=gt,
                             gerekce="cümle düzeyi kurulamadı: bir tarafta tek birim; pasaj düzeyinde bırakıldı",
                             yontem="tek-birim", model="yok", inceleme=inc, butunluk=butunluk(bb), ogretici_uygun=(inc == "hayır" and not kusur(bb))))
            continue
        yol = dp_hizala(ar_u, tr_u)
        hesap = [cumle_guveni(ai, ti, z, bon, ov, g) for (ai, ti, z, bon, ov) in yol]
        kotu = sum(1 for (cg, _), (ai, ti, *_r) in zip(hesap, yol) if cg < 0.35 or not ai or not ti)
        if kotu / len(yol) > 0.4:
            ana.append(dict(taban, id=cid(p["ar"]), duzey="cumle_kurulamadi", ust=pid, ar_ids=[pid.replace("-p", "-a")],
                            tr_ids=[pid.replace("-p", "-t")], ar=p["ar"], tr=p["tr"], esleme="%d-%d" % (len(ar_u), len(tr_u)),
                            guven=min(g, 0.4), gerekce="cümle düzeyi kurulamadı: DP eşleşmelerinin %%%d'si düşük güvenli ya da atlamalı; pasaj düzeyinde bırakıldı" % round(100 * kotu / len(yol)),
                            yontem="uzunluk-DP+leksik (reddedildi)", model="yok", inceleme="insan",
                            butunluk=butunluk(ba + ["cumle_kurulamadi"]), ogretici_uygun=False))
            continue
        for ((ai, ti, z, bon, ov), (cg, neden)) in zip(yol, hesap):
            bb = satir_bay(ti, ai) if ti else list(ba)
            yon_ = artik_suphe([ar_u[x] for x in ai], [tr_u[x] for x in ti]) if (ti and ai) else None
            if yon_ and "artik_oge_suphe" not in bb:
                bb.append("artik_oge_suphe")   # G-032 (Ö-1)
            inc_s = "insan" if (cg < ESIK_INCELEME or (inc == "insan" and g < ESIK_BANT_ALT)) else "hayır"
            ana.append(satir(ai, ti, id=cid(ar_u[ai[0]] if ai else p["ar"], ar_pu[ai[0]] if ai else None), duzey="cumle", esleme="%d-%d" % (len(ai), len(ti)),
                             guven=cg, gerekce=neden, yontem="uzunluk-DP+baglac+leksik", model="yok (gömme modeli ölçülmedi)",
                             inceleme=inc_s, butunluk=butunluk(bb), ogretici_uygun=(inc_s == "hayır" and not kusur(bb)),
                             **({"kayma_yonu": yon_} if yon_ else {})))

    # Kısa artık kayması komşu satırı da kısmi yapar (G-031 Ö-1): şüpheli satırın yanındaki satırlar öğretici dışı
    sat = [k for k in ana if k["duzey"] == "cumle"]
    for i_, k in enumerate(sat):
        if "artik_oge_suphe" in k["butunluk"]["bayraklar"]:
            yon_ = k.get("kayma_yonu", "ikisi")   # G-037: yalnız kayma yönündeki komşu
            for j_ in {"onceki": (i_ - 1,), "sonraki": (i_ + 1,)}.get(yon_, (i_ - 1, i_ + 1)):
                if 0 <= j_ < len(sat) and sat[j_]["ust"] == k["ust"] and "artik_oge_suphe" not in sat[j_]["butunluk"]["bayraklar"] \
                        and "komsu_suphe" not in sat[j_]["butunluk"]["bayraklar"]:
                    bl_ = sat[j_]["butunluk"]["bayraklar"] + ["komsu_suphe"]
                    sat[j_]["butunluk"] = butunluk(bl_)
                    sat[j_]["ogretici_uygun"] = False

    # ---- alıntılar
    maks_q = reg["maks_q"]
    for a in sonuc["alintilar"]:
        s, t = a["ar_seg"], a["tr_seg"]
        ar = " ".join(b["metin"] for b in s["bloklar"])
        qid = reg["alinti"].get(norm_ar(ar)[:70])
        if not qid or qid in kullanilan:
            maks_q += 1
            qid = "%s-q%04d" % (kimlik, maks_q)
        kullanilan.add(qid)
        bay = ["dil_etiketi_tutarsiz"] if a["dil_tutarsiz_blok"] else []
        k = {"id": qid, "surum": SURUM, "duzey": "alinti", "tur": "alinti", "egitim_cifti": False,
             "fass": fass_no, "ar": ar, "dil": a["dil_tespit"], "dil_etiketi": sorted({b["dil"] for b in s["bloklar"]}),
             "kaynak_ar": kaynak(s["idx"]), "neden": a["neden"], "butunluk": butunluk(bay)}
        if t:
            k["tr"] = satir_birlestir([b["metin"] for b in t["bloklar"]])
            k["kaynak_tr"] = kaynak(t["idx"])
        if a.get("sahte"):
            k["onceki_sahte_pasaj"] = True
            k["onceki_pasaj_id"] = reg["pasaj"].get(norm_ar(ar_parantezsiz(ar))[:70]) or reg["pasaj"].get(norm_ar(ar)[:70])
            if a.get("izah"):
                k["tr_izah"] = a["izah"]
        alinti.append(k)

    # ---- dipnotlar (+ neşir varyantları)
    for no, d in sorted(sonuc["dipnotlar"].items()):
        bagli = [pid for pid, p in zip(pasaj_idleri, sonuc["pasajlar"]) if no in p["fn"]]
        nasil = "atif-pasajin-turkcesinde" if bagli else None
        if not bagli and no in sonuc["dip_ref_idx"]:
            once = [(p["s"]["idx"][0], pid) for pid, p in zip(pasaj_idleri, sonuc["pasajlar"]) if p["s"]["idx"][0] < sonuc["dip_ref_idx"][no]]
            if once:
                bagli, nasil = [max(once)[1]], "atif-serhte;yakin-onceki-pasaj"
        kayit = {"id": "%s-d%03d" % (kimlik, no), "surum": SURUM, "tur": "dipnot", "no": no, "sayfa": d["sayfa"],
                 "metin": d["metin"], "bagli_pasaj": bagli, "bagli_nasil": nasil}
        if no in dip_ar:
            kayit["ar_parcalari"] = dip_ar[no]
            kayit["tur"] = "dipnot_varyant" if re.search(r"nüsha|neşir|ibâre|ilâve|ilave|şeklinde|mevcut", d["metin"]) else "dipnot_arapca"
            if not bagli:
                kayit["not"] = "atıf bir pasajın Türkçesinde bulunamadı; pasaja bağlanamadı (insan incelemesi)"
        dipnot.append(kayit)
    return ana, alinti, dipnot


def _bosluksuz(t):
    return re.sub(r"\s+", "", t or "")


def tamlik_kontrol(ana, alinti, bloklar, bas, bit):
    """Yapısal tamlık (G-032): (1) pasaj ve alıntı Arapçası kaynak bloklarla aynı; (2) fassın Arapça blokları pasaj,
    alıntı ya da başlık/besmele olarak sayılmış (kayıp yok); (3) cümle satırları birleşince pasaj Arapçası ve
    Türkçesi çıkıyor. Dönüş: hata listesi (boşsa tamam)."""
    hata = []
    pos = {(b["sayfa"], b["sira"]): i for i, b in enumerate(bloklar)}

    def kaynak_ar(kay):
        i0, i1 = pos[(kay["ilk"]["sayfa"], kay["ilk"]["sira"])], pos[(kay["son"]["sayfa"], kay["son"]["sira"])]
        return [bloklar[i]["metin"] for i in range(i0, i1 + 1) if bloklar[i]["tur"] == "arapca"], range(i0, i1 + 1)

    kapsanan = set()
    kayit_ar = {}   # Arapça blok indeksi -> (tür, kayıt kimliği): yalnız kaydın kendi Arapça serisi
    for k in ana:
        if k["duzey"] == "pasaj":
            bl, rng = kaynak_ar(k["kaynak_ar"])
            for i in rng:
                if bloklar[i]["tur"] == "arapca":
                    kayit_ar[i] = ("pasaj", k["id"])
            kapsanan.update(rng)
            kapsanan.update(kaynak_ar(k["kaynak_tr"])[1])   # Türkçe paragrafın içindeki satır içi Arapça bloklar
            if _bosluksuz(norm_ar(" ".join(bl))) != _bosluksuz(norm_ar(k["ar_parantezli"])):
                hata.append((k["id"], "pasaj Arapçası kaynak değil"))
    for k in alinti:
        bl, rng = kaynak_ar(k["kaynak_ar"])
        for i in rng:
            if bloklar[i]["tur"] == "arapca":
                kayit_ar[i] = ("alinti", k["id"])
        kapsanan.update(rng)
        if "kaynak_tr" in k:
            kapsanan.update(kaynak_ar(k["kaynak_tr"])[1])
        if _bosluksuz(norm_ar(" ".join(bl))) != _bosluksuz(norm_ar(k["ar"])):
            hata.append((k["id"], "alıntı Arapçası kaynak değil"))
    baslik = next((k for k in ana if k["duzey"] == "baslik"), None)
    if baslik:
        kapsanan.update(kaynak_ar(baslik["kaynak"])[1])
    for i in range(bas, bit):
        b = bloklar[i]
        if b["tur"] == "arapca" and i not in kapsanan and len(AR_LETTER.findall(norm_ar(b["metin"]))) > 3:
            hata.append(("blok %d (s. %s)" % (i, b["sayfa"]), "Arapça blok hiçbir kayda bağlanmadı: " + b["metin"][:30]))
    # Fusûs Arapçası bölünmüş mü? Araya yalnız işaret / sayfa başlığı / dipnot giren ardışık Arapça bloklar aynı kayıtta
    # olmalı; biri pasaja öbürü alıntıya gittiyse (G-034 Ö-1: kırık sayfa işareti) hata.
    onceki_i = None
    for i in range(bas, bit):
        t = bloklar[i]["tur"]
        if t in ("isaret", "baslik_sayfa", "dipnot"):
            continue
        if t == "arapca" and i in kayit_ar:
            if onceki_i is not None and kayit_ar[onceki_i] != kayit_ar[i]:
                hata.append((kayit_ar[onceki_i][1] + " | " + kayit_ar[i][1], "ardışık Arapça bloklar farklı kayıtlara düşmüş (bölünmüş Fusûs Arapçası, s. %s)" % bloklar[i]["sayfa"]))
            onceki_i = i
        else:
            onceki_i = None
    pas = {k["id"]: k for k in ana if k["duzey"] == "pasaj"}
    satirlar = {}
    for k in ana:
        if k["duzey"] in ("cumle", "cumle_kurulamadi"):
            satirlar.setdefault(k["ust"], []).append(k)
    for pid, k in pas.items():
        sat = satirlar.get(pid, [])
        if not sat:
            hata.append((pid, "pasajın cümle satırı yok"))
            continue
        if sat[0]["duzey"] == "cumle_kurulamadi":
            continue
        if _bosluksuz(" ".join(x["ar_parantezli"] for x in sat)) != _bosluksuz(k["ar_parantezli"]):
            hata.append((pid, "cümle Arapçası birleşince pasaj Arapçası çıkmıyor"))
        if _bosluksuz(" ".join(x["tr_parantezli"] for x in sat)) != _bosluksuz(k["tr_parantezli"]):
            hata.append((pid, "cümle Türkçesi birleşince pasaj Türkçesi çıkmıyor"))
    return hata


def yaz(yol, kayit):
    with open(yol, "w", encoding="utf-8") as f:
        for k in kayit:
            f.write(json.dumps(k, ensure_ascii=False) + "\n")


def en_yeni_surum_dizini(cikti):
    kok = os.path.join(cikti, "surum")
    if not os.path.isdir(kok):
        return os.path.join(kok, "hat-0.1")
    adaylar = []
    for d in os.listdir(kok):
        m = re.fullmatch(r"hat-(\d+(?:\.\d+)*)", d)
        if m:
            adaylar.append((tuple(int(x) for x in m.group(1).split(".")), d))
    return os.path.join(kok, max(adaylar)[1]) if adaylar else os.path.join(kok, "hat-0.1")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cilt", type=int, default=1, help="Konuk cildi (1, 2); girdi/çıktı/kimlik öneki buna göre seçilir")
    ap.add_argument("--girdi", default=None)
    ap.add_argument("--cikti", default=None)
    ap.add_argument("--fass", type=int, default=1, help="cilt içindeki fass sırası (1 = ciltteki ilk fass)")
    ap.add_argument("--onceki", default=None, help="kimlikleri korunacak önceki sürüm dizini (varsayılan: <cikti>/surum/hat-0.1)")
    a = ap.parse_args(argv)
    ay = cilt_ayari(a.cilt)
    girdi, cikti = a.girdi or ay["girdi"], a.cikti or ay["cikti"]
    onceki = a.onceki or en_yeni_surum_dizini(cikti)
    bloklar = yukle(girdi)
    sonuc = hizala(bloklar, a.fass, ay["min_sayfa"], ay.get("son_baslik"))
    ana, alinti, dipnot = kayitlar(sonuc, a.fass, onceki=onceki if os.path.isdir(onceki) else None, kimlik_oneki=ay["kimlik"])
    os.makedirs(cikti, exist_ok=True)
    hatalar = tamlik_kontrol(ana, alinti, bloklar, sonuc["bas"], sonuc["bit"])
    for h in hatalar:
        print("TAMLIK HATASI:", h, file=sys.stderr)
    ad = "fass-%02d" % a.fass
    yaz(os.path.join(cikti, ad + ".jsonl"), ana)
    yaz(os.path.join(cikti, ad + ".alinti.jsonl"), alinti)
    yaz(os.path.join(cikti, ad + ".dipnot.jsonl"), dipnot)
    b0, b1 = bloklar[sonuc["bas"]], bloklar[sonuc["bit"] - 1]
    bas_b = next((bloklar[i]["basili_sayfa"] for i in range(sonuc["bas"], sonuc["bit"]) if bloklar[i]["basili_sayfa"]), None)
    son_b = next((bloklar[i]["basili_sayfa"] for i in range(sonuc["bit"] - 1, sonuc["bas"], -1) if bloklar[i]["basili_sayfa"]), None)
    pas = [k for k in ana if k["duzey"] == "pasaj"]
    cum = [k for k in ana if k["duzey"] == "cumle"]
    print("fass %d (%s): PDF s. %s-%s (basılı %s-%s); pasaj %d (insan %d, bütünlük kontrol %d), cümle %d (insan %d, bütünlük kontrol %d, öğretici uygun %d), alıntı %d, dipnot %d" % (
        a.fass, SURUM, b0["sayfa"], b1["sayfa"], bas_b, son_b, len(pas),
        sum(k["inceleme"] == "insan" for k in pas), sum(k["butunluk"]["durum"] == "kontrol" for k in pas), len(cum),
        sum(k["inceleme"] == "insan" for k in cum), sum(k["butunluk"]["durum"] == "kontrol" for k in cum),
        sum(k["ogretici_uygun"] for k in cum), len(alinti), len(dipnot)) + "; sahte pasaj->alıntı %d; tamlık %s" % (
        sum(1 for q in alinti if q.get("onceki_sahte_pasaj")), "tamam" if not hatalar else "%d HATA" % len(hatalar)))


if __name__ == "__main__":
    main()
