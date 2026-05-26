#!/usr/bin/env python3
"""
Lighthouse / PageSpeed Insights probe — calls Google PSI API for Core Web Vitals.

Stdlib only (urllib). No API key needed for low volume (25K queries/day per IP).
Runs mobile + desktop in parallel via threading.

Returns Lighthouse lab scores (performance/a11y/best-practices/seo), lab Core
Web Vitals (LCP/CLS/INP/FCP/TBT/TTFB/SI), and CrUX field data percentiles when
available. Verdicts use Google's official thresholds and prefer field over lab.
"""

from __future__ import annotations

import json
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict, field
from typing import Any

PSI_ENDPOINT = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
CATEGORIES = ["performance", "accessibility", "best-practices", "seo"]
TIMEOUT_SECONDS = 30.0


@dataclass
class StrategyResult:
    performance_score: int | None = None
    accessibility_score: int | None = None
    best_practices_score: int | None = None
    seo_score: int | None = None
    lcp_ms: float | None = None
    cls: float | None = None
    inp_ms: float | None = None
    fcp_ms: float | None = None
    tbt_ms: float | None = None
    ttfb_ms: float | None = None
    speed_index_ms: float | None = None
    field_data_available: bool = False
    field_lcp_p75_ms: float | None = None
    field_cls_p75: float | None = None
    field_inp_p75_ms: float | None = None
    failed_audits: list[dict] = field(default_factory=list)
    raw_lighthouse_version: str = ""


def _call_psi(url: str, strategy: str) -> tuple[dict | None, str | None]:
    """Returns (json_payload, error_message). Either side is None."""
    params = [("url", url), ("strategy", strategy)] + [("category", c) for c in CATEGORIES]
    api_url = PSI_ENDPOINT + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(api_url, headers={"User-Agent": "canmarket-audit/1.1"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            return json.loads(resp.read().decode("utf-8")), None
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8")[:300]
        except Exception:
            err_body = ""
        return None, f"HTTP {e.code}: {err_body}"
    except urllib.error.URLError as e:
        return None, f"URL error: {e.reason}"
    except (TimeoutError, OSError) as e:
        return None, f"network error: {e}"
    except json.JSONDecodeError as e:
        return None, f"invalid JSON from PSI: {e}"


def _score_to_int(raw: Any) -> int | None:
    if raw is None:
        return None
    try:
        return int(round(float(raw) * 100))
    except (TypeError, ValueError):
        return None


def _audit_numeric(audits: dict, audit_id: str) -> float | None:
    a = audits.get(audit_id) or {}
    val = a.get("numericValue")
    try:
        return float(val) if val is not None else None
    except (TypeError, ValueError):
        return None


def _extract_failed_audits(lh: dict, top_n: int = 10) -> list[dict]:
    audits = lh.get("audits", {}) or {}
    perf_refs = ((lh.get("categories", {}) or {}).get("performance") or {}).get("auditRefs") or []
    weights = {ref.get("id", ""): float(ref.get("weight", 0) or 0) for ref in perf_refs}
    failed: list[dict] = []
    for audit_id, a in audits.items():
        score = a.get("score")
        if score is None or a.get("scoreDisplayMode") not in ("numeric", "binary"):
            continue
        try:
            score_f = float(score)
        except (TypeError, ValueError):
            continue
        if score_f >= 0.9:
            continue
        failed.append({
            "id": audit_id,
            "title": a.get("title", ""),
            "score": score_f,
            "_w": weights.get(audit_id, 0.0),
        })
    failed.sort(key=lambda x: x["_w"], reverse=True)
    return [{k: v for k, v in item.items() if k != "_w"} for item in failed[:top_n]]


def _parse_payload(payload: dict) -> StrategyResult:
    lh = payload.get("lighthouseResult", {}) or {}
    cats = lh.get("categories", {}) or {}
    audits = lh.get("audits", {}) or {}
    res = StrategyResult()
    res.performance_score = _score_to_int((cats.get("performance") or {}).get("score"))
    res.accessibility_score = _score_to_int((cats.get("accessibility") or {}).get("score"))
    res.best_practices_score = _score_to_int((cats.get("best-practices") or {}).get("score"))
    res.seo_score = _score_to_int((cats.get("seo") or {}).get("score"))
    res.lcp_ms = _audit_numeric(audits, "largest-contentful-paint")
    res.cls = _audit_numeric(audits, "cumulative-layout-shift")
    res.inp_ms = _audit_numeric(audits, "interaction-to-next-paint")
    res.fcp_ms = _audit_numeric(audits, "first-contentful-paint")
    res.tbt_ms = _audit_numeric(audits, "total-blocking-time")
    res.ttfb_ms = _audit_numeric(audits, "server-response-time")
    res.speed_index_ms = _audit_numeric(audits, "speed-index")

    metrics = (payload.get("loadingExperience") or {}).get("metrics") or {}
    res.field_data_available = bool(metrics)
    if metrics:
        lcp_p = (metrics.get("LARGEST_CONTENTFUL_PAINT_MS") or {}).get("percentile")
        cls_p = (metrics.get("CUMULATIVE_LAYOUT_SHIFT_SCORE") or {}).get("percentile")
        inp_p = (metrics.get("INTERACTION_TO_NEXT_PAINT") or {}).get("percentile")
        res.field_lcp_p75_ms = float(lcp_p) if lcp_p is not None else None
        res.field_cls_p75 = (float(cls_p) / 100.0) if cls_p is not None else None
        res.field_inp_p75_ms = float(inp_p) if inp_p is not None else None

    res.failed_audits = _extract_failed_audits(lh)
    res.raw_lighthouse_version = lh.get("lighthouseVersion", "")
    return res


def probe(url: str, strategy: str = "mobile") -> dict:
    """Run PSI once for one strategy. Returns {result, error}."""
    if strategy not in ("mobile", "desktop"):
        raise ValueError(f"strategy must be 'mobile' or 'desktop', got {strategy!r}")
    payload, err = _call_psi(url, strategy)
    if err is not None or payload is None:
        return {"result": asdict(StrategyResult()), "error": err or "unknown PSI error"}
    return {"result": asdict(_parse_payload(payload)), "error": None}


def _verdict_lcp(lcp_ms: float | None) -> str:
    if lcp_ms is None:
        return "poor"
    return "good" if lcp_ms < 2500 else ("needs_improvement" if lcp_ms <= 4000 else "poor")


def _verdict_cls(cls: float | None) -> str:
    if cls is None:
        return "poor"
    return "good" if cls < 0.1 else ("needs_improvement" if cls <= 0.25 else "poor")


def _verdict_inp(inp_ms: float | None, has_field: bool) -> str:
    if inp_ms is None:
        return "no_field_data" if not has_field else "good"
    return "good" if inp_ms < 200 else ("needs_improvement" if inp_ms <= 500 else "poor")


def _build_verdicts(mobile: dict) -> dict:
    has_field = bool(mobile.get("field_data_available"))
    lcp = mobile.get("field_lcp_p75_ms") if has_field else mobile.get("lcp_ms")
    cls = mobile.get("field_cls_p75") if has_field else mobile.get("cls")
    inp_field = mobile.get("field_inp_p75_ms")
    v_lcp, v_cls = _verdict_lcp(lcp), _verdict_cls(cls)
    v_inp = _verdict_inp(inp_field, has_field and inp_field is not None)
    inputs = [v_lcp, v_cls] + ([v_inp] if v_inp != "no_field_data" else [])
    overall = (
        "poor" if any(v == "poor" for v in inputs)
        else "needs_improvement" if any(v == "needs_improvement" for v in inputs)
        else "good"
    )
    return {"lcp": v_lcp, "cls": v_cls, "inp": v_inp, "overall_mobile": overall}


def probe_both(url: str) -> dict:
    """Run mobile + desktop in parallel. Returns full result envelope."""
    results: dict[str, dict] = {}

    def _worker(strategy: str) -> None:
        results[strategy] = probe(url, strategy)

    threads = [threading.Thread(target=_worker, args=(s,)) for s in ("mobile", "desktop")]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=TIMEOUT_SECONDS + 10)

    empty = {"result": asdict(StrategyResult()), "error": "thread missing"}
    mobile_env = results.get("mobile", empty)
    desktop_env = results.get("desktop", empty)
    errors = [e for e in (mobile_env.get("error"), desktop_env.get("error")) if e]
    return {
        "url": url,
        "mobile": mobile_env["result"],
        "desktop": desktop_env["result"],
        "verdicts": _build_verdicts(mobile_env["result"]),
        "error": "; ".join(errors) if errors else None,
    }


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: lighthouse_psi.py <url>", file=sys.stderr)
        return 2
    url = sys.argv[1]
    if not urllib.parse.urlparse(url).scheme:
        url = "https://" + url
    json.dump(probe_both(url), sys.stdout, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
