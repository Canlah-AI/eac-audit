#!/usr/bin/env python3
"""Report data contract.

The contract is the neutral, template-agnostic structure that sits between
the data layer (probes) and the presentation layer (templates). Any template
renders this same dict; swapping templates never touches the data.

`build_contract` takes:
  - base: the on-site infra audit (4 modules) from eac_audit.run_audit()
  - offsite: the off-site probe outputs from engine.run_offsite_probes()
and returns a unified report_data dict with all modules merged, the overall
score recalculated, and top actions re-ranked.

The off-site module builders are brand-agnostic — no client-specific copy is
hardcoded. Remediation code snippets are generic templates the reader adapts.
"""
from __future__ import annotations

from typing import Any

_FINDING_DEFAULTS = {
    "confidence": 0.85,
    "needs_account": False,
    "code_snippet": None,
    "code_language": None,
    "paste_location": None,
    "evidence": "",
    "rule_id": "OFFSITE",
}

_SEVERITY_DEDUCT = {"P0": 25, "P1": 10, "P2": 3, "PASS": 0}
_MODULE_DEDUCT = {"P0": 30, "P1": 15, "P2": 5, "PASS": 0}


def _finding(severity: str, title: str, impact: str, action: str,
             rule_id: str, probe: str, evidence: str = "",
             code_snippet: str | None = None,
             code_language: str | None = None,
             paste_location: str | None = None,
             confidence: float = 0.85) -> dict:
    return {
        **_FINDING_DEFAULTS,
        "severity": severity,
        "title_zh": title,
        "impact_zh": impact,
        "action_zh": action,
        "rule_id": rule_id,
        "evidence": evidence,
        "code_snippet": code_snippet,
        "code_language": code_language,
        "paste_location": paste_location,
        "confidence": confidence,
        "_source_probe": probe,
    }


def _module_score(findings: list[dict], base: int = 100) -> int:
    score = base
    for f in findings:
        score -= _MODULE_DEDUCT.get(f.get("severity", "").upper(), 0)
    return max(0, min(100, score))


# ---------------------------------------------------------------------------
# Off-site module builders (brand-agnostic)
# ---------------------------------------------------------------------------

def _module_offsite_authority(backlink: dict, community: dict, news: dict) -> dict:
    ext = backlink.get("external_mentions_estimate", 0)
    unlinked = backlink.get("unlinked_mention_count", 0)
    bl_grade = backlink.get("backlink_grade") or backlink.get("mention_grade", "UNKNOWN")
    reddit = community.get("reddit", {}).get("mention_count", 0)
    total_comm = community.get("total_community_mentions", 0)
    comm_grade = community.get("community_grade", "NONE")
    news_count = news.get("total_articles_found", 0)
    news_grade = news.get("coverage_grade", "NONE")
    kp = news.get("knowledge_panel_detected", False)

    findings: list[dict] = []
    if ext < 10 or bl_grade in ("UNKNOWN", "WEAK", "NONE"):
        findings.append(_finding(
            "P1", "站外链接权威度不足",
            f"检测到 {ext} 个外部提及，{unlinked} 个未链接品牌提及。反链是 Google 排名核心信号。",
            "联系已提及品牌但未加链接的网站请求加链（转化率最高），同时开展 Digital PR 争取行业媒体报道。",
            "OFFSITE-001", "backlink",
            evidence=f"外部提及 {ext} 个，未链接品牌提及 {unlinked} 个（来源：Google 搜索结果采样，非验证反链）。"))
    if news_count == 0:
        findings.append(_finding(
            "P1", "无新闻媒体报道",
            "零新闻曝光意味着品牌在 Google Knowledge Panel、AI 搜索引用中缺席。新闻报道是 E-E-A-T 权威信号的核心来源。",
            "向行业媒体投稿品牌故事，并在 Crunchbase/Wikidata 建立企业档案以触发 Knowledge Panel。",
            "OFFSITE-002", "news",
            evidence=f"Serper 新闻搜索未找到相关报道。Knowledge Panel: {'已检测' if kp else '未检测到'}。"))

    return {
        "icon": "🌐", "title_zh": "站外 SEO 权威度", "title_en": "Off-Site SEO Authority",
        "score": _module_score(findings),
        "summary_html": f"<p>社区讨论 {total_comm} 条（{comm_grade}），新闻报道 {news_count} 篇（{news_grade}），外部提及 {ext} 个。</p>",
        "data_table": {"headers": ["指标", "数值", "评级"], "rows": [
            ["社区讨论总数", str(total_comm), comm_grade],
            ["Reddit 提及", str(reddit), "—"],
            ["新闻报道数", str(news_count), news_grade],
            ["外部提及数", str(ext), bl_grade],
            ["未链接品牌提及", str(unlinked), "🔗 待转化" if unlinked > 0 else "—"],
        ]},
        "findings": findings,
    }


def _module_schema_ai(schema: dict, freshness: dict) -> dict:
    block_count = schema.get("block_count", 0)
    found_types = schema.get("found_types", [])
    comp = schema.get("composite_score", 0)
    sitemap = freshness.get("sitemap_found", False)
    fresh = freshness.get("freshness", {})
    fresh_grade = fresh.get("freshness_grade", "UNKNOWN")
    total_urls = freshness.get("total_urls_in_sitemap", 0)
    stale = fresh.get("stale_pages_1yr", 0)
    pct90 = fresh.get("pct_updated_90d", 0)
    types_str = ", ".join(found_types) if found_types else "无"

    findings: list[dict] = []
    if stale > 50:
        findings.append(_finding(
            "P2", "大量页面内容过期",
            f"{stale} 个页面超过 1 年未更新。Google 偏好新鲜内容，AI 搜索引擎更倾向引用近期更新的页面。",
            f"启动内容刷新计划：优先更新流量最高的 Top 20 过期页面，每月至少更新 10-15 个。",
            "SCHEMA-001", "freshness",
            evidence=f"Sitemap 含 {total_urls} 个 URL，{stale} 个超 1 年未更新，仅 {pct90}% 近 90 天更新。"))
    missing = schema.get("missing_expected_types", [])
    if missing:
        findings.append(_finding(
            "P2", "缺少推荐的 Schema 标记",
            "Organization/Product 等 Schema 是 Google Knowledge Panel 和 AI 搜索引用的基础信号，缺失会降低品牌可见度。",
            "在首页添加缺失的 JSON-LD 标记，包含品牌名称、logo、社交链接（sameAs）等。",
            "SCHEMA-002", "schema",
            evidence=f"缺少期望的 Schema 类型: {', '.join(missing[:6])}。",
            code_snippet=(
                '{\n  "@context": "https://schema.org",\n  "@type": "Organization",\n'
                '  "name": "<品牌名>",\n  "url": "<网站>",\n  "logo": "<logo URL>",\n'
                '  "sameAs": ["<社媒1>", "<社媒2>"]\n}'),
            code_language="JSON-LD", paste_location="首页 <head> 标签内", confidence=0.75))

    score = comp
    for f in findings:
        score -= _MODULE_DEDUCT.get(f["severity"], 0)
    return {
        "icon": "🤖", "title_zh": "结构化数据与 AI 就绪度", "title_en": "Schema & AI Readiness",
        "score": max(0, min(100, score)),
        "summary_html": f"<p>检测到 {block_count} 个 JSON-LD 块（{types_str}）。评分 {comp}/100。内容更新: {fresh_grade}。</p>",
        "data_table": {"headers": ["指标", "数值", "状态"], "rows": [
            ["JSON-LD 块数", str(block_count), "✅" if block_count > 0 else "❌"],
            ["Schema 类型", types_str, "—"],
            ["Schema 评分", f"{comp}/100", "✅" if comp >= 60 else "⚠️"],
            ["Sitemap", "✅ 已检测" if sitemap else "❌ 未检测到", "—"],
            ["内容更新", fresh_grade, "—"],
            ["Sitemap URL 数", str(total_urls), "—"],
            ["过期页面 (>1年)", str(stale), "⚠️" if stale > 50 else "—"],
        ]},
        "findings": findings,
    }


def _module_social_nap(social: dict, nap: dict) -> dict:
    profiles = social.get("profiles_analyzed", 0)
    reach = social.get("total_reach", 0)
    active = social.get("active_platforms", 0)
    inf_grade = social.get("influence_grade", "ABSENT")
    nap_grade = nap.get("nap_grade", "UNKNOWN")
    has_schema = nap.get("onsite_nap", {}).get("has_schema_org", False)
    issues = nap.get("consistency_issues", [])

    findings: list[dict] = []
    if inf_grade in ("ABSENT", "DORMANT"):
        findings.append(_finding(
            "P1", "社交媒体影响力不足",
            f"社媒影响力评级 {inf_grade}，{profiles} 个账号，总触达 {reach}。社交信号影响品牌搜索量和 AI 搜索引用频率。",
            "在网站页脚添加所有社媒链接并在 Schema sameAs 中声明。重点运营高相关平台，每月发布 8+ 条内容。",
            "SOCIAL-001", "social",
            evidence=f"社媒影响力评级: {inf_grade}，活跃平台 {active} 个。"))
    if nap_grade in ("INCONSISTENT", "PARTIAL"):
        issues_text = "; ".join(issues[:3]) if issues else "信息不一致"
        findings.append(_finding(
            "P2", "NAP 信息跨平台不一致",
            "品牌名称/地址/电话在不同平台存在差异。NAP 不一致会降低 Google Local SEO 排名信号。",
            "统一所有平台的品牌名称、地址、电话，更新目录信息，并添加 LocalBusiness JSON-LD 供搜索引擎程序化验证。",
            "SOCIAL-002", "nap",
            evidence=f"NAP 一致性评级: {nap_grade}。问题: {issues_text}",
            code_snippet=(
                '{\n  "@context": "https://schema.org",\n  "@type": "LocalBusiness",\n'
                '  "name": "<统一品牌名>",\n  "address": {"@type": "PostalAddress", "streetAddress": "<地址>", "addressCountry": "<国家>"},\n'
                '  "telephone": "<电话>"\n}'),
            code_language="JSON-LD", paste_location="首页 <head> 标签内", confidence=0.80))

    return {
        "icon": "📱", "title_zh": "社交媒体与信息一致性", "title_en": "Social & NAP Consistency",
        "score": _module_score(findings),
        "summary_html": f"<p>社媒影响力: {inf_grade}（{profiles} 账号，触达 {reach}）。NAP: {nap_grade}。</p>",
        "data_table": {"headers": ["指标", "数值", "状态"], "rows": [
            ["社媒账号", str(profiles), "—"],
            ["总粉丝触达", str(reach), inf_grade],
            ["活跃平台", str(active), "—"],
            ["NAP 一致性", nap_grade, "✅" if nap_grade == "CONSISTENT" else "⚠️"],
            ["Schema.org NAP", "有" if has_schema else "无", "✅" if has_schema else "❌"],
        ]},
        "findings": findings,
    }


# ---------------------------------------------------------------------------
# Contract builder
# ---------------------------------------------------------------------------

def build_contract(base: dict, offsite: dict[str, dict]) -> dict:
    """Merge base on-site audit + off-site probes into one report contract."""
    offsite_modules = [
        _module_offsite_authority(
            offsite.get("backlink", {}), offsite.get("community", {}), offsite.get("news", {})),
        _module_schema_ai(
            offsite.get("schema", {}), offsite.get("freshness", {})),
        _module_social_nap(
            offsite.get("social", {}), offsite.get("nap", {})),
    ]

    data = dict(base)  # shallow copy of the base report_data
    data["modules"] = list(base.get("modules", [])) + offsite_modules

    # Recalculate counts + overall score across ALL modules (skip score == -1)
    p0 = p1 = p2 = passes = 0
    for mod in data["modules"]:
        if mod.get("score", -1) == -1:
            continue
        for f in mod.get("findings", []):
            sev = f.get("severity", "").upper()
            if sev == "P0":
                p0 += 1
            elif sev == "P1":
                p1 += 1
            elif sev == "P2":
                p2 += 1
            elif sev == "PASS":
                passes += 1
    data["p0_count"], data["p1_count"], data["p2_count"], data["pass_count"] = p0, p1, p2, passes
    data["overall_score"] = max(0, 100 - (p0 * 25 + p1 * 10 + p2 * 3))

    # Re-rank top actions across all findings
    all_findings: list[dict] = []
    for mod in data["modules"]:
        all_findings.extend(mod.get("findings", []))
    order = {"P0": 0, "P1": 1, "P2": 2, "PASS": 3}
    all_findings.sort(key=lambda f: order.get(f.get("severity", "").upper(), 9))
    data["top_actions"] = [{
        "title": f.get("action_zh", f.get("title_zh", "")),
        "impact": f"{f.get('severity', 'P1')} · {f.get('impact_zh', '')}",
        "effort": "30 分钟" if f.get("code_snippet") else "需评估",
    } for f in all_findings[:3]]

    data["next_steps_text"] = (
        f"本报告中标记为 P0 的 {p0} 个问题建议在 7 天内优先处理。"
        f"如需协助实施，请联系我们的技术团队。")
    data["_offsite_raw"] = offsite
    return data
