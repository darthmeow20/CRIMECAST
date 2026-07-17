"""
CRIMECAST local database layer.

**SQLite** (default) — best for this project:
  - Zero server setup; single file under `data/crimecast.db`
  - Works offline with Streamlit on a laptop
  - Easy backup (copy the .db file)
  - Enough for news harvest, sentiment scores, district aggregates

**PostgreSQL** would be better later for multi-user / cloud deploy.
  Set env CRIMECAST_DATABASE_URL=postgresql://... to use it (optional).

Schema stores:
  - news_headlines (media support)
  - district_sentiment (aggregated polarity / negative share)
  - rape_2026 (forecast snapshot)
  - meta (last sync times)
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_SQLITE = DATA_DIR / "crimecast.db"
OUTPUT_DIR = PROJECT_ROOT / "model_outputs"


def _use_postgres() -> str | None:
    url = os.environ.get("CRIMECAST_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if url and url.startswith("postgres"):
        return url
    return None


def get_sqlite_path() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return Path(os.environ.get("CRIMECAST_SQLITE_PATH", DEFAULT_SQLITE))


def connect() -> sqlite3.Connection:
    """Open SQLite connection (row factory for dict-like access)."""
    path = get_sqlite_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db(conn: sqlite3.Connection | None = None) -> None:
    own = conn is None
    if own:
        conn = connect()
    assert conn is not None
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS news_headlines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            headline TEXT NOT NULL,
            date TEXT,
            district TEXT,
            source TEXT,
            url TEXT,
            lang TEXT,
            polarity REAL,
            sentiment_label TEXT,
            confidence REAL,
            crime_intensity REAL,
            crime_types TEXT,
            scored INTEGER DEFAULT 0,
            created_at TEXT,
            UNIQUE(headline, date)
        );

        CREATE TABLE IF NOT EXISTS district_sentiment (
            district TEXT PRIMARY KEY,
            n_headlines INTEGER,
            polarity_mean REAL,
            negative_share REAL,
            positive_share REAL,
            intensity_mean REAL,
            concern_score REAL,
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS rape_2026 (
            district TEXT PRIMARY KEY,
            predicted_2026_rape_incidents REAL,
            pred_low REAL,
            pred_high REAL,
            rape_risk_index REAL,
            risk_level TEXT,
            method TEXT,
            payload_json TEXT,
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS alert_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            level TEXT,
            title TEXT,
            detail TEXT,
            UNIQUE(level, title, detail)
        );
        """
    )
    conn.commit()
    if own:
        conn.close()


def set_meta(key: str, value: str, conn: sqlite3.Connection | None = None) -> None:
    own = conn is None
    if own:
        conn = connect()
        init_db(conn)
    assert conn is not None
    conn.execute(
        """
        INSERT INTO meta(key, value, updated_at) VALUES(?,?,?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
        """,
        (key, value, datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    if own:
        conn.close()


def get_meta(key: str, default: str = "") -> str:
    init_db()
    conn = connect()
    try:
        row = conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return str(row["value"]) if row else default
    finally:
        conn.close()


def upsert_headlines(df: pd.DataFrame) -> int:
    """Insert/update news rows from harvest DataFrame. Returns rows touched."""
    if df is None or df.empty:
        return 0
    init_db()
    conn = connect()
    n = 0
    now = datetime.now().isoformat(timespec="seconds")
    hcol = next((c for c in ("headline", "text", "source_text") if c in df.columns), None)
    if not hcol:
        conn.close()
        return 0
    for _, r in df.iterrows():
        headline = str(r.get(hcol) or "").strip()
        if not headline:
            continue
        date = str(r.get("date") or "")[:32]
        district = str(r.get("district") or r.get("district_city") or "")
        source = str(r.get("source") or "")
        url = str(r.get("url") or "")
        lang = str(r.get("lang") or "")
        pol = r.get("polarity")
        label = str(r.get("sentiment_label") or r.get("label") or "")
        conf = r.get("confidence")
        intensity = r.get("crime_intensity")
        ctypes = str(r.get("crime_types") or r.get("crime_type") or "")
        scored = 1 if pol is not None and str(pol) not in ("", "nan") else 0
        try:
            pol_f = float(pol) if pol is not None and str(pol) not in ("", "nan") else None
        except (TypeError, ValueError):
            pol_f = None
        try:
            conf_f = float(conf) if conf is not None and str(conf) not in ("", "nan") else None
        except (TypeError, ValueError):
            conf_f = None
        try:
            int_f = float(intensity) if intensity is not None and str(intensity) not in ("", "nan") else None
        except (TypeError, ValueError):
            int_f = None
        conn.execute(
            """
            INSERT INTO news_headlines(
                headline, date, district, source, url, lang,
                polarity, sentiment_label, confidence, crime_intensity, crime_types,
                scored, created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(headline, date) DO UPDATE SET
                district=excluded.district,
                source=excluded.source,
                url=excluded.url,
                lang=excluded.lang,
                polarity=COALESCE(excluded.polarity, news_headlines.polarity),
                sentiment_label=CASE
                    WHEN excluded.scored=1 THEN excluded.sentiment_label
                    ELSE news_headlines.sentiment_label END,
                confidence=COALESCE(excluded.confidence, news_headlines.confidence),
                crime_intensity=COALESCE(excluded.crime_intensity, news_headlines.crime_intensity),
                crime_types=CASE
                    WHEN excluded.crime_types != '' THEN excluded.crime_types
                    ELSE news_headlines.crime_types END,
                scored=MAX(news_headlines.scored, excluded.scored)
            """,
            (
                headline[:500], date, district, source, url, lang,
                pol_f, label, conf_f, int_f, ctypes[:200], scored, now,
            ),
        )
        n += 1
    conn.commit()
    set_meta("last_news_upsert", now, conn)
    conn.close()
    return n


def save_district_sentiment(df: pd.DataFrame) -> int:
    if df is None or df.empty:
        return 0
    init_db()
    conn = connect()
    now = datetime.now().isoformat(timespec="seconds")
    n = 0
    for _, r in df.iterrows():
        dist = str(r.get("district") or r.get("district_city") or "").strip()
        if not dist:
            continue
        conn.execute(
            """
            INSERT INTO district_sentiment(
                district, n_headlines, polarity_mean, negative_share, positive_share,
                intensity_mean, concern_score, updated_at
            ) VALUES (?,?,?,?,?,?,?,?)
            ON CONFLICT(district) DO UPDATE SET
                n_headlines=excluded.n_headlines,
                polarity_mean=excluded.polarity_mean,
                negative_share=excluded.negative_share,
                positive_share=excluded.positive_share,
                intensity_mean=excluded.intensity_mean,
                concern_score=excluded.concern_score,
                updated_at=excluded.updated_at
            """,
            (
                dist,
                int(r.get("n_headlines") or 0),
                float(r["polarity_mean"]) if pd.notna(r.get("polarity_mean")) else None,
                float(r["negative_share"]) if pd.notna(r.get("negative_share")) else None,
                float(r["positive_share"]) if pd.notna(r.get("positive_share")) else None,
                float(r["intensity_mean"]) if pd.notna(r.get("intensity_mean")) else None,
                float(r["concern_score"]) if pd.notna(r.get("concern_score")) else None,
                now,
            ),
        )
        n += 1
    conn.commit()
    set_meta("last_district_sentiment", now, conn)
    conn.close()
    return n


def load_district_sentiment() -> pd.DataFrame:
    init_db()
    conn = connect()
    try:
        return pd.read_sql_query(
            "SELECT * FROM district_sentiment ORDER BY concern_score DESC",
            conn,
        )
    except Exception:
        return pd.DataFrame()
    finally:
        conn.close()


def load_scored_headlines(limit: int = 500) -> pd.DataFrame:
    init_db()
    conn = connect()
    try:
        return pd.read_sql_query(
            f"""
            SELECT * FROM news_headlines
            WHERE scored=1
            ORDER BY date DESC, id DESC
            LIMIT {int(limit)}
            """,
            conn,
        )
    except Exception:
        return pd.DataFrame()
    finally:
        conn.close()


def save_rape_2026(df: pd.DataFrame) -> int:
    if df is None or df.empty:
        return 0
    init_db()
    conn = connect()
    now = datetime.now().isoformat(timespec="seconds")
    ncol = "district" if "district" in df.columns else "district_city"
    n = 0
    for _, r in df.iterrows():
        dist = str(r.get(ncol) or "").strip()
        if not dist:
            continue
        payload = {k: (None if pd.isna(v) else v) for k, v in r.items()}
        # json-safe
        for k, v in list(payload.items()):
            if hasattr(v, "item"):
                try:
                    payload[k] = v.item()
                except Exception:
                    payload[k] = str(v)
        conn.execute(
            """
            INSERT INTO rape_2026(
                district, predicted_2026_rape_incidents, pred_low, pred_high,
                rape_risk_index, risk_level, method, payload_json, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?)
            ON CONFLICT(district) DO UPDATE SET
                predicted_2026_rape_incidents=excluded.predicted_2026_rape_incidents,
                pred_low=excluded.pred_low,
                pred_high=excluded.pred_high,
                rape_risk_index=excluded.rape_risk_index,
                risk_level=excluded.risk_level,
                method=excluded.method,
                payload_json=excluded.payload_json,
                updated_at=excluded.updated_at
            """,
            (
                dist,
                _f(r.get("predicted_2026_rape_incidents")),
                _f(r.get("pred_low")),
                _f(r.get("pred_high")),
                _f(r.get("rape_risk_index")),
                str(r.get("risk_level") or ""),
                str(r.get("method") or ""),
                json.dumps(payload, default=str),
                now,
            ),
        )
        n += 1
    conn.commit()
    set_meta("last_rape_2026_sync", now, conn)
    conn.close()
    return n


def load_rape_2026() -> pd.DataFrame:
    init_db()
    conn = connect()
    try:
        return pd.read_sql_query("SELECT * FROM rape_2026 ORDER BY rape_risk_index DESC", conn)
    except Exception:
        return pd.DataFrame()
    finally:
        conn.close()


def _f(v: Any) -> float | None:
    try:
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def sync_from_csv_outputs() -> dict[str, Any]:
    """Pull latest CSVs from model_outputs into SQLite."""
    init_db()
    stats: dict[str, Any] = {"news": 0, "sentiment_raw": 0, "rape_2026": 0}
    # Prefer combined harvest
    harvest_paths = [
        OUTPUT_DIR / "media_harvest_tn_crime_latest.csv",
        OUTPUT_DIR / "news_signals_raw.csv",
    ]
    for p in sorted(OUTPUT_DIR.glob("media_harvest_tn_crime_*.csv"), key=lambda x: x.stat().st_mtime, reverse=True)[:3]:
        harvest_paths.append(p)
    for p in harvest_paths:
        if p.exists():
            try:
                stats["news"] += upsert_headlines(pd.read_csv(p))
            except Exception:
                pass
    raw = OUTPUT_DIR / "news_signals_raw.csv"
    if raw.exists():
        try:
            stats["sentiment_raw"] += upsert_headlines(pd.read_csv(raw))
        except Exception:
            pass
    rape = OUTPUT_DIR / "rape_predictions_2026_all_districts.csv"
    if rape.exists():
        try:
            stats["rape_2026"] = save_rape_2026(pd.read_csv(rape))
        except Exception:
            pass
    set_meta("last_full_sync", datetime.now().isoformat(timespec="seconds"))
    stats["db_path"] = str(get_sqlite_path())
    stats["backend"] = "postgresql" if _use_postgres() else "sqlite"
    return stats


def log_alerts(alerts: list[dict[str, str]]) -> int:
    """Persist unique HIGH/MED alerts with timestamp. Returns rows inserted."""
    if not alerts:
        return 0
    init_db()
    conn = connect()
    now = datetime.now().isoformat(timespec="seconds")
    n = 0
    for a in alerts:
        level = str(a.get("level") or "MED")
        title = str(a.get("title") or "")[:300]
        detail = str(a.get("detail") or "")[:800]
        if not title:
            continue
        try:
            cur = conn.execute(
                """
                INSERT OR IGNORE INTO alert_log(created_at, level, title, detail)
                VALUES (?,?,?,?)
                """,
                (now, level, title, detail),
            )
            n += int(cur.rowcount or 0)
        except Exception:
            continue
    conn.commit()
    if n:
        set_meta("last_alert_log", now, conn)
    conn.close()
    return n


def load_alert_log(limit: int = 40) -> pd.DataFrame:
    init_db()
    conn = connect()
    try:
        return pd.read_sql_query(
            f"""
            SELECT created_at, level, title, detail
            FROM alert_log
            ORDER BY id DESC
            LIMIT {int(limit)}
            """,
            conn,
        )
    except Exception:
        return pd.DataFrame()
    finally:
        conn.close()


def db_status() -> dict[str, Any]:
    init_db()
    conn = connect()
    try:
        news_n = conn.execute("SELECT COUNT(*) AS n FROM news_headlines").fetchone()["n"]
        scored_n = conn.execute("SELECT COUNT(*) AS n FROM news_headlines WHERE scored=1").fetchone()["n"]
        dist_n = conn.execute("SELECT COUNT(*) AS n FROM district_sentiment").fetchone()["n"]
        rape_n = conn.execute("SELECT COUNT(*) AS n FROM rape_2026").fetchone()["n"]
        try:
            alert_n = conn.execute("SELECT COUNT(*) AS n FROM alert_log").fetchone()["n"]
        except Exception:
            alert_n = 0
    finally:
        conn.close()
    return {
        "backend": "postgresql" if _use_postgres() else "sqlite",
        "path": str(get_sqlite_path()),
        "news_headlines": int(news_n),
        "scored_headlines": int(scored_n),
        "district_sentiment_rows": int(dist_n),
        "rape_2026_rows": int(rape_n),
        "alert_log_rows": int(alert_n),
        "last_sync": get_meta("last_full_sync"),
        "last_sentiment": get_meta("last_district_sentiment"),
    }
