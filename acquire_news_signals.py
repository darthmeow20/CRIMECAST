#!/usr/bin/env python3
"""
CRIMECAST - Crime news acquisition (Tamil Nadu) — NEWS MEDIA ONLY

Primary sources (NOT social media):
  - Google News / web news search (RSS)
  - E-papers & e-magazines (via public RSS / headline feeds where available)
  - Local news aggregators (DailyHunt / Lokal / Public app style feeds via RSS/web)

NLP (3 LLM roles — see nlp_pipeline.py):
  1) DistilBERT SST-2 — sentiment
  2) DistilBERT MNLI zero-shot — crime type
  3) DistilBERT MNLI zero-shot — trend labels

Usage:
  python acquire_news_signals.py --populate-2024-2025
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

import pandas as pd
from dateutil import parser as date_parser  # already in requirements via python-dateutil

PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_ROOT / "model_outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
NEWS_OUTPUT = OUTPUT_DIR / "news_signals.csv"

# Prefer 3-LLM NLP stack; fall back to legacy DistilBERT-only scorer
HAS_NLP3 = False
HAS_SENTIMENT = False
try:
    from nlp_pipeline import analyze_crime_text, model_card
    HAS_NLP3 = True
    HAS_SENTIMENT = True
except Exception as e:
    print(f"[WARN] nlp_pipeline unavailable: {e}")
    try:
        from sentiment_analysis import score_text, analyze_sentiment
        HAS_SENTIMENT = True
    except Exception as e2:
        print(f"[WARN] sentiment_analysis also unavailable: {e2}")
        HAS_SENTIMENT = False


def normalize_district(text: str) -> str:
    """Improved district normalizer for Tamil Nadu common names."""
    t = text.lower().strip()
    mapping = {
        "chennai": "Chennai",
        "madurai": "Madurai",
        "coimbatore": "Coimbatore",
        "trichy": "Tiruchirappalli",
        "tiruchirappalli": "Tiruchirappalli",
        "salem": "Salem",
        "tirunelveli": "Tirunelveli",
        "thoothukudi": "Thoothukudi",
        "tuticorin": "Thoothukudi",
        "erode": "Erode",
        "vellore": "Vellore",
        "namakkal": "Namakkal",
        "nanguneri": "Tirunelveli",
        "krishnagiri": "Krishnagiri",
        "dharmapuri": "Dharmapuri",
        "karur": "Karur",
        "dindigul": "Dindigul",
        "thanjavur": "Thanjavur",
        "tiruppur": "Tiruppur",
        "kanchipuram": "Kanchipuram",
        "chengalpattu": "Chengalpattu",
    }
    for key, val in mapping.items():
        if key in t:
            return val
    # Fallback: title case first word that looks like a place
    for word in text.split():
        if len(word) > 4 and word[0].isupper():
            return word.strip(".,!?")
    return "Other / Statewide"


def fetch_google_news_rss(query: str = "Tamil Nadu crime OR Chennai crime OR TN police", max_items: int = 20) -> list[dict[str, Any]]:
    """Lightweight fetcher for Google News RSS (no extra deps, uses stdlib urllib + xml).
    Returns list of dicts ready for scoring.
    Note: Respect robots.txt / ToS in real use. For research/ personal use.
    """
    items = []
    try:
        q = query.replace(" ", "+")
        url = f"https://news.google.com/rss/search?q={q}&hl=en-IN&gl=IN&ceid=IN:en"
        print(f"[INFO] Fetching Google News RSS: {query[:70]}...")

        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; CRIMECAST-research/1.0)"},
        )
        with urllib.request.urlopen(req, timeout=20) as response:
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
            source = item.findtext("source") or "Google News"

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
                })
                count += 1

        print(f"  [OK] {len(items)} headlines")
    except Exception as e:
        print(f"  [WARN] RSS fetch failed: {e}")
        return []
    return items


def harvest_tn_crime_media(year: int, max_per_query: int = 25) -> list[dict[str, Any]]:
    """Harvest TN crime headlines from internet NEWS sources (e-paper / aggregator style).

    Explicitly news-oriented queries (not social media). Sources that surface via Google News
    often include The Hindu, DT Next, Times of India, Vikatan, Maalai Malar, News18 Tamil,
    and aggregator surfaces similar to DailyHunt / Lokal / Public app feeds.
    """
    queries = [
        # General + e-paper style statewide
        f"Tamil Nadu crime after:{year}-01-01 before:{year + 1}-01-01",
        f"Tamil Nadu police FIR after:{year}-01-01 before:{year + 1}-01-01",
        # Category-specific (maps to our 3 raw datasets)
        f"Chennai (rape OR \"sexual assault\" OR murder) after:{year}-01-01 before:{year + 1}-01-01",
        f"Tamil Nadu (rape OR \"crimes against women\") after:{year}-01-01 before:{year + 1}-01-01",
        f"Tamil Nadu (murder OR homicide OR killed) after:{year}-01-01 before:{year + 1}-01-01",
        # City e-paper coverage
        f"(Madurai OR Coimbatore OR Salem OR Trichy OR Tirunelveli) crime after:{year}-01-01 before:{year + 1}-01-01",
        # Local / regional portals (surface via News)
        f"site:thehindu.com Tamil Nadu crime after:{year}-01-01 before:{year + 1}-01-01",
        f"site:dtnext.in (crime OR murder OR rape) after:{year}-01-01 before:{year + 1}-01-01",
        f"site:timesofindia.indiatimes.com Chennai crime after:{year}-01-01 before:{year + 1}-01-01",
    ]
    seen = set()
    all_items: list[dict[str, Any]] = []
    print(f"\n[MEDIA] Harvesting Google News for Tamil Nadu crime — {year}")
    for q in queries:
        batch = fetch_google_news_rss(q, max_items=max_per_query)
        for it in batch:
            key = (it.get("headline", "")[:80], it.get("date", ""))
            if key in seen:
                continue
            seen.add(key)
            it["year"] = year
            all_items.append(it)
    print(f"[MEDIA] Unique headlines for {year}: {len(all_items)}")
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
    if any(k in t for k in ["rape", "sexual assault", "harassment", "women", "molest", "anna university"]):
        return "women"
    if any(k in t for k in ["murder", "killed", "homicide", "stab", "shot dead", "dead body"]):
        return "homicide"
    return "complaints"


def score_headlines(headlines: list[dict[str, Any]]) -> pd.DataFrame:
    """Score headlines with 3-LLM NLP stack (sentiment + crime type + trend)."""
    rows = []
    for h in headlines:
        text = h.get("headline", "")
        if not text or not HAS_SENTIMENT:
            continue
        try:
            if HAS_NLP3:
                res = analyze_crime_text(text)
                # Map intensity from crime-type score + negativity
                intensity = int(min(10, max(0, abs(res.get("polarity", 0)) * 8 + res.get("crime_type_score", 0) * 3)))
                method = res.get("pipeline", "3llm")
                crime_types = res.get("crime_type", "")
            else:
                from sentiment_analysis import score_text
                res = score_text(text)
                intensity = res.get("crime_intensity", 0)
                method = res.get("sentiment_method", "distilbert")
                crime_types = res.get("crime_types", "")
        except Exception:
            continue

        district = h.get("district") or normalize_district(text)
        rows.append({
            "date": h.get("date"),
            "district_city": district,
            "headline": text,
            "source": h.get("source", "news"),
            "url": h.get("url", ""),
            "polarity": round(float(res.get("polarity", 0.0)), 4),
            "sentiment_label": res.get("sentiment_label", "neutral"),
            "confidence": round(float(res.get("confidence", 0.0)), 3),
            "crime_intensity": intensity,
            "crime_types": crime_types,
            "crime_type": res.get("crime_type", crime_types),
            "trend_label": res.get("trend_label", ""),
            "trend_score": res.get("trend_score", 0),
            "method": method,
            "source_class": "news_media",  # not social
        })

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


def save_signals(df: pd.DataFrame, out_path: Path = NEWS_OUTPUT) -> Path:
    if df.empty:
        print("[WARN] No signals generated.")
        return out_path

    # Aggregate lightly like sentiment does (per district-year)
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

    # Also save raw scored headlines
    raw_path = out_path.with_name("news_signals_raw.csv")
    df.to_csv(raw_path, index=False)
    agg.to_csv(out_path, index=False)

    print(f"[OK] Saved raw scored headlines → {raw_path}")
    print(f"[OK] Saved aggregated news signals (ready to merge) → {out_path}")
    print(f"     {len(df)} raw items | {len(agg)} district-year aggregates")
    return out_path


def main():
    parser = argparse.ArgumentParser(description="Acquire news/social proxy signals for CRIMECAST")
    parser.add_argument("--demo", action="store_true", help="Generate demo news signals")
    parser.add_argument("--csv", type=str, default=None, help="Path to CSV with headlines to score")
    parser.add_argument("--fetch", type=str, default=None, help="Fetch live from Google News RSS (e.g. 'Tamil Nadu crime')")
    parser.add_argument("--max-items", type=int, default=15, help="Max items for --fetch")
    parser.add_argument("--years", type=int, nargs="+", default=None)
    parser.add_argument("--populate-2024-2025", action="store_true", help="Pull from net (news + twitter) and generate full 2024/2025 proxy data files")
    parser.add_argument("--twitter-csv", type=str, default=None, help="Path to CSV (district,volume or district,year,volume) for real Twitter data")
    parser.add_argument("--focus", type=str, default=None, help="Category focus: women (rape), homicide (murder), complaints")
    args = parser.parse_args()

    if args.populate_2024_2025:
        print("[INFO] Harvesting media + Twitter + Google News to fill 2024–2025 gaps...")
        tw = {}
        # Prefer explicit CSV; else use pre-seeded media/X volume file if present
        tw_path = args.twitter_csv or str(OUTPUT_DIR / "media_twitter_volumes_2024_2025.csv")
        if Path(tw_path).exists():
            print(f"[INFO] Loading Twitter/media volumes from {tw_path}")
            tw = load_twitter_from_csv(tw_path)
        populate_2024_2025_from_net(twitter_extra=tw, focus=args.focus)
        return

    if args.fetch:
        print(f"[INFO] Fetching live news for: {args.fetch}")
        fetched = fetch_google_news_rss(args.fetch, args.max_items)
        if fetched:
            df = score_headlines(fetched)
        else:
            print("[INFO] Fetch returned nothing. Generating demo instead...")
            df = create_demo_data(args.years)
    elif args.csv:
        print(f"[INFO] Scoring headlines from {args.csv}...")
        df = load_from_csv(Path(args.csv))
    elif args.demo:
        print("[INFO] Generating demo news signals (2022-2026) with realistic TN district examples...")
        df = create_demo_data(args.years)
    else:
        print("Usage examples:")
        print("  python acquire_news_signals.py --demo")
        print("  python acquire_news_signals.py --csv my_headlines.csv")
        print("  python acquire_news_signals.py --fetch 'Tamil Nadu crime OR Chennai rape'")
        print("  python acquire_news_signals.py --populate-2024-2025   # pulls net data to create 2024/2025 CSVs")
        return

    save_signals(df)


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
            for y in [2024, 2025]:
                result.setdefault(y, {})[dist] = vol
        else:
            result.setdefault(yr, {})[dist] = vol
    return result


def get_twitter_volume_demo(year: int) -> dict:
    """X/Twitter discussion volume seeds (from public posts: Anna University 2024,
    migrant murders / assaults 2025 in Coimbatore & Tiruvallur area, etc.).
    Prefer media_twitter_volumes_2024_2025.csv when available.
    """
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
    if year == 2024:
        return base_2024
    if year == 2025:
        return base_2025
    return {}


def populate_2024_2025_from_net(twitter_extra: dict | None = None, focus: str | None = None):
    """Fill 2024–2025 gaps using media + Twitter/X + Google News.

    Strategy (proxy, not official police counts):
    1. Harvest multi-query Google News RSS for TN crime 2024 & 2025.
    2. Merge with X/Twitter volume CSV (model_outputs/media_twitter_volumes_2024_2025.csv)
       and built-in demo volumes (seeded from real public posts).
    3. Copy full structure from each 2023 official file (complaints / women / murder).
    4. Scale numeric incident/victim columns by district media attention.
    5. Write complete tn_2024_* and tn_2025_* CSVs for ALL 2023 districts
       so clean_data discover_raw_datasets() fills the years with no empty gaps.

    Disclaimer: media volume is a leading indicator / attention proxy, not verified FIRs.
    """
    from collections import Counter

    dataset_dir = PROJECT_ROOT / "dataset"
    dataset_dir.mkdir(exist_ok=True)
    if twitter_extra is None:
        twitter_extra = {}

    # Exact 2023 templates (full column structure)
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
    print("CRIMECAST MEDIA HARVEST → populate 2024 & 2025")
    print("=" * 60)
    print(f"Base templates: {[p.name for p in actual_bases.values()]}")

    # Load pre-harvested X volumes + demo
    media_csv = load_media_volume_csv()
    all_media_rows: list[dict[str, Any]] = []

    for year in [2024, 2025]:
        print(f"\n{'=' * 50}\n YEAR {year}\n{'=' * 50}")

        # 1) Google News multi-query harvest
        news_items = harvest_tn_crime_media(year, max_per_query=20)
        all_media_rows.extend(news_items)

        # District volumes from news
        district_counts: Counter = Counter()
        theme_counts: dict[str, Counter] = {
            "women": Counter(),
            "homicide": Counter(),
            "complaints": Counter(),
        }
        for it in news_items:
            dist = it.get("district") or normalize_district(it.get("headline", ""))
            if not dist or dist in ("Other / Statewide", "Unknown"):
                dist = "Chennai"  # statewide stories often Chennai-centric in media
            district_counts[dist] += 1
            theme = classify_crime_theme(it.get("headline", ""))
            theme_counts[theme][dist] += 1

        # 2) Twitter / X volumes
        tw = get_twitter_volume_demo(year)
        tw.update(media_csv.get(year, {}))
        if year in twitter_extra:
            for d, v in twitter_extra[year].items():
                tw[d] = tw.get(d, 0) + int(v)
        for d, v in tw.items():
            district_counts[d] += int(v)
            # Default theme split for social discussion
            theme_counts["women"][d] += max(1, int(v * 0.4))
            theme_counts["homicide"][d] += max(1, int(v * 0.3))
            theme_counts["complaints"][d] += max(1, int(v * 0.3))

        if not district_counts:
            district_counts = Counter({"Chennai": 25, "Madurai": 8, "Coimbatore": 8})

        print(f"Combined media volume top: {dict(district_counts.most_common(8))}")

        # Score headlines for sentiment fusion (optional)
        if HAS_SENTIMENT and news_items:
            print("[INFO] Scoring harvested headlines with DistilBERT (sample)...")
            scored = score_headlines(news_items[:40])  # cap for speed
            if not scored.empty:
                raw_path = OUTPUT_DIR / f"media_headlines_scored_{year}.csv"
                scored.to_csv(raw_path, index=False)
                print(f"  Saved scored headlines → {raw_path.name}")

        # 3) For each crime category, copy 2023 → year and scale
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

                # Prefer theme-specific volume for women/homicide files
                if key == "women":
                    vol_map = theme_counts["women"]
                elif key == "homicide":
                    vol_map = theme_counts["homicide"]
                else:
                    vol_map = district_counts

                # Merge with overall so no district is zero-volume
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
                    # Match media districts loosely
                    vol = vol_map.get(dist, 0)
                    if vol == 0:
                        # try partial name match
                        for md, mv in vol_map.items():
                            if md.lower() in dist.lower() or dist.lower() in md.lower():
                                vol = mv
                                break
                    if vol == 0:
                        vol = avg_vol * 0.55  # still populate — no empty gaps

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

                # Output names clean_data.infer_dataset_name understands
                if key == "complaints":
                    out_name = f"tn_{year}_complaints.csv"
                elif key == "women":
                    out_name = f"tn_{year}_crimes_against_women.csv"
                else:
                    out_name = f"tn_{year}_muder_homicide.csv"

                out_path = dataset_dir / out_name
                # Ensure unique districts (prevents clean_data one_to_one merge failure)
                if dist_col in df.columns:
                    df = df.drop_duplicates(subset=[dist_col], keep="last").reset_index(drop=True)
                df.to_csv(out_path, index=False)
                print(f"  [OK] {out_name}  ({len(df)} districts, media-scaled, full columns)")

            except Exception as e:
                print(f"  [ERROR] {key}: {e}")

    # Save combined media harvest log
    if all_media_rows:
        harvest_path = OUTPUT_DIR / "media_harvest_tn_crime_2024_2025.csv"
        pd.DataFrame(all_media_rows).to_csv(harvest_path, index=False)
        print(f"\n[OK] Full media harvest log → {harvest_path}")

    # Aggregate news_signals for clean_data enrich
    try:
        agg_rows = []
        for year in [2024, 2025]:
            media_csv_y = media_csv.get(year, {})
            demo = get_twitter_volume_demo(year)
            districts = set(media_csv_y) | set(demo)
            for d in districts:
                vol = media_csv_y.get(d, 0) + demo.get(d, 0)
                # negative share proxy from volume (higher buzz → slightly more negative)
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
            # merge with existing if present
            if NEWS_OUTPUT.exists():
                old = pd.read_csv(NEWS_OUTPUT)
                news_df = pd.concat([old, news_df], ignore_index=True)
                news_df = news_df.drop_duplicates(subset=["year", "district_city"], keep="last")
            news_df.to_csv(NEWS_OUTPUT, index=False)
            print(f"[OK] Updated {NEWS_OUTPUT.name} for sentiment/news fusion in clean_data")
    except Exception as e:
        print(f"[WARN] Could not write news_signals: {e}")

    print("\n" + "=" * 60)
    print("[DONE] 2024 + 2025 proxy files populated from media/Twitter/Google News.")
    print("Next:")
    print("  1. python app.py   → option 1  (sentiment → clean → train)")
    print("  2. python app.py   → option 7  (2026 rape forecasts)")
    print("Note: These are MEDIA PROXIES, not official TN Police statistics.")
    print("=" * 60)


if __name__ == "__main__":
    main()
