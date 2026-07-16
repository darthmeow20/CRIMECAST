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
    "Avadi", "Tambaram", "Madurai City", "Coimbatore City", "Salem City",
    "Trichy City", "Tiruppur City", "Thirunelveli City",
]

# Alias → canonical
_ALIASES: dict[str, str] = {
    "chennai": "Chennai",
    "madras": "Chennai",
    "madurai": "Madurai",
    "madurai city": "Madurai City",
    "coimbatore": "Coimbatore",
    "kovai": "Coimbatore",
    "coimbatore city": "Coimbatore City",
    "trichy": "Tiruchirappalli",
    "tiruchi": "Tiruchirappalli",
    "tiruchirappalli": "Tiruchirappalli",
    "tiruchirapalli": "Tiruchirappalli",
    "trichy city": "Trichy City",
    "salem": "Salem",
    "salem city": "Salem City",
    "tirunelveli": "Tirunelveli",
    "thirunelveli": "Tirunelveli",
    "nellai": "Tirunelveli",
    "thirunelveli city": "Thirunelveli City",
    "thoothukudi": "Thoothukudi",
    "thoothukkudi": "Thoothukudi",
    "tuticorin": "Thoothukudi",
    "erode": "Erode",
    "vellore": "Vellore",
    "namakkal": "Namakkal",
    "krishnagiri": "Krishnagiri",
    "dharmapuri": "Dharmapuri",
    "karur": "Karur",
    "dindigul": "Dindigul",
    "thanjavur": "Thanjavur",
    "tanjore": "Thanjavur",
    "tiruppur": "Tiruppur",
    "tirupur": "Tiruppur",
    "tiruppur city": "Tiruppur City",
    "kanchipuram": "Kanchipuram",
    "kancheepuram": "Kanchipuram",
    "chengalpattu": "Chengalpattu",
    "villupuram": "Villupuram",
    "viluppuram": "Villupuram",
    "cuddalore": "Cuddalore",
    "nagapattinam": "Nagapattinam",
    "mayiladuthurai": "Mayiladuthurai",
    "ariyalur": "Ariyalur",
    "perambalur": "Perambalur",
    "pudukkottai": "Pudukkottai",
    "pudukottai": "Pudukkottai",
    "sivaganga": "Sivaganga",
    "sivagangai": "Sivaganga",
    "ramanathapuram": "Ramnathapuram",
    "ramnathapuram": "Ramnathapuram",
    "ramnad": "Ramnathapuram",
    "virudhunagar": "Virudhunagar",
    "theni": "Theni",
    "tenkasi": "Tenkasi",
    "kanyakumari": "Kanyakumari",
    "kanniyakumari": "Kanyakumari",
    "nagercoil": "Kanyakumari",
    "tiruvannamalai": "Tiruvannamalai",
    "thiruvannamalai": "Tiruvannamalai",
    "tiruvallur": "Tiruvallur",
    "thiruvallur": "Tiruvallur",
    "ranipet": "Ranipet",
    "tirupattur": "Tiruppattur",
    "tiruppattur": "Tiruppattur",
    "nilgiris": "Nilgiris",
    "the nilgiris": "Nilgiris",
    "ooty": "Nilgiris",
    "udhagamandalam": "Nilgiris",
    "kallakurichi": "Kallakurichi",
    "thiruvarur": "Thiruvarur",
    "tiruvarur": "Thiruvarur",
    "avadi": "Avadi",
    "tambaram": "Tambaram",
    # Tamil script aliases (common)
    "சென்னை": "Chennai",
    "மதுரை": "Madurai",
    "கோவை": "Coimbatore",
    "கோயம்புத்தூர்": "Coimbatore",
    "சேலம்": "Salem",
    "திருச்சி": "Tiruchirappalli",
    "தூத்துக்குடி": "Thoothukudi",
    "திருநெல்வேலி": "Tirunelveli",
    "வேலூர்": "Vellore",
    "ஈரோடு": "Erode",
    "தஞ்சாவூர்": "Thanjavur",
    "விழுப்புரம்": "Villupuram",
}

_JUNK = {
    "india", "tamil nadu", "tn", "other", "statewide", "unknown", "quick",
    "killed", "teenage", "courier", "pushpa", "dinamani", "dmk", "telangana",
    "taramani", "poonamallee", "periyapalayam", "police", "crime", "news",
    "hindu", "times", "express", "arrest", "case", "court", "high",
}


def _norm_key(s: str) -> str:
    s = str(s).strip().lower()
    s = re.sub(r"[^a-z0-9\u0b80-\u0bff\s]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


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
        return _ALIASES[key]

    # Exact district name
    for d in TN_DISTRICTS:
        if _norm_key(d) == key:
            return d

    # Substring match longest alias first
    for alias in sorted(_ALIASES.keys(), key=len, reverse=True):
        if len(alias) >= 4 and alias in key:
            return _ALIASES[alias]

    # Title-case token fallback only if not junk
    for word in re.findall(r"[A-Za-z\u0b80-\u0bff]{4,}", raw):
        wk = _norm_key(word)
        if wk in _JUNK:
            continue
        if wk in _ALIASES:
            return _ALIASES[wk]
        for d in TN_DISTRICTS:
            if _norm_key(d).startswith(wk) or wk in _norm_key(d):
                return d

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
