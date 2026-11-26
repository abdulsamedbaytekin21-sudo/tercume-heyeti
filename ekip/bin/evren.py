#!/usr/bin/env python3
"""EVREN (OpenAI uyumlu API) ile toplu ve ucuz işler.

Ayar: ortam değişkenleri EVREN_URL (ör. https://.../v1) ve EVREN_ANAHTAR,
ya da depo kökünde .evren-anahtar dosyası (git dışında). Varsayılan model ekip/evren.json'dan okunur.

  evren.py modeller
  evren.py sor  --model M --sistem "..." --girdi "..."        (@dosya yolu ya da - kabul edilir)
  evren.py toplu --model M --sistem @istem.md --girdi giris.jsonl --cikti cikis.jsonl [--alan metin] [--paralel 4]

Kural: veri/kasa/ altındaki (telifli) hiçbir dosya EVREN'e gönderilmez; araç bunu reddeder.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

ROOT = Path(os.environ.get("HEYET_KOK") or Path(__file__).resolve().parents[2])
AYAR = json.loads((ROOT / "ekip" / "evren.json").read_text(encoding="utf-8"))
KULLANIM = ROOT / "ekip" / "evren_kullanim.jsonl"


def _ayar():
    url = os.environ.get("EVREN_URL") or AYAR.get("url")
    anahtar = os.environ.get("EVREN_ANAHTAR")
    if not anahtar and (ROOT / ".evren-anahtar").exists():
        anahtar = (ROOT / ".evren-anahtar").read_text(encoding="utf-8").strip()
    if not url or not anahtar:
        raise SystemExit("EVREN ayarı eksik: EVREN_URL ve EVREN_ANAHTAR tanımlı olmalı "
                         "(bulut ortamında ortam değişkeni, bilgisayarda .evren-anahtar dosyası).")
    return url.rstrip("/"), anahtar


def _kasa_kontrol(yol: str) -> None:
    p = Path(yol).resolve()
    kasa = (ROOT / "veri" / "kasa").resolve()
    if p == kasa or kasa in p.parents:
        raise SystemExit(f"Reddedildi: {yol} telifli kasada. Kasadaki veri EVREN'e gönderilmez.")


def _metin(deger: str) -> str:
    if deger == "-":
        return sys.stdin.read()
    if deger.startswith("@"):
        _kasa_kontrol(deger[1:])
        return Path(deger[1:]).read_text(encoding="utf-8")
    return deger


def _istek(yol: str, govde: dict | None = None, deneme: int = 3):
    url, anahtar = _ayar()
    veri = json.dumps(govde, ensure_ascii=False).encode() if govde is not None else None
    for i in range(deneme):
        istek = urllib.request.Request(url + yol, data=veri, method="POST" if veri else "GET", headers={
            "Authorization": f"Bearer {anahtar}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(istek, timeout=180) as y:
                return json.loads(y.read().decode())
        except urllib.error.HTTPError as e:
            govde_hata = e.read().decode(errors="replace")[:300]
            if e.code in (429, 500, 502, 503, 504) and i < deneme - 1:
                time.sleep(2 ** i * 3)
                continue
            raise SystemExit(f"EVREN hatası {e.code}: {govde_hata}")
        except urllib.error.URLError as e:
            if i < deneme - 1:
                time.sleep(2 ** i * 3)
                continue
            raise SystemExit(f"EVREN'e ulaşılamadı ({e.reason}). Ağ erişiminde EVREN alan adı izinli mi?")


def _kaydet(model: str, kullanim: dict, adet: int = 1) -> None:
    KULLANIM.parent.mkdir(parents=True, exist_ok=True)
    with KULLANIM.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"zaman": datetime.now().astimezone().isoformat(timespec="seconds"),
                            "model": model, "istek": adet, **(kullanim or {})}, ensure_ascii=False) + "\n")


def sor(model: str, sistem: str, girdi: str, sicaklik: float = 0.2, json_kip: bool = False) -> tuple[str, dict]:
    govde = {"model": model, "temperature": sicaklik,
             "messages": ([{"role": "system", "content": sistem}] if sistem else []) +
                         [{"role": "user", "content": girdi}]}
    if json_kip:
        govde["response_format"] = {"type": "json_object"}
    r = _istek("/chat/completions", govde)
    return r["choices"][0]["message"]["content"], r.get("usage") or {}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="evren.py")
    alt = p.add_subparsers(dest="komut", required=True)
    alt.add_parser("modeller")
    for ad in ("sor", "toplu"):
        a = alt.add_parser(ad)
        a.add_argument("--model", default=AYAR.get("varsayilan_model"))
        a.add_argument("--sistem", default="")
        a.add_argument("--sicaklik", type=float, default=0.2)
        a.add_argument("--json", action="store_true", help="Yanıtı JSON nesnesi olarak iste")
        a.add_argument("--girdi", required=True)
        if ad == "toplu":
            a.add_argument("--cikti", required=True)
            a.add_argument("--alan", default="metin", help="Girdi JSONL'de modele gidecek alan")
            a.add_argument("--paralel", type=int, default=4)
    ar = p.parse_args(argv)

    if ar.komut == "modeller":
        r = _istek("/models")
        for m in r.get("data", []):
            print(m.get("id"))
        return 0

    if not ar.model:
        raise SystemExit("Model belirtilmedi: --model verin ya da ekip/evren.json'a varsayilan_model yazın.")
    sistem = _metin(ar.sistem) if ar.sistem else ""

    if ar.komut == "sor":
        cevap, kul = sor(ar.model, sistem, _metin(ar.girdi), ar.sicaklik, ar.json)
        _kaydet(ar.model, kul)
        print(cevap)
        return 0

    _kasa_kontrol(ar.girdi)
    _kasa_kontrol(ar.cikti)
    satirlar = [json.loads(s) for s in Path(ar.girdi).read_text(encoding="utf-8").splitlines() if s.strip()]
    toplam = {"prompt_tokens": 0, "completion_tokens": 0}

    def isle(k):
        try:
            cevap, kul = sor(ar.model, sistem, str(k[ar.alan]), ar.sicaklik, ar.json)
            return {**k, "evren": cevap, "evren_model": ar.model}, kul
        except SystemExit as e:
            return {**k, "evren_hata": str(e), "evren_model": ar.model}, {}

    with ThreadPoolExecutor(max_workers=max(1, ar.paralel)) as h, Path(ar.cikti).open("w", encoding="utf-8") as f:
        hatali = 0
        for sonuc, kul in h.map(isle, satirlar):
            f.write(json.dumps(sonuc, ensure_ascii=False) + "\n")
            hatali += "evren_hata" in sonuc
            for k in toplam:
                toplam[k] += int(kul.get(k) or 0)
    _kaydet(ar.model, toplam, len(satirlar))
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        import ekip
        ekip.ruzname_ekle("katip", "evren", f"{len(satirlar)} istek, {ar.model}, "
                          f"{toplam['prompt_tokens'] + toplam['completion_tokens']} token, {hatali} hata")
    except Exception:
        pass
    print(f"{len(satirlar)} satır işlendi, {hatali} hata. Token: {toplam}. Çıktı: {ar.cikti}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
