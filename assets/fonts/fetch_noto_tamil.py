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
    "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansTamil/NotoSansTamil-Regular.ttf",
]
BACKUP_SRC = pathlib.Path(r"C:\Windows\Fonts\Nirmala.ttc")
BACKUP_OUT = HERE / "Nirmala.ttc"
TTF_SIGS = (b"\x00\x01\x00\x00", b"OTTO", b"true", b"ttcf")
MIN_BYTES = 40_000
PROBE = "கைது"


def _looks_like_font(path: pathlib.Path) -> bool:
    if not path.is_file() or path.stat().st_size < MIN_BYTES:
        return False
    return path.read_bytes()[:4] in TTF_SIGS


def _renders_tamil(path: pathlib.Path) -> bool:
    try:
        from PIL import Image, ImageDraw, ImageFont

        try:
            font = ImageFont.truetype(str(path), 40)
        except OSError:
            font = ImageFont.truetype(str(path), 40, index=0)
        img = Image.new("L", (220, 80), 0)
        ImageDraw.Draw(img).text((4, 4), PROBE, fill=255, font=font)
        return img.getbbox() is not None and max(img.getdata()) > 20
    except Exception as exc:
        print(f"render check fail: {exc}")
        return False


def main() -> int:
    HERE.mkdir(parents=True, exist_ok=True)
    # Prefer system Nirmala (best on Windows)
    if BACKUP_SRC.is_file():
        shutil.copy2(BACKUP_SRC, BACKUP_OUT)
        if _renders_tamil(BACKUP_OUT):
            print(f"copied + verified {BACKUP_OUT} ({BACKUP_OUT.stat().st_size} bytes)")
            return 0
    for url in URLS:
        try:
            print(f"try {url}")
            urllib.request.urlretrieve(url, OUT)
            if _looks_like_font(OUT) and _renders_tamil(OUT):
                print(f"saved + verified {OUT} ({OUT.stat().st_size} bytes)")
                return 0
            print(f"reject size={OUT.stat().st_size if OUT.exists() else 0}")
            if OUT.exists():
                OUT.unlink()
        except Exception as exc:
            print(f"fail: {exc}")
    print("ERROR: could not obtain a Tamil font that renders glyphs", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
