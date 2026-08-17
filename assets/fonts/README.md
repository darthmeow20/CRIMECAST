# Tamil fonts for word clouds

WordCloud’s default font has **no Tamil glyphs**, so Tamil words appear as □ boxes
on Streamlit Cloud / Linux.

## Auto (preferred)

When the Sentiment word cloud runs, `sentiment_wordclouds.ensure_tamil_font()`:

1. Uses a font already in this folder, or
2. Copies Windows **Nirmala** (`C:\Windows\Fonts\Nirmala.ttc`), or
3. Downloads **Noto Sans Tamil** into this folder, or
4. Uses Linux **Lohit Tamil** if installed via `packages.txt` (`fonts-lohit-taml`)

## Manual (one-time)

```bat
python assets\fonts\fetch_noto_tamil.py
```

or double-click `download_noto_tamil.bat`.

Then commit `NotoSansTamil-Regular.ttf` so cloud deploys don’t need a download.

## Do not commit

Temporary junk (`_bin_test*`) — only `.ttf` / `.ttc` fonts matter.
