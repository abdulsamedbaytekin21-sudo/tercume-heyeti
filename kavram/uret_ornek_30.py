import json, sys
sys.path.insert(0, "/home/user/tercume-heyeti/metin")
from normallestir import normalize_ar

SURUM = 2
DEG = {"tarih": "2026-11-26", "yapan": "istilahci", "kart": "G-013",
       "onceki": "G-006 (sürüm 1)", "ozet": "G-006 denetim şartları Ş1-Ş3, K1, K2: durum=taslak; Fusûs ana metin tanıklıkları E-006; Konuk dönemi h14; harf-i tarifsiz lemma; IST-I-0009 karsit->ilgili"}
DN = "doğrulanmadı"
FASS = {
 "adem": "1. Fass-ı Âdemî (hikmet-i ilâhiyye)",
 "sis": "2. Fass-ı Şîsî (hikmet-i nefsiyye; nüsha farkı doğrulanmadı)",
 "nuh": "3. Fass-ı Nûhî (hikmet-i sübbûhiyye)",
 "ibrahim": "5. Fass-ı İbrâhîmî (hikmet-i mühîmiyye)",
 "yusuf": "9. Fass-ı Yûsufî (hikmet-i nûriyye)",
 "suayb": "12. Fass-ı Şuaybî (hikmet-i kalbiyye)",
 "uzeyr": "14. Fass-ı Uzeyrî (hikmet-i kaderiyye)",
 "suleyman": "16. Fass-ı Süleymânî (hikmet-i rahmâniyye)",
 "davud": "17. Fass-ı Dâvûdî (hikmet-i vücûdiyye)",
 "muhammed": "27. Fass-ı Muhammedî (hikmet-i ferdiyye)",
 "basliklar": "Fass başlıkları (\"fass hikmet ... fî kelime ...\" kalıbı), eser geneli",
}
# tanıklık kaynakları: ekol/dönem burada, anlamda değil
KAYNAK = {
 "fusus": dict(eser="E-006", eser_not="Fusûsu'l-hikem Arapça ana metni (E-006; veri/envanter/fusus-ana-metin.md). Dayanılan Arapça baskı doğrulanmadı (E-001/E-002 önsözleri bekliyor).",
               muellif="İbnü'l-Arabî", muellif_vefat="638/1240 (genel bilgi, doğrulanmadı)", ekol="ekol:ekberi", donem="donem:h7"),
 "konuk": dict(eser="E-001", eser_not="Konuk'un Türkçe şerhi (şârih yorumu, ana metin değil).",
               muellif="Ahmed Avni Konuk", muellif_vefat="1938 (doğrulanmadı)", ekol="ekol:ekberi", donem="donem:h14"),
}

# (lafız, okunuş, kök[], dil_türü, terim_notu, [anlamlar])
# anlam: (tanım, güven, gerekçe, [(kaynak, fass, tanıklık_gerekçe_ek)])
T = [
 ("فص", "fass", ["ف ص ص"], "isim", "Eserin bölüm adı.", [
   ("Eserin bölüm birimi: her biri bir peygamberin 'kelime'sine nispet edilen ve bir hikmete tahsis edilen yirmi yedi bölümden biri; asıl anlamı yüzük kaşı.", "yuksek", "Eser yapısından açık.", [("fusus", "basliklar", "")]),
   ("Şârihlere göre hikmetin nakşedildiği mahal olarak nebînin kalbi (yüzük kaşına nakşedilen mühür benzetmesi).", "dusuk", "Ana metinde açık tanım yok; şerh geleneğinin yorumu. Konuk'ta bu yorumun bulunduğu yer okunmadı.", [("konuk", None, "Şerhin mukaddime veya ilk fass açıklaması varsayıldı; yer okunmadı.")]),
 ]),
 ("كلمة", "kelime", ["ك ل م"], "isim", "Dilbilgisel 'kelime' anlamı ıstılah sayılmaz, kaydedilmedi.", [
   ("Peygamberin şahsı/hakikati olarak ilâhî 'kelime': her fassın nispet edildiği nebî, Hakk'ın 'kün' emriyle var olan bir kelime olarak anılır.", "orta", "Başlık kalıbından kullanım açık; 'kelime = nebînin hakikati' tanımı şerh sistematiğine dayanır.", [("fusus", "basliklar", "")]),
 ]),
 ("حكمة", "hikmet", ["ح ك م"], "isim", "", [
   ("Her fassa tahsis edilen ve o nebînin hakikatine özgü ilâhî bilgi türü (ilâhiyye, nefsiyye, sübbûhiyye ... ferdiyye sıfatlarıyla nitelenir).", "yuksek", "Başlık kalıbından açık.", [("fusus", "basliklar", "")]),
 ]),
 ("الكون الجامع", "el-kevnü'l-câmi'", ["ك و ن", "ج م ع"], "isim tamlaması (sıfatlı)", "", [
   ("Hakk'ın isimlerinin bütününü kendinde toplayan ve Hakk'ın kendini onda gördüğü kapsayıcı varlık; insan (Âdem) için kullanılır.", "yuksek", "Fass-ı Âdemî girişinin ana kavramı.", [("fusus", "adem", "")]),
 ]),
 ("مرآة", "mir'ât", ["ر أ ي"], "isim", "Kök r-'-y; hemze yazımı normalleştirmede elife iner.", [
   ("Hakk'ın kendini ve isimlerini temaşa ettiği yansıtıcı mahal; âlem cilasız ayna, Âdem bu aynanın cilası olarak anılır.", "yuksek", "Fass-ı Âdemî'nin bilinen imgesi.", [("fusus", "adem", "")]),
   ("Tecellîde görenin, gördüğünü kendi kabiliyeti ölçüsünde görmesi; Hakk'ın kulun, kulun Hakk'ın aynası olması.", "orta", "Ayna imgesinin ikinci kullanımı; ayrı anlam mı aynı anlamın uzantısı mı tartışılabilir.", [("fusus", "sis", "")]),
 ]),
 ("الإنسان الكامل", "el-insânü'l-kâmil", ["أ ن س", "ك م ل"], "isim tamlaması (sıfatlı)", "", [
   ("İlâhî isimlerin tamamını câmi', âlemin ruhu ve halîfe olan insan; insan türünün kemal mertebesi.", "orta", "Kavram açık; lafzın Fass-ı Âdemî'de bu kalıpla aynen geçtiği baskıdan teyit edilmedi.", [("fusus", "adem", "Lafzın bu fassta aynen geçişi teyitsiz.")]),
 ]),
 ("خلافة", "hilâfet", ["خ ل ف"], "isim (mastar)", "İlgili lafız: خليفة (halîfe).", [
   ("İnsanın, Hakk'ın isim ve sıfatlarının sûreti üzere âlemde O'nun yerine tasarrufu; insan-ı kâmilin mertebesi.", "yuksek", "Fass-ı Âdemî'de ve Dâvûdî'de ayetle (Bakara 2:30, Sâd 38:26) birlikte işlenir.", [("fusus", "adem", ""), ("fusus", "davud", "")]),
 ]),
 ("صورة", "sûret", ["ص و ر"], "isim", "", [
   ("'Allah Âdem'i kendi sûreti üzere yarattı' hadisi bağlamında: ilâhî isim ve sıfatların insanda toplu bulunuşu.", "orta", "Bağlam açık; zamirin kime döndüğü (Allah/Âdem) geleneksel tartışmadır, Fusûs okuması Allah'a döndürür.", [("fusus", "adem", "")]),
   ("Mânâ/hakikat karşısında zâhir görünüş; bir hakikatin bir mertebedeki belirişi.", "dusuk", "Genel kullanım; ıstılahi bir anlam olarak 1. anlamdan ayrılması tartışmalı; özgül tanıklık yeri belirlenmedi.", [("fusus", "yusuf", "Rüya ve tabir bağlamındaki sûret-mânâ ayrımı varsayıldı; yer okunmadı.")]),
 ]),
 ("الأسماء الإلهية", "el-esmâü'l-ilâhiyye", ["س م و", "أ ل ه"], "isim tamlaması (sıfatlı)", "Eserde 'el-esmâü'l-hüsnâ' lafzıyla da geçer.", [
   ("Hakk'ın âlemle ilişkisini belirleyen, sayısız ve her biri bir eserin (âlemde bir hükmün) kaynağı olan isimler; 'görülmeyi isteyen' isimler.", "yuksek", "Fass-ı Âdemî açılışı.", [("fusus", "adem", "")]),
 ]),
 ("الأعيان الثابتة", "el-a'yânü's-sâbite", ["ع ي ن", "ث ب ت"], "isim tamlaması (sıfatlı)", "", [
   ("Şeylerin, dış varlıkta bulunmadan önce Hakk'ın ilminde sabit olan hakikatleri; dış varlığa çıkmamış ('vücûdun kokusunu almamış') ma'lûmlar.", "yuksek", "Kavram açık; Ekberî metafiziğinin temel ıstılahı.", [("fusus", "uzeyr", ""), ("fusus", "adem", "")]),
 ]),
 ("عين", "ayn", ["ع ي ن"], "isim", "Çok anlamlı lafız; göz, kaynak anlamları ıstılah değil, kaydedilmedi.", [
   ("Bir şeyin kendisi, özü ('aynuhû' = onun kendisi); özdeşlik bildiren kullanım ('Hakk'ın aynı').", "dusuk", "Lafız eserde yoğun ve çok anlamlı; anlam ayrımı (özdeşlik / sabit hakikat / mevcut şahıs) tartışmalı, cümle cümle karar gerekir.", [("fusus", "adem", "Özgül cümle seçilmedi.")]),
   ("Tekil sabit hakikat (ayn-ı sâbite); 'a'yân'ın tekili olarak ilmî hakikat.", "dusuk", "IST-T-0010 ile örtüşür; ayrı anlam mı yoksa o terime bağlanacak tekil kullanım mı insan kararı gerekir.", [("fusus", "uzeyr", "")]),
 ]),
 ("الفيض الأقدس", "el-feyzü'l-akdes", ["ف ي ض", "ق د س"], "isim tamlaması (sıfatlı)", "", [
   ("A'yânın ve isti'dâdlarının Hakk'ın ilminde taayyün etmesini sağlayan ilk tecellî; kabil olanı da veren feyz.", "orta", "Lafız Fass-ı Âdemî'de geçer; 'ilmî taayyün' olarak tanımı Konevî-Kâşânî şerh sistematiğine dayanır.", [("fusus", "adem", "")]),
 ]),
 ("الفيض المقدس", "el-feyzü'l-mukaddes", ["ف ي ض", "ق د س"], "isim tamlaması (sıfatlı)", "", [
   ("A'yânın, isti'dâdları ölçüsünde dış varlığa çıkmasını sağlayan ikinci (vücûdî) tecellî.", "dusuk", "Akdes/mukaddes ayrımı şârihlerde sistemleşir; lafzın Fusûs ana metninde geçtiği teyit edilmedi. Tanıklık şerhe bağlandı.", [("konuk", None, "Konuk'ta ilgili açıklamanın yeri okunmadı.")]),
 ]),
 ("استعداد", "isti'dâd", ["ع د د"], "isim (mastar, istif'âl)", "", [
   ("Bir aynın, sâbit hakikatinden gelen ve feyzi ancak kendi ölçüsünde almasını belirleyen kabiliyeti.", "yuksek", "Fass-ı Âdemî ve Şîsî'de tecellî ve kabil kavramlarıyla birlikte işlenir.", [("fusus", "adem", ""), ("fusus", "sis", "")]),
 ]),
 ("قابل", "kâbil", ["ق ب ل"], "isim (ism-i fâil)", "İlgili: قابلية (kâbiliyyet).", [
   ("Feyzi kabul eden mahal; kabul edenin kendisi de feyz-i akdesten gelir.", "orta", "Kavram açık; terimin isti'dâd ile ayrı terim olarak tutulması insan kararı gerektirebilir.", [("fusus", "adem", "")]),
 ]),
 ("تجلي", "tecellî", ["ج ل و"], "isim (mastar, tefa''ul)", "", [
   ("Hakk'ın isim ve sıfatlarıyla bir mahalde kendini göstermesi; tecellî edilen, ancak kendi isti'dâdı ölçüsünde görür.", "yuksek", "Fass-ı Şîsî'nin ana konusu.", [("fusus", "sis", "")]),
 ]),
 ("خاتم الأولياء", "hâtemü'l-evliyâ", ["خ ت م", "و ل ي"], "isim tamlaması", "Kimliği (müellifin kendisi mi, İsa mı) ayrı tartışmadır; bu kayıt kavramı tanımlar, kimliğe hüküm vermez.", [
   ("Velâyeti mühürleyen ve her velînin (nebîler dahil) bilgiyi velâyet yönünden ondan aldığı velî; hâtemü'r-rusulün velâyet cihetiyle de ilgilidir.", "orta", "Kavram Fass-ı Şîsî'de işlenir; 'ondan alma'nın kapsamı şârihler arasında tartışmalıdır.", [("fusus", "sis", "")]),
 ]),
 ("ولاية", "velâyet", ["و ل ي"], "isim (mastar)", "Okunuş velâyet/vilâyet farkı ayrıca not edilmeli.", [
   ("Hakk'ın isimlerinden 'el-Velî'ye dayanan, kesintisiz ve genel mertebe; nübüvvet ve risâletin kapsayıcısı.", "yuksek", "Fass-ı Uzeyrî'de nübüvvet-risâlet ile karşılaştırmalı işlenir.", [("fusus", "uzeyr", "")]),
 ]),
 ("نبوة", "nübüvvet", ["ن ب أ"], "isim (mastar)", "Kökün ن ب أ mı ن ب و mı olduğu dilciler arasında tartışmalıdır; ن ب أ esas alındı, guven: orta.", [
   ("Teşrî nübüvveti: şeriat getiren ve Hz. Muhammed'le sona eren nübüvvet.", "orta", "Ayrım Fass-ı Uzeyrî'de işlenir; 'nübüvvet-i teşrî' / 'nübüvvet-i âmme' adlandırmasının ana metindeki lafzı teyit edilmedi.", [("fusus", "uzeyr", "")]),
   ("Genel (âmme) nübüvvet: teşrî içermeyen, velîlerde devam eden haber alma.", "dusuk", "Bu anlamın Fusûs'ta mı yoksa Fütûhât'ta mı açıkça işlendiği teyit edilmedi; anlam ayrımı tartışmalı.", [("fusus", "uzeyr", "Yer varsayımdır.")]),
 ]),
 ("رسالة", "risâlet", ["ر س ل"], "isim (mastar)", "", [
   ("Tebliğle görevli olma mertebesi; nübüvvetin özel hâli, velâyetten daha dar kapsamlı.", "yuksek", "Fass-ı Uzeyrî'de velâyet-nübüvvet-risâlet sıralaması içinde işlenir.", [("fusus", "uzeyr", "")]),
 ]),
 ("سر القدر", "sırrü'l-kader", ["س ر ر", "ق د ر"], "isim tamlaması", "", [
   ("Hakk'ın her şey hakkındaki hükmünün, o şeyin sabit aynının ve isti'dâdının gerektirdiğine göre olması; kaderin, aynın kendi hâlinden gelmesi.", "yuksek", "Fass-ı Uzeyrî'nin konusu.", [("fusus", "uzeyr", "")]),
 ]),
 ("تنزيه", "tenzîh", ["ن ز ه"], "isim (mastar, tef'îl)", "", [
   ("Hakk'ı yaratılmışlara benzemekten arındırma; tek başına yapıldığında Hakk'ı sınırlayan bir tahdit sayılır.", "yuksek", "Fass-ı Nûhî'nin ana konusu.", [("fusus", "nuh", "")]),
 ]),
 ("تشبيه", "teşbîh", ["ش ب ه"], "isim (mastar, tef'îl)", "", [
   ("Hakk'ı tecellî ettiği sûretlerle nitelemek; tenzîhle birlikte yapıldığında doğru marifet olarak görülür.", "yuksek", "Fass-ı Nûhî'de tenzîh ile birlikte işlenir.", [("fusus", "nuh", "")]),
 ]),
 ("قلب", "kalb", ["ق ل ب"], "isim", "", [
   ("Hakk'ı kuşatan (sığdıran) mahal: 'Yerim ve göğüm beni sığdırmadı, mü'min kulumun kalbi sığdırdı' bağlamında genişlik (vüs'at).", "yuksek", "Fass-ı Şuaybî'nin konusu.", [("fusus", "suayb", "")]),
   ("Takallüb: kalbin tecellîlere göre sürekli dönüşmesi, her inançta Hakk'ı tanıyabilmesi.", "orta", "Kök oyunu üzerinden işlenir; 1. anlamdan ayrı anlam mı, aynı kavramın yönü mü tartışılabilir.", [("fusus", "suayb", "")]),
 ]),
 ("الخلق الجديد", "el-halku'l-cedîd", ["خ ل ق", "ج د د"], "isim tamlaması (sıfatlı)", "İlgili ifade: teceddüdü'l-emsâl.", [
   ("Âlemin her an yeniden yaratılması; benzerlerin yenilenmesi nedeniyle sürekliliğin fark edilmemesi.", "yuksek", "Fass-ı Şuaybî'de Eş'arîlerin araz görüşü ve Hisbâniyye eleştirisiyle işlenir.", [("fusus", "suayb", "")]),
 ]),
 ("الإله المعتقد", "el-ilâhü'l-mu'teked", ["أ ل ه", "ع ق د"], "isim tamlaması (sıfatlı)", "Lafız varyantı: 'el-ilâhü'l-mahlûk fi'l-i'tikâdât'. Hangi kalıbın Fusûs'ta geçtiği teyit edilmedi.", [
   ("İnançlarda yaratılmış ilâh: her inanan Hakk'ı kendi inancının biçimiyle sınırlar; kalbin kabı inancın şeklini belirler.", "orta", "Kavram açık; lafız kalıbı ve yeri teyitsiz.", [("fusus", "suayb", "Yer varsayımdır.")]),
 ]),
 ("خيال", "hayâl", ["خ ي ل"], "isim", "", [
   ("Âlemin (kevn) bir hayâl olması, duyulurun tabir gerektiren bir rüya gibi okunması; 'insanlar uykudadır, ölünce uyanırlar'.", "yuksek", "Fass-ı Yûsufî'nin konusu.", [("fusus", "yusuf", "")]),
 ]),
 ("تعبير", "ta'bîr", ["ع ب ر"], "isim (mastar, tef'îl)", "", [
   ("Rüyada (ve hayâl olarak âlemde) görülen sûretten mânâya geçiş; görülenin yorumlanması.", "yuksek", "Fass-ı Yûsufî'de rüya tabiri üzerinden işlenir.", [("fusus", "yusuf", "")]),
 ]),
 ("تخلل", "tahallül", ["خ ل ل"], "isim (mastar, tefa''ul)", "Halîl (Hz. İbrâhîm) adıyla kök ilişkisi üzerinden.", [
   ("Hakk'ın kulun sûretlerine/sıfatlarına ve kulun Hakk'ın isimlerine nüfuz etmesi; 'halîl' adının bu nüfuzla açıklanması.", "yuksek", "Fass-ı İbrâhîmî'nin açılış kavramı.", [("fusus", "ibrahim", "")]),
 ]),
 ("رحمة", "rahmet", ["ر ح م"], "isim", "", [
   ("Rahmet-i imtinân: hiçbir amele karşılık olmaksızın lütfen verilen, her şeyi kuşatan rahmet (Rahmân).", "orta", "Ayrım Fass-ı Süleymânî'de işlenir; ıstılah adları (imtinân/vücûb) ana metindeki lafızla teyit edilmedi.", [("fusus", "suleyman", "")]),
   ("Rahmet-i vücûb: Hakk'ın kendi üzerine yazdığı, amele karşılık verilen rahmet (Rahîm).", "orta", "Aynı gerekçe.", [("fusus", "suleyman", "")]),
 ]),
]

ILISKI = [
 ("karsit", "IST-A-0022-1", "IST-A-0023-1", "yuksek", "Tenzîh ve teşbîh Fass-ı Nûhî'de birlikte, birbirini tamamlayan karşıtlar olarak işlenir."),
 ("ilgili", "IST-A-0012-1", "IST-A-0013-1", "orta", "Feyz-i akdes / mukaddes ikilisi; ikincisinin ana metin tanıklığı yok."),
 ("ust_kavram", "IST-A-0018-1", "IST-A-0019-1", "yuksek", "Velâyet nübüvveti kapsar (Fass-ı Uzeyrî)."),
 ("ust_kavram", "IST-A-0019-1", "IST-A-0020-1", "yuksek", "Nübüvvet risâleti kapsar (Fass-ı Uzeyrî)."),
 ("ilgili", "IST-A-0010-1", "IST-A-0021-1", "yuksek", "Sırrü'l-kader a'yân-ı sâbitenin hâline dayanır."),
 ("ilgili", "IST-A-0014-1", "IST-A-0016-1", "yuksek", "Tecellî isti'dâd ölçüsünde alınır."),
 ("ilgili", "IST-A-0011-2", "IST-A-0010-1", "dusuk", "Ayn'ın 2. anlamı a'yân-ı sâbitenin tekili olabilir; birleştirme kararı insan incelemesinde."),
 ("ilgili", "IST-A-0007-1", "IST-A-0006-1", "yuksek", "Hilâfet insan-ı kâmilin mertebesidir."),
 ("ilgili", "IST-A-0030-1", "IST-A-0030-2", "orta", "İmtinân ve vücûb rahmetleri karşıt değil, aynı cinsin (rahmetin) iki türüdür; Fass-ı Süleymânî'de birlikte anılır (G-006 Ö3/Ş3)."),
 ("sarih_yorumu", "IST-A-0001-2", "IST-A-0001-1", "dusuk", "Fass = nebînin kalbi yorumu, bölüm birimi anlamına şerhten eklenen katmandır."),
]

out = []
nt = na = nn = 0
for i, (lafiz, okunus, kok, tur, notu, anlamlar) in enumerate(T, 1):
    tid = f"IST-T-{i:04d}"
    out.append(dict(tur="terim", kimlik=tid, surum=SURUM, lafiz=lafiz, lafiz_harekesiz=normalize_ar(lafiz),
                    okunus=okunus, kok=kok, dil_turu=tur, not_=notu or None, degisiklik=DEG)); nt += 1
    for k, (tanim, g, ger, tlist) in enumerate(anlamlar, 1):
        aid = f"IST-A-{i:04d}-{k}"
        out.append(dict(tur="anlam", kimlik=aid, surum=SURUM, terim=tid, sira=k, tanim=tanim, guven=g, gerekce=ger,
                        inceleme="insan" if g == "dusuk" else None, degisiklik=DEG)); na += 1
        assert tlist, aid
        for m, (kay, fass, ek) in enumerate(tlist, 1):
            src = KAYNAK[kay]
            yer = FASS[fass] if fass else DN
            g_ger = "Baskı, cilt ve sayfa doğrulanmadı; dayanılan Arapça baskı belirlenmedi (G-001). Fass ataması baskıdan okunmadı."
            if ek: g_ger += " " + ek
            out.append(dict(tur="taniklik", kimlik=f"IST-N-{i:04d}-{k}-{m}", surum=SURUM, anlam=aid, eser=src["eser"],
                            eser_not=src["eser_not"], baski=DN, cilt=DN, sayfa=DN, yer=yer, alinti=None,
                            muellif=src["muellif"], muellif_vefat=src["muellif_vefat"], ekol=src["ekol"],
                            donem=src["donem"], cift_id=None, guven="dusuk", gerekce=g_ger, inceleme="insan",
                            degisiklik=DEG)); nn += 1
ids = {r["kimlik"] for r in out}
for j, (tk, a, b, g, ger) in enumerate(ILISKI, 1):
    assert a in ids and b in ids, (a, b)
    out.append(dict(tur="iliski", kimlik=f"IST-I-{j:04d}", surum=SURUM, tur_kenar=tk, kaynak=a, hedef=b, guven=g,
                    gerekce=ger, inceleme="insan" if g == "dusuk" else None, degisiklik=DEG))
with open("/home/user/tercume-heyeti/veri/kavram/ornek_30.jsonl", "w", encoding="utf-8") as f:
    for r in out:
        r = {("not" if k == "not_" else k): v for k, v in r.items()}
        d = r.pop("degisiklik"); r["durum"] = "taslak"; r["degisiklik"] = d
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print(nt, na, nn, len(ILISKI))
