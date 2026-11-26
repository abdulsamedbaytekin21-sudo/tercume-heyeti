#!/usr/bin/env python3
"""Tercüme Heyeti paneli — yerel sunucu.

Yalnızca bu bilgisayardan erişilir (127.0.0.1). Python standart kütüphanesi yeterlidir.
    python3 ekip/panel/sunucu.py            → http://127.0.0.1:4317
    python3 ekip/panel/sunucu.py --port 5000
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BURASI = Path(__file__).resolve().parent
sys.path.insert(0, str(BURASI.parent / "bin"))
import ekip  # noqa: E402

UYANDIRMA_ISTEMI = (
    "Panelden yeni talimat geldi. Bekleyen talimatlarını işle, gerekiyorsa heyeti görevlendir "
    "ve ekip/rapor.md'yi güncelle."
)


def uyandir() -> dict:
    """Claude Code penceresi kapalıyken Reis'i başsız (headless) bir turla çalıştırır."""
    d = ekip.durum_oku("reis")
    if d.get("hal") == "calisiyor":
        return {"tamam": False, "mesaj": "Reis zaten çalışıyor; talimat bir sonraki adımında ona iletilecek."}
    claude = shutil.which("claude")
    if not claude:
        return {"tamam": False, "mesaj": "Bu bilgisayarda 'claude' komutu bulunamadı. Claude Code'u açıp Reis'e "
                                         "'devam' yazmanız yeterli; talimat ona otomatik iletilir."}
    gunluk = ekip.EKIP / "gunluk"
    gunluk.mkdir(exist_ok=True)
    dosya = gunluk / f"uyandirma-{datetime.now():%Y%m%d-%H%M%S}.log"
    with dosya.open("w", encoding="utf-8") as f:
        subprocess.Popen([claude, "--continue", "-p", UYANDIRMA_ISTEMI, "--permission-mode", "acceptEdits"],
                         cwd=str(ekip.ROOT), stdout=f, stderr=subprocess.STDOUT, start_new_session=True)
    ekip.ruzname_ekle("kullanici", "uyandirma", "Reis panelden uyandırıldı")
    return {"tamam": True, "mesaj": "Reis uyandırıldı. Çalışmayı panelden izleyebilirsiniz."}


class Isleyici(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _gonder(self, kod: int, govde, tur="application/json; charset=utf-8"):
        veri = govde if isinstance(govde, bytes) else json.dumps(govde, ensure_ascii=False).encode("utf-8")
        self.send_response(kod)
        self.send_header("Content-Type", tur)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(veri)))
        self.end_headers()
        self.wfile.write(veri)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._gonder(200, (BURASI / "index.html").read_bytes(), "text/html; charset=utf-8")
        elif self.path.startswith("/api/durum"):
            self._gonder(200, ekip.ozet())
        else:
            self._gonder(404, {"hata": "Bulunamadı"})

    def do_POST(self):
        # Yalnızca aynı kökten gelen istekler (başka sitelerin bu panele yazmasını engeller)
        koken = self.headers.get("Origin")
        if koken and not koken.startswith(("http://127.0.0.1", "http://localhost")):
            return self._gonder(403, {"hata": "İzin verilmeyen köken"})
        try:
            uzunluk = int(self.headers.get("Content-Length") or 0)
            veri = json.loads(self.rfile.read(uzunluk) or b"{}")
            if self.path == "/api/talimat":
                k = ekip.talimat_ekle(veri.get("hedef", ""), veri.get("metin", ""), kimden="kullanici")
                self._gonder(200, {"tamam": True, "talimat": k})
            elif self.path == "/api/devret":
                g = ekip.gorev_devret(veri.get("gorev", ""))
                self._gonder(200, {"tamam": True, "istem": g["istem"], "gorev": g["id"]})
            elif self.path == "/api/uyandir":
                self._gonder(200, uyandir())
            else:
                self._gonder(404, {"hata": "Bulunamadı"})
        except ValueError as e:
            self._gonder(400, {"hata": str(e)})


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=4317)
    a = p.parse_args()
    sunucu = ThreadingHTTPServer(("127.0.0.1", a.port), Isleyici)
    print(f"Tercüme Heyeti paneli: http://127.0.0.1:{a.port}  (kapatmak için Ctrl+C)")
    try:
        sunucu.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
