"""
Tamil Nadu district map + heatmap helpers for CRIMECAST dashboard.
Uses public district GeoJSON (cached under assets/).
"""

from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

PROJECT_ROOT = Path(__file__).resolve().parent
ASSETS_DIR = PROJECT_ROOT / "assets"
GEOJSON_PATH = ASSETS_DIR / "tamil_nadu_districts.geojson"

# Public TN district boundaries (GeoJSON)
GEOJSON_URLS = [
    "https://cdn.jsdelivr.net/gh/udit-001/india-maps-data@ef25ebc/geojson/states/tamil-nadu.geojson",
    "https://raw.githubusercontent.com/udit-001/india-maps-data/ef25ebc/geojson/states/tamil-nadu.geojson",
]


def _normalize_name(name: str) -> str:
    s = str(name).strip().lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    # Common aliases
    aliases = {
        "chennai city": "chennai",
        "madurai city": "madurai",
        "coimbatore city": "coimbatore",
        "salem city": "salem",
        "tirunelveli city": "tirunelveli",
        "thirunelveli": "tirunelveli",
        "thirunelveli city": "tirunelveli",
        "trichy": "tiruchirappalli",
        "trichy city": "tiruchirappalli",
        "tiruchirapalli": "tiruchirappalli",
        "tiruchchirappalli": "tiruchirappalli",
        "thoothukudi": "thoothukkudi",
        "tuticorin": "thoothukkudi",
        "kanyakumari": "kanniyakumari",
        "kanniyakumari": "kanniyakumari",
        "sivagangai": "sivaganga",
        "pudukottai": "pudukkottai",
        "ramnathapuram": "ramanathapuram",
        "ramanathapuram": "ramanathapuram",
        "tiruvallur": "thiruvallur",
        "thiruvallur": "thiruvallur",
        "tiruvannamalai": "thiruvannamalai",
        "thiruvannamalai": "thiruvannamalai",
        "villupuram": "viluppuram",
        "viluppuram": "viluppuram",
        "nilgiris": "the nilgiris",
        "the nilgiris": "the nilgiris",
        "tiruppur": "tiruppur",
        "tirupur": "tiruppur",
    }
    return aliases.get(s, s)


def ensure_tn_geojson() -> dict[str, Any] | None:
    """Download/cache TN district GeoJSON; return parsed dict or None."""
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    if GEOJSON_PATH.exists() and GEOJSON_PATH.stat().st_size > 1000:
        try:
            return json.loads(GEOJSON_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass

    for url in GEOJSON_URLS:
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "CRIMECAST/1.0 (research)"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
            GEOJSON_PATH.write_bytes(data)
            return json.loads(data.decode("utf-8"))
        except Exception as e:
            print(f"[tn_map] GeoJSON download failed ({url}): {e}")
    return None


def _feature_name_key(geojson: dict) -> str:
    """Detect property key used for district name in GeoJSON."""
    feats = geojson.get("features") or []
    if not feats:
        return "district"
    props = feats[0].get("properties") or {}
    for key in (
        "district",
        "DISTRICT",
        "District",
        "dtname",
        "DT_NAME",
        "name",
        "NAME",
        "NAME_2",
        "stname",
    ):
        if key in props:
            return key
    # first string prop
    for k, v in props.items():
        if isinstance(v, str) and len(v) > 2:
            return k
    return list(props.keys())[0] if props else "district"


# Standard TN districts (display names) — ensure map never drops "zero crime" places
TN_DISTRICT_CANONICAL = [
    "Ariyalur", "Chengalpattu", "Chennai", "Coimbatore", "Cuddalore", "Dharmapuri",
    "Dindigul", "Erode", "Kallakurichi", "Kanchipuram", "Kanniyakumari", "Karur",
    "Krishnagiri", "Madurai", "Mayiladuthurai", "Nagapattinam", "Namakkal",
    "The Nilgiris", "Perambalur", "Pudukkottai", "Ramanathapuram", "Ranipet",
    "Salem", "Sivaganga", "Tenkasi", "Thanjavur", "Theni", "Thoothukkudi",
    "Tiruchirappalli", "Tirunelveli", "Tirupathur", "Tiruppur", "Tiruvallur",
    "Tiruvannamalai", "Tiruvarur", "Vellore", "Viluppuram", "Virudhunagar",
]


def load_media_fill_series() -> pd.Series:
    """
    District → proxy intensity from news / media volume files.
    Used to fill null or zero values so every district paints on the map.
    """
    volumes: dict[str, float] = {}
    out = PROJECT_ROOT / "model_outputs"
    candidates = [
        out / "media_harvest_tn_crime_latest.csv",
        *sorted(out.glob("media_harvest_tn_crime_*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)[:3],
        out / "news_signals.csv",
        out / "media_twitter_volumes_2024_2025.csv",
        out / "media_harvest_tn_crime_2024_2025.csv",
    ]
    # de-dupe paths while preserving order
    seen_p: set[str] = set()
    uniq: list[Path] = []
    for p in candidates:
        k = str(p.resolve()) if p.exists() else str(p)
        if k not in seen_p:
            seen_p.add(k)
            uniq.append(p)
    candidates = uniq
    for path in candidates:
        if not path.exists():
            continue
        try:
            m = pd.read_csv(path)
        except Exception:
            continue
        # news_signals: news_count or negative_news_share
        if "district_city" in m.columns and "news_count" in m.columns:
            g = m.groupby(m["district_city"].map(_normalize_name))["news_count"].sum()
            for k, v in g.items():
                volumes[k] = volumes.get(k, 0) + float(v)
        elif "district" in m.columns and "volume" in m.columns:
            g = m.groupby(m["district"].map(_normalize_name))["volume"].sum()
            for k, v in g.items():
                volumes[k] = volumes.get(k, 0) + float(v)
        elif "district" in m.columns or "district_city" in m.columns:
            col = "district_city" if "district_city" in m.columns else "district"
            g = m.groupby(m[col].map(_normalize_name)).size()
            for k, v in g.items():
                volumes[k] = volumes.get(k, 0) + float(v)
        elif "headline" in m.columns:
            # count mentions of district names in headlines
            for d in TN_DISTRICT_CANONICAL:
                n = m["headline"].astype(str).str.lower().str.contains(
                    re.escape(d.lower().split()[0]), na=False
                ).sum()
                if n:
                    key = _normalize_name(d)
                    volumes[key] = volumes.get(key, 0) + float(n)

    if not volumes:
        return pd.Series(dtype=float)
    s = pd.Series(volumes, dtype=float)
    # Normalize media volume to a mild 0–max scale (proxy intensity)
    if s.max() > 0:
        s = (s / s.max()) * max(s.max(), 5.0)
    return s


def prepare_map_dataframe(
    df: pd.DataFrame,
    value_col: str,
    name_col: str = "district",
    fill_nulls_from_media: bool = True,
    geojson: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Aggregate values by district; fill missing/zero districts from news/media proxies."""
    work = df.copy() if df is not None and not df.empty else pd.DataFrame()
    if not work.empty:
        if name_col not in work.columns:
            if "district_city" in work.columns:
                name_col = "district_city"
            else:
                work = pd.DataFrame()

    rows = []
    if not work.empty and value_col in work.columns:
        w = work[[name_col, value_col]].copy()
        w[value_col] = pd.to_numeric(w[value_col], errors="coerce")
        w["district_norm"] = w[name_col].map(_normalize_name)
        w["district_label"] = w[name_col].astype(str).str.strip()
        agg = (
            w.groupby("district_norm", as_index=False)
            .agg(value=(value_col, "mean"), district_label=("district_label", "first"))
        )
        rows = agg.to_dict("records")

    data = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["district_norm", "value", "district_label"])

    # Full district list from geojson + canonical list
    all_norms: dict[str, str] = {}
    for d in TN_DISTRICT_CANONICAL:
        all_norms[_normalize_name(d)] = d
    if geojson:
        prop_key = _feature_name_key(geojson)
        for feat in geojson.get("features", []):
            props = feat.get("properties") or {}
            raw = str(props.get(prop_key, "")).strip()
            if raw:
                all_norms[_normalize_name(raw)] = raw

    media = load_media_fill_series() if fill_nulls_from_media else pd.Series(dtype=float)
    # Baseline so zeros still show on map (tiny floor from media or small constant)
    media_mean = float(media.mean()) if len(media) else 1.0
    if media_mean <= 0:
        media_mean = 1.0

    existing = set(data["district_norm"].tolist()) if not data.empty else set()
    filled = []
    for norm, label in all_norms.items():
        if norm in existing:
            row = data.loc[data["district_norm"] == norm].iloc[0]
            val = float(row["value"]) if pd.notna(row["value"]) else np.nan
            if pd.isna(val) or val == 0:
                # Zero / null → populate from news & media
                mval = float(media.get(norm, media_mean * 0.35))
                if mval <= 0:
                    mval = media_mean * 0.25
                filled.append({
                    "district_norm": norm,
                    "district_label": label,
                    "value": mval,
                    "value_source": "media_fill",
                })
            else:
                filled.append({
                    "district_norm": norm,
                    "district_label": str(row["district_label"]),
                    "value": val,
                    "value_source": "data",
                })
        else:
            mval = float(media.get(norm, media_mean * 0.3))
            if mval <= 0:
                mval = media_mean * 0.2
            filled.append({
                "district_norm": norm,
                "district_label": label,
                "value": mval,
                "value_source": "media_fill",
            })

    out = pd.DataFrame(filled)
    return out


# White → light blue → deep blue (clear low→high differentiation)
HEAT_WHITE_BLUE = [
    "#ffffff",
    "#e0f2fe",
    "#bae6fd",
    "#7dd3fc",
    "#38bdf8",
    "#0ea5e9",
    "#0284c7",
    "#0369a1",
    "#075985",
    "#0c4a6e",
]

# Plotly sequential colorscale pairs for heatmap matrix
HEAT_WHITE_BLUE_PLOTLY = [
    [0.0, "#ffffff"],
    [0.15, "#e0f2fe"],
    [0.35, "#7dd3fc"],
    [0.55, "#0ea5e9"],
    [0.75, "#0369a1"],
    [1.0, "#0c4a6e"],
]


def plot_tn_choropleth(
    df: pd.DataFrame,
    value_col: str,
    name_col: str = "district",
    title: str = "Tamil Nadu — District Heat Map",
    fill_nulls_from_media: bool = True,
    color_scale: list | str | None = None,
    colorbar_title: str = "Intensity",
) -> go.Figure | None:
    """Choropleth heat map of ALL TN districts (zeros/nulls filled from news/media).

    Default colour scale: white (low) → blue (high) for clear differentiation.
    """
    geojson = ensure_tn_geojson()
    if geojson is None:
        return None

    prop_key = _feature_name_key(geojson)
    for feat in geojson.get("features", []):
        props = feat.setdefault("properties", {})
        raw = str(props.get(prop_key, ""))
        props["district_norm"] = _normalize_name(raw)
        props["district_display"] = raw

    data = prepare_map_dataframe(
        df, value_col, name_col,
        fill_nulls_from_media=fill_nulls_from_media,
        geojson=geojson,
    )
    if data.empty:
        return None

    n_fill = int((data["value_source"] == "media_fill").sum()) if "value_source" in data.columns else 0
    map_title = title
    if n_fill:
        map_title = f"{title}  ·  {n_fill} districts filled from news/media"

    scale = color_scale if color_scale is not None else HEAT_WHITE_BLUE

    fig = px.choropleth(
        data,
        geojson=geojson,
        locations="district_norm",
        featureidkey="properties.district_norm",
        color="value",
        hover_name="district_label",
        hover_data={"value": ":.2f", "value_source": True, "district_norm": False},
        color_continuous_scale=scale,
        title=map_title,
    )
    fig.update_geos(
        fitbounds="locations",
        visible=False,
        bgcolor="rgba(0,0,0,0)",
        projection_type="mercator",
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#d1d5db",
        margin=dict(l=0, r=0, t=48, b=0),
        height=560,
        coloraxis_colorbar=dict(title=colorbar_title, thickness=12),
    )
    return fig


def plot_district_heatmap_matrix(
    df: pd.DataFrame,
    value_cols: list[str] | None = None,
    name_col: str = "district_city",
    title: str = "District × Metric Heatmap",
    top_n: int = 25,
) -> go.Figure | None:
    """
    Classic heatmap: rows = districts, columns = metrics (numeric).
    Good fallback + second view beside the map.
    """
    if df.empty:
        return None
    if name_col not in df.columns:
        if "district" in df.columns:
            name_col = "district"
        else:
            return None

    work = df.copy()
    # Latest year if present
    if "year" in work.columns:
        work = work.sort_values("year").groupby(name_col, as_index=False).tail(1)

    num_cols = work.select_dtypes(include=[np.number]).columns.tolist()
    num_cols = [c for c in num_cols if c not in ("year", "year_centered", "is_latest_year", "rank")]
    if value_cols:
        num_cols = [c for c in value_cols if c in work.columns]
    if not num_cols:
        return None

    # Pick top metrics by variance, limit columns for readability
    if len(num_cols) > 8 and not value_cols:
        variances = work[num_cols].var().sort_values(ascending=False)
        num_cols = variances.head(6).index.tolist()

    # Top districts by first metric
    sort_col = num_cols[0]
    work = work.nlargest(min(top_n, len(work)), sort_col)

    matrix = work.set_index(name_col)[num_cols]
    # z-score per column for comparable heat colors
    z = (matrix - matrix.mean()) / matrix.std(ddof=0).replace(0, 1)
    z = z.fillna(0)

    fig = go.Figure(
        data=go.Heatmap(
            z=z.values,
            x=[c.replace("_", " ")[:28] for c in z.columns],
            y=list(z.index),
            colorscale=HEAT_WHITE_BLUE_PLOTLY,
            colorbar=dict(title="z-score"),
            hovertemplate="District: %{y}<br>%{x}: %{z:.2f}<extra></extra>",
        )
    )
    fig.update_layout(
        title=title,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#0e0e12",
        font_color="#d1d5db",
        height=max(400, 22 * len(z)),
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis=dict(side="top", tickangle=-35),
        yaxis=dict(autorange="reversed"),
    )
    return fig
