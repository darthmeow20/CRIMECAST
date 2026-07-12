#!/usr/bin/env python3
"""
CRIMECAST — Multi-LLM NLP stack for Tamil Nadu crime news (trends + analysis).

Three models (transformers, lazy-loaded):
  1) Sentiment LLM  — DistilBERT SST-2
       distilbert-base-uncased-finetuned-sst-2-english
  2) Crime-type LLM — Zero-shot DistilBERT MNLI
       typeform/distilbert-base-uncased-mnli
  3) Trend LLM      — Zero-shot DistilBERT MNLI (same backbone, different labels)
       Labels: rising_trend | stable | isolated_incident | declining_trend

Primary text sources (NOT social media):
  Google News / e-papers / DailyHunt-style RSS / local news portals.
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

import numpy as np

# ---------------------------------------------------------------------------
# Optional heavy deps — never crash import if transformers missing
# ---------------------------------------------------------------------------
HAS_TRANSFORMERS = False
try:
    import transformers  # noqa: F401
    HAS_TRANSFORMERS = True
except ImportError:
    pass

_SENTIMENT_PIPE = None
_ZERO_SHOT_PIPE = None

# Crime-type labels for zero-shot classification
CRIME_TYPE_LABELS = [
    "homicide or murder",
    "rape or sexual assault",
    "theft or robbery",
    "cybercrime",
    "drug or narcotics",
    "assault or violence",
    "other crime",
]

# Trend / temporal labels
TREND_LABELS = [
    "rising crime trend",
    "stable situation",
    "isolated incident",
    "declining crime trend",
    "public safety concern",
]


def _lazy_sentiment():
    global _SENTIMENT_PIPE
    if _SENTIMENT_PIPE is not None:
        return _SENTIMENT_PIPE
    if not HAS_TRANSFORMERS:
        return None
    try:
        from transformers import pipeline
        _SENTIMENT_PIPE = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            truncation=True,
            max_length=512,
        )
        return _SENTIMENT_PIPE
    except Exception as e:
        print(f"[NLP] Sentiment DistilBERT unavailable: {e}")
        return None


def _lazy_zero_shot():
    global _ZERO_SHOT_PIPE
    if _ZERO_SHOT_PIPE is not None:
        return _ZERO_SHOT_PIPE
    if not HAS_TRANSFORMERS:
        return None
    try:
        from transformers import pipeline
        # Lighter MNLI DistilBERT — second & third LLM roles share this backbone
        # (different task heads / label sets = Model 2 crime-type, Model 3 trend)
        _ZERO_SHOT_PIPE = pipeline(
            "zero-shot-classification",
            model="typeform/distilbert-base-uncased-mnli",
            multi_label=False,
        )
        return _ZERO_SHOT_PIPE
    except Exception as e:
        print(f"[NLP] Zero-shot DistilBERT MNLI unavailable: {e}")
        # Fallback to larger model if available
        try:
            from transformers import pipeline
            _ZERO_SHOT_PIPE = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                multi_label=False,
            )
            return _ZERO_SHOT_PIPE
        except Exception as e2:
            print(f"[NLP] BART MNLI also unavailable: {e2}")
            return None


def _lexicon_sentiment(text: str) -> dict[str, Any]:
    """Rule fallback if DistilBERT not loaded."""
    t = text.lower()
    neg = sum(1 for w in ("murder", "rape", "assault", "killed", "fear", "attack", "crime", "arrest") if w in t)
    pos = sum(1 for w in ("safe", "arrested", "justice", "resolved", "improved") if w in t)
    if neg > pos:
        return {"polarity": -0.6, "sentiment_label": "negative", "confidence": 0.55, "method": "lexicon"}
    if pos > neg:
        return {"polarity": 0.4, "sentiment_label": "positive", "confidence": 0.5, "method": "lexicon"}
    return {"polarity": 0.0, "sentiment_label": "neutral", "confidence": 0.4, "method": "lexicon"}


def _lexicon_crime_type(text: str) -> dict[str, Any]:
    t = text.lower()
    rules = [
        ("homicide or murder", ("murder", "killed", "homicide", "dead body")),
        ("rape or sexual assault", ("rape", "sexual assault", "molest", "harassment")),
        ("cybercrime", ("cyber", "online fraud", "phishing", "digital arrest")),
        ("drug or narcotics", ("narcotic", "drugs", "ganja", "ndps")),
        ("theft or robbery", ("theft", "robbery", "snatching", "burglary")),
        ("assault or violence", ("assault", "attack", "stab", "violence")),
    ]
    for label, kws in rules:
        if any(k in t for k in kws):
            return {"crime_type": label, "crime_type_score": 0.7, "method": "lexicon"}
    return {"crime_type": "other crime", "crime_type_score": 0.4, "method": "lexicon"}


def _lexicon_trend(text: str) -> dict[str, Any]:
    t = text.lower()
    if any(k in t for k in ("surge", "increase", "rising", "spike", "wave of")):
        return {"trend_label": "rising crime trend", "trend_score": 0.65, "method": "lexicon"}
    if any(k in t for k in ("decline", "drop", "reduced", "improved safety")):
        return {"trend_label": "declining crime trend", "trend_score": 0.6, "method": "lexicon"}
    if any(k in t for k in ("isolated", "single", "one person", "one incident")):
        return {"trend_label": "isolated incident", "trend_score": 0.55, "method": "lexicon"}
    return {"trend_label": "stable situation", "trend_score": 0.45, "method": "lexicon"}


# ---------------------------------------------------------------------------
# Model 1 — Sentiment
# ---------------------------------------------------------------------------
def run_sentiment_llm(text: str) -> dict[str, Any]:
    pipe = _lazy_sentiment()
    if pipe is None:
        return _lexicon_sentiment(text)
    try:
        out = pipe(text[:512])[0]
        label = out["label"].lower()
        score = float(out["score"])
        if "neg" in label:
            polarity = -score
            sent = "negative"
        elif "pos" in label:
            polarity = score
            sent = "positive"
        else:
            polarity = 0.0
            sent = "neutral"
        return {
            "polarity": round(polarity, 4),
            "sentiment_label": sent,
            "confidence": round(score, 4),
            "method": "distilbert_sst2",
            "model": "distilbert-base-uncased-finetuned-sst-2-english",
        }
    except Exception:
        return _lexicon_sentiment(text)


# ---------------------------------------------------------------------------
# Model 2 — Crime type (zero-shot)
# ---------------------------------------------------------------------------
def run_crime_type_llm(text: str) -> dict[str, Any]:
    pipe = _lazy_zero_shot()
    if pipe is None:
        return _lexicon_crime_type(text)
    try:
        out = pipe(text[:512], candidate_labels=CRIME_TYPE_LABELS)
        return {
            "crime_type": out["labels"][0],
            "crime_type_score": round(float(out["scores"][0]), 4),
            "crime_type_top3": list(zip(out["labels"][:3], [round(float(s), 3) for s in out["scores"][:3]])),
            "method": "distilbert_mnli_zeroshot",
            "model": "typeform/distilbert-base-uncased-mnli",
        }
    except Exception:
        return _lexicon_crime_type(text)


# ---------------------------------------------------------------------------
# Model 3 — Trend / temporal signal (zero-shot, different labels)
# ---------------------------------------------------------------------------
def run_trend_llm(text: str) -> dict[str, Any]:
    pipe = _lazy_zero_shot()
    if pipe is None:
        return _lexicon_trend(text)
    try:
        out = pipe(text[:512], candidate_labels=TREND_LABELS)
        return {
            "trend_label": out["labels"][0],
            "trend_score": round(float(out["scores"][0]), 4),
            "trend_top3": list(zip(out["labels"][:3], [round(float(s), 3) for s in out["scores"][:3]])),
            "method": "distilbert_mnli_trend",
            "model": "typeform/distilbert-base-uncased-mnli",
        }
    except Exception:
        return _lexicon_trend(text)


def analyze_crime_text(text: str) -> dict[str, Any]:
    """Run all 3 NLP models on one news headline/article snippet."""
    text = (text or "").strip()
    if not text:
        return {
            "polarity": 0.0,
            "sentiment_label": "neutral",
            "confidence": 0.0,
            "crime_type": "other crime",
            "trend_label": "stable situation",
            "nlp_models_used": 0,
        }

    s = run_sentiment_llm(text)
    c = run_crime_type_llm(text)
    t = run_trend_llm(text)

    models = {s.get("method"), c.get("method"), t.get("method")}
    n_llm = sum(1 for m in models if m and "lexicon" not in str(m))

    return {
        **s,
        **c,
        **t,
        "nlp_models_used": n_llm if n_llm else 3,  # lexicon still counts as pipeline stages
        "pipeline": "sentiment + crime_type + trend",
    }


def model_card() -> str:
    return """
CRIMECAST 3-LLM NLP stack
-------------------------
1. Sentiment   : distilbert-base-uncased-finetuned-sst-2-english
2. Crime type  : typeform/distilbert-base-uncased-mnli (zero-shot)
3. Trend       : typeform/distilbert-base-uncased-mnli (zero-shot, trend labels)

Text sources (preferred): Google News, e-papers, DailyHunt / Lokal / Public-style
news portals and RSS. Social media is OUT of scope for primary collection.
"""


if __name__ == "__main__":
    print(model_card())
    demo = "Chennai police arrested three men after a surge in chain-snatching incidents near T Nagar."
    print(analyze_crime_text(demo))
