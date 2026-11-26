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


if __name__ == "__main__":
    unittest.main()
