"""hat.py için basit testler (sentetik veri; telifli metin yok). Çalıştır: cd hizalama && python3 -m unittest"""
import unittest

import hat


def blok(tur, metin, sayfa=100, sira=0, dil="tr"):
    return {"sayfa": sayfa, "basili_sayfa": sayfa - 24, "sira": sira, "tur": tur, "dil": dil, "metin": metin}


def sentetik():
    b = [
        blok("arapca", "فَصُّ حِكْمَةٍ إلٰهِيَّةٍ فِي كَلِمَةٍ آدَمِيَّةٍ", dil="ar"),
        blok("baslik", "KELİME-İ ÂDEMİYYE’DE"),
        blok("serh", "Şerh paragrafı."),
        blok("arapca", "فَاسْتَدْلَلْنَا بِنَا عَلَيْهِ، فَوَصَفَ نَفْسَهُ لَنَا", dil="ar"),
        blok("terceme", "Binâenaleyh biz, bizim ile, O’na istidlâl ettik; böyle olun-"),
        blok("terceme", "ca nefsini bize vasfeyledi. [ilave söz][^7]"),
        blok("terceme", "Ya’ni bu bir îzâhtır."),
        blok("serh", "Başka şerh."),
        blok("arapca", "وَاللّٰهُ يَخْتَصُّ بِرَحْمَتِهِ", dil="ar"),
        blok("serh", "[Allah rahmetini tahsîs eder.]"),
        blok("arapca", "فَصُّ حِكْمَةٍ نَفْثِيَّةٍ فِي كَلِمَةٍ شِيثِيَّةٍ", dil="ar"),
    ]
    for i, x in enumerate(b):
        x["sira"] = i
        x["sayfa"] = 143 + i // 5
    return b


class HatTest(unittest.TestCase):
    def test_fass_sinirlari(self):
        bas, bit = hat.fass_sinirlari(sentetik(), 1)
        self.assertEqual((bas, bit), (0, 10))

    def test_cift_ve_alinti_ayrimi(self):
        s = hat.hizala(sentetik(), 1)
        self.assertEqual(len(s["pasajlar"]), 1)
        self.assertEqual(len(s["alintilar"]), 1)  # şerh içi ayet çifte girmez
        p = s["pasajlar"][0]
        self.assertIn("olunca", p["tr"])          # satır sonu tire birleşti
        self.assertEqual(p["ilaveler"], ["ilave söz"])
        self.assertEqual(p["fn"], [7])
        self.assertTrue(p["izah"].startswith("Ya’ni"))  # îzâh çiftin dışında

    def test_kayit_alanlari(self):
        ana, alinti, _ = hat.kayitlar(hat.hizala(sentetik(), 1))
        pas = [k for k in ana if k["duzey"] == "pasaj"][0]
        for alan in ("id", "surum", "guven", "gerekce", "yontem", "model", "inceleme", "ar_id", "tr_id"):
            self.assertIn(alan, pas)
        self.assertFalse(alinti[0]["egitim_cifti"])

    def test_tr_cumleler_kisaltma(self):
        self.assertEqual(len(hat.tr_cumleler("Resûl (s.a.v.) geldi. Sonra gitti; ve döndü.")), 3)

    def test_dp_monoton(self):
        yol = hat.dp_hizala(["وَصَفَ نَفْسَهُ،", "فَشَهِدَ نَفْسَهُ،"], ["Nefsini vasfetti;", "ve nefsini müşâhede etti."])
        self.assertEqual([(a, t) for a, t, *_ in yol], [([0], [0]), ([1], [1])])

    def test_leksik_ayirir(self):
        iyi = hat.leksik_ortak("فَوَصَفَ نَفْسَهُ لَنَا", "Böyle olunca nefsini bize vasfeyledi")
        kotu = hat.leksik_ortak("فَوَصَفَ نَفْسَهُ لَنَا", "Zîrâ melâike halîfe neş’esini görmedi")
        self.assertGreater(iyi, kotu)

    # ---- hat-0.2 (G-027)
    def test_parantezsiz_ve_alanlar(self):
        s = hat.hizala(sentetik(), 1)
        p = s["pasajlar"][0]
        self.assertNotIn("[", p["tr"])
        self.assertIn("[ilave söz]", p["tr_parantezli"])
        self.assertEqual(p["ilaveler"], ["ilave söz"])

    def test_parantez_cumle_siniri_bolmez(self):
        t = "Önce şunu dedi [birinci kısım; ikinci kısım. üçüncü] ve sonra gitti; ardından döndü."
        for u in hat.tr_cumleler(t):
            self.assertEqual(u.count("["), u.count("]"))
        self.assertEqual(len(hat.tr_cumleler(t)), 2)

    def test_atif_ve_satir_ici_arapca_temizlenir(self):
        t = "onlar, haysiyetinden {ar: أَ تَجْعَلُ} (Bakara, 2/30) ya’ni “Yâ Rab” dediler."
        self.assertEqual(hat.parantezsiz(t), "onlar, haysiyetinden أَ تَجْعَلُ ya’ni “Yâ Rab” dediler.")  # Arapça yerinde kalır
        ar = hat.ic_arapca_araliklari(t, hat.parantezsiz(t))[0]
        self.assertEqual(hat.parantezsiz(t)[ar["bas"]:ar["son"]], "أَ تَجْعَلُ")
        self.assertEqual(hat.parantezsiz("a [ilave {ar: نفثية}] b"), "a b")
        self.assertEqual(hat.ilave_ve_atiflar(t)[1], ["Bakara, 2/30"])
        self.assertEqual(hat.tr_cumleler("(Nisâ, 4/1) Ey nâs! Korkun."), ["(Nisâ, 4/1) Ey nâs!", "Korkun."])

    def test_satir_ici_devam_kurali(self):
        def seg(*m):
            return {"k": "tr", "bloklar": [blok("terceme", x) for x in m], "idx": [0], "isaretler": []}
        ar = {"k": "ar", "bloklar": [blok("arapca", "نفثية", dil="ar")], "idx": [0], "isaretler": []}
        self.assertTrue(hat.devam_mi(seg("onlar neş’et haysiyetinden"), ar, seg("(Bakara, 2/30) ya’ni dediler")))
        self.assertTrue(hat.devam_mi(seg("Mündemic ["), ar, seg("], ba’dehû")))
        self.assertFalse(hat.devam_mi(seg("Bitti."), ar, seg("İmdi başka pasaj")))

    def test_butunluk_bayragi(self):
        b = sentetik()
        b.insert(5, blok("arapca", "نفثية", dil="ar"))
        b.insert(6, blok("terceme", "devam eden satır.", dil="tr"))
        for i, x in enumerate(b):
            x["sira"] = i
        s = hat.hizala(b, 1)
        ana, _, _ = hat.kayitlar(s)
        pas = [k for k in ana if k["duzey"] == "pasaj"][0]
        self.assertIn("satir_ici_arapca", pas["butunluk"]["bilgi"])
        self.assertNotIn("satir_ici_arapca", pas["butunluk"]["bayraklar"])  # bilgi amaçlı, kusur değil
        self.assertTrue(pas["tr_satir_ici_arapca"][0]["metin"] == "نفثية")

    def test_dil_tespit(self):
        self.assertEqual(hat.dil_tespit("حق جانِ جهان است و جهان جمله بدن"), "fa")
        self.assertEqual(hat.dil_tespit("وَاللّٰهُ يَخْتَصُّ بِرَحْمَتِهِ مَنْ يَشَاءُ"), "ar")

    def test_kimlik_korunur(self):
        import tempfile, os
        ana, alinti, dipnot = hat.kayitlar(hat.hizala(sentetik(), 1))
        with tempfile.TemporaryDirectory() as d:
            hat.yaz(os.path.join(d, "fass-01.jsonl"), ana)
            hat.yaz(os.path.join(d, "fass-01.alinti.jsonl"), alinti)
            ana2, alinti2, _ = hat.kayitlar(hat.hizala(sentetik(), 1), onceki=d)
        self.assertEqual([k["id"] for k in ana], [k["id"] for k in ana2])
        self.assertEqual([k["id"] for k in alinti], [k["id"] for k in alinti2])


if __name__ == "__main__":
    unittest.main()
