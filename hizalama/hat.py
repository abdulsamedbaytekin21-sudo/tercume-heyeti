#!/usr/bin/env python3
"""Mukabeleci: Konuk Fusûs şerhinden bir fassın Arapça-Türkçe hizalama hattı (sürüm hat-0.1).

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
import json
import math
import os
import re
import sys
import unicodedata

SURUM = "hat-0.1"
ESIK_INCELEME = 0.60

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


def fass_sinirlari(bloklar, no=1):
    """Fass başlığı (Arapça 'فص حكمة ...') bloğundan sonraki fass başlığının basmalasına kadar.

    Dönüş: (baslik_idx, bitis_idx_dahil_degil). no: 1 = ilk fass.
    """
    basliklar = []
    for i, b in enumerate(bloklar):
        if b["tur"] == "arapca" and norm_ar(b["metin"]).startswith("فص حكمة") and b["sayfa"] > 40:
            basliklar.append(i)
    if len(basliklar) < no:
        raise ValueError("fass başlığı bulunamadı")
    bas = basliklar[no - 1]
    bit = basliklar[no] if len(basliklar) > no else len(bloklar)
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


def satir_birlestir(satirlar):
    """Fiziksel satırları birleştirir; satır sonu tireyi kaldırır (izâfet 'ât-ı' gibi kısa devamlar hariç)."""
    out = ""
    for s in satirlar:
        s = s.strip()
        if not s:
            continue
        if out.endswith("-") and out[-2:-1].isalpha():
            ilk = re.split(r"[\s,.;:?!”’)\]]", s, maxsplit=1)[0]
            if ilk[:1].islower() and ilk not in IZAFET:
                out = out[:-1] + s  # hece bölünmesi: 'üze-/re' -> 'üzere'
            else:
                out += s
            continue
        out = (out + " " + s) if out else s
    return out


def ilave_ve_isaretler(tr):
    """Köşeli parantez ilavelerini, sayfa işaretlerini, dipnot atıflarını ayıkla.

    Dönüş: (metin_isaretli, ilaveler, sayfa_isaretleri, dipnot_ref, parantezler)
    metin_isaretli: ilaveler korunur ('[...]'); sayfa/dipnot işaretleri çıkarılır.
    """
    fn = [int(x) for x in FN_REF.findall(tr)]
    t = FN_REF.sub("", tr)
    sayfa = [m.group(0).strip() for m in PAGE_MARK.finditer(t)]
    t = PAGE_MARK.sub(" ", t)
    t = re.sub(r"\s+", " ", t).strip()
    ilaveler = [m.group(1).strip() for m in re.finditer(r"\[([^\[\]]+)\]", t)]
    paren = []
    for m in re.finditer(r"\(([^()]{1,80})\)", t):
        ic = m.group(1)
        if re.fullmatch(r"(?:[a-zA-Z]\.){1,4}[a-zA-Z]?\.?\)?", ic) or re.fullmatch(r"(?:r|a|s|c|k)\.[a-z.]+", ic):
            continue  # (r.a.) (a.s.) benzeri salavat/rıdvan formülleri
        paren.append({"metin": ic, "tur": "atif" if re.search(r"\d+/\d+", ic) else "aciklama"})
    return t, ilaveler, sayfa, fn, paren


def ilavesiz(t):
    return re.sub(r"\s+", " ", re.sub(r"\[[^\[\]]+\]", " ", t)).strip()


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
    t = [tr_iskelet(w) for w in ilavesiz(tr_metin).split() if w.lower().strip("’'.,;:“”") not in _TR_STOP]
    t = [x for x in t if len(x) >= 3]
    ok = sum(any(x in y for y in t) for x in a)
    return ok / len(a)


ABBR = re.compile(r"(?:^|\s)(?:\w{1,2}|Hz|Bk|bk|vs|ö|yy)\.$")


def tr_cumleler(t):
    """Türkçeyi cümle/öbeğe böler: ';' her zaman, '.', '?', '!' büyük harf/tırnak öncesi."""
    parcalar, bas = [], 0
    for m in re.finditer(r"[.;?!]+[”’\"»)\]]*\s+", t):
        son = m.end()
        onceki = t[bas:m.start() + 1]
        sonraki = t[son:son + 1]
        isaret = t[m.start()]
        if isaret == ";":
            pass
        elif ABBR.search(onceki[-12:]):
            continue
        elif not (sonraki.isupper() or sonraki in "“\"‘[(«"):
            continue
        parcalar.append(t[bas:son].strip())
        bas = son
    son_parca = t[bas:].strip()
    if son_parca:
        parcalar.append(son_parca)
    return parcalar


def ar_cumleler(t):
    """Arapçayı '،' '؛' '.' '؟' ve ﴾ sonrasında böler (Konuk Arapçasında noktalama seyrektir)."""
    parcalar, bas = [], 0
    for m in re.finditer(r"[،؛.؟﴾]+\s*", t):
        parcalar.append(t[bas:m.end()].strip())
        bas = m.end()
    kalan = t[bas:].strip()
    if kalan:
        parcalar.append(kalan)
    # çok kısa parçaları (ör. tek sözcük) bir sonrakiyle birleştir
    out = []
    for p in parcalar:
        if out and len(AR_LETTER.findall(norm_ar(out[-1]))) < 6:
            out[-1] = out[-1] + " " + p
        else:
            out.append(p)
    if len(out) > 1 and len(AR_LETTER.findall(norm_ar(out[-1]))) < 6:
        out[-2] = out[-2] + " " + out.pop()
    return out


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


def kucuk_harfle_basliyor(seg):
    t = seg["bloklar"][0]["metin"].lstrip()
    return bool(LATIN_LOWER.match(t))


def satir_ici_birlestir(segs):
    """tr + ar + tr(küçük harfle devam) -> tek Türkçe seri; Arapça parça 'satır içi' işaretlenir."""
    out, i = [], 0
    while i < len(segs):
        s = segs[i]
        if (
            s["k"] == "tr" and i + 2 < len(segs)
            and segs[i + 1]["k"] == "ar" and segs[i + 2]["k"] == "tr"
            and kucuk_harfle_basliyor(segs[i + 2])
        ):
            s = dict(s)
            s["parcalar"] = s.get("parcalar") or [("tr", s["bloklar"])]
            s["isaretler"] = list(s["isaretler"])
            while (
                i + 2 < len(segs)
                and segs[i + 1]["k"] == "ar" and segs[i + 2]["k"] == "tr"
                and kucuk_harfle_basliyor(segs[i + 2])
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


ALINTI_TR = re.compile(r"^(Tercüme|Îzâhen|Ya[’']ni\s*:)")
IZAH_TR = re.compile(r"^Ya[’']ni\b")


def farsca_mi(metin):
    harf = AR_LETTER.findall(metin)
    return bool(harf) and len(FARSI_ONLY.findall(metin)) / len(harf) > 0.01


def tr_serisini_ayir(seg):
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
                    literal_parcalar.append(satir_birlestir(satirlar))
                    satirlar = []
                izahta = True
            if izahta:
                izah.append(b["metin"])
            else:
                satirlar.append(b["metin"])
        if satirlar:
            literal_parcalar.append(satir_birlestir(satirlar))
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
    lt = [max(1, len(re.sub(r"[^\w]", "", ilavesiz(x)))) for x in tr_u]
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
    g = min(g, 0.9, pasaj_guveni + 0.05)
    neden = "uzunluk z=%.2f, leksik örtüşme %.2f, eşleşme %d-%d%s" % (abs(z), ov, tur[0], tur[1], ", bağlaç çapası" if bon else "")
    return round(g, 3), neden


# ---------------------------------------------------------------- pasaj güveni

def pasaj_guveni(ar_kelime, tr_kelime, ort_ln_oran, sd_ln, ic_ar, farsca, ov):
    """Yapı temiz (Arapça seri -> Türkçe seri bitişik) ise 0.92 taban; oran sapması ve küçüklük cezası."""
    gerekce = ["yapı: Arapça seri + bitişik 'terceme' serisi"]
    g = 0.92
    if ar_kelime == 0 or tr_kelime == 0:
        return 0.0, ["boş taraf"]
    ln = math.log(tr_kelime / ar_kelime)
    z = (ln - ort_ln_oran) / max(sd_ln, 0.12)
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

def hizala(bloklar, fass_no=1):
    bas, bit = fass_sinirlari(bloklar, fass_no)
    segs, dipnot_bloklari = segmentle(bloklar, bas, bit)
    segs = satir_ici_birlestir(segs)
    dipnotlar = dipnotlari_coz(dipnot_bloklari)

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

    # pasaj verisi
    pasajlar = []
    for s, t in adaylar:
        ar = " ".join(b["metin"] for b in s["bloklar"])
        literal, izah, ic_ar = tr_serisini_ayir(t)
        tr_t, ilaveler, sayfa_isaret, fn, paren = ilave_ve_isaretler(literal)
        # {ar: ...} parçaları ilave_ve_isaretler'den geçerken bozulmaz; köşeli parantez yok
        izah_t, _, _, fn2, _ = ilave_ve_isaretler(izah) if izah else ("", [], [], [], [])
        ar_kel = len(norm_ar(ar).split())
        tr_kel = len(ilavesiz(re.sub(r"\{ar:[^}]*\}", " ", tr_t)).split())
        pasajlar.append({
            "s": s, "t": t, "ar": ar, "tr": tr_t, "izah": izah_t, "ic_ar": ic_ar, "ilaveler": ilaveler,
            "sayfa_isaret": sorted(set(s["isaretler"] + t["isaretler"] + sayfa_isaret)),
            "fn": sorted(set(fn + fn2)), "paren": paren, "ar_kel": ar_kel, "tr_kel": tr_kel,
        })
    loglar = sorted(math.log(p["tr_kel"] / p["ar_kel"]) for p in pasajlar if p["ar_kel"] >= 6 and p["tr_kel"] >= 6)
    ort = loglar[len(loglar) // 2] if loglar else 0.3
    sd = (sorted(abs(x - ort) for x in loglar)[len(loglar) // 2] * 1.4826) if loglar else 0.2
    return {
        "bas": bas, "bit": bit, "baslik": baslik, "pasajlar": pasajlar, "alintilar": alintilar,
        "dipnotlar": dipnotlar, "ort": ort, "sd": sd, "bloklar": bloklar,
    }


def kayitlar(sonuc, fass_no=1, eser_ar="E-006", eser_tr="E-001"):
    """JSONL kayıtlarını üretir. Dönüş: (ana, alinti, dipnot)"""
    bl = sonuc["bloklar"]
    kimlik = "fusus-konuk-f%02d" % fass_no
    ana, alinti, dipnot = [], [], []

    def kaynak(idx):
        return {"ilk": {"sayfa": bl[idx[0]]["sayfa"], "basili": bl[idx[0]]["basili_sayfa"], "sira": bl[idx[0]]["sira"]},
                "son": {"sayfa": bl[idx[-1]]["sayfa"], "basili": bl[idx[-1]]["basili_sayfa"], "sira": bl[idx[-1]]["sira"]}}

    taban = {"surum": SURUM, "eser_ar": eser_ar, "eser_tr": eser_tr, "fass": fass_no}
    if sonuc["baslik"]:
        b = sonuc["baslik"]
        ana.append(dict(taban, id="%s-b0001" % kimlik, duzey="baslik", ar_id="%s-a-b0001" % kimlik, tr_id="%s-t-b0001" % kimlik,
                        ar=b["ar"], tr=b["tr"], esleme="1-1", guven=0.9, gerekce="fass başlığı: Arapça başlık satırı + bitişik Türkçe başlık",
                        yontem="yapi-capa", model="yok", inceleme="hayır", kaynak=kaynak(b["blok"])))

    for n, p in enumerate(sonuc["pasajlar"], 1):
        pid = "%s-p%04d" % (kimlik, n)
        g, gerekce = pasaj_guveni(p["ar_kel"], p["tr_kel"], sonuc["ort"], sonuc["sd"], p["ic_ar"], farsca_mi(p["ar"]), leksik_ortak(p["ar"], p["tr"]))
        inc = "insan" if g < ESIK_INCELEME else "hayır"
        ana.append(dict(taban, id=pid, duzey="pasaj", ar_id=pid.replace("-p", "-a"), tr_id=pid.replace("-p", "-t"),
                        ar=p["ar"], ar_norm=norm_ar(p["ar"]), tr=p["tr"], tr_ilavesiz=ilavesiz(re.sub(r"\{ar:[^}]*\}", " ", p["tr"])),
                        tr_izah=p["izah"], ilaveler=p["ilaveler"], parantezler=p["paren"], tr_satir_ici_arapca=p["ic_ar"],
                        dipnot_ref=p["fn"], sayfa_isaretleri=p["sayfa_isaret"], esleme="1-1", ar_kelime=p["ar_kel"], tr_kelime=p["tr_kel"],
                        guven=g, gerekce="; ".join(gerekce), yontem="yapi-capa+oran", model="yok (gömme modeli ölçülmedi)",
                        inceleme=inc, kaynak_ar=kaynak(p["s"]["idx"]), kaynak_tr=kaynak(p["t"]["idx"])))
        # cümle düzeyi
        ar_u = ar_cumleler(p["ar"])
        tr_u = tr_cumleler(p["tr"])
        if len(ar_u) <= 1 or len(tr_u) <= 1:
            ana.append(dict(taban, id=pid + "-c01", duzey="cumle", ust=pid, ar_ids=[pid.replace("-p", "-a") + "-c01"],
                            tr_ids=[pid.replace("-p", "-t") + "-c01"], ar=p["ar"], tr=p["tr"], esleme="%d-%d" % (len(ar_u) or 1, len(tr_u) or 1),
                            guven=g, gerekce="cümle düzeyi kurulamadı: bir tarafta tek birim; pasaj düzeyinde bırakıldı",
                            yontem="tek-birim", model="yok", inceleme=inc))
            continue
        yol = dp_hizala(ar_u, tr_u)
        hesap = [cumle_guveni(ai, ti, z, bon, ov, g) for (ai, ti, z, bon, ov) in yol]
        kotu = sum(1 for (cg, _), (ai, ti, *_r) in zip(hesap, yol) if cg < 0.35 or not ai or not ti)
        if kotu / len(yol) > 0.4:
            ana.append(dict(taban, id=pid + "-c01", duzey="cumle", ust=pid, ar_ids=[pid.replace("-p", "-a") + "-c01"],
                            tr_ids=[pid.replace("-p", "-t") + "-c01"], ar=p["ar"], tr=p["tr"], esleme="%d-%d" % (len(ar_u), len(tr_u)),
                            guven=min(g, 0.4), gerekce="cümle düzeyi kurulamadı: DP eşleşmelerinin %%%d'si düşük güvenli ya da atlamalı; pasaj düzeyinde bırakıldı" % round(100 * kotu / len(yol)),
                            yontem="uzunluk-DP+leksik (reddedildi)", model="yok", inceleme="insan"))
            continue
        for k, ((ai, ti, z, bon, ov), (cg, neden)) in enumerate(zip(yol, hesap), 1):
            ana.append(dict(taban, id="%s-c%02d" % (pid, k), duzey="cumle", ust=pid,
                            ar_ids=["%s-c%02d" % (pid.replace("-p", "-a"), x + 1) for x in ai],
                            tr_ids=["%s-c%02d" % (pid.replace("-p", "-t"), x + 1) for x in ti],
                            ar=" ".join(ar_u[x] for x in ai), tr=" ".join(tr_u[x] for x in ti),
                            esleme="%d-%d" % (len(ai), len(ti)), guven=cg, gerekce=neden,
                            yontem="uzunluk-DP+baglac", model="yok (gömme modeli ölçülmedi)",
                            ilave_var=any("[" in tr_u[x] for x in ti),
                            inceleme="insan" if (cg < ESIK_INCELEME or inc == "insan") else "hayır"))

    for n, a in enumerate(sonuc["alintilar"], 1):
        s, t = a["ar_seg"], a["tr_seg"]
        ar = " ".join(b["metin"] for b in s["bloklar"])
        varyant = varyant_ara(ar, s["idx"][0], sonuc["pasajlar"], ana)
        k = {"id": "%s-q%04d" % (kimlik, n), "surum": SURUM, "duzey": "alinti", "tur": "alinti", "egitim_cifti": False,
             "fass": fass_no, "ar": ar, "dil": "fa" if farsca_mi(ar) else "ar", "kaynak_ar": kaynak(s["idx"]), "neden": a["neden"]}
        if varyant:
            k["tur"] = "varyant"
            k["varyant_pasaj"] = varyant
            k["neden"] = "pasaj Arapçasının sözcükleriyle büyük ölçüde örtüşüyor: nüsha farkı/yinelenen ibare olabilir; çifte girmedi"
        if t:
            k["tr"] = satir_birlestir([b["metin"] for b in t["bloklar"]])
            k["kaynak_tr"] = kaynak(t["idx"])
        alinti.append(k)

    for no, d in sorted(sonuc["dipnotlar"].items()):
        bagli = [p["id"] for p in ana if p.get("duzey") == "pasaj" and no in p.get("dipnot_ref", [])]
        dipnot.append({"id": "%s-d%03d" % (kimlik, no), "surum": SURUM, "tur": "dipnot", "no": no, "sayfa": d["sayfa"],
                       "metin": d["metin"], "bagli_pasaj": bagli})
    return ana, alinti, dipnot


def varyant_ara(ar, idx0, pasajlar, ana):
    """Eşsiz kalan, Farsça olmayan, >=6 sözcüklük Arapça ibare en yakın önceki pasajla örtüşüyorsa pasaj kimliğini verir."""
    kel = norm_ar(ar).split()
    if len(kel) < 6 or farsca_mi(ar):
        return None
    onceki = [(k, p) for k, p in enumerate(pasajlar) if p["s"]["idx"][0] < idx0]
    if not onceki:
        return None
    k, p = onceki[-1]
    havuz = set(norm_ar(p["ar"]).split())
    oran = sum(w in havuz for w in kel) / len(kel)
    return "fusus-konuk-f%02d-p%04d" % (ana[0]["fass"] if ana else 1, k + 1) if oran >= 0.6 else None


def yaz(yol, kayit):
    with open(yol, "w", encoding="utf-8") as f:
        for k in kayit:
            f.write(json.dumps(k, ensure_ascii=False) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--girdi", default="veri/kasa/metin/konuk1/temiz.jsonl")
    ap.add_argument("--cikti", default="veri/kasa/hizalama/fusus-konuk")
    ap.add_argument("--fass", type=int, default=1)
    a = ap.parse_args(argv)
    bloklar = yukle(a.girdi)
    sonuc = hizala(bloklar, a.fass)
    ana, alinti, dipnot = kayitlar(sonuc, a.fass)
    os.makedirs(a.cikti, exist_ok=True)
    ad = "fass-%02d" % a.fass
    yaz(os.path.join(a.cikti, ad + ".jsonl"), ana)
    yaz(os.path.join(a.cikti, ad + ".alinti.jsonl"), alinti)
    yaz(os.path.join(a.cikti, ad + ".dipnot.jsonl"), dipnot)
    b0, b1 = bloklar[sonuc["bas"]], bloklar[sonuc["bit"] - 1]
    bas_b = next((bloklar[i]["basili_sayfa"] for i in range(sonuc["bas"], sonuc["bit"]) if bloklar[i]["basili_sayfa"]), None)
    son_b = next((bloklar[i]["basili_sayfa"] for i in range(sonuc["bit"] - 1, sonuc["bas"], -1) if bloklar[i]["basili_sayfa"]), None)
    b0 = dict(b0, basili_sayfa=bas_b)
    b1 = dict(b1, basili_sayfa=son_b)
    pas = [k for k in ana if k["duzey"] == "pasaj"]
    cum = [k for k in ana if k["duzey"] == "cumle"]
    print("fass %d: PDF s. %s-%s (basılı %s-%s); pasaj %d (inceleme:insan %d), cümle %d (insan %d), alıntı %d, dipnot %d" % (
        a.fass, b0["sayfa"], b1["sayfa"], b0["basili_sayfa"], b1["basili_sayfa"], len(pas),
        sum(k["inceleme"] == "insan" for k in pas), len(cum), sum(k["inceleme"] == "insan" for k in cum), len(alinti), len(dipnot)))


if __name__ == "__main__":
    main()
