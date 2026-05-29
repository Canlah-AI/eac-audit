# CanMarket template (placeholder)

This is a slot for a CanMarket-branded report template. It is **not yet built**.

To make it real, add a `report.html.j2` here (and optional `cover.html` /
`executive.html` includes + an `assets/` folder). It renders the exact same
report data contract the `google/` template consumes — see
[`../../contract.py`](../../contract.py) for the field list. Nothing in the
data layer changes; you only restyle.

Once `report.html.j2` exists, it auto-appears in:

```bash
python report.py --list-templates
python report.py <url> --template canmarket --format pdf
```

The contract gives you (top-level keys, all template-agnostic):

- `brand_name`, `target_url`, `audit_date`, `target_markets`
- `overall_score`, `p0_count`, `p1_count`, `p2_count`, `pass_count`
- `top_actions[]` — `{title, impact, effort}`
- `modules[]` — `{icon, title_zh, title_en, score, summary_html, data_table, findings[]}`
- `findings[]` — `{severity, title_zh, impact_zh, action_zh, evidence, code_snippet, ...}`
- `next_steps_text`, `leakage_risk`, `readiness_items[]`

Start by copying `../google/report.html.j2` and restyling to the CanMarket
brand system (Inter, Interactive Blue `#2563EB`, hierarchy via size/weight).
