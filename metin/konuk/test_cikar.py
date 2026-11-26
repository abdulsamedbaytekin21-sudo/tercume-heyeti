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


if __name__ == "__main__":
    unittest.main()
