"""cikar.py birim testleri. Sentetik veri kullanır (kitaptan metin parçası yok).
Çalıştırma: cd metin/konuk && python3 -m unittest"""
import unittest

import cikar

AR = "Scheherazade"


def ch(text, x0, x1=None, font=AR, size=14.0, top=100.0, cid=None):
    fn = font if cid is None else "%s#%d" % (font, cid)
    return {"text": text, "x0": x0, "x1": x0 + 2.0 if x1 is None else x1, "fontname": fn,
            "size": size, "top": top, "bottom": top + size}


class ArLogical(unittest.TestCase):
    def test_ters_sira(self):
        # görsel (soldan sağa) akış: ب sonra ك -> mantıksal "كب"
        _, t = cikar.ar_logical([ch("ب", 10), ch("ك", 14)])
        self.assertEqual(t, "كب")

    def test_hemzeli_elif_fffd(self):
        # أن : akışta ن, أ(0 genişlik), U+FFFD(taban) ; mantıksal "أن"
        s = [ch("ن", 10), ch("أ", 14, 14, cid=913), ch("�", 14, 16, cid=257)]
        _, t = cikar.ar_logical(s)
        self.assertEqual(t, "أن")

    def test_hemze_ve_duz_elif_tabani(self):
        # hemze + ayrı ا tabanı (lam-elif ligatürü) -> tek hemzeli elif
        s = [ch("ن", 10), ch("إ", 14, 14, cid=914), ch("ا", 14.2, 16.5)]
        _, t = cikar.ar_logical(s)
        self.assertEqual(t, "إن")

    def test_yalniz_fffd_elif_olur(self):
        s = [ch("ل", 10), ch("�", 12, 14, cid=257)]
        _, t = cikar.ar_logical(s)
        self.assertEqual(t, "ال")

    def test_cid_ile_fetha(self):
        s = [ch("أ", 10, 10, cid=1110), ch("�", 10, 12, cid=257)]
        _, t = cikar.ar_logical(s)
        self.assertEqual(t, "أَ")

    def test_cid_ile_damme(self):
        s = [ch("أ", 10, 10, cid=1111), ch("�", 10, 12, cid=257)]
        _, t = cikar.ar_logical(s)
        self.assertEqual(t, "أُ")

    def test_serbest_ayri_ا_ve_hemze_birlesmez(self):
        # hemze taban genişliğinin dışında -> ا ayrı harf kalır
        s = [ch("ن", 10), ch("أ", 14, 14, cid=913), ch("�", 14, 16, cid=257), ch("ا", 20, 22)]
        _, t = cikar.ar_logical(s)
        self.assertEqual(t, "اأن")


class Temizlik(unittest.TestCase):
    def test_tatvil_ve_bosluk(self):
        self.assertEqual(cikar.clean_ar("كـــتاب  ب"), "كتاب ب")

    def test_shey_bosluk(self):
        self.assertEqual(cikar.clean_ar("شَيْ ءٌ"), "شَيْءٌ")

    def test_yetim_hareke(self):
        self.assertEqual(cikar.clean_ar("َ كتاب"), "كتاب")

    def test_dil(self):
        self.assertEqual(cikar.ar_lang("چراغ"), "fa")
        self.assertEqual(cikar.ar_lang("في الأرض"), "ar")
        self.assertEqual(cikar.ar_lang("از تو به من"), "fa")

    def test_tire_birlestirme(self):
        self.assertEqual(cikar.tr_clean(["tefsî-", "rinde şöyle"]), "tefsîrinde şöyle")
        self.assertEqual(cikar.tr_clean(["Ahmed-", "İbn"]), "Ahmed- İbn")


class Parcalama(unittest.TestCase):
    def test_satir_ve_dil_siniri(self):
        a = [ch("ا", 10 + i * 3) for i in range(3)]
        t = [ch("a", 50, font="AGaramondPro-Regular", size=11.5)]
        b = [ch("ب", 10, top=140.0)]
        runs = cikar.split_runs(a + t + b)
        self.assertEqual([m for m, _ in runs], ["ar", "tr", "ar"])

    def test_hemistis_bosluk(self):
        a = [ch("ا", 10), ch("ب", 13), ch("ج", 80)]
        runs = cikar.split_runs(a)
        self.assertEqual(len(runs), 2)

    def test_ust_indis_satiri_bolmez(self):
        g = "AGaramondPro-Regular"
        s = [ch("a", 10, font=g, size=11.5), ch("1", 20, font=g, size=6.7, top=95.0)]
        s.append(ch("b", 25, font=g, size=11.5))
        self.assertEqual(len(cikar.split_runs(s)), 1)
        text, temiz = cikar.tr_line_text(s[:2], None)
        self.assertEqual(temiz, "a[^1]")


class FakeSayfa:
    def __init__(self, chars, sep_top=None):
        self.chars = chars
        self.rects = []
        self.lines = [] if sep_top is None else [{"top": sep_top, "bottom": sep_top, "x0": 60, "x1": 200}]


G = "AGaramondPro-Regular"


def tr(text, x0, top, x1=None):
    return ch(text, x0, x0 + 40.0 if x1 is None else x1, font=G, size=11.5, top=top)


class KarisikSatir(unittest.TestCase):
    """G-026: satır içi Arapçalı Türkçe satırlar. Sentetik veri."""

    def metinler(self, blocks):
        return [(b["tur"], b["metin"]) for b in blocks]

    def test_turkce_arapca_turkce_sirasi(self):
        # satır 1: "bir" (x80) | Arapça (x130-170) | "kavli, siz-" (x180); satır 2: "den sonra" (x80)
        # PDF akışı soldan sağa; Türkçe parça Arapçanın SOLUNDA ve SAĞINDA
        chars = [tr("kavli, siz-", 180, 100.0), ch("ب", 130, 134, top=101.0), ch("ك", 134, 138, top=101.0),
                 tr("bir", 80, 100.0), tr("den sonra", 80, 114.5)]
        b = cikar.page_blocks(FakeSayfa(chars))
        self.assertEqual(self.metinler(b), [("serh", "bir"), ("arapca", "كب"), ("serh", "kavli, sizden sonra")])

    def test_arapca_iki_satira_tasan_parca(self):
        # satır 1: Türkçe | Arapça(başı); satır 2: Arapça(devamı) | Türkçe
        chars = [tr("önce", 80, 100.0), ch("ب", 150, 154, top=101.0),
                 ch("ك", 90, 94, top=115.0), tr("(Nisâ)", 130, 114.5)]
        b = cikar.page_blocks(FakeSayfa(chars))
        self.assertEqual([t for t, _ in self.metinler(b)], ["serh", "arapca", "arapca", "serh"])
        self.assertEqual(self.metinler(b)[0][1], "önce")
        self.assertEqual(self.metinler(b)[-1][1], "(Nisâ)")

    def test_yalniz_arapca_satir_sagdan_sola(self):
        chars = [ch("ب", 100, 104), ch("ك", 300, 304)]
        b = cikar.page_blocks(FakeSayfa(chars))
        self.assertEqual([x["metin"] for x in b], ["ك", "ب"])

    def test_dipnot_arapcasi_dipnotta_kalir(self):
        chars = [tr("gövde metni", 80, 100.0),
                 tr("99 ibâreyi", 70, 520.0), ch("ب", 140, 144, top=521.0), tr("şeklinde", 160, 520.0)]
        b = cikar.page_blocks(FakeSayfa(chars, sep_top=500.0))
        self.assertEqual([x["tur"] for x in b], ["serh", "dipnot"])
        self.assertEqual(b[1]["metin"], "99 ibâreyi {ar: ب} şeklinde")

    def test_fdfa_korunur(self):
        self.assertEqual(cikar.clean_ar("قال ﷺ ثم"), "قال ﷺ ثم")
        self.assertEqual(cikar.clean_ar("ﷲ"), "ﷲ")
        self.assertEqual(cikar.clean_ar("ﻻ"), "لا")   # diğer sunum biçimleri NFKC ile standarda iner


class Cilt2(unittest.TestCase):
    """G-033: 2. cilt (TYEK 2024) dizgi farkları. Sentetik veri."""

    def test_bolum_isareti_ust_indisi_dipnot_cagrisi_degil(self):
        g = G
        s = [ch("[", 10, font=g, size=11.5), ch("2", 14, font=g, size=11.5), ch("5", 18, font=g, size=11.5),
             ch("1", 22, font=g, size=6.7, top=95.0), ch("/", 25, font=g, size=11.5), ch("4", 29, font=g, size=11.5),
             ch("]", 33, font=g, size=11.5)]
        _, t = cikar.tr_line_text(s, None)
        self.assertEqual(t, "[25¹/4]")
        # dipnot çağrısı hâlâ [^n]
        s2 = [ch("a", 10, font=g, size=11.5), ch("1", 14, font=g, size=6.7, top=95.0), ch("b", 18, font=g, size=11.5)]
        self.assertEqual(cikar.tr_line_text(s2, None)[1], "a[^1]b")

    def test_dizinde_ust_indis_duz_rakam(self):
        cikar.INDEKS = True
        try:
            s = [ch("a", 10, font=G, size=11.5), ch("1", 14, font=G, size=6.7, top=95.0)]
            self.assertEqual(cikar.tr_line_text(s, None)[1], "a1")
        finally:
            cikar.INDEKS = False

    def test_okunamayan_glif_isaretlenir(self):
        # TraditionalNaskh: metin katmanında (cid:N) ve İbrani yer tutucu; tahmin edilmez
        n = "TraditionalNaskh"
        s = [ch("ب", 10, font=n), ch("(cid:243)", 14, font=n), ch("(cid:220)", 18, font=n), ch("כ", 22, font=n), ch("ك", 26, font=n)]
        _, t = cikar.ar_logical(s)
        self.assertEqual(t, "ك⟨?⟩ب")

    def test_arapca_icindeki_rakam_ters_cevrilmez(self):
        n = "TraditionalNaskh"
        s = [ch("1", 10, font=n), ch("2", 14, font=n), ch("0", 18, font=n), ch(" ", 22, font=n), ch("ب", 26, font=n)]
        _, t = cikar.ar_logical(s)
        self.assertEqual(t, "ب 120")


if __name__ == "__main__":
    unittest.main()
