import unittest
from normallestir import normalize_ar, parse, normalize_document, sample_errors

ORNEK = """[s. 1]
## fass: Mukaddime
بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ[^1]
الحمد لله [ilave] ⟨?⟩ الكلم
[^1]: dipnot metni
[s. 2]
أَحَدِيَّةِ الطَّرِيقِ
"""


class T(unittest.TestCase):
    def test_harekeler_ve_elif(self):
        self.assertEqual(normalize_ar("بِسْمِ اللَّهِ"), "بسم الله")
        self.assertEqual(normalize_ar("أَحَدِيَّة"), "احدية")
        self.assertEqual(normalize_ar("مـــوسى"), "موسي")
        self.assertEqual(normalize_ar("رحمة"), "رحمة")
        self.assertEqual(normalize_ar("رحمة", ta_marbuta=True), "رحمه")

    def test_okunamayan_korunur(self):
        self.assertIn("⟨?⟩", normalize_ar("كَلِمة ⟨?⟩"))

    def test_katmanlar(self):
        p = parse(ORNEK)
        self.assertEqual(p["basliklar"][0]["metin"], "Mukaddime")
        self.assertEqual(p["basliklar"][0]["sayfa"], 1)
        self.assertEqual(p["dipnotlar"], [{"sayfa": 1, "no": "1", "metin": "dipnot metni"}])
        self.assertEqual(p["ilaveler"][0]["metin"], "ilave")
        self.assertEqual(len(p["okunamayan"]), 1)
        self.assertEqual(len(p["govde"]), 3)
        for g in p["govde"]:
            self.assertNotIn("dipnot", g["satir"])
            self.assertNotIn("[", g["satir"])

    def test_sayfa_isareti_ilave_sayilmaz(self):
        self.assertEqual(parse(ORNEK)["govde"][-1]["sayfa"], 2)
        self.assertEqual(len(parse(ORNEK)["ilaveler"]), 1)

    def test_girdi_degismez(self):
        kopya = str(ORNEK)
        normalize_document(ORNEK)
        self.assertEqual(ORNEK, kopya)
        self.assertIn("بِسْمِ", ORNEK)

    def test_normallesmis_belge(self):
        d = normalize_document(ORNEK)
        self.assertEqual(d[0], {"sayfa": 1, "satir": "بسم الله الرحمن الرحيم"})

    def test_oran(self):
        self.assertEqual(sample_errors([("a", "a"), ("a", "b")]), (2, 1, 0.5))
        self.assertEqual(sample_errors([]), (0, 0, 0.0))


if __name__ == "__main__":
    unittest.main()
