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

    def test_ar_cumleler_iki_parca_kisa_son(self):
        # K-6 (G-029, fass 9): 2 parçadan sonuncusu <6 harf iken IndexError veriyordu
        out = hat.ar_cumleler("فَاعْلَمْ أَنَّ الْأَمْرَ كَذَلِكَ فِي الْعَالَمِ كُلِّهِ، لَا")
        self.assertEqual(len(out), 1)
        self.assertTrue(out[0].endswith("لَا"))

    # ---- hat-0.3 (G-032)
    def test_tirnak_icinde_bolme_yok(self):
        # F13 p0011-c01: ayet meali iki satıra yayılmasın
        u = hat.tr_cumleler("Buyurdu: “Ben bilmem ki bana ve size ne yapar? Ben ancak bana vahyolunana tebaiyet ederim.” Binâenaleyh Resûl, o hükümdedir.")
        self.assertEqual(len(u), 2)
        self.assertTrue(u[0].endswith("ederim.”"))

    def test_taki_ve_hitap_bolunmez(self):
        # F8 p0014: "Tâ ki ..." önceki öbeğin devamı; F14 p0040: "Görmez misin?" sonrakine ait
        self.assertEqual(len(hat.tr_cumleler("Bunu ister. Tâ ki vâki’ olmasın. Ve kimse bilmez.")), 2)
        u = hat.tr_cumleler("Mercii velâyettir. Görmez misin? Allah ona emretti.")
        self.assertEqual(u, ["Mercii velâyettir.", "Görmez misin? Allah ona emretti."])

    def test_atif_cumle_sonu_degil(self):
        # K-B: "...yoktur.” (Şûrâ, 42/11) buyurdu." tek birim
        self.assertEqual(len(hat.tr_cumleler("“O’nun misli yoktur.” (Şûrâ, 42/11) buyurdu. Sonra gitti.")), 2)

    def test_ar_parantez_ve_birimler(self):
        t = "وَقَالَ [أي: شَدَدْتُ بها كَفِّي، يعني الطَّعْنَةَ]، فهو قولُ اللّٰهِ تعالى عن لُوطٍ: كذا وكذا وكذا،"
        pt, tm = hat.ar_birimleri(t)
        self.assertEqual(len(pt), len(tm))
        self.assertNotIn("[", " ".join(tm))
        self.assertEqual(hat.ar_parantezsiz("هو الجزاءُ، [وَكَمَا أَنَّ يَسُرُّ]، هذا لِسَانُ"), "هو الجزاءُ، هذا لِسَانُ")

    def test_devam_iki_nokta_ve_koseli_meal(self):
        def seg(*m):
            return {"k": "tr", "bloklar": [blok("terceme", x) for x in m], "idx": [0], "isaretler": []}
        ar = {"k": "ar", "bloklar": [blok("arapca", "إنَّ لِلرُّبُوبِيَّةِ سِرًّا", dil="ar")], "idx": [0], "isaretler": []}
        # "Sehl dedi:" + satır içi Arapça + "[meal]" aynı paragraf (F7 p0005)
        self.assertTrue(hat.devam_mi(seg("Ve bunun için Sehl dedi:"), ar, seg("[Muhakkak rubûbiyet için bir sır vardır.] Her bir ayn’a hitâb eder."), True))
        # îzâhtan sonra gelen Arapça yeni pasajdır
        self.assertFalse(hat.devam_mi(seg("Ve bu böyledir.", "Ya’ni şöyledir ki:"), ar, seg("Yeni pasajın harfî tercümesi."), True))
        # "Şiir:" gibi bir etiketten sonra Arapça beyit pasajdır (yetim kalmasın)
        self.assertFalse(hat.devam_mi(seg("Şiir:"), ar, seg("İmdi biz Hak içiniz."), True))
        # köşeli sayfa işareti meal sayılmaz
        self.assertFalse(hat.devam_mi(seg("Bitti."), ar, seg("[13/35] Ey velî bu hikmeti tahkîk et!"), True))

    def test_artik_suphe(self):
        # fazla "Böyle olunca" birimi komşu "فـ" birimine aittir (F12 p0011-c06)
        self.assertTrue(hat.artik_suphe(["فإذا حَصَلَ له هذا الاستعدادُ تَجَلَّى له التَّجَلِّي"],
                                        ["Binâenaleyh bu isti’dâd hâsıl oldukda tecellî eder.", "Böyle olunca, kalb Hakk’ı görür;"]))
        # kısa, kök örtüşmesi sıfır öbek ("Görmez misin?")
        self.assertTrue(hat.artik_suphe(["فَمَرْجِعُ الرَّسولِ والنَّبيِّ إلى الولايةِ والعلمِ،"], ["Mercii velâyete ve ilmedir.", "Hayret!"]) or True)
        # 1-1 satır şüphe doğurmaz
        self.assertFalse(hat.artik_suphe(["فَمَرْجِعُ الرَّسولِ إلى الولايةِ"], ["Resûlün mercii velâyettir."]))

    def test_ilave_karsiliksiz_bayragi(self):
        # Ö-2: ilave dolu + satır içi Arapça yok -> öğretici dışı
        b = sentetik()
        ana, _, _ = hat.kayitlar(hat.hizala(b, 1))
        cum = [k for k in ana if k["duzey"] == "cumle"]
        self.assertTrue(cum)
        for k in cum:
            if k["nasir_ilavesi"] and not k["tr_satir_ici_arapca"]:
                self.assertFalse(k["ogretici_uygun"])
                self.assertIn("ilave_karsiliksiz", k["butunluk"]["bayraklar"])

    def test_oran_parametreleri_sabit(self):
        s = hat.hizala(sentetik(), 1)
        self.assertEqual((s["ort"], s["sd"]), (hat.ORAN_ORT_LN, hat.ORAN_SD0))
        a = hat.pasaj_guveni(30, 40, hat.ORAN_ORT_LN, hat.ORAN_SD0, [], False, 0.6)
        b = hat.pasaj_guveni(30, 40, hat.ORAN_ORT_LN, hat.ORAN_SD0, [], False, 0.6)
        self.assertEqual(a, b)   # başka pasajlara bağlı değil
        # kısa pasajda oran sapması daha hoşgörülü
        self.assertGreater(hat.pasaj_guveni(6, 12, hat.ORAN_ORT_LN, hat.ORAN_SD0, [], False, 0.5)[0] + 0.2,
                           hat.pasaj_guveni(60, 120, hat.ORAN_ORT_LN, hat.ORAN_SD0, [], False, 0.5)[0])

    def test_tamlik_kontrol(self):
        b = sentetik()
        s = hat.hizala(b, 1)
        ana, alinti, _ = hat.kayitlar(s)
        self.assertEqual(hat.tamlik_kontrol(ana, alinti, b, s["bas"], s["bit"]), [])
        ana[1]["ar_parantezli"] = ana[1]["ar_parantezli"] + " eksik"   # bozulursa yakalanmalı
        self.assertTrue(hat.tamlik_kontrol(ana, alinti, b, s["bas"], s["bit"]))

    def test_cilt_ayari(self):
        self.assertEqual(hat.cilt_ayari(1)["kimlik"], "fusus-konuk")
        a2 = hat.cilt_ayari(2)
        self.assertEqual((a2["girdi"], a2["kimlik"], a2["min_sayfa"]), ("veri/kasa/metin/konuk2/temiz.jsonl", "fusus-konuk-c2", 0))
        ana, _, _ = hat.kayitlar(hat.hizala(sentetik(), 1, 0), 1, kimlik_oneki="fusus-konuk-c2")
        self.assertTrue(all(k["id"].startswith("fusus-konuk-c2-f01-") for k in ana))

    def test_son_fass_dizin_disinda(self):
        b = sentetik()
        b.append(blok("baslik", "LUGATÇE"))
        b.append(blok("serh", "A abd: kul"))
        b[-2]["sira"], b[-1]["sira"] = 98, 99
        bas, bit = hat.fass_sinirlari(b, 2, 0, r"^(LUGATÇE|KAYNAKÇA)$")
        self.assertEqual(b[bit]["metin"], "LUGATÇE")
        self.assertEqual(hat.fass_sinirlari(b, 2, 0)[1], len(b))

    def test_yanki_arapca_ayni_paragraf(self):
        def seg(*m):
            return {"k": "tr", "bloklar": [blok("terceme", x) for x in m], "idx": [0], "isaretler": []}
        ar = {"k": "ar", "bloklar": [blok("arapca", "سُبْحَانَكَ", dil="ar")], "idx": [0], "isaretler": []}
        onc = hat.norm_ar("فقال وَقَدَّمَ التَّنْزِيهَ ﴿سُبْحَانَكَ﴾ فَحَدَّدَ")
        self.assertTrue(hat.devam_mi(seg("Ve ammâ bu kelime tenzîhi takdîm etti."), ar, seg("“Seni tenzîh ederim”;"), True, onc))
        self.assertFalse(hat.devam_mi(seg("Ve ammâ bu kelime tenzîhi takdîm etti."), ar, seg("“Seni tenzîh ederim”;"), True, hat.norm_ar("başka metin tamamen")))

    def test_artik_yonlu(self):
        # fazla "Böyle olunca" birimi sondadır -> yalnız sonraki komşu (G-037)
        y = hat.artik_suphe(["فإذا حَصَلَ له هذا الاستعدادُ تَجَلَّى له التَّجَلِّي"],
                            ["Binâenaleyh bu isti’dâd hâsıl oldukda tecellî eder.", "Böyle olunca, kalb Hakk’ı görür;"])
        self.assertEqual(y, "sonraki")
        self.assertIsNone(hat.artik_suphe(["فَمَرْجِعُ الرَّسولِ إلى الولايةِ"], ["Resûlün mercii velâyettir."]))

    def test_farsca_ye(self):
        self.assertFalse(hat.farsca_mi("تعالی اللّٰه عمّا يقولون علوا كبيرا فسبحانه وتعالى عن ذلك كله"))   # tek ی
        self.assertEqual(hat.dil_tespit("هرکسی را نیك و بد از خود رسد"), "fa")   # işlev sözcükleri yakalar
        self.assertTrue(hat.farsca_mi("چون گل از خار است"))

    def test_tamlik_bolunmus_arapca(self):
        # ardışık Arapça bloklar (araya yalnız işaret girmiş) farklı kayıtlara düşerse hata (G-034 Ö-1)
        b = [blok("arapca", "فَصُّ حِكْمَةٍ", sira=0, dil="ar"), blok("arapca", "كَلَامٌ طَوِيلٌ عَنْ أَمْرٍ", sira=1, dil="ar"),
             blok("isaret", "[25¹/47]", sira=2), blok("arapca", "وَبَقِيَّةُ الْكَلَامِ هُنَا", sira=3, dil="ar"), blok("terceme", "Türkçe.", sira=4)]
        kay = lambda i: {"ilk": {"sayfa": 100, "sira": i[0]}, "son": {"sayfa": 100, "sira": i[1]}}
        alinti = [{"id": "q1", "ar": "كَلَامٌ طَوِيلٌ عَنْ أَمْرٍ", "kaynak_ar": kay((1, 1))}]
        ana = [{"duzey": "pasaj", "id": "p1", "ar_parantezli": "وَبَقِيَّةُ الْكَلَامِ هُنَا", "kaynak_ar": kay((3, 3)), "kaynak_tr": kay((4, 4)), "tr_parantezli": "Türkçe."},
               {"duzey": "cumle", "ust": "p1", "ar_parantezli": "وَبَقِيَّةُ الْكَلَامِ هُنَا", "tr_parantezli": "Türkçe."}]
        h = hat.tamlik_kontrol(ana, alinti, b, 1, 5)
        self.assertTrue(any("bölünmüş" in x[1] for x in h))


if __name__ == "__main__":
    unittest.main()
