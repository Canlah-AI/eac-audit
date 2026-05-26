# EAC Infrastructure Audit

Automated website infrastructure audit for cross-border e-commerce sellers. Runs 4 parallel probes and generates a branded HTML + PDF report with severity-ranked findings and actionable recommendations.

Built for the Google EAC (E-Commerce Acceleration Center) program.

## What It Audits

| Module | Probe | What It Checks |
|--------|-------|----------------|
| Global Speed | `eac_speed_probe` | TTFB, LCP (mobile + desktop), CDN detection, server geolocation, HTTP/2 |
| Lead Form Security | `eac_form_probe` | CAPTCHA protection, form field friction, CMS detection, anti-spam |
| Trust Content | `eac_trust_probe` | Blog/content section, product page trust signals (specs, testimonials, certifications, comparison), SSL |
| Conversion Tracking | `eac_tracking_probe` | GA4, GTM, Google Ads, Meta Pixel, Consent Mode v2, Enhanced Conversions, ad spend leakage risk |

All 4 probes run concurrently. A typical audit completes in **10-30 seconds**.

## Output

- **HTML report** — A4-ready branded report with executive summary, module scores, severity matrix (P0/P1/P2), and inline code fix snippets
- **JSON data** — Machine-readable findings for integration with other tools
- **PDF** — Print-ready version via WeasyPrint (optional)

### Scoring

| Severity | Deduction | SLA |
|----------|-----------|-----|
| P0 — Critical | -25 pts | Fix within 7 days |
| P1 — Warning | -10 pts | Fix within 30 days |
| P2 — Info | -3 pts | Nice to have |

Overall score = 100 - total deductions (floor 0).

## Quick Start

```bash
# Install dependencies
pip install requests jinja2 weasyprint

# Run a basic audit
python eac_audit.py https://example.com --company "Example Corp" --market US,EU

# Full audit with form and product page
python eac_audit.py https://example.com \
    --form-url https://example.com/contact \
    --thank-you-url https://example.com/thank-you \
    --product-page https://example.com/product/abc \
    --company "某某科技" \
    --market US,EU,SEA \
    --open
```

### CLI Options

| Flag | Required | Description |
|------|----------|-------------|
| `url` | Yes | Target website URL |
| `--form-url` | No | Lead form page (skips form probe if omitted) |
| `--thank-you-url` | No | Thank-you page for conversion tracking check |
| `--product-page` | No | Product detail page for trust signal audit |
| `--company` | No | Company name (used in report header) |
| `--market` | No | Target markets, comma-separated (default: `全球`) |
| `--output-dir` | No | Output path (default: `output/{domain}`) |
| `--open` | No | Open HTML report in browser after generation |

## Project Structure

```
eac-audit/
├── eac_audit.py              # Orchestrator — runs all probes, assembles report
├── eac_demo.py               # Demo data generator for template testing
├── probes/
│   ├── eac_speed_probe.py    # TTFB, LCP, CDN, server location
│   ├── eac_form_probe.py     # CAPTCHA, form fields, CMS detection
│   ├── eac_trust_probe.py    # Blog, product specs, testimonials, SSL
│   ├── eac_tracking_probe.py # GA4, GTM, Ads, Consent Mode v2
│   └── lighthouse_psi.py     # Google PageSpeed Insights API wrapper
└── render/
    ├── html_to_pdf.py        # WeasyPrint HTML → PDF converter
    ├── assets/               # EAC branding logos (PNG)
    └── templates/
        ├── eac-report.html.j2  # Main Jinja2 report template
        ├── eac-cover.html      # Cover page
        └── eac-executive.html  # Executive summary
```

## How It Works

```
                    ┌─────────────────┐
                    │   eac_audit.py  │
                    │  (orchestrator) │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼───┐  ┌──────▼─────┐ ┌──────▼──────┐
     │ speed_probe │  │ form_probe │ │ trust_probe │
     │   + PSI API │  │            │ │             │
     └─────────────┘  └────────────┘ └─────────────┘
              │              │              │
              │       ┌──────▼──────┐       │
              │       │tracking_probe│      │
              │       └─────────────┘       │
              └──────────────┬──────────────┘
                             │
                    ┌────────▼────────┐
                    │  Jinja2 render  │
                    │  HTML → PDF     │
                    └─────────────────┘
```

All probes run in parallel via `ThreadPoolExecutor(max_workers=4)`.

## Dependencies

- **Python 3.10+**
- `requests` — HTTP client for probes
- `jinja2` — HTML report templating
- `weasyprint` — HTML to PDF conversion (optional, requires system deps)

No API keys required. The PageSpeed Insights API allows 25K queries/day per IP without authentication.

## Sample Reports

See the [`audit-reports/`](../audit-reports/) directory for generated examples:

| Site | Score | Date | Key Findings |
|------|-------|------|-------------|
| canlah.ai | 77/100 | 2026-05-25 | Cloudflare CDN active, missing Consent Mode v2, product page needs trust signals |
| modernshade.org | 70/100 | 2026-05-25 | No blog/content section, missing product specs, needs competitor comparison |

## Extending

Each probe follows the same interface:

```python
def probe(url: str, **kwargs) -> dict:
    """Returns dict with 'findings' list and '_probe_status' string."""
    return {
        "_probe_status": "ok",  # or "error" / "skipped"
        "findings": [
            {
                "severity": "P1",
                "title_zh": "...",
                "impact_zh": "...",
                "action_zh": "...",
                "code_snippet": "...",  # optional inline fix
            }
        ]
    }
```

To add a new probe: create `probes/eac_new_probe.py` with a `probe()` function, then wire it into `eac_audit.py`.

## License

MIT

---

Built by [Canlah AI](https://canlah.ai) for the Google EAC program.
