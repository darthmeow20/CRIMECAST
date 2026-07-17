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
        "chengalpattu": "chengalpattu",
        "chengalpettu": "chengalpattu",
        "chengalpet": "chengalpattu",
        "kancheepuram": "kanchipuram",
        "kanchipuram": "kanchipuram",
        "kancipuram": "kanchipuram",
    }
    return aliases.get(s, s)


_GEOJSON_MEM: dict[str, Any] | None = None


def ensure_tn_geojson() -> dict[str, Any] | None:
    """Download/cache TN district GeoJSON; return parsed dict or None (in-memory cached)."""
    global _GEOJSON_MEM
    if _GEOJSON_MEM is not None:
        return _GEOJSON_MEM

    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    if GEOJSON_PATH.exists() and GEOJSON_PATH.stat().st_size > 1000:
        try:
            _GEOJSON_MEM = json.loads(GEOJSON_PATH.read_text(encoding="utf-8"))
            return _GEOJSON_MEM
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
            _GEOJSON_MEM = json.loads(data.decode("utf-8"))
            return _GEOJSON_MEM
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


_MEDIA_FILL_CACHE: pd.Series | None = None
_MEDIA_FILL_MTIME: float = -1.0


def load_media_fill_series() -> pd.Series:
    """
    District → proxy intensity from news / media volume files.
    Used to fill null or zero values so every district paints on the map.
    Cached in-process; only reloads when harvest mtime changes.
    """
    global _MEDIA_FILL_CACHE, _MEDIA_FILL_MTIME
    out = PROJECT_ROOT / "model_outputs"
    # Prefer single latest harvest (avoid scanning many large CSVs — was very slow)
    candidates = [
        out / "media_harvest_tn_crime_latest.csv",
        out / "news_signals.csv",
    ]
    latest_path = None
    latest_m = -1.0
    for p in candidates:
        if p.exists():
            m = p.stat().st_mtime
            if m > latest_m:
                latest_m = m
                latest_path = p
    if _MEDIA_FILL_CACHE is not None and latest_m == _MEDIA_FILL_MTIME:
        return _MEDIA_FILL_CACHE

    volumes: dict[str, float] = {}
    if latest_path is not None:
        try:
            m = pd.read_csv(latest_path)
            if "district_city" in m.columns and "news_count" in m.columns:
                g = m.groupby(m["district_city"].map(_normalize_name))["news_count"].sum()
                for k, v in g.items():
                    volumes[str(k)] = float(v)
            elif "district" in m.columns or "district_city" in m.columns:
                col = "district_city" if "district_city" in m.columns else "district"
                g = m.groupby(m[col].map(_normalize_name)).size()
                for k, v in g.items():
                    volumes[str(k)] = float(v)
        except Exception:
            pass

    if not volumes:
        _MEDIA_FILL_CACHE = pd.Series(dtype=float)
        _MEDIA_FILL_MTIME = latest_m
        return _MEDIA_FILL_CACHE
    s = pd.Series(volumes, dtype=float)
    if s.max() > 0:
        s = (s / s.max()) * max(float(s.max()), 5.0)
    _MEDIA_FILL_CACHE = s
    _MEDIA_FILL_MTIME = latest_m
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
        # Skip expensive coastline/land layers
        showcountries=False,
        showcoastlines=False,
        showland=False,
        showocean=False,
        showlakes=False,
        showrivers=False,
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#d1d5db",
        margin=dict(l=0, r=0, t=48, b=0),
        height=480,
        coloraxis_colorbar=dict(title=colorbar_title, thickness=12),
        # Faster client render
        uirevision="tn-map",
    )
    return fig


# Distinct colours for A / B comparison selection (plot_tn_compare_districts defined at end of file)
COMPARE_PALETTE = ["#ef4444", "#3b82f6", "#22c55e", "#f59e0b", "#a855f7"]
OTHER_DISTRICT_COLOR = "#2a2a32"


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


# ---------------------------------------------------------------------------
# Compare / carved-out district maps
# ---------------------------------------------------------------------------
if "COMPARE_PALETTE" not in globals():
    COMPARE_PALETTE = ["#ef4444", "#3b82f6", "#22c55e", "#f59e0b", "#a855f7"]
if "OTHER_DISTRICT_COLOR" not in globals():
    OTHER_DISTRICT_COLOR = "#2a2a32"


def _annotate_geojson_norms(geojson: dict[str, Any]) -> str:
    """Write district_norm on every feature; return property name key used."""
    prop_key = _feature_name_key(geojson)
    for feat in geojson.get("features", []):
        props = feat.setdefault("properties", {})
        raw = str(props.get(prop_key, ""))
        props["district_norm"] = _normalize_name(raw)
        props["district_display"] = raw
    return prop_key


def _norm_matches_pick(norm: str, pick_norm: str) -> bool:
    if not norm or not pick_norm:
        return False
    if norm == pick_norm:
        return True
    # avoid over-matching short stems (e.g. "tiru")
    if len(pick_norm) >= 5 and (norm.startswith(pick_norm) or pick_norm.startswith(norm)):
        return True
    return False


def _resolve_pick_norms(picks: list[str], geojson: dict[str, Any]) -> dict[str, str]:
    """
    Map user district label → geojson district_norm (best match).
    Returns {geo_norm: display_label}.
    """
    all_norms = {
        str((f.get("properties") or {}).get("district_norm", ""))
        for f in geojson.get("features", [])
    }
    all_norms.discard("")
    out: dict[str, str] = {}
    for d in picks:
        pn = _normalize_name(d)
        hit = None
        if pn in all_norms:
            hit = pn
        else:
            for n in all_norms:
                if _norm_matches_pick(n, pn):
                    hit = n
                    break
        if hit:
            out[hit] = d
    return out


def carve_geojson_districts(
    geojson: dict[str, Any],
    district_norms: set[str] | list[str],
) -> dict[str, Any] | None:
    """Return a FeatureCollection with ONLY the requested district polygons."""
    want = set(district_norms)
    if not want:
        return None
    feats = []
    for feat in geojson.get("features", []):
        props = feat.get("properties") or {}
        n = str(props.get("district_norm", ""))
        if n in want or any(_norm_matches_pick(n, w) for w in want):
            feats.append(feat)
    if not feats:
        return None
    return {"type": "FeatureCollection", "features": feats}


def _metric_for_norm(
    df: pd.DataFrame | None,
    value_col: str | None,
    name_col: str,
    geo_norm: str,
    display: str,
) -> float | None:
    if df is None or getattr(df, "empty", True) or not value_col or value_col not in df.columns:
        return None
    work = df.copy()
    ncol = name_col if name_col in work.columns else (
        "district_city" if "district_city" in work.columns else (
            "district" if "district" in work.columns else None
        )
    )
    if not ncol:
        return None
    work["_n"] = work[ncol].map(_normalize_name)
    m = work[work["_n"].map(lambda x: _norm_matches_pick(str(x), geo_norm))]
    if m.empty:
        m = work[work[ncol].astype(str).str.casefold().str.contains(
            display.casefold()[:6], na=False
        )]
    if m.empty:
        return None
    try:
        return float(pd.to_numeric(m[value_col], errors="coerce").mean())
    except Exception:
        return None


def plot_district_carved_out(
    district: str,
    *,
    color: str = "#ef4444",
    letter: str | None = None,  # unused; kept for call-site compatibility
    df: pd.DataFrame | None = None,
    value_col: str | None = None,
    name_col: str = "district",
    title: str | None = None,
    height: int = 380,
) -> go.Figure | None:
    """
    Carve ONE district out of TN and draw it alone (zoomed polygon).
    Side-by-side comparison uses district name only (no A/B labels).
    """
    name = str(district or "").strip()
    if not name:
        return None
    geojson = ensure_tn_geojson()
    if geojson is None:
        return None
    _annotate_geojson_norms(geojson)
    resolved = _resolve_pick_norms([name], geojson)
    if not resolved:
        return None
    geo_norm, display = next(iter(resolved.items()))
    carved = carve_geojson_districts(geojson, {geo_norm})
    if carved is None:
        return None

    val = _metric_for_norm(df, value_col, name_col, geo_norm, display)
    val_txt = f"{val:.2f}" if val is not None else "—"
    role = display  # district name only
    data = pd.DataFrame(
        [{
            "district_norm": geo_norm,
            "district_label": display,
            "role": role,
            "value": val if val is not None else 1.0,
            "metric_display": val_txt,
        }]
    )

    fig = px.choropleth(
        data,
        geojson=carved,
        locations="district_norm",
        featureidkey="properties.district_norm",
        color="role",
        hover_name="district_label",
        hover_data={"role": True, "metric_display": True, "district_norm": False, "value": False},
        color_discrete_map={role: color},
        title=title or display,
    )
    fig.update_geos(
        fitbounds="locations",
        visible=False,
        bgcolor="rgba(0,0,0,0)",
        projection_type="mercator",
        showcountries=False,
        showcoastlines=False,
        showland=False,
        showocean=False,
        showlakes=False,
        showrivers=False,
        # padding so polygon isn't edge-clipped
        lataxis_range=None,
        lonaxis_range=None,
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#d1d5db",
        margin=dict(l=4, r=4, t=48, b=4),
        height=height,
        showlegend=False,
        uirevision=f"carve-{geo_norm}",
        annotations=[
            dict(
                text=f"<b>{display}</b><br><span style='font-size:12px;color:#9ca3af'>"
                     f"{value_col or 'district'} · {val_txt}</span>",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.02,
                showarrow=False,
                font=dict(size=14, color="#e5e7eb"),
                align="center",
            )
        ],
    )
    fig.update_traces(
        marker_line_width=2.2,
        marker_line_color="#f8fafc",
        marker_opacity=0.92,
    )
    return fig


def plot_tn_compare_districts(
    districts,
    df=None,
    value_col=None,
    name_col="district",
    title=None,
    mode: str = "carved",
):
    """
    Head-to-head district map.

    mode:
      - "carved"  (default): ONLY selected districts drawn, zoomed to them (carved out of TN)
      - "context": full TN with selection highlighted, others dim gray
    """
    picks = [str(d).strip() for d in (districts or []) if str(d).strip()]
    if not picks:
        return None

    geojson = ensure_tn_geojson()
    if geojson is None:
        return None
    _annotate_geojson_norms(geojson)

    resolved = _resolve_pick_norms(picks, geojson)
    if not resolved:
        return None

    # Preserve user order of picks → roles
    ordered_norms: list[tuple[str, str, int]] = []  # geo_norm, display, index
    used = set()
    for i, d in enumerate(picks):
        pn = _normalize_name(d)
        hit = None
        for gn, label in resolved.items():
            if gn in used:
                continue
            if _norm_matches_pick(gn, pn) or label.casefold() == d.casefold():
                hit = (gn, d if label else d, i)
                break
        if hit is None:
            # fallback any unresolved entry matching this pick
            for gn, label in resolved.items():
                if gn not in used and _norm_matches_pick(gn, pn):
                    hit = (gn, d, i)
                    break
        if hit:
            ordered_norms.append(hit)
            used.add(hit[0])

    if not ordered_norms:
        return None

    # Role = district name only (no A/B prefixes)
    role_for_norm = {gn: label for gn, label, i in ordered_norms}
    pick_norms = {gn for gn, _, _ in ordered_norms}

    mode = (mode or "carved").lower().strip()
    if mode == "carved":
        draw_geo = carve_geojson_districts(geojson, pick_norms)
        if draw_geo is None:
            return None
        rows = []
        for gn, label, i in ordered_norms:
            val = _metric_for_norm(df, value_col, name_col, gn, label)
            rows.append({
                "district_norm": gn,
                "district_label": label,
                "role": role_for_norm[gn],
                "value": val if val is not None else float(i + 1),
                "metric_display": f"{val:.2f}" if val is not None else "—",
            })
        data = pd.DataFrame(rows)
        show_other = False
    else:
        draw_geo = geojson
        # all districts for context mode
        all_rows = []
        for feat in geojson.get("features", []):
            props = feat.get("properties") or {}
            gn = str(props.get("district_norm", ""))
            label = str(props.get("district_display", gn))
            if gn in role_for_norm:
                role = role_for_norm[gn]
                val = _metric_for_norm(df, value_col, name_col, gn, label)
            else:
                role = "Other TN districts"
                val = None
            all_rows.append({
                "district_norm": gn,
                "district_label": label if gn not in role_for_norm else role_for_norm[gn].split(" · ", 1)[-1],
                "role": role,
                "value": val if val is not None else 0.0,
                "metric_display": f"{val:.2f}" if val is not None else "—",
            })
        data = pd.DataFrame(all_rows)
        show_other = True

    if data is None or data.empty:
        return None

    color_map = {}
    if show_other:
        color_map["Other TN districts"] = OTHER_DISTRICT_COLOR
    for gn, label, i in ordered_norms:
        color_map[role_for_norm[gn]] = COMPARE_PALETTE[i % len(COMPARE_PALETTE)]

    map_title = title or (
        " vs ".join(label for _, label, _ in ordered_norms)
        + (" · carved out" if mode == "carved" else " · in TN")
    )
    hover_cols = {"role": True, "district_norm": False, "metric_display": True, "value": False}
    cat_order = [role_for_norm[gn] for gn, _, _ in ordered_norms]
    if show_other:
        cat_order = cat_order + ["Other TN districts"]

    fig = px.choropleth(
        data,
        geojson=draw_geo,
        locations="district_norm",
        featureidkey="properties.district_norm",
        color="role",
        hover_name="district_label",
        hover_data=hover_cols,
        color_discrete_map=color_map,
        category_orders={"role": cat_order},
        title=map_title,
    )
    fig.update_geos(
        fitbounds="locations",
        visible=False,
        bgcolor="rgba(0,0,0,0)",
        projection_type="mercator",
        showcountries=False,
        showcoastlines=False,
        showland=False,
        showocean=False,
        showlakes=False,
        showrivers=False,
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#d1d5db",
        margin=dict(l=0, r=0, t=52, b=0),
        height=520 if mode == "carved" else 480,
        legend_title_text="Selection",
        uirevision=f"tn-compare-{mode}",
    )
    # Strong outline so carved polygons read as separate shapes
    line_w = 2.0 if mode == "carved" else 0.7
    line_c = "#f8fafc" if mode == "carved" else "#6b7280"
    fig.update_traces(marker_line_width=line_w, marker_line_color=line_c, marker_opacity=0.93)
    return fig
