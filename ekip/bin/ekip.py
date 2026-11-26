#!/usr/bin/env python3
"""Tercüme Heyeti ortak kayıt aracı.

Durum, talimat, görev kartları ve rûznâme (olay günlüğü) burada tutulur.
Hem ajanlar (komut satırı), hem Claude Code hook'ları, hem panel sunucusu bu modülü kullanır.
Yalnızca Python standart kütüphanesi gerekir.

Kullanım örnekleri:
  ekip.py durum mukabeleci "Fass 3 paragraf hizalaması" [--hal calisiyor|bekliyor|bosta] [--gorev G-002]
  ekip.py talimat mimar "Şemada sürüm alanını unutma"
  ekip.py gorev yeni --baslik "..." --atanan mimar --amac "..." --cikti "..." --kabul "..." [--model opus]
  ekip.py gorev durum G-001 tamam [--not "..."]
  ekip.py gorev teslim G-001 --ozet "..." [--yurutucu antigravity]
  ekip.py gorev devret G-001
  ekip.py gorev liste
  ekip.py ozet
  ekip.py hook post-tool|subagent-start|subagent-stop|stop|user-prompt|session-start   (stdin: hook JSON)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(os.environ.get("HEYET_KOK") or Path(__file__).resolve().parents[2])
EKIP = ROOT / "ekip"
DURUM = EKIP / "durum"
TALIMAT = EKIP / "talimat"
GOREV = EKIP / "gorevler"
ANTIGRAVITY = EKIP / "antigravity"
RUZNAME = EKIP / "ruzname.jsonl"
RAPOR = EKIP / "rapor.md"
KADRO = EKIP / "kadro.json"

GOREV_DURUMLARI = ["sirada", "calisiyor", "bekliyor", "incelemede", "iade", "devredildi", "tamam"]
UYE_HALLERI = ["calisiyor", "bekliyor", "bosta"]
ADIM_SINIRI = 25
DIS_YURUTUCU = "antigravity"


# ---------------------------------------------------------------- yardımcılar

def simdi() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def yaz_atomik(yol: Path, icerik: str) -> None:
    yol.parent.mkdir(parents=True, exist_ok=True)
    fd, gecici = tempfile.mkstemp(dir=yol.parent, prefix=".tmp-")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(icerik)
    os.replace(gecici, yol)


def json_oku(yol: Path, varsayilan):
    try:
        return json.loads(yol.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return varsayilan


def jsonl_oku(yol: Path) -> list[dict]:
    if not yol.exists():
        return []
    satirlar = []
    for s in yol.read_text(encoding="utf-8").splitlines():
        s = s.strip()
        if s:
            try:
                satirlar.append(json.loads(s))
            except json.JSONDecodeError:
                pass
    return satirlar


def jsonl_ekle(yol: Path, kayit: dict) -> None:
    yol.parent.mkdir(parents=True, exist_ok=True)
    with yol.open("a", encoding="utf-8") as f:
        f.write(json.dumps(kayit, ensure_ascii=False) + "\n")


def kisalt(metin: str, n: int = 110) -> str:
    metin = " ".join(str(metin).split())
    return metin if len(metin) <= n else metin[: n - 1] + "…"


# ---------------------------------------------------------------- kadro

def kadro() -> dict:
    return json_oku(KADRO, {"proje": "", "uyeler": []})


def uye_idleri() -> list[str]:
    return [u["id"] for u in kadro()["uyeler"]]


def uye_mi(uid: str) -> bool:
    return uid in uye_idleri() or uid == DIS_YURUTUCU


def uye_model(uid: str) -> str | None:
    for u in kadro()["uyeler"]:
        if u["id"] == uid:
            return u.get("model")
    return None


# ---------------------------------------------------------------- rûznâme

def ruzname_ekle(kim: str, olay: str, metin: str = "") -> None:
    jsonl_ekle(RUZNAME, {"zaman": simdi(), "kim": kim, "olay": olay, "metin": kisalt(metin, 240)})


def ruzname_son(n: int = 60) -> list[dict]:
    return jsonl_oku(RUZNAME)[-n:]


# ---------------------------------------------------------------- durum

def durum_oku(uid: str) -> dict:
    d = json_oku(DURUM / f"{uid}.json", {})
    d.setdefault("id", uid)
    d.setdefault("hal", "bosta")
    d.setdefault("su_an", "")
    d.setdefault("gorev", None)
    d.setdefault("adimlar", [])
    d.setdefault("guncellendi", None)
    return d


def durum_yaz(uid: str, **alanlar) -> dict:
    d = durum_oku(uid)
    for k, v in alanlar.items():
        if v is not None:
            d[k] = v
    d["guncellendi"] = simdi()
    yaz_atomik(DURUM / f"{uid}.json", json.dumps(d, ensure_ascii=False, indent=1))
    return d


def adim_ekle(uid: str, arac: str, ozet: str) -> None:
    d = durum_oku(uid)
    d["adimlar"] = (d.get("adimlar") or [])[-(ADIM_SINIRI - 1):] + [
        {"zaman": simdi(), "arac": arac, "ozet": kisalt(ozet)}
    ]
    if d.get("hal") == "bosta":
        d["hal"] = "calisiyor"
    d["guncellendi"] = simdi()
    yaz_atomik(DURUM / f"{uid}.json", json.dumps(d, ensure_ascii=False, indent=1))


# ---------------------------------------------------------------- talimat

def talimatlar(uid: str) -> list[dict]:
    return jsonl_oku(TALIMAT / f"{uid}.jsonl")


def _talimat_yaz(uid: str, liste: list[dict]) -> None:
    yaz_atomik(TALIMAT / f"{uid}.jsonl", "".join(json.dumps(t, ensure_ascii=False) + "\n" for t in liste))


def talimat_ekle(hedef: str, metin: str, kimden: str = "kullanici") -> dict:
    if not uye_mi(hedef):
        raise ValueError(f"Bilinmeyen üye: {hedef}")
    metin = metin.strip()
    if not metin:
        raise ValueError("Talimat boş olamaz")
    tumu = [t for u in uye_idleri() for t in talimatlar(u)]
    no = 1 + max([int(t["id"].split("-")[1]) for t in tumu if t.get("id", "").startswith("T-")] or [0])
    kayit = {"id": f"T-{no:04d}", "zaman": simdi(), "kimden": kimden, "metin": metin, "durum": "bekliyor"}
    liste = talimatlar(hedef) + [kayit]
    _talimat_yaz(hedef, liste)
    ruzname_ekle(kimden, "talimat", f"{hedef}: {metin}")
    return kayit


def talimat_bekleyen(uid: str) -> list[dict]:
    return [t for t in talimatlar(uid) if t.get("durum") == "bekliyor"]


def talimat_ilet(uid: str) -> list[dict]:
    liste = talimatlar(uid)
    iletilen = []
    for t in liste:
        if t.get("durum") == "bekliyor":
            t["durum"] = "iletildi"
            t["iletildi"] = simdi()
            iletilen.append(t)
    if iletilen:
        _talimat_yaz(uid, liste)
        ruzname_ekle(uid, "talimat-iletildi", ", ".join(t["id"] for t in iletilen))
    return iletilen


def talimat_metni(liste: list[dict], kime: str) -> str:
    if not liste:
        return ""
    satirlar = [f"[Panelden talimat] {kime} için {len(liste)} yeni talimat var. Kullanıcının talimatı önceliklidir:"]
    for t in liste:
        satirlar.append(f"- {t['id']} ({t['zaman'][11:16]}): {t['metin']}")
    satirlar.append("Talimatı işle; kararını ve etkisini teslim notuna ya da ekip/rapor.md'ye yaz.")
    return "\n".join(satirlar)


# ---------------------------------------------------------------- görev kartları

_ON_RE = re.compile(r"^---\n(.*?)\n---\n?(.*)$", re.S)


def gorev_oku(yol: Path) -> dict:
    metin = yol.read_text(encoding="utf-8")
    m = _ON_RE.match(metin)
    alanlar, govde = {}, metin
    if m:
        for s in m.group(1).splitlines():
            if ":" in s:
                k, v = s.split(":", 1)
                alanlar[k.strip()] = v.strip()
        govde = m.group(2)
    alanlar["govde"] = govde
    alanlar.setdefault("id", yol.stem)
    alanlar.setdefault("durum", "sirada")
    alanlar.setdefault("yurutucu", "claude")
    return alanlar


def gorev_kaydet(g: dict) -> None:
    sira = ["id", "baslik", "atanan", "durum", "yurutucu", "model", "olusturuldu", "guncellendi"]
    on = [f"{k}: {g[k]}" for k in sira if g.get(k)]
    on += [f"{k}: {v}" for k, v in g.items() if k not in sira and k != "govde" and v]
    yaz_atomik(GOREV / f"{g['id']}.md", "---\n" + "\n".join(on) + "\n---\n" + g.get("govde", ""))


def gorev_bul(gid: str) -> dict:
    yol = GOREV / f"{gid}.md"
    if not yol.exists():
        raise ValueError(f"Görev bulunamadı: {gid}")
    return gorev_oku(yol)


def gorevler() -> list[dict]:
    if not GOREV.exists():
        return []
    return [gorev_oku(p) for p in sorted(GOREV.glob("G-*.md"))]


def _kayit_ekle(g: dict, satir: str) -> None:
    govde = g.get("govde", "").rstrip("\n")
    if "\n## Kayıt" not in "\n" + govde:
        govde += "\n\n## Kayıt\n"
    g["govde"] = govde.rstrip("\n") + f"\n- {simdi()[:16].replace('T', ' ')} {satir}\n"


def gorev_yeni(baslik, atanan, amac, cikti, kabul, girdi="", model=None) -> dict:
    if not uye_mi(atanan):
        raise ValueError(f"Bilinmeyen üye: {atanan}")
    no = 1 + max([int(g["id"].split("-")[1]) for g in gorevler()] or [0])
    g = {
        "id": f"G-{no:03d}", "baslik": baslik, "atanan": atanan, "durum": "sirada", "yurutucu": "claude",
        "model": model or uye_model(atanan) or "", "olusturuldu": simdi(), "guncellendi": simdi(),
        "govde": (f"\n## Amaç\n{amac}\n\n## Girdi\n{girdi or '-'}\n\n## Beklenen çıktı\n{cikti}\n\n"
                  f"## Kabul ölçütü\n{kabul}\n"),
    }
    _kayit_ekle(g, "Kart açıldı.")
    gorev_kaydet(g)
    ruzname_ekle("reis", "gorev-yeni", f"{g['id']} {baslik} → {atanan}")
    return g


def gorev_durum(gid: str, durum: str, not_: str = "") -> dict:
    if durum not in GOREV_DURUMLARI:
        raise ValueError(f"Geçersiz durum: {durum}. Seçenekler: {', '.join(GOREV_DURUMLARI)}")
    g = gorev_bul(gid)
    g["durum"], g["guncellendi"] = durum, simdi()
    _kayit_ekle(g, f"Durum: {durum}." + (f" {not_}" if not_ else ""))
    gorev_kaydet(g)
    ruzname_ekle("reis", "gorev-durum", f"{gid} → {durum}" + (f": {not_}" if not_ else ""))
    return g


def gorev_teslim(gid: str, ozet: str, yurutucu: str | None = None) -> dict:
    g = gorev_bul(gid)
    kim = yurutucu or g.get("atanan", "?")
    g["durum"], g["guncellendi"] = "incelemede", simdi()
    g["teslim"] = kisalt(ozet, 300)
    _kayit_ekle(g, f"Teslim ({kim}): {ozet}")
    gorev_kaydet(g)
    if uye_mi(kim):
        durum_yaz(kim, hal="bosta", su_an=f"{gid} teslim edildi", gorev=gid)
    ruzname_ekle(kim, "teslim", f"{gid}: {ozet}")
    if yurutucu == DIS_YURUTUCU:
        talimat_ekle("reis", f"{gid} Antigravity tarafından teslim edildi. Teslimi denetle: {kisalt(ozet, 160)}",
                     kimden="sistem")
    return g


def gorev_devret(gid: str) -> dict:
    g = gorev_bul(gid)
    if g.get("durum") == "tamam":
        raise ValueError(f"{gid} zaten tamamlanmış")
    onceki = g.get("atanan", "")
    g["yurutucu"], g["durum"], g["guncellendi"] = DIS_YURUTUCU, "devredildi", simdi()
    _kayit_ekle(g, f"Kullanıcı görevi Antigravity'e devretti (önceki yürütücü: {onceki}).")
    gorev_kaydet(g)
    brif = (
        f"# {gid} — {g.get('baslik', '')}\n\n"
        f"Bu görev Tercüme Heyeti'nden sana devredildi. Önce depo kökündeki `AGENTS.md`'yi, sonra "
        f"`proje/mimari.md` ve `proje/kararlar.md`'yi oku.\n\n"
        f"Başlarken: `python3 ekip/bin/ekip.py durum antigravity \"{gid} başladı\" --gorev {gid}`\n"
        f"Bitirince: `python3 ekip/bin/ekip.py gorev teslim {gid} --yurutucu antigravity --ozet \"...\"`\n\n"
        f"---\n{g.get('govde', '')}"
    )
    yaz_atomik(ANTIGRAVITY / f"{gid}.md", brif)
    durum_yaz(DIS_YURUTUCU, hal="bekliyor", su_an=f"{gid} devralınmayı bekliyor", gorev=gid)
    ruzname_ekle("kullanici", "devir", f"{gid} Antigravity'e devredildi")
    talimat_ekle("reis", f"Kullanıcı {gid} görevini Antigravity'e devretti. Bu kartı yürütme; teslimi bekle.",
                 kimden="sistem")
    if onceki in uye_idleri() and onceki != "reis":
        talimat_ekle(onceki, f"{gid} Antigravity'e devredildi. Bu kart üzerinde çalışıyorsan dur; o ana kadar "
                             f"yaptığını dosyaya kaydet ve kart kaydına not düş.", kimden="sistem")
        if durum_oku(onceki).get("gorev") == gid and durum_oku(onceki).get("hal") != "calisiyor":
            durum_yaz(onceki, su_an=f"{gid} Antigravity'e devredildi")
    g["istem"] = (f"Bu depodaki AGENTS.md kurallarına uy. Görevi okumak için: python3 ekip/bin/ekip.py gorev goster {gid}"
                  f" — sonra görevi yürüt; başlarken ve bitirince AGENTS.md'deki durum komutlarını çalıştır.")
    return g


# ---------------------------------------------------------------- özet (panel)

def ozet() -> dict:
    k = kadro()
    uyeler = []
    for u in k["uyeler"]:
        d = durum_oku(u["id"])
        uyeler.append({**u, "durum": d, "talimatlar": talimatlar(u["id"])[-12:],
                       "bekleyen": len(talimat_bekleyen(u["id"]))})
    ag = durum_oku(DIS_YURUTUCU)
    return {
        "proje": k.get("proje", ""),
        "zaman": simdi(),
        "uyeler": uyeler,
        "antigravity": ag,
        "gorevler": [{kk: vv for kk, vv in g.items()} for g in gorevler()],
        "rapor": RAPOR.read_text(encoding="utf-8") if RAPOR.exists() else "",
        "ruzname": ruzname_son(80),
    }


def adim_ve_ilet(uid: str, arac: str, ozet_: str, ilet: bool = True) -> list[dict]:
    if arac:
        adim_ekle(uid, arac, ozet_)
    return talimat_ilet(uid) if ilet else []


def gorev_goster(gid: str) -> dict:
    return gorev_bul(gid)


def rapor_yaz(metin: str) -> None:
    mevcut = RAPOR.read_text(encoding="utf-8") if RAPOR.exists() else ""
    if mevcut != metin:
        yaz_atomik(RAPOR, metin)


def ekip_ozet_satiri() -> str:
    return _ekip_kisa()


# ---------------------------------------------------------------- uzak kayıt (Supabase)
# ekip/uzak.json varsa ve erişim anahtarı (HEYET_ANAHTAR ortam değişkeni ya da depo kökündeki
# .heyet-anahtar dosyası) bulunursa bütün kayıtlar Supabase'e yazılır; panel ve telefon aynı yeri görür.

UZAK_AYAR = json_oku(EKIP / "uzak.json", None)


def _anahtar() -> str | None:
    if not UZAK_AYAR:
        return None
    a = os.environ.get(UZAK_AYAR.get("anahtar_degiskeni", "HEYET_ANAHTAR"))
    if not a:
        dosya = ROOT / UZAK_AYAR.get("anahtar_dosyasi", ".heyet-anahtar")
        if dosya.exists():
            a = dosya.read_text(encoding="utf-8").strip()
    return a or None


ANAHTAR = _anahtar()
UZAK = bool(UZAK_AYAR and ANAHTAR)


def api(islem: str, **args):
    import urllib.error
    import urllib.request
    url = UZAK_AYAR["url"].rstrip("/") + "/rest/v1/rpc/heyet_api"
    govde = json.dumps({"p_anahtar": ANAHTAR, "p_islem": islem, "p_args": args}, ensure_ascii=False).encode()
    istek = urllib.request.Request(url, data=govde, method="POST", headers={
        "apikey": UZAK_AYAR["yayimlanabilir_anahtar"], "Content-Type": "application/json",
        "Accept": "application/json"})
    try:
        with urllib.request.urlopen(istek, timeout=8) as y:
            return json.loads(y.read().decode() or "null")
    except urllib.error.HTTPError as e:
        try:
            mesaj = json.loads(e.read().decode()).get("message", str(e))
        except Exception:
            mesaj = str(e)
        raise ValueError(f"Ortak kayıt hatası: {mesaj}") from None
    except urllib.error.URLError as e:
        raise ValueError(f"Ortak kayda ulaşılamadı ({e.reason}). Ağ erişiminde *.supabase.co izinli mi?") from None


if UZAK:
    def ruzname_ekle(kim, olay, metin=""):
        api("ruzname_ekle", kim=kim, olay=olay, metin=metin)

    def durum_oku(uid):
        d = api("durum_oku", uye=uid) or {}
        d.setdefault("hal", "bosta"); d.setdefault("su_an", ""); d.setdefault("adimlar", [])
        return d

    def durum_yaz(uid, hal=None, su_an=None, gorev=None, adimlar=None):
        api("durum_yaz", uye=uid, hal=hal, su_an=su_an, gorev=gorev, adimlari_sifirla=adimlar == [])

    def adim_ekle(uid, arac, ozet_):
        api("adim", uye=uid, arac=arac, ozet=ozet_, ilet=False)

    def adim_ve_ilet(uid, arac, ozet_, ilet=True):
        if not arac:
            return talimat_ilet(uid) if ilet else []
        return api("adim", uye=uid, arac=arac, ozet=ozet_, ilet=ilet) or []

    def talimat_ekle(hedef, metin, kimden="kullanici"):
        return api("talimat_ekle", hedef=hedef, metin=metin, kimden=kimden)

    def talimat_ilet(uid):
        return api("talimat_ilet", uye=uid) or []

    def talimat_bekleyen(uid):
        return [None] * int(api("talimat_bekleyen", uye=uid) or 0)

    def gorevler():
        return api("ozet").get("gorevler", [])

    def gorev_yeni(baslik, atanan, amac, cikti, kabul, girdi="", model=None):
        govde = (f"\n## Amaç\n{amac}\n\n## Girdi\n{girdi or '-'}\n\n## Beklenen çıktı\n{cikti}\n\n"
                 f"## Kabul ölçütü\n{kabul}\n")
        return {"id": api("gorev_yeni", baslik=baslik, atanan=atanan, govde=govde, model=model)}

    def gorev_durum(gid, durum, not_=""):
        if durum not in GOREV_DURUMLARI:
            raise ValueError(f"Geçersiz durum: {durum}. Seçenekler: {', '.join(GOREV_DURUMLARI)}")
        api("gorev_durum", id=gid, durum=durum, **{"not": not_})

    def gorev_teslim(gid, ozet_, yurutucu=None):
        api("gorev_teslim", id=gid, ozet=ozet_, yurutucu=yurutucu)

    def gorev_devret(gid):
        r = api("gorev_devret", id=gid)
        return {"id": gid, "istem": r["istem"]}

    def gorev_goster(gid):
        g = api("gorev_goster", id=gid)
        if not g:
            raise ValueError(f"Görev bulunamadı: {gid}")
        return g

    def rapor_yaz(metin):
        api("rapor_yaz", metin=metin)

    def ozet():
        return api("ozet")

    def ekip_ozet_satiri():
        o = api("ozet")
        satir = [f"{u['ad']}: {u['durum']['hal']}" + (f", {u['bekleyen']} bekleyen talimat" if u["bekleyen"] else "")
                 + (f" — {u['durum']['su_an']}" if u["durum"].get("su_an") else "")
                 for u in o["uyeler"] if u["durum"]["hal"] != "bosta" or u["bekleyen"]]
        sayac = {}
        for g in o["gorevler"]:
            sayac[g["durum"]] = sayac.get(g["durum"], 0) + 1
        gs = ", ".join(f"{k}: {v}" for k, v in sayac.items())
        return ("[Heyet durumu] " + ("; ".join(satir) + "." if satir else "Tüm üyeler boşta.") +
                (f" Görevler: {gs}." if gs else ""))


# ---------------------------------------------------------------- hook'lar

def _arac_ozeti(arac: str, girdi: dict) -> str:
    def rel(p):
        try:
            return str(Path(p).resolve().relative_to(ROOT))
        except Exception:
            return str(p)
    if arac == "Bash":
        return girdi.get("description") or girdi.get("command", "")
    if arac in ("Read", "Write", "Edit", "MultiEdit", "NotebookEdit"):
        fiil = {"Read": "Okudu", "Write": "Yazdı", "Edit": "Düzenledi", "MultiEdit": "Düzenledi"}.get(arac, arac)
        return f"{fiil}: {rel(girdi.get('file_path') or girdi.get('notebook_path') or '')}"
    if arac in ("Grep", "Glob"):
        return f"Aradı: {girdi.get('pattern', '')}"
    if arac == "WebSearch":
        return f"Web araması: {girdi.get('query', '')}"
    if arac == "WebFetch":
        return f"Sayfa okudu: {girdi.get('url', '')}"
    if arac in ("Agent", "Task"):
        return f"Görevlendirdi: {girdi.get('subagent_type', '?')} — {girdi.get('description', '')}"
    return arac


def _cikti(olay: str, ek_baglam: str = "", engelle: str = "") -> None:
    if engelle:
        print(json.dumps({"decision": "block", "reason": engelle}, ensure_ascii=False))
    elif ek_baglam:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": olay, "additionalContext": ek_baglam}},
                         ensure_ascii=False))


def _uye_bul(veri: dict) -> str:
    tur = veri.get("agent_type") or ""
    return tur if tur in uye_idleri() else "reis"


def _ekip_kisa() -> str:
    satir = []
    for u in kadro()["uyeler"]:
        d = durum_oku(u["id"])
        if d["hal"] != "bosta" or talimat_bekleyen(u["id"]):
            b = talimat_bekleyen(u["id"])
            satir.append(f"{u['ad']}: {d['hal']}" + (f", {len(b)} bekleyen talimat" if b else "") +
                         (f" — {d['su_an']}" if d.get("su_an") else ""))
    sayac = {}
    for g in gorevler():
        sayac[g["durum"]] = sayac.get(g["durum"], 0) + 1
    gs = ", ".join(f"{k}: {v}" for k, v in sayac.items())
    return ("[Heyet durumu] " + ("; ".join(satir) + "." if satir else "Tüm üyeler boşta.") +
            (f" Görevler: {gs}." if gs else ""))


def hook(olay: str) -> None:
    try:
        ham = sys.stdin.read()
        veri = json.loads(ham) if ham.strip() else {}
    except Exception:
        veri = {}
    uye = _uye_bul(veri)

    if olay == "post-tool":
        arac = veri.get("tool_name", "")
        girdi = veri.get("tool_input") or {}
        girdi = girdi if isinstance(girdi, dict) else {}
        komut = girdi.get("command", "")
        kaydet = "ekip/bin/ekip.py" not in komut
        iletilen = adim_ve_ilet(uye, arac if kaydet else "", _arac_ozeti(arac, girdi))
        yol = str(girdi.get("file_path") or "")
        if UZAK and arac in ("Write", "Edit", "MultiEdit") and yol.replace("\\", "/").endswith("ekip/rapor.md"):
            try:
                rapor_yaz(Path(yol).read_text(encoding="utf-8"))
            except OSError:
                pass
        if arac in ("Agent", "Task"):
            hedef = girdi.get("subagent_type", "")
            if hedef in uye_idleri():
                ruzname_ekle(hedef, "teslim-alindi", girdi.get("description", ""))
        _cikti("PostToolUse", talimat_metni(iletilen, uye))

    elif olay == "subagent-start":
        if uye == "reis":
            return
        aktif = [g for g in gorevler() if g.get("atanan") == uye and g.get("yurutucu") != DIS_YURUTUCU
                 and g.get("durum") in ("sirada", "calisiyor", "iade")]
        gid = aktif[0]["id"] if aktif else None
        if gid and aktif[0]["durum"] != "calisiyor":
            gorev_durum(gid, "calisiyor", f"{uye} işe başladı.")
        durum_yaz(uye, hal="calisiyor", su_an="Görevi okuyor", gorev=gid, adimlar=[])
        ruzname_ekle(uye, "basladi", gid or "")
        baglam = (f"Sen Tercüme Heyeti'nin {uye} üyesisin." +
                  (f" Aktif kartın {gid}; oku: python3 ekip/bin/ekip.py gorev goster {gid}" if gid else ""))
        t = talimat_metni(talimat_ilet(uye), uye)
        _cikti("SubagentStart", baglam + ("\n" + t if t else ""))

    elif olay == "subagent-stop":
        if uye == "reis":
            return
        bekleyen = talimat_bekleyen(uye)
        if bekleyen and not veri.get("stop_hook_active"):
            _cikti("SubagentStop", engelle=talimat_metni(talimat_ilet(uye), uye))
            return
        d = durum_oku(uye)
        durum_yaz(uye, hal="bosta", su_an=d.get("su_an") or "Bitirdi")
        ruzname_ekle(uye, "bitirdi", d.get("gorev") or "")

    elif olay == "stop":
        bekleyen = talimat_bekleyen("reis")
        if bekleyen and not veri.get("stop_hook_active"):
            _cikti("Stop", engelle=talimat_metni(talimat_ilet("reis"), "Reis"))
            return
        d = durum_oku("reis")
        if d["hal"] != "bekliyor":
            durum_yaz("reis", hal="bosta")

    elif olay == "user-prompt":
        durum_yaz("reis", hal="calisiyor")
        t = talimat_metni(talimat_ilet("reis"), "Reis")
        _cikti("UserPromptSubmit", "\n".join(x for x in (t, ekip_ozet_satiri()) if x))

    elif olay == "session-start":
        durum_yaz("reis", hal="calisiyor", su_an="Oturum açıldı; kayıtları okuyor")
        ruzname_ekle("reis", "oturum", "Claude Code oturumu açıldı")
        t = talimat_metni(talimat_ilet("reis"), "Reis")
        _cikti("SessionStart", "\n".join(x for x in (ekip_ozet_satiri(), t) if x))


# ---------------------------------------------------------------- komut satırı

def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="ekip.py", description="Tercüme Heyeti kayıt aracı")
    alt = p.add_subparsers(dest="komut", required=True)

    a = alt.add_parser("durum", help="Üyenin şu an ne yaptığını yaz")
    a.add_argument("uye"); a.add_argument("metin")
    a.add_argument("--hal", choices=UYE_HALLERI); a.add_argument("--gorev")

    a = alt.add_parser("talimat", help="Bir üyeye talimat bırak")
    a.add_argument("hedef"); a.add_argument("metin"); a.add_argument("--kimden", default="reis")

    a = alt.add_parser("talimat-oku", help="Bekleyen talimatları oku ve iletildi say")
    a.add_argument("uye")

    g = alt.add_parser("gorev", help="Görev kartları").add_subparsers(dest="alt", required=True)
    b = g.add_parser("yeni")
    for f in ("baslik", "atanan", "amac", "cikti", "kabul"):
        b.add_argument(f"--{f}", required=True)
    b.add_argument("--girdi", default=""); b.add_argument("--model")
    b = g.add_parser("durum"); b.add_argument("id"); b.add_argument("durum"); b.add_argument("--not", dest="not_", default="")
    b = g.add_parser("teslim"); b.add_argument("id"); b.add_argument("--ozet", required=True); b.add_argument("--yurutucu")
    b = g.add_parser("devret"); b.add_argument("id")
    b = g.add_parser("goster"); b.add_argument("id")
    g.add_parser("liste")

    a = alt.add_parser("rapor", help="ekip/rapor.md'yi ortak kayda gönder")
    a.add_argument("--dosya", default=str(RAPOR))

    alt.add_parser("ozet", help="Panel için JSON özet")
    a = alt.add_parser("hook"); a.add_argument("olay")

    ar = p.parse_args(argv)
    try:
        if ar.komut == "hook":
            try:
                hook(ar.olay)
            except Exception as e:  # hook asla oturumu bozmasın
                print(f"ekip hook hatası: {e}", file=sys.stderr)
            return 0
        if ar.komut == "durum":
            if not uye_mi(ar.uye):
                raise ValueError(f"Bilinmeyen üye: {ar.uye}")
            durum_yaz(ar.uye, su_an=kisalt(ar.metin, 200), hal=ar.hal or "calisiyor", gorev=ar.gorev)
            if ar.hal == "bekliyor":
                ruzname_ekle(ar.uye, "bekliyor", ar.metin)
            print("tamam")
        elif ar.komut == "talimat":
            print(json.dumps(talimat_ekle(ar.hedef, ar.metin, ar.kimden), ensure_ascii=False))
        elif ar.komut == "talimat-oku":
            print(talimat_metni(talimat_ilet(ar.uye), ar.uye) or "Bekleyen talimat yok.")
        elif ar.komut == "gorev":
            if ar.alt == "yeni":
                r = gorev_yeni(ar.baslik, ar.atanan, ar.amac, ar.cikti, ar.kabul, ar.girdi, ar.model)
                print(r["id"])
            elif ar.alt == "durum":
                gorev_durum(ar.id, ar.durum, ar.not_); print("tamam")
            elif ar.alt == "teslim":
                gorev_teslim(ar.id, ar.ozet, ar.yurutucu); print("tamam")
            elif ar.alt == "devret":
                print(gorev_devret(ar.id)["istem"])
            elif ar.alt == "goster":
                x = gorev_goster(ar.id)
                print(f"# {x['id']} — {x.get('baslik','')}\nAtanan: {x.get('atanan','')}  Durum: {x.get('durum','')}  "
                      f"Yürütücü: {x.get('yurutucu','')}  Model: {x.get('model','')}\n{x.get('govde','')}")
            elif ar.alt == "liste":
                for x in gorevler():
                    print(f"{x['id']}  {x.get('durum',''):<11} {x.get('atanan',''):<12} {x.get('baslik','')}")
        elif ar.komut == "rapor":
            rapor_yaz(Path(ar.dosya).read_text(encoding="utf-8")); print("tamam")
        elif ar.komut == "ozet":
            print(json.dumps(ozet(), ensure_ascii=False, indent=1))
    except ValueError as e:
        print(f"Hata: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
