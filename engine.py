#!/usr/bin/env python3
"""Adapter to the canmarket-site-audit probe engine.

The probe engine (data layer) lives in a separate repo. This module locates
it, runs the off-site SEO probes, and returns their raw output keyed by a
short name the contract builder understands.

The engine path is resolved in this order:
  1. $CANMARKET_AUDIT_PATH env var
  2. ~/dev/canmarket-site-audit-v1.1  (default dev location)
  3. ~/dev/canmarket-site-audit

Off-site probes run concurrently. Each is independent; a failure in one
returns an empty dict for that probe rather than aborting the whole run.
"""
from __future__ import annotations

import importlib.util
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

logger = logging.getLogger("engine")

# (result_key, module_name, callable, needs_brand)
OFFSITE_PROBES: list[tuple[str, str, str, bool]] = [
    ("backlink", "backlink_scan", "probe", True),
    ("community", "community_mention_scan", "probe", True),
    ("news", "news_coverage_scan", "probe", True),
    ("social", "social_influence_scan", "probe", True),
    ("nap", "nap_consistency_scan", "probe", True),
    ("schema", "schema_validator", "probe", False),
    ("freshness", "content_freshness_scan", "probe", False),
]


def locate_engine() -> Path:
    """Return the path to the canmarket-site-audit repo, or raise."""
    candidates = []
    env = os.environ.get("CANMARKET_AUDIT_PATH")
    if env:
        candidates.append(Path(env).expanduser())
    candidates.append(Path.home() / "dev" / "canmarket-site-audit-v1.1")
    candidates.append(Path.home() / "dev" / "canmarket-site-audit")
    for c in candidates:
        if (c / "probes").is_dir():
            return c
    raise FileNotFoundError(
        "canmarket-site-audit engine not found. Set $CANMARKET_AUDIT_PATH or "
        f"clone it to one of: {[str(c) for c in candidates]}"
    )


def _load_probe_module(engine_root: Path, module_name: str):
    """Load a probe module by FILE PATH from the engine's probes/ dir.

    We deliberately avoid `import probes.<name>` because this repo also has a
    `probes` package (the on-site EAC infra probes). Importing by path under a
    unique module name (`_engine_probe_<name>`) dodges that name collision and
    lets the engine's probe import its own siblings via the path entry.
    """
    probe_path = engine_root / "probes" / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(f"_engine_probe_{module_name}", probe_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {probe_path}")
    mod = importlib.util.module_from_spec(spec)
    # Register before exec: Python 3.12+ @dataclass / typing look the module up
    # via sys.modules[cls.__module__]; an unregistered path-loaded module makes
    # that return None and crash with "'NoneType' has no attribute '__dict__'".
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _run_one(engine_root: Path, key: str, module_name: str, fn_name: str,
             needs_brand: bool, url: str, brand: str | None) -> tuple[str, dict]:
    try:
        mod = _load_probe_module(engine_root, module_name)
        fn = getattr(mod, fn_name)
        result = fn(url, brand) if needs_brand else fn(url)
        return key, (result if isinstance(result, dict) else {"value": result})
    except Exception as e:  # noqa: BLE001 — one probe failing must not abort the run
        logger.warning("off-site probe %s failed: %s", module_name, e)
        return key, {"_probe_status": "error", "_reason": str(e)[:300]}


def run_offsite_probes(url: str, brand: str | None = None,
                       max_workers: int = 3) -> dict[str, dict]:
    """Run all off-site probes and return {key: probe_output}.

    Concurrency is capped at 3 (not 7) on purpose: each probe fires 4-6 Serper
    calls, so running all 7 at once bursts ~30 calls in seconds and trips the
    Serper free-tier rate limit (HTTP 400). Three-at-a-time spreads the load
    while still finishing in well under a minute.
    """
    engine_root = locate_engine()
    # Put the engine root on sys.path so engine probes that do
    # `from probes import X` for their own siblings resolve correctly.
    if str(engine_root) not in sys.path:
        sys.path.append(str(engine_root))
    logger.info("using engine at %s", engine_root)

    results: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [
            pool.submit(_run_one, engine_root, key, mod, fn, nb, url, brand)
            for (key, mod, fn, nb) in OFFSITE_PROBES
        ]
        for fut in as_completed(futures):
            key, output = fut.result()
            results[key] = output
            status = output.get("_probe_status", "ok")
            logger.info("  [%s] %s", key, status)
    return results
