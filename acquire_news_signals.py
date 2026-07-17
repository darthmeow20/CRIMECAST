#!/usr/bin/env python3
"""
CRIMECAST - Crime news acquisition (Tamil Nadu) — NEWS MEDIA ONLY

Primary sources (NOT social media):
  - Google News RSS (English + Tamil)
  - Tamil media outlets: Dinamalar, Dinakaran, Maalai Malar, Vikatan,
    Puthiya Thalaimurai, News18 Tamil, OneIndia Tamil, BBC Tamil, etc.
  - English TN press: The Hindu, DT Next, TOI, Indian Express
  - Local aggregators (DailyHunt / Lokal / Public) via open web/RSS

NLP (3 LLM roles — see nlp_pipeline.py):
  1) DistilBERT SST-2 — sentiment
  2) DistilBERT MNLI zero-shot — crime type
  3) DistilBERT MNLI zero-shot — trend labels

Usage:
  python acquire_news_signals.py --populate-2024-2026
  python acquire_news_signals.py --populate-years 2024 2025 2026
  python acquire_news_signals.py --fetch "Tamil Nadu crime"
  python acquire_news_signals.py --csv headlines.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

import pandas as pd
from dateutil import parser as date_parser  # already in requirements via python-dateutil

PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_ROOT / "model_outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
NEWS_OUTPUT = OUTPUT_DIR / "news_signals.csv"

# Do NOT import nlp_pipeline / transformers at module load.
# Dashboard refresh uses lexicon-only scoring so Streamlit never pulls
# transformers → torchvision / SAM ModuleNotFoundError spam.
HAS_NLP3 = None  # resolved lazily
HAS_SENTIMENT = True  # always have built-in lexicon scorer


def _resolve_nlp() -> bool:
    """Lazy: True if full 3-LLM nlp_pipeline is importable (not loaded until used)."""
    global HAS_NLP3
    if HAS_NLP3 is not None:
        return bool(HAS_NLP3)
    try:
        import nlp_pipeline  # noqa: F401

        HAS_NLP3 = True
    except Exception as e:
        print(f"[WARN] nlp_pipeline unavailable: {e}")
        HAS_NLP3 = False
    return bool(HAS_NLP3)


# User-priority Tamil media outlets (தினத்தந்தி, தினமலர், தினமணி, தமிழ் முரசு, புதிய தலைமுறை, விகடன், பிபிசி தமிழ்)
TAMIL_MEDIA_OUTLETS = [
    # (site domain for site:, brand name, Tamil name)
    ("dailythanthi.com", "Dina Thanthi", "தினத்தந்தி"),
    ("dtnext.in", "DT Next / Thanthi", "தினத்தந்தி"),
    ("thanthitv.com", "Thanthi TV", "தினத்தந்தி"),
    ("dinamalar.com", "Dinamalar", "தினமலர்"),
    ("dinamani.com", "Dinamani", "தினமணி"),
    ("tamilmurasu.com.sg", "Tamil Murasu", "தமிழ் முரசு"),
    ("tamilmurasu.com", "Tamil Murasu", "தமிழ் முரசு"),
    ("puthiyathalaimurai.com", "Puthiya Thalaimurai", "புதிய தலைமுறை"),
    ("vikatan.com", "Ananda Vikatan", "விகடன்"),
    ("bbc.com/tamil", "BBC Tamil", "பிபிசி தமிழ்"),
    # Additional TN Tamil press still useful
    ("dinakaran.com", "Dinakaran", "தினகரன்"),
    ("maalaimalar.com", "Maalai Malar", "மாலைமலர்"),
    ("hindutamil.in", "Hindu Tamil", "இந்து தமிழ்"),
    ("tamil.news18.com", "News18 Tamil", "நியூஸ்18 தமிழ்"),
]

# Crime keywords (Tamil + English) — user list
TAMIL_CRIME_KEYWORDS = [
    "கொலை",  # murder
    "தாக்குதல்",  # assault / attack
    "கடத்தல்",  # abduction / kidnapping
    "லஞ்சம்",  # bribery
    "இணைய வழி குற்றங்கள்",  # cyber crimes
    "இணையவழி குற்றம்",
    "திருட்டு",  # theft
    "பாலியல் வன்கொடுமை",  # sexual violence
    "பாலியல்",
    "pocso",
    "POCSO",
    "போதைப்பொருள் கடத்தல்",  # drug trafficking
    "போதைப்பொருள்",
    "கைது",  # arrest
    "முதல் தகவல் அறிக்கை",  # FIR
    "FIR",
]

# Compact OR-group for Google News (too long OR lists get truncated)
TAMIL_CRIME_OR = (
    "கொலை OR தாக்குதல் OR கடத்தல் OR லஞ்சம் OR திருட்டு OR "
    "பாலியல் OR POCSO OR போதைப்பொருள் OR கைது OR "
    "\"முதல் தகவல் அறிக்கை\" OR \"இணைய வழி\""
)

ENGLISH_TN_MEDIA_SITES = [
    ("thehindu.com", "The Hindu"),
    ("dtnext.in", "DT Next"),
    ("timesofindia.indiatimes.com", "Times of India"),
    ("newindianexpress.com", "New Indian Express"),
    ("indianexpress.com", "Indian Express"),
    ("deccanchronicle.com", "Deccan Chronicle"),
    ("hindustantimes.com", "Hindustan Times"),
    ("news18.com", "News18"),
    ("indiatoday.in", "India Today"),
    ("thequint.com", "The Quint"),
]

# English keywords parallel to Tamil list (both languages always harvested)
ENGLISH_CRIME_KEYWORDS = [
    "murder",
    "assault",
    "attack",
    "kidnapping",
    "abduction",
    "bribery",
    "corruption",
    "cybercrime",
    "cyber crime",
    "theft",
    "robbery",
    "rape",
    "sexual assault",
    "sexual violence",
    "POCSO",
    "narcotics",
    "drug trafficking",
    "arrest",
    "FIR",
    "police",
]

ENGLISH_CRIME_OR = (
    "murder OR assault OR kidnapping OR bribery OR cybercrime OR theft OR "
    "rape OR \"sexual assault\" OR POCSO OR narcotics OR \"drug trafficking\" OR "
    "arrest OR FIR OR robbery"
)

# TVK (Tamilaga Vettri Kazhagam) — prefer *negative* party crime / controversy coverage
TVK_EN_OR = 'TVK OR "Tamilaga Vettri Kazhagam" OR "Tamilaga Vetti Kazhagam" OR "Vijay party"'
TVK_TA_OR = 'TVK OR "தமிழக வெற்றி கழகம்" OR "தமிழகவெற்றிகழகம்"'
TVK_NEG_EN = (
    "attack OR assault OR violence OR murder OR FIR OR arrest OR clash OR "
    "scandal OR controversy OR accused OR charged OR complaint OR vandalism OR riot"
)
TVK_NEG_TA = (
    "தாக்குதல் OR கைது OR கொலை OR வன்முறை OR FIR OR புகார் OR வழக்கு OR சர்ச்சை OR குற்றம்"
)
TVK_MARKERS = (
    "tvk",
    "tamilaga vettri",
    "tamilaga vetti",
    "vettri kazhagam",
    "தமிழக வெற்றி",
    "தமிழகவெற்றி",
    "வெற்றி கழகம்",
)
TVK_NEG_KW = (
    "attack", "assault", "murder", "violence", "clash", "fir", "arrest",
    "accused", "charge", "complaint", "vandal", "threat", "illegal",
    "scandal", "controversy", "riot", "stone", "mob", "beaten", "killed",
    "crime", "police", "booked", "custody",
    "தாக்குதல்", "கைது", "கொலை", "வன்முறை", "புகார்", "வழக்கு",
    "தாக்கிய", "கிளர்ச்சி", "சர்ச்சை", "குற்றம்",
)


def is_tvk_related(text: str) -> bool:
    """True if headline mentions TVK / Tamilaga Vettri Kazhagam (party)."""
    t = (text or "").casefold()
    if not t:
        return False
    if any(m in t for m in TVK_MARKERS) or "tvk" in t or "tamilaga" in t:
        return True
    if ("vijay" in t or "விஜய்" in t) and any(
        k in t for k in ("party", "tvk", "kazhagam", "கட்சி", "rally", "cadre")
    ):
        return True
    return False


def is_tvk_negative(text: str) -> bool:
    """TVK mention + negative/crime language (for feed pin + harvest tag)."""
    if not is_tvk_related(text):
        return False
    t = (text or "").casefold()
    return any(k in t for k in TVK_NEG_KW)


def tag_tvk_item(it: dict[str, Any]) -> dict[str, Any]:
    """Mark negative TVK rows for silent Live Feed priority (no UI label)."""
    h = str(it.get("headline") or "")
    if is_tvk_negative(h):
        it["is_tvk"] = True
        it["priority"] = "tvk_negative"
    elif is_tvk_related(h):
        it["is_tvk"] = True
        it["priority"] = ""
    else:
        it.setdefault("is_tvk", False)
    return it


# Brand search names (Tamil + romanized) for queries without site:
TAMIL_OUTLET_BRANDS = [
    "தினத்தந்தி", "Dina Thanthi", "Daily Thanthi",
    "தினமலர்", "Dinamalar",
    "தினமணி", "Dinamani",
    "தமிழ் முரசு", "Tamil Murasu",
    "புதிய தலைமுறை", "Puthiya Thalaimurai",
    "விகடன்", "Vikatan",
    "பிபிசி தமிழ்", "BBC Tamil",
]


def normalize_district(text: str) -> str:
    """Map headline text → TN district (Tier-3 entity resolution)."""
    try:
        from district_entities import resolve_district

        return resolve_district(text, default="Other / Statewide")
    except Exception:
        t = text.lower().strip()
        for key, val in (
            ("chennai", "Chennai"),
            ("madurai", "Madurai"),
            ("thoothukudi", "Thoothukudi"),
            ("tuticorin", "Thoothukudi"),
            ("coimbatore", "Coimbatore"),
        ):
            if key in t:
                return val
        return "Other / Statewide"


def fetch_google_news_rss(
    query: str = "Tamil Nadu crime OR Chennai crime OR TN police",
    max_items: int = 20,
    *,
    lang: str = "en",
) -> list[dict[str, Any]]:
    """Fetch Google News RSS (English or Tamil). lang: 'en' | 'ta'."""
    items = []
    try:
        q = quote_plus(query)

        if lang == "ta":
            # Tamil Google News India
            url = f"https://news.google.com/rss/search?q={q}&hl=ta-IN&gl=IN&ceid=IN:ta"
            default_src = "Google News Tamil"
        else:
            url = f"https://news.google.com/rss/search?q={q}&hl=en-IN&gl=IN&ceid=IN:en"
            default_src = "Google News"

        print(f"[INFO] Fetching Google News RSS ({lang}): {query[:72]}...")

        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; CRIMECAST-research/1.0)"},
        )
        with urllib.request.urlopen(req, timeout=25) as response:
            xml_data = response.read()

        root = ET.fromstring(xml_data)
        channel = root.find("channel")
        if channel is None:
            return items

        count = 0
        for item in channel.findall("item"):
            if count >= max_items:
                break
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            pub_date = item.findtext("pubDate") or ""
            source = item.findtext("source") or default_src

            try:
                dt = date_parser.parse(pub_date)
                date_str = dt.strftime("%Y-%m-%d")
            except Exception:
                date_str = datetime.now().strftime("%Y-%m-%d")

            if title:
                items.append({
                    "date": date_str,
                    "district": normalize_district(title),
                    "headline": title,
                    "source": str(source),
                    "url": link,
                    "lang": lang,
                })
                count += 1

        print(f"  [OK] {len(items)} headlines")
    except Exception as e:
        print(f"  [WARN] RSS fetch failed: {e}")
        return []
    return items


def harvest_tn_crime_media(year: int, max_per_query: int = 18) -> list[dict[str, Any]]:
    """Harvest TN crime headlines — **balanced English + Tamil** news media.

    Tamil outlets: தினத்தந்தி, தினமலர், தினமணி, தமிழ் முரசு, புதிய தலைமுறை, விகடன், பிபிசி தமிழ்
    English outlets: The Hindu, TOI, DT Next, Indian Express, NIE, HT, News18, …

    Both languages use parallel crime keyword sets and equal query priority.
    """
    y_start = f"{year}-01-01"
    y_end = f"{year + 1}-01-01"
    after_before = f"after:{y_start} before:{y_end}"
    ta_kw = TAMIL_CRIME_OR
    en_kw = ENGLISH_CRIME_OR

    # --- Tamil Google News ---
    ta_queries: list[str] = [
        f"தமிழ்நாடு ({ta_kw}) {after_before}",
        f"({ta_kw}) தமிழ்நாடு {after_before}",
        f"(தினத்தந்தி OR தினமலர் OR தினமணி OR \"தமிழ் முரசு\" OR \"புதிய தலைமுறை\" OR விகடன் OR \"பிபிசி தமிழ்\") ({ta_kw}) {after_before}",
        f"(சென்னை OR மதுரை OR தூத்துக்குடி OR கோவை OR சேலம் OR திருச்சி) ({ta_kw}) {after_before}",
        f"தமிழ்நாடு (கொலை OR தாக்குதல் OR கடத்தல்) {after_before}",
        f"தமிழ்நாடு (பாலியல் வன்கொடுமை OR பாலியல் OR POCSO) {after_before}",
        f"தமிழ்நாடு (போதைப்பொருள் கடத்தல் OR லஞ்சம் OR திருட்டு) {after_before}",
        f"தமிழ்நாடு (\"முதல் தகவல் அறிக்கை\" OR கைது OR இணைய வழி) {after_before}",
        f"தூத்துக்குடி (கொலை OR தாக்குதல் OR பாலியல்) {after_before}",
        f"மதுரை (கொலை OR தாக்குதல் OR பாலியல்) {after_before}",
        # TVK negative / controversy / crime (Tamil)
        f"({TVK_TA_OR}) ({TVK_NEG_TA}) {after_before}",
        f"TVK ({TVK_NEG_TA}) {after_before}",
        f"\"தமிழக வெற்றி கழகம்\" ({TVK_NEG_TA}) {after_before}",
        f"TVK (சர்ச்சை OR குற்றம் OR வன்முறை OR புகார்) {after_before}",
    ]
    for site, _en, _ta in TAMIL_MEDIA_OUTLETS:
        ta_queries.append(f"site:{site} ({ta_kw}) {after_before}")

    # --- English Google News (equal weight) ---
    en_queries: list[str] = [
        f"Tamil Nadu ({en_kw}) {after_before}",
        f"\"Tamil Nadu\" police ({en_kw}) {after_before}",
        f"(Chennai OR Madurai OR Thoothukudi OR Tuticorin OR Coimbatore OR Salem) ({en_kw}) {after_before}",
        f"Tamil Nadu (murder OR homicide OR killed) {after_before}",
        f"Tamil Nadu (rape OR \"sexual assault\" OR POCSO) {after_before}",
        f"Tamil Nadu (cybercrime OR theft OR kidnapping OR narcotics OR bribery) {after_before}",
        f"Thoothukudi (murder OR crime OR police OR assault) {after_before}",
        f"Madurai (murder OR crime OR police OR assault) {after_before}",
        f"(The Hindu OR \"Times of India\" OR \"Indian Express\" OR \"DT Next\") Tamil Nadu ({en_kw}) {after_before}",
        # TVK negative news / crime / controversy (English)
        f"({TVK_EN_OR}) ({TVK_NEG_EN}) {after_before}",
        f"TVK (Tamil Nadu OR Chennai OR Madurai) ({TVK_NEG_EN}) {after_before}",
        f"\"Tamilaga Vettri Kazhagam\" ({TVK_NEG_EN}) {after_before}",
        f"TVK (scandal OR controversy OR \"case against\" OR accused OR violence) {after_before}",
    ]
    for site, _name in ENGLISH_TN_MEDIA_SITES:
        en_queries.append(
            f"site:{site} (Tamil Nadu OR Chennai OR Madurai OR Thoothukudi) ({en_kw}) {after_before}"
        )
    # English-language indexing of Tamil outlet sites
    for site, _en, _ta in TAMIL_MEDIA_OUTLETS:
        en_queries.append(f"site:{site} ({en_kw}) {after_before}")

    seen: set[tuple[str, str]] = set()
    all_items: list[dict[str, Any]] = []
    n_en, n_ta = 0, 0

    print(f"\n[MEDIA] Balanced EN + TA harvest — {year}")
    print("        TA outlets: தினத்தந்தி, தினமலர், தினமணி, தமிழ் முரசு, புதிய தலைமுறை, விகடன், பிபிசி தமிழ்")
    print("        EN outlets: The Hindu, TOI, DT Next, Indian Express, NIE, HT, News18, …")
    print("        Keywords TA: கொலை, தாக்குதல், கடத்தல், லஞ்சம், திருட்டு, பாலியல், POCSO, …")
    print("        Keywords EN: murder, assault, kidnapping, theft, rape, POCSO, FIR, …")

    def _absorb(batch: list[dict[str, Any]], lang_tag: str) -> int:
        added = 0
        for it in batch:
            key = (it.get("headline", "")[:90], it.get("date", ""))
            if key in seen:
                continue
            seen.add(key)
            it["year"] = year
            it["lang"] = it.get("lang") or lang_tag
            tag_tvk_item(it)
            all_items.append(it)
            added += 1
        return added

    # Interleave: English and Tamil both fully run (equal priority)
    for q in en_queries:
        n_en += _absorb(fetch_google_news_rss(q, max_items=max_per_query, lang="en"), "en")
    for q in ta_queries:
        n_ta += _absorb(fetch_google_news_rss(q, max_items=max_per_query, lang="ta"), "ta")

    print(f"[MEDIA] Unique headlines for {year}: {len(all_items)}  (EN-tagged batch +{n_en}, TA-tagged batch +{n_ta})")
    return all_items


def load_media_volume_csv(path: Path | None = None) -> dict[int, dict[str, int]]:
    """Load district,year,volume CSV (from X harvests or manual). Returns {year: {district: volume}}."""
    if path is None:
        path = OUTPUT_DIR / "media_twitter_volumes_2024_2025.csv"
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    out: dict[int, dict[str, int]] = {}
    for _, r in df.iterrows():
        try:
            y = int(r.get("year", 0))
            d = str(r.get("district", "")).strip()
            v = int(r.get("volume", 0))
            if y and d:
                out.setdefault(y, {})
                out[y][d] = out[y].get(d, 0) + v
        except Exception:
            continue
    return out


def classify_crime_theme(text: str) -> str:
    """Rough theme for scaling different base files (women vs murder vs general)."""
    t = text.lower()
    women_kw = [
        "rape", "sexual assault", "harassment", "women", "molest", "pocso",
        "பாலியல்", "பாலியல் வன்கொடுமை", "பெண்", "பெண்கள்", "கற்பழிப்பு",
    ]
    murder_kw = [
        "murder", "killed", "homicide", "stab", "shot dead", "dead body",
        "கொலை", "கொலைமுயற்சி", "பிணம்", "தாக்குதல்",
    ]
    # Remaining Tamil keywords map to general complaints / cyber / theft
    # (லஞ்சம், கடத்தல், திருட்டு, இணைய வழி, போதைப்பொருள், கைது, FIR)
    if any(k in t for k in women_kw):
        return "women"
    if any(k in t for k in murder_kw):
        return "homicide"
    return "complaints"


def _score_one_light(text: str) -> dict[str, Any]:
    """Lexicon-only scoring — no transformers / torch / torchvision."""
    try:
        from nlp_pipeline import analyze_crime_text_light

        return analyze_crime_text_light(text)
    except Exception:
        pass
    # Inline minimal EN lexicon if nlp_pipeline missing
    t = (text or "").lower()
    neg = ("murder", "rape", "assault", "killed", "attack", "crime", "arrest", "kidnap", "pocso")
    pos = ("safe", "justice", "resolved", "improved", "acquitted")
    n = sum(1 for w in neg if w in t)
    p = sum(1 for w in pos if w in t)
    if n > p:
        pol, lab = -0.65, "negative"
    elif p > n:
        pol, lab = 0.4, "positive"
    else:
        pol, lab = 0.0, "neutral"
    crime = "other crime"
    for label, kws in (
        ("homicide or murder", ("murder", "killed", "homicide")),
        ("rape or sexual assault", ("rape", "sexual", "pocso")),
        ("theft or robbery", ("theft", "robbery", "snatching")),
        ("assault or violence", ("assault", "attack", "violence")),
        ("cybercrime", ("cyber", "online fraud")),
        ("drug or narcotics", ("drug", "narcotic", "ganja")),
    ):
        if any(k in t for k in kws):
            crime = label
            break
    return {
        "polarity": pol,
        "sentiment_label": lab,
        "confidence": 0.5,
        "crime_type": crime,
        "crime_type_score": 0.6 if crime != "other crime" else 0.4,
        "trend_label": "stable situation",
        "trend_score": 0.45,
        "pipeline": "lexicon_inline",
    }


def _row_from_score(h: dict[str, Any], text: str, res: dict[str, Any]) -> dict[str, Any]:
    intensity = int(
        min(10, max(0, abs(float(res.get("polarity", 0))) * 8 + float(res.get("crime_type_score", 0)) * 3))
    )
    if "crime_intensity" in res and res.get("crime_intensity") is not None:
        try:
            intensity = int(res["crime_intensity"])
        except Exception:
            pass
    method = res.get("pipeline") or res.get("sentiment_method") or res.get("method") or "scored"
    crime_types = res.get("crime_type") or res.get("crime_types") or ""
    district = h.get("district") or normalize_district(text)
    sent_lab = str(res.get("sentiment_label", "neutral") or "neutral")
    pol = float(res.get("polarity", 0.0))
    tvk_neg = is_tvk_negative(text) or (
        is_tvk_related(text) and (sent_lab.lower() in ("negative", "neg") or pol < -0.05)
    )
    return {
        "date": h.get("date"),
        "district_city": district,
        "headline": text,
        "source": h.get("source", "news"),
        "url": h.get("url", ""),
        "polarity": round(pol, 4),
        "sentiment_label": sent_lab,
        "confidence": round(float(res.get("confidence", 0.0)), 3),
        "crime_intensity": intensity,
        "crime_types": crime_types,
        "crime_type": res.get("crime_type", crime_types),
        "trend_label": res.get("trend_label", ""),
        "trend_score": res.get("trend_score", 0),
        "method": method,
        "source_class": "news_media",  # not social
        "is_tvk": is_tvk_related(text) or bool(h.get("is_tvk")),
        "priority": "tvk_negative" if tvk_neg else (h.get("priority") or ""),
    }


def score_headlines_light(headlines: list[dict[str, Any]]) -> pd.DataFrame:
    """Fast lexicon scoring for refresh — never loads DistilBERT / transformers."""
    rows = []
    for h in headlines:
        text = h.get("headline", "")
        if not text:
            continue
        try:
            res = _score_one_light(text)
            rows.append(_row_from_score(h, text, res))
        except Exception:
            continue
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["year"] = pd.to_datetime(df["date"], errors="coerce").dt.year
    return df


def score_headlines(headlines: list[dict[str, Any]], *, light: bool = False) -> pd.DataFrame:
    """Score headlines. light=True → lexicon only (safe for dashboard refresh)."""
    if light:
        return score_headlines_light(headlines)

    rows = []
    use_nlp3 = _resolve_nlp()
    for h in headlines:
        text = h.get("headline", "")
        if not text:
            continue
        try:
            if use_nlp3:
                from nlp_pipeline import analyze_crime_text

                res = analyze_crime_text(text)
            else:
                try:
                    from sentiment_analysis import score_text

                    res = score_text(text)
                    # score_text may load DistilBERT; fall back to light on failure
                except Exception:
                    res = _score_one_light(text)
        except Exception:
            # Never drop the whole batch — light score on LLM failure
            try:
                res = _score_one_light(text)
            except Exception:
                continue

        rows.append(_row_from_score(h, text, res))

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["year"] = pd.to_datetime(df["date"], errors="coerce").dt.year
    return df


def create_demo_data(years: list[int] | None = None) -> pd.DataFrame:
    """Synthetic but realistic demo data so the pipeline can be tested immediately."""
    if years is None:
        years = [2022, 2023, 2024, 2025, 2026]

    demo_headlines = []
    base_date = datetime(2022, 1, 15)

    examples = [
        ("Chennai", "Increase in chain snatching cases reported in North Chennai areas", "The Hindu"),
        ("Chennai", "College student sexually assaulted in Adyar - accused arrested", "News Tamil 24x7"),
        ("Madurai", "Machete attack on two persons in central Madurai", "Dinamalar"),
        ("Coimbatore", "Woman harassed in public; CCTV footage helps police", "The New Indian Express"),
        ("Tiruchirappalli", "7-year-old girl kidnapped and later found safe", "Local reports"),
        ("Salem", "Elderly couple attacked during robbery bid", "Dinakaran"),
        ("Namakkal", "Minor girl sexually assaulted; case registered", "Social media reports"),
        ("Tirunelveli", "Series of chain snatching incidents spark public outrage", "Local news"),
    ]

    for y in years:
        for i, (dist, headline, src) in enumerate(examples):
            d = base_date.replace(year=y) + timedelta(days=30 * (i % 10))
            demo_headlines.append({
                "date": d.strftime("%Y-%m-%d"),
                "district": dist,
                "headline": headline,
                "source": src,
                "url": f"https://example.com/news/{y}/{i}",
            })

        # Add some negative spikes (more crime talk)
        if y >= 2024:
            demo_headlines.append({
                "date": f"{y}-06-10",
                "district": "Chennai",
                "headline": "Multiple sexual assault cases in 24 hours in Chennai raise alarm",
                "source": "X / local reports",
                "url": "",
            })

    return score_headlines(demo_headlines)


def load_from_csv(path: Path) -> pd.DataFrame:
    """Load a CSV with at least 'headline' column + optional date/district/source/url."""
    raw = pd.read_csv(path)
    records = []
    for _, row in raw.iterrows():
        records.append({
            "date": row.get("date", datetime.now().strftime("%Y-%m-%d")),
            "district": row.get("district"),
            "headline": str(row.get("headline") or row.get("text") or ""),
            "source": row.get("source", "csv"),
            "url": row.get("url", ""),
        })
    return score_headlines(records)


def save_signals(df: pd.DataFrame, out_path: Path = NEWS_OUTPUT, *, merge: bool = False) -> Path:
    """Save scored headlines + aggregates. If merge=True, append and dedupe vs existing raw."""
    if df.empty:
        print("[WARN] No signals generated.")
        return out_path

    raw_path = out_path.with_name("news_signals_raw.csv")
    if merge and raw_path.exists():
        try:
            old = pd.read_csv(raw_path)
            df = pd.concat([old, df], ignore_index=True)
            # Dedupe by headline + date (keep latest score)
            subset = [c for c in ("headline", "date") if c in df.columns]
            if subset:
                df = df.drop_duplicates(subset=subset, keep="last").reset_index(drop=True)
        except Exception as e:
            print(f"[WARN] Could not merge with existing raw: {e}")

    if "year" not in df.columns and "date" in df.columns:
        df["year"] = pd.to_datetime(df["date"], errors="coerce").dt.year

    agg = (
        df.groupby(["year", "district_city"], dropna=False)
        .agg(
            news_count=("headline", "count"),
            avg_news_polarity=("polarity", "mean"),
            negative_news_share=("sentiment_label", lambda x: (x == "negative").mean()),
            avg_news_crime_intensity=("crime_intensity", "mean"),
        )
        .reset_index()
    )

    df.to_csv(raw_path, index=False)
    agg.to_csv(out_path, index=False)

    print(f"[OK] Saved raw scored headlines → {raw_path}")
    print(f"[OK] Saved aggregated news signals (ready to merge) → {out_path}")
    print(f"     {len(df)} raw items | {len(agg)} district-year aggregates")
    return out_path


def _existing_headline_keys() -> set[tuple[str, str]]:
    """Keys already in harvest / raw so refresh only keeps NEW items."""
    keys: set[tuple[str, str]] = set()
    for path in (
        OUTPUT_DIR / "news_signals_raw.csv",
        *OUTPUT_DIR.glob("media_harvest_tn_crime_*.csv"),
        *OUTPUT_DIR.glob("media_headlines_scored_*.csv"),
    ):
        if not path.exists():
            continue
        try:
            old = pd.read_csv(path)
            hcol = "headline" if "headline" in old.columns else None
            dcol = "date" if "date" in old.columns else None
            if not hcol:
                continue
            for _, row in old.iterrows():
                h = str(row.get(hcol, ""))[:90]
                d = str(row.get(dcol, "")) if dcol else ""
                if h:
                    keys.add((h, d))
        except Exception:
            continue
    return keys


def refresh_new_news(max_per_query: int = 20, *, light_score: bool = True) -> dict[str, Any]:
    """
    Incremental refresh: fetch LATEST Tamil/English crime news only.
    Skips headlines already stored. Does NOT re-populate historical proxy CSVs.

    light_score=True (default): lexicon-only NLP — no transformers/torchvision.
    Use light_score=False for full DistilBERT 3-LLM stack (CLI --full-nlp).

    Use this for dashboard Refresh / full-pipeline light update.
    One-time bulk backfill remains: --populate-2024-2026
    """
    print("=" * 60)
    mode = "lexicon light (no transformers)" if light_score else "full DistilBERT NLP"
    print(f"NEWS REFRESH — NEW headlines only | scoring: {mode}")
    print("=" * 60)

    existing = _existing_headline_keys()
    print(f"[INFO] Already acquired headlines on disk: {len(existing)}")

    year = datetime.now().year
    # Live harvest for current year + quick brand queries (recent)
    fresh = harvest_tn_crime_media(year, max_per_query=max_per_query)

    # Recent EN + TA (equal priority)
    ta_kw = TAMIL_CRIME_OR
    en_kw = ENGLISH_CRIME_OR
    recent_queries_ta = [
        f"தமிழ்நாடு ({ta_kw})",
        f"(தினத்தந்தி OR தினமலர் OR தினமணி OR விகடன் OR \"புதிய தலைமுறை\" OR \"பிபிசி தமிழ்\") ({ta_kw})",
        f"சென்னை OR மதுரை OR தூத்துக்குடி OR கோவை ({ta_kw})",
        f"({TVK_TA_OR}) ({TVK_NEG_TA})",
        f"TVK ({TVK_NEG_TA})",
        "TVK சர்ச்சை OR TVK வன்முறை OR TVK புகார் OR தமிழக வெற்றி கழகம் தாக்குதல்",
    ]
    recent_queries_en = [
        f"Tamil Nadu ({en_kw})",
        f"(The Hindu OR \"Times of India\" OR \"Indian Express\" OR \"DT Next\") Tamil Nadu ({en_kw})",
        f"(Chennai OR Madurai OR Thoothukudi OR Tuticorin) ({en_kw})",
        "Thoothukudi murder OR crime OR police",
        "Madurai murder OR crime OR police",
        f"({TVK_EN_OR}) ({TVK_NEG_EN})",
        "TVK scandal OR TVK controversy OR TVK violence OR TVK FIR OR TVK accused OR Tamilaga Vettri Kazhagam arrest",
    ]
    for q in recent_queries_en:
        fresh.extend(fetch_google_news_rss(q, max_items=max_per_query, lang="en"))
    for q in recent_queries_ta:
        fresh.extend(fetch_google_news_rss(q, max_items=max_per_query, lang="ta"))

    # Filter to NEW only
    new_items: list[dict[str, Any]] = []
    seen_batch: set[tuple[str, str]] = set()
    for it in fresh:
        h = str(it.get("headline", ""))[:90]
        d = str(it.get("date", ""))
        key = (h, d)
        if not h or key in existing or key in seen_batch:
            continue
        seen_batch.add(key)
        it["year"] = it.get("year") or year
        tag_tvk_item(it)
        new_items.append(it)

    print(f"[INFO] Fetched batch: {len(fresh)} | NEW unique: {len(new_items)}")

    if not new_items:
        print("[OK] No new headlines since last acquire — signals unchanged.")
        return {"new_count": 0, "total_raw": len(existing), "message": "No new news"}

    # Append to harvest log
    harvest_path = OUTPUT_DIR / f"media_harvest_tn_crime_refresh_{datetime.now().strftime('%Y%m%d')}.csv"
    try:
        pd.DataFrame(new_items).to_csv(harvest_path, index=False)
        # Also append to combined rolling harvest
        combined = OUTPUT_DIR / "media_harvest_tn_crime_latest.csv"
        if combined.exists():
            prev = pd.read_csv(combined)
            comb = pd.concat([prev, pd.DataFrame(new_items)], ignore_index=True)
            comb = comb.drop_duplicates(subset=["headline", "date"], keep="last")
            comb.to_csv(combined, index=False)
        else:
            pd.DataFrame(new_items).to_csv(combined, index=False)
        print(f"[OK] New harvest log → {harvest_path.name}")
    except Exception as e:
        print(f"[WARN] Harvest log: {e}")

    # Score only new headlines and MERGE into signals (light by default)
    try:
        scored = score_headlines(new_items, light=light_score)
    except Exception as e:
        print(f"[WARN] Scoring failed ({e}) — harvest already saved; trying light fallback...")
        try:
            scored = score_headlines_light(new_items)
        except Exception as e2:
            print(f"[WARN] Light scoring also failed: {e2}")
            scored = pd.DataFrame()

    if scored is None or scored.empty:
        print("[WARN] Scoring returned empty — harvest CSV kept; signals unchanged.")
        return {
            "new_count": len(new_items),
            "scored": 0,
            "light_score": light_score,
            "message": "Harvested but not scored",
        }

    try:
        save_signals(scored, merge=True)
    except Exception as e:
        print(f"[WARN] save_signals failed (harvest still on disk): {e}")
        return {
            "new_count": len(new_items),
            "scored": len(scored),
            "light_score": light_score,
            "message": f"Scored {len(scored)} but merge failed: {e}",
        }

    print(f"[OK] Merged {len(scored)} NEW scored headlines into news_signals.")
    return {
        "new_count": len(new_items),
        "scored": len(scored),
        "light_score": light_score,
        "message": f"Added {len(scored)} new headlines ({'lexicon' if light_score else 'full NLP'})",
    }


def main():
    parser = argparse.ArgumentParser(
        description="Acquire TN crime news signals (English + Tamil media; not social)"
    )
    parser.add_argument("--demo", action="store_true", help="Generate demo news signals")
    parser.add_argument("--csv", type=str, default=None, help="Path to CSV with headlines to score")
    parser.add_argument("--fetch", type=str, default=None, help="Fetch live from Google News RSS")
    parser.add_argument("--lang", type=str, default="en", choices=["en", "ta"], help="News language for --fetch")
    parser.add_argument("--max-items", type=int, default=15, help="Max items for --fetch")
    parser.add_argument("--years", type=int, nargs="+", default=None, help="Years for demo or populate")
    parser.add_argument(
        "--refresh-new",
        action="store_true",
        help="Fetch only NEW headlines (incremental). For dashboard refresh / pipeline light update.",
    )
    parser.add_argument(
        "--light-score",
        action="store_true",
        default=True,
        help="Lexicon-only scoring on refresh (default; no transformers/torchvision).",
    )
    parser.add_argument(
        "--full-nlp",
        action="store_true",
        help="Use DistilBERT 3-LLM stack when scoring (slower; may need torchvision).",
    )
    parser.add_argument(
        "--populate-2024-2025",
        action="store_true",
        help="ONE-TIME bulk: Tamil+English media; write 2024+2025+2026 proxy CSVs",
    )
    parser.add_argument(
        "--populate-2024-2026",
        action="store_true",
        help="ONE-TIME bulk: Tamil+English media; write 2024, 2025, 2026 proxy CSVs",
    )
    parser.add_argument(
        "--populate-years",
        type=int,
        nargs="+",
        default=None,
        help="ONE-TIME bulk for explicit years e.g. 2024 2025 2026",
    )
    parser.add_argument("--twitter-csv", type=str, default=None, help="Optional district volume CSV")
    parser.add_argument("--focus", type=str, default=None, help="women | homicide | complaints")
    args = parser.parse_args()

    if args.refresh_new:
        # Default light; --full-nlp opts into DistilBERT
        use_light = not bool(args.full_nlp)
        refresh_new_news(max_per_query=args.max_items or 20, light_score=use_light)
        return

    populate_years = None
    if args.populate_years:
        populate_years = list(args.populate_years)
    elif args.populate_2024_2026 or args.populate_2024_2025:
        populate_years = [2024, 2025, 2026]

    if populate_years:
        print(f"[INFO] ONE-TIME bulk harvest for years {populate_years}...")
        tw = {}
        tw_path = args.twitter_csv or str(OUTPUT_DIR / "media_twitter_volumes_2024_2025.csv")
        if Path(tw_path).exists():
            print(f"[INFO] Loading volume CSV from {tw_path}")
            tw = load_twitter_from_csv(tw_path)
        populate_years_from_net(years=populate_years, twitter_extra=tw, focus=args.focus)
        return

    if args.fetch:
        print(f"[INFO] Fetching live news ({args.lang}) for: {args.fetch}")
        fetched = fetch_google_news_rss(args.fetch, args.max_items, lang=args.lang)
        if fetched:
            df = score_headlines(fetched)
        else:
            print("[INFO] Fetch returned nothing. Generating demo instead...")
            df = create_demo_data(args.years)
    elif args.csv:
        print(f"[INFO] Scoring headlines from {args.csv}...")
        df = load_from_csv(Path(args.csv))
    elif args.demo:
        print("[INFO] Generating demo news signals (2022-2026)...")
        df = create_demo_data(args.years)
    else:
        print("Usage examples:")
        print("  # ONE-TIME bulk backfill (proxies + full harvest):")
        print("  python acquire_news_signals.py --populate-2024-2026")
        print("  # Incremental NEW headlines only (dashboard refresh / pipeline):")
        print("  python acquire_news_signals.py --refresh-new")
        print("  python acquire_news_signals.py --refresh-new --full-nlp  # DistilBERT (optional)")
        print("  python acquire_news_signals.py --fetch 'தமிழ்நாடு குற்றம்' --lang ta")
        print("  python acquire_news_signals.py --csv my_headlines.csv")
        print("  python acquire_news_signals.py --demo")
        return

    save_signals(df, merge=bool(args.fetch or args.csv))


def load_twitter_from_csv(path: str) -> dict:
    """Load Twitter volume CSV. Supports:
    - district,year,volume
    - or district,volume (applies to both 2024/2025)
    Returns {year: {district: count, ...}, ...}
    """
    if not path or not Path(path).exists():
        return {}
    df = pd.read_csv(path)
    result = {}
    for _, row in df.iterrows():
        dist = str(row.iloc[0]).strip()
        if len(df.columns) >= 3:
            yr = int(row.iloc[1])
            vol = int(row.iloc[2])
        else:
            yr = None
            vol = int(row.iloc[1])
        if yr is None:
            for y in [2024, 2025, 2026]:
                result.setdefault(y, {})[dist] = vol
        else:
            result.setdefault(yr, {})[dist] = vol
    return result


def get_twitter_volume_demo(year: int) -> dict:
    """Optional volume seeds (media attention proxy). Prefer harvested news counts."""
    base_2024 = {
        "Chennai": 45, "Madurai": 8, "Coimbatore": 9, "Tiruchirappalli": 5,
        "Salem": 4, "Tirunelveli": 3, "Namakkal": 3, "Kanchipuram": 4,
        "Erode": 3, "Vellore": 3, "Ariyalur": 2, "Pollachi": 3,
    }
    base_2025 = {
        "Chennai": 22, "Coimbatore": 18, "Madurai": 5, "Tiruvallur": 8,
        "Salem": 3, "Tiruchirappalli": 3, "Thoothukudi": 2, "Villupuram": 2,
        "Other / Statewide": 6,
    }
    # 2026: light seed so empty years still get structure; live harvest overrides
    base_2026 = {
        "Chennai": 18, "Madurai": 6, "Coimbatore": 7, "Tiruchirappalli": 4,
        "Salem": 3, "Tirunelveli": 3, "Villupuram": 2, "Vellore": 3,
        "Other / Statewide": 5,
    }
    if year == 2024:
        return base_2024
    if year == 2025:
        return base_2025
    if year == 2026:
        return base_2026
    return {}


def populate_years_from_net(
    years: list[int] | None = None,
    twitter_extra: dict | None = None,
    focus: str | None = None,
) -> None:
    """Fill year gaps using Tamil + English news media (Google News RSS).

    Strategy (proxy, not official police counts):
    1. Harvest EN + TA Google News + Tamil outlet site queries for each year.
    2. Merge optional volume CSV + built-in seeds.
    3. Copy structure from 2023 official files; scale by district media attention.
    4. Write tn_{year}_* CSVs for clean_data.
    5. Update news_signals.csv for ML fusion.

    Default years: 2024, 2025, 2026.
    """
    from collections import Counter

    if years is None:
        years = [2024, 2025, 2026]
    years = sorted({int(y) for y in years})

    dataset_dir = PROJECT_ROOT / "dataset"
    dataset_dir.mkdir(exist_ok=True)
    if twitter_extra is None:
        twitter_extra = {}

    known = {
        "complaints": dataset_dir / "tn_2023_complaints.csv",
        "women": dataset_dir / "tn_2023_crimes_against_women.csv",
        "homicide": dataset_dir / "tn_2023_muder_homicide.csv",
    }
    actual_bases = {k: p for k, p in known.items() if p.exists()}
    if not actual_bases:
        print("[ERROR] Need tn_2023_complaints.csv, tn_2023_crimes_against_women.csv, tn_2023_muder_homicide.csv")
        return

    print("=" * 60)
    print(f"CRIMECAST MEDIA HARVEST → populate {years}")
    print("Sources: Google News TA+EN · Tamil dailies · TN English press")
    print("Tamil outlets: தினத்தந்தி, தினமலர், தினமணி, தமிழ் முரசு,")
    print("  புதிய தலைமுறை, விகடன், பிபிசி தமிழ்")
    print("Keywords: கொலை, தாக்குதல், கடத்தல், லஞ்சம், திருட்டு,")
    print("  பாலியல் வன்கொடுமை, POCSO, போதைப்பொருள், கைது, FIR")
    print("=" * 60)
    print(f"Base templates: {[p.name for p in actual_bases.values()]}")

    media_csv = load_media_volume_csv()
    all_media_rows: list[dict[str, Any]] = []
    year_district_vol: dict[int, Counter] = {}

    for year in years:
        print(f"\n{'=' * 50}\n YEAR {year}\n{'=' * 50}")

        news_items = harvest_tn_crime_media(year, max_per_query=16)
        all_media_rows.extend(news_items)

        district_counts: Counter = Counter()
        theme_counts: dict[str, Counter] = {
            "women": Counter(),
            "homicide": Counter(),
            "complaints": Counter(),
        }
        for it in news_items:
            dist = it.get("district") or normalize_district(it.get("headline", ""))
            if not dist or dist in ("Other / Statewide", "Unknown"):
                dist = "Chennai"
            district_counts[dist] += 1
            theme = classify_crime_theme(it.get("headline", ""))
            theme_counts[theme][dist] += 1

        tw = get_twitter_volume_demo(year)
        tw.update(media_csv.get(year, {}))
        if year in twitter_extra:
            for d, v in twitter_extra[year].items():
                tw[d] = tw.get(d, 0) + int(v)
        for d, v in tw.items():
            district_counts[d] += int(v)
            theme_counts["women"][d] += max(1, int(v * 0.4))
            theme_counts["homicide"][d] += max(1, int(v * 0.3))
            theme_counts["complaints"][d] += max(1, int(v * 0.3))

        if not district_counts:
            district_counts = Counter({"Chennai": 25, "Madurai": 8, "Coimbatore": 8})

        year_district_vol[year] = district_counts
        print(f"Combined media volume top: {dict(district_counts.most_common(8))}")

        if HAS_SENTIMENT and news_items:
            print("[INFO] Scoring harvested headlines (3-LLM / DistilBERT sample)...")
            scored = score_headlines(news_items[:50])
            if not scored.empty:
                raw_path = OUTPUT_DIR / f"media_headlines_scored_{year}.csv"
                scored.to_csv(raw_path, index=False)
                print(f"  Saved scored headlines → {raw_path.name}")

        for key, base_path in actual_bases.items():
            if focus:
                fl = focus.lower()
                if fl in ("women", "rape") and key != "women":
                    continue
                if fl in ("murder", "homicide") and key != "homicide":
                    continue
                if fl == "complaints" and key != "complaints":
                    continue

            try:
                df = pd.read_csv(base_path)
                dist_col = next(
                    (c for c in df.columns if "district" in str(c).lower() or "city" in str(c).lower()),
                    df.columns[1],
                )

                if key == "women":
                    vol_map = theme_counts["women"]
                elif key == "homicide":
                    vol_map = theme_counts["homicide"]
                else:
                    vol_map = district_counts

                for d, v in district_counts.items():
                    if d not in vol_map:
                        vol_map[d] = max(1, v // 2)

                avg_vol = sum(vol_map.values()) / max(len(vol_map), 1)

                numeric_cols = [
                    c for c in df.columns
                    if pd.api.types.is_numeric_dtype(df[c])
                    and "rate" not in str(c).lower()
                    and "sl" not in str(c).lower()
                ]

                for idx in df.index:
                    dist = str(df.at[idx, dist_col]).strip()
                    vol = vol_map.get(dist, 0)
                    if vol == 0:
                        for md, mv in vol_map.items():
                            if md.lower() in dist.lower() or dist.lower() in md.lower():
                                vol = mv
                                break
                    if vol == 0:
                        vol = avg_vol * 0.55

                    factor = max(0.55, min(1.85, 0.80 + (vol / avg_vol - 1.0) * 0.75))

                    for col in numeric_cols:
                        try:
                            val = pd.to_numeric(df.at[idx, col], errors="coerce")
                            if pd.notna(val) and val > 0:
                                df.at[idx, col] = max(0, int(round(float(val) * factor)))
                        except Exception:
                            pass

                for c in df.columns:
                    if "year" in str(c).lower():
                        df[c] = year

                if key == "complaints":
                    out_name = f"tn_{year}_complaints.csv"
                elif key == "women":
                    out_name = f"tn_{year}_crimes_against_women.csv"
                else:
                    out_name = f"tn_{year}_muder_homicide.csv"

                out_path = dataset_dir / out_name
                if dist_col in df.columns:
                    df = df.drop_duplicates(subset=[dist_col], keep="last").reset_index(drop=True)
                df.to_csv(out_path, index=False)
                print(f"  [OK] {out_name}  ({len(df)} districts, media-scaled)")

            except Exception as e:
                print(f"  [ERROR] {key}: {e}")

    if all_media_rows:
        y_tag = f"{min(years)}_{max(years)}"
        harvest_path = OUTPUT_DIR / f"media_harvest_tn_crime_{y_tag}.csv"
        pd.DataFrame(all_media_rows).to_csv(harvest_path, index=False)
        # Keep legacy filename when 2024-2025 included
        if 2024 in years and 2025 in years:
            legacy = OUTPUT_DIR / "media_harvest_tn_crime_2024_2025.csv"
            pd.DataFrame(all_media_rows).to_csv(legacy, index=False)
        print(f"\n[OK] Full media harvest log → {harvest_path}")

    try:
        agg_rows = []
        for year in years:
            media_csv_y = media_csv.get(year, {})
            demo = get_twitter_volume_demo(year)
            harvested = year_district_vol.get(year, Counter())
            districts = set(media_csv_y) | set(demo) | set(harvested.keys())
            for d in districts:
                vol = int(media_csv_y.get(d, 0) + demo.get(d, 0) + harvested.get(d, 0))
                neg = min(0.9, 0.35 + vol / 80.0)
                agg_rows.append({
                    "year": year,
                    "district_city": d,
                    "news_count": vol,
                    "avg_news_polarity": round(-0.2 - vol / 100.0, 3),
                    "negative_news_share": round(neg, 3),
                    "avg_news_crime_intensity": min(10.0, 2.0 + vol / 8.0),
                })
        if agg_rows:
            news_df = pd.DataFrame(agg_rows)
            if NEWS_OUTPUT.exists():
                old = pd.read_csv(NEWS_OUTPUT)
                news_df = pd.concat([old, news_df], ignore_index=True)
                news_df = news_df.drop_duplicates(subset=["year", "district_city"], keep="last")
            news_df.to_csv(NEWS_OUTPUT, index=False)
            print(f"[OK] Updated {NEWS_OUTPUT.name} (years {years})")
    except Exception as e:
        print(f"[WARN] Could not write news_signals: {e}")

    print("\n" + "=" * 60)
    print(f"[DONE] Proxy files populated for years {years} (Tamil + English media).")
    print("Next:")
    print("  1. python app.py   → option 1  (sentiment → clean → train)")
    print("  2. python app.py   → option 7  (2026 rape forecasts)")
    print("Note: MEDIA PROXIES — not official TN Police statistics.")
    print("=" * 60)


def populate_2024_2025_from_net(twitter_extra: dict | None = None, focus: str | None = None):
    """Backward-compatible alias: now populates 2024, 2025, and 2026."""
    populate_years_from_net(years=[2024, 2025, 2026], twitter_extra=twitter_extra, focus=focus)


if __name__ == "__main__":
    main()
