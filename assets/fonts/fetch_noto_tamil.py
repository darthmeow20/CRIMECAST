"""Download Noto Sans Tamil Regular into this directory."""
from __future__ import annotations

import pathlib
import shutil
import sys
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "NotoSansTamil-Regular.ttf"
URLS = [
    "https://notofonts.github.io/tamil/fonts/NotoSansTamil/full/ttf/NotoSansTamil-Regular.ttf",
    "https://cdn.jsdelivr.net/gh/openmaptiles/fonts@master/noto-sans/NotoSansTamil-Regular.ttf",
    "https://raw.githubusercontent.com/openmaptiles/fonts/master/noto-sans/NotoSansTamil-Regular.ttf",
    "https://github.com/notofonts/tamil/raw/main/fonts/NotoSansTamil/full/ttf/NotoSansTamil-Regular.ttf",
    "https://raw.githubusercontent.com/notofonts/tamil/main/fonts/NotoSansTamil/full/ttf/NotoSansTamil-Regular.ttf",
]
BACKUP_SRC = pathlib.Path(r"C:\Windows\Fonts\Nirmala.ttc")
BACKUP_OUT = HERE / "Nirmala.ttc"
TTF_SIGS = (b"\x00\x01\x00\x00", b"OTTO", b"true", b"ttcf")


def _looks_like_font(path: pathlib.Path) -> bool:
    if not path.is_file() or path.stat().st_size < 10_000:
        return False
    return path.read_bytes()[:4] in TTF_SIGS


def main() -> int:
    HERE.mkdir(parents=True, exist_ok=True)
    for url in URLS:
        try:
            print(f"try {url}")
            urllib.request.urlretrieve(url, OUT)
            if _looks_like_font(OUT):
                print(f"saved {OUT} ({OUT.stat().st_size} bytes)")
                return 0
            print(f"reject size={OUT.stat().st_size if OUT.exists() else 0}")
            if OUT.exists():
                OUT.unlink()
        except Exception as exc:
            print(f"fail: {exc}")
    if BACKUP_SRC.is_file():
        shutil.copy2(BACKUP_SRC, BACKUP_OUT)
        print(f"copied backup {BACKUP_OUT} ({BACKUP_OUT.stat().st_size} bytes)")
        return 0
    print("ERROR: could not obtain a Tamil font", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
