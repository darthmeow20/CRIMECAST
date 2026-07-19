# -*- coding: utf-8 -*-
"""
TN district entity resolution (Tier-3).
Maps free-text / headlines → canonical district names; drops junk tokens.
"""
from __future__ import annotations

import re
from typing import Iterable

# Display names used across CRIMECAST
TN_DISTRICTS: list[str] = [
    "Ariyalur", "Chengalpattu", "Chennai", "Coimbatore", "Cuddalore", "Dharmapuri",
    "Dindigul", "Erode", "Kallakurichi", "Kanchipuram", "Kanyakumari", "Karur",
    "Krishnagiri", "Madurai", "Mayiladuthurai", "Nagapattinam", "Namakkal",
    "Nilgiris", "Perambalur", "Pudukkottai", "Ramnathapuram", "Ranipet",
    "Salem", "Sivaganga", "Tenkasi", "Thanjavur", "Theni", "Thoothukudi",
    "Tiruchirappalli", "Tirunelveli", "Tiruppattur", "Tiruppur", "Tiruvallur",
    "Tiruvannamalai", "Thiruvarur", "Vellore", "Villupuram", "Virudhunagar",
    # Avadi / Tambaram are Greater Chennai city units — roll into Chennai (not separate map districts)
    "Madurai City", "Coimbatore City", "Salem City",
    "Trichy City", "Tiruppur City", "Thirunelveli City",
]

# Official 38 TN districts (maps / scoreboard / sentiment — no city units)
TN38: list[str] = [
    "Ariyalur", "Chengalpattu", "Chennai", "Coimbatore", "Cuddalore", "Dharmapuri",
    "Dindigul", "Erode", "Kallakurichi", "Kanchipuram", "Kanniyakumari", "Karur",
    "Krishnagiri", "Madurai", "Mayiladuthurai", "Nagapattinam", "Namakkal",
    "The Nilgiris", "Perambalur", "Pudukkottai", "Ramanathapuram", "Ranipet",
    "Salem", "Sivaganga", "Tenkasi", "Thanjavur", "Theni", "Thoothukkudi",
    "Tiruchirappalli", "Tirunelveli", "Tirupathur", "Tiruppur", "Tiruvallur",
    "Tiruvannamalai", "Tiruvarur", "Vellore", "Viluppuram", "Virudhunagar",
]
# City / metro units → parent among the 38
CITY_TO_DISTRICT: dict[str, str] = {
    "avadi": "Chennai",
    "tambaram": "Chennai",
    "tamabram": "Chennai",
    "thambaram": "Chennai",
    "avadi city": "Chennai",
    "tambaram city": "Chennai",
    "chennai city": "Chennai",
    "greater chennai": "Chennai",
    "gcc": "Chennai",
    "madras": "Chennai",
    "madurai city": "Madurai",
    "coimbatore city": "Coimbatore",
    "salem city": "Salem",
    "trichy city": "Tiruchirappalli",
    "tiruchirappalli city": "Tiruchirappalli",
    "tiruppur city": "Tiruppur",
    "tirupur city": "Tiruppur",
    "thirunelveli city": "Tirunelveli",
    "tirunelveli city": "Tirunelveli",
    "thoothukudi city": "Thoothukkudi",
    "vellore city": "Vellore",
    "erode city": "Erode",
}

# Alias → canonical (always one of TN38 where possible)
_ALIASES: dict[str, str] = {
    "chennai": "Chennai",
    "madras": "Chennai",
    "chennai city": "Chennai",
    "greater chennai": "Chennai",
    "avadi": "Chennai",
    "tambaram": "Chennai",
    "tamabram": "Chennai",
    "thambaram": "Chennai",
    "avadi city": "Chennai",
    "tambaram city": "Chennai",
    "madurai": "Madurai",
    "madurai city": "Madurai",
    "coimbatore": "Coimbatore",
    "kovai": "Coimbatore",
    "coimbatore city": "Coimbatore",
    "trichy": "Tiruchirappalli",
    "tiruchi": "Tiruchirappalli",
    "tiruchirappalli": "Tiruchirappalli",
    "tiruchirapalli": "Tiruchirappalli",
    "trichy city": "Tiruchirappalli",
    "salem": "Salem",
    "salem city": "Salem",
    "tirunelveli": "Tirunelveli",
    "thirunelveli": "Tirunelveli",
    "nellai": "Tirunelveli",
    "thirunelveli city": "Tirunelveli",
    "tirunelveli city": "Tirunelveli",
    "thoothukudi": "Thoothukkudi",
    "thoothukkudi": "Thoothukkudi",
    "tuticorin": "Thoothukkudi",
    "erode": "Erode",
    "erode city": "Erode",
    "vellore": "Vellore",
    "vellore city": "Vellore",
    "namakkal": "Namakkal",
    "krishnagiri": "Krishnagiri",
    "dharmapuri": "Dharmapuri",
    "karur": "Karur",
    "dindigul": "Dindigul",
    "thanjavur": "Thanjavur",
    "tanjore": "Thanjavur",
    "tiruppur": "Tiruppur",
    "tirupur": "Tiruppur",
    "tiruppur city": "Tiruppur",
    "kanchipuram": "Kanchipuram",
    "kancheepuram": "Kanchipuram",
    "chengalpattu": "Chengalpattu",
    "villupuram": "Viluppuram",
    "viluppuram": "Viluppuram",
    "cuddalore": "Cuddalore",
    "nagapattinam": "Nagapattinam",
    "mayiladuthurai": "Mayiladuthurai",
    "ariyalur": "Ariyalur",
    "perambalur": "Perambalur",
    "pudukkottai": "Pudukkottai",
    "pudukottai": "Pudukkottai",
    "sivaganga": "Sivaganga",
    "sivagangai": "Sivaganga",
    "ramanathapuram": "Ramanathapuram",
    "ramnathapuram": "Ramanathapuram",
    "ramnad": "Ramanathapuram",
    "virudhunagar": "Virudhunagar",
    "theni": "Theni",
    "tenkasi": "Tenkasi",
    "kanyakumari": "Kanniyakumari",
    "kanniyakumari": "Kanniyakumari",
    "nagercoil": "Kanniyakumari",
    "tiruvannamalai": "Tiruvannamalai",
    "thiruvannamalai": "Tiruvannamalai",
    "tiruvallur": "Tiruvallur",
    "thiruvallur": "Tiruvallur",
    "ranipet": "Ranipet",
    "tirupattur": "Tirupathur",
    "tiruppattur": "Tirupathur",
    "tirupathur": "Tirupathur",
    "nilgiris": "The Nilgiris",
    "the nilgiris": "The Nilgiris",
    "ooty": "The Nilgiris",
    "udhagamandalam": "The Nilgiris",
    "kallakurichi": "Kallakurichi",
    "thiruvarur": "Tiruvarur",
    "tiruvarur": "Tiruvarur",
    # Tamil script aliases (common)
    "சென்னை": "Chennai",
    "ஆவடி": "Chennai",
    "தாம்பரம்": "Chennai",
    "மதுரை": "Madurai",
    "கோவை": "Coimbatore",
    "கோயம்புத்தூர்": "Coimbatore",
    "சேலம்": "Salem",
    "திருச்சி": "Tiruchirappalli",
    "தூத்துக்குடி": "Thoothukkudi",
    "திருநெல்வேலி": "Tirunelveli",
    "வேலூர்": "Vellore",
    "ஈரோடு": "Erode",
    "தஞ்சாவூர்": "Thanjavur",
    "விழுப்புரம்": "Viluppuram",
}

_JUNK = {
    "india", "tamil nadu", "tn", "other", "statewide", "unknown", "quick",
    "killed", "teenage", "courier", "pushpa", "dinamani", "dmk", "telangana",
    "taramani", "poonamallee", "periyapalayam", "police", "crime", "news",
    "hindu", "times", "express", "arrest", "case", "court", "high",
}

# Approximate mid-year projected population (lakhs) for TN districts / cities.
# Used when SCRB/ML population is missing or zero — college prototype estimates
# (aligned roughly with Census 2011 → 2020s growth; not official live stats).
TN_POPULATION_EST_LAKHS: dict[str, float] = {
    "chennai": 72.0,
    "coimbatore": 35.0,
    "madurai": 31.0,
    "tiruchirappalli": 28.0,
    "salem": 35.0,
    "tirunelveli": 31.0,
    "tiruppur": 25.0,
    "erode": 23.0,
    "vellore": 22.0,
    "thanjavur": 24.0,
    "thoothukudi": 18.0,
    "thoothukkudi": 18.0,
    "dindigul": 22.0,
    "villupuram": 35.0,
    "viluppuram": 35.0,
    "cuddalore": 26.0,
    "kanchipuram": 22.0,
    "kancheepuram": 22.0,
    "chengalpattu": 26.0,
    "tiruvallur": 38.0,
    "thiruvallur": 38.0,
    "tiruvannamalai": 25.0,
    "thiruvannamalai": 25.0,
    "namakkal": 18.0,
    "karur": 11.0,
    "nagapattinam": 16.0,
    "thiruvarur": 13.0,
    "tiruvarur": 13.0,
    "pudukkottai": 16.0,
    "ramanathapuram": 14.0,
    "ramnathapuram": 14.0,
    "sivaganga": 14.0,
    "virudhunagar": 20.0,
    "theni": 13.0,
    "kanyakumari": 19.0,
    "kanniyakumari": 19.0,
    "dharmapuri": 15.0,
    "krishnagiri": 19.0,
    "nilgiris": 8.0,
    "the nilgiris": 8.0,
    "ariyalur": 8.0,
    "perambalur": 6.0,
    "tenkasi": 14.0,
    "kallakurichi": 14.0,
    "ranipet": 12.0,
    "tirupathur": 12.0,
    "tiruppattur": 12.0,
    "mayiladuthurai": 9.0,
    # city units (if not rolled up)
    "avadi": 8.0,
    "tambaram": 7.0,
    "madurai city": 15.0,
    "coimbatore city": 16.0,
    "salem city": 9.0,
    "trichy city": 10.0,
    "tiruppur city": 9.0,
    "thirunelveli city": 5.0,
}


def _norm_key(s: str) -> str:
    s = str(s).strip().lower()
    s = re.sub(r"[^a-z0-9\u0b80-\u0bff\s]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def parent_district(name: str) -> str:
    """
    Roll city units into parent district among the 38.
    Madurai City → Madurai, Avadi/Tambaram → Chennai, etc.
    """
    if not name or not str(name).strip():
        return str(name or "")
    raw = str(name).strip()
    key = _norm_key(raw)
    # Strip trailing " city"
    if key.endswith(" city"):
        base = key[: -len(" city")].strip()
        if base in CITY_TO_DISTRICT:
            return CITY_TO_DISTRICT[base]
        if base in _ALIASES:
            return _ALIASES[base]
    if key in CITY_TO_DISTRICT:
        return CITY_TO_DISTRICT[key]
    if key in _ALIASES:
        return _ALIASES[key]
    # Exact TN38 match (case-insensitive)
    for d in TN38:
        if _norm_key(d) == key:
            return d
    # Known legacy display names
    legacy = {
        "avadi": "Chennai",
        "tambaram": "Chennai",
        "madurai city": "Madurai",
        "coimbatore city": "Coimbatore",
        "salem city": "Salem",
        "trichy city": "Tiruchirappalli",
        "tiruppur city": "Tiruppur",
        "thirunelveli city": "Tirunelveli",
        "nilgiris": "The Nilgiris",
        "kanyakumari": "Kanniyakumari",
        "thoothukudi": "Thoothukkudi",
        "villupuram": "Viluppuram",
        "ramnathapuram": "Ramanathapuram",
        "tiruppattur": "Tirupathur",
    }
    if key in legacy:
        return legacy[key]
    return raw


def to_tn38(name: str, default: str | None = None) -> str | None:
    """Map any label → one of the 38 TN districts, or default/None if unknown."""
    if not name:
        return default
    p = parent_district(str(name))
    pk = _norm_key(p)
    for d in TN38:
        if _norm_key(d) == pk:
            return d
    if pk in _ALIASES:
        a = _ALIASES[pk]
        for d in TN38:
            if _norm_key(d) == _norm_key(a):
                return d
    # fuzzy start
    for d in TN38:
        dk = _norm_key(d)
        if len(pk) >= 5 and (dk.startswith(pk) or pk.startswith(dk)):
            return d
    return default


def estimate_population_lakhs(district_name: str) -> float | None:
    """Return estimated population in lakhs for a district name, or None."""
    if not district_name:
        return None
    key = _norm_key(str(district_name))
    if key in TN_POPULATION_EST_LAKHS:
        return float(TN_POPULATION_EST_LAKHS[key])
    parent = parent_district(str(district_name))
    pk = _norm_key(parent)
    if pk in TN_POPULATION_EST_LAKHS:
        return float(TN_POPULATION_EST_LAKHS[pk])
    for k, v in TN_POPULATION_EST_LAKHS.items():
        if len(k) >= 5 and (key.startswith(k) or k.startswith(key)):
            return float(v)
    return None


def fill_population_lakhs_series(names, existing=None):
    """
    Fill missing/zero population with estimates.
    Returns list of floats. Default mid-TN ~15 lakh if unknown.
    """
    import math

    try:
        name_list = list(names)
    except Exception:
        name_list = [names]
    out = []
    for i, name in enumerate(name_list):
        val = None
        if existing is not None:
            try:
                val = existing.iloc[i] if hasattr(existing, "iloc") else existing[i]
            except Exception:
                val = None
        try:
            if val is None or (isinstance(val, float) and math.isnan(val)):
                f = float("nan")
            else:
                f = float(val)
                if math.isnan(f):
                    f = float("nan")
        except Exception:
            f = float("nan")
        if math.isnan(f) or f <= 0.05:
            canon = to_tn38(str(name), default=None) or str(name)
            est = estimate_population_lakhs(canon)
            if est is None:
                est = estimate_population_lakhs(str(name))
            out.append(float(est) if est is not None else 15.0)
        else:
            out.append(float(f))
    return out


def resolve_district(text: str, default: str = "Other / Statewide") -> str:
    """Map free text (headline or token) to a TN district name."""
    if not text or not str(text).strip():
        return default
    raw = str(text).strip()
    key = _norm_key(raw)

    if key in _JUNK or len(key) < 3:
        # still try embed match below
        pass
    if key in _ALIASES:
        return parent_district(_ALIASES[key])

    # Exact district name
    for d in TN_DISTRICTS:
        if _norm_key(d) == key:
            return parent_district(d)

    # Substring match longest alias first
    for alias in sorted(_ALIASES.keys(), key=len, reverse=True):
        if len(alias) >= 4 and alias in key:
            return parent_district(_ALIASES[alias])

    # Title-case token fallback only if not junk
    for word in re.findall(r"[A-Za-z\u0b80-\u0bff]{4,}", raw):
        wk = _norm_key(word)
        if wk in _JUNK:
            continue
        if wk in _ALIASES:
            return parent_district(_ALIASES[wk])
        for d in TN_DISTRICTS:
            if _norm_key(d).startswith(wk) or wk in _norm_key(d):
                return parent_district(d)

    return default


def is_valid_district(name: str) -> bool:
    if not name:
        return False
    k = _norm_key(name)
    if k in _JUNK or "other" in k or "statewide" in k:
        return False
    if name in TN_DISTRICTS or k in _ALIASES:
        return True
    resolved = resolve_district(name, default="")
    return bool(resolved) and resolved != "Other / Statewide"


def filter_district_series(names: Iterable[str]) -> list[str]:
    out = []
    for n in names:
        r = resolve_district(str(n), default="")
        if r and r != "Other / Statewide":
            out.append(r)
    return out
