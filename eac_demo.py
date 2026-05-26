"""Generate a demo EAC report to validate the template visually."""
import json
import os
import sys
from pathlib import Path
from datetime import date
from jinja2 import Environment, FileSystemLoader

TEMPLATE_DIR = Path(__file__).parent / "templates"

DEMO_DATA = {
    "brand_name": "深圳某某科技有限公司",
    "target_url": "https://www.example-tech.com",
    "audit_date": date.today().strftime("%Y-%m-%d"),
    "target_markets": "美国 / 欧盟 / 东南亚",
    "overall_score": 42,
    "p0_count": 3,
    "p1_count": 5,
    "p2_count": 4,
    "pass_count": 6,
    "leakage_risk": "high",
    "leakage_description": "检测到 Google Ads 广告代码，但 Thank You 页面没有转化追踪。您的广告点击无法关联到实际询盘，预算效率不可衡量。",
    "top_actions": [
        {
            "title": "在 Thank You 页面部署 Google Ads 转化追踪代码",
            "impact": "P0 · 解决广告预算追踪盲区，预计可量化 100% 的表单询盘来源",
            "effort": "30 分钟",
        },
        {
            "title": "配置 Cloudflare CDN 加速全球访问",
            "impact": "P0 · 美国用户当前 TTFB 3.2 秒，配置后预计降至 < 800ms",
            "effort": "2 小时",
        },
        {
            "title": "为留资表单添加 reCAPTCHA v3 保护",
            "impact": "P0 · 当前表单无任何反垃圾保护，可能导致垃圾询盘污染线索库",
            "effort": "15 分钟",
        },
    ],
    "modules": [
        {
            "icon": "🚀",
            "title_zh": "全球网站访问加速",
            "title_en": "Global Website Speed Optimization",
            "score": 35,
            "summary_html": "<p>网站服务器位于中国大陆，海外用户访问延迟严重。未配置任何 CDN 服务。</p>",
            "data_table": {
                "headers": ["目标市场", "TTFB (ms)", "LCP (s)", "评级"],
                "rows": [
                    ["🇺🇸 美国", "3,241", "5.8", "❌ 严重超标"],
                    ["🇩🇪 德国", "2,890", "4.9", "❌ 超标"],
                    ["🇸🇬 新加坡", "1,200", "2.1", "⚠️ 临界"],
                    ["🇨🇳 中国", "180", "0.9", "✅ 正常"],
                ],
            },
            "findings": [
                {
                    "severity": "P0",
                    "rule_id": "SPEED-001",
                    "title_zh": "美国市场 TTFB 超过 2 秒阈值",
                    "evidence": "TTFB from US (Virginia): 3,241ms · 测试时间: 2026-05-24 02:30 UTC · 数据来源: Google PageSpeed Insights API",
                    "confidence": 0.95,
                    "impact_zh": "B2B 客户在背景调查阶段首次访问您的网站，如果 3 秒内未加载完成，53% 的用户会直接离开。这是'第一印象'环节的致命瓶颈。",
                    "action_zh": "配置 Cloudflare CDN (免费方案即可)，将静态资源缓存到全球边缘节点。预计 TTFB 降至 < 800ms。",
                    "needs_account": False,
                    "code_snippet": None,
                    "code_language": None,
                    "paste_location": None,
                },
                {
                    "severity": "P1",
                    "rule_id": "SPEED-002",
                    "title_zh": "未检测到 CDN 服务",
                    "evidence": "HTTP 响应头中未发现 Cloudflare / Akamai / AWS CloudFront 特征。DNS CNAME 直接指向源站 IP 47.xxx.xxx.xxx (阿里云华东)。",
                    "confidence": 0.9,
                    "impact_zh": "所有海外请求直接回源到中国大陆服务器，跨洋传输延迟不可避免。CDN 是成本最低、效果最显著的加速手段。",
                    "action_zh": "注册 Cloudflare 账号 → 添加域名 → 修改 DNS 到 Cloudflare nameserver → 开启代理模式。",
                    "needs_account": False,
                    "code_snippet": "# Cloudflare DNS 配置示例\n# 1. 登录 cloudflare.com → Add Site\n# 2. 选择 Free 方案\n# 3. 修改域名 DNS 到:\n#    ns1.cloudflare.com\n#    ns2.cloudflare.com\n# 4. 在 DNS 页面开启代理 (橙色云图标)",
                    "code_language": "配置指南",
                    "paste_location": "域名注册商 DNS 设置",
                },
            ],
        },
        {
            "icon": "📝",
            "title_zh": "留资页面检查",
            "title_en": "Lead Form Security Audit",
            "score": 30,
            "summary_html": "<p>留资表单缺少反垃圾保护，且表单字段过多（12 个必填项），可能导致转化率下降。</p>",
            "data_table": None,
            "findings": [
                {
                    "severity": "P0",
                    "rule_id": "FORM-001",
                    "title_zh": "留资表单无 reCAPTCHA / Cloudflare Turnstile 保护",
                    "evidence": "DOM 扫描: 未检测到 .g-recaptcha / .cf-turnstile / grecaptcha.badge 元素。表单 action 指向 /api/contact，无前端验证。",
                    "confidence": 0.95,
                    "impact_zh": "无反垃圾保护的表单可能收到 99% 的机器人垃圾提交，污染您的线索库，浪费销售团队时间。",
                    "action_zh": "安装 reCAPTCHA v3（隐形验证，不影响用户体验）。以下代码适用于您的 WordPress 站点。",
                    "needs_account": False,
                    "code_snippet": '<!-- reCAPTCHA v3 安装代码 -->\n<!-- 步骤 1: 在 <head> 中添加 -->\n<script src="https://www.google.com/recaptcha/api.js?render=YOUR_SITE_KEY"></script>\n\n<!-- 步骤 2: 在表单提交时调用 -->\n<script>\nfunction onSubmit(token) {\n  document.getElementById("contact-form").submit();\n}\ngrecaptcha.ready(function() {\n  grecaptcha.execute(\'YOUR_SITE_KEY\', {action: \'submit\'}).then(onSubmit);\n});\n</script>\n\n<!-- 注册 Site Key: https://www.google.com/recaptcha/admin -->',
                    "code_language": "HTML",
                    "paste_location": "WordPress → 外观 → 主题编辑器 → header.php",
                },
                {
                    "severity": "P1",
                    "rule_id": "FORM-002",
                    "title_zh": "表单必填字段过多（12 项）",
                    "evidence": "检测到 12 个 required 字段: 姓名、公司、职位、邮箱、电话、国家、城市、产品类别、预算范围、需求描述、了解渠道、验证码",
                    "confidence": 0.9,
                    "impact_zh": "研究表明表单字段超过 5 个时，每增加一个字段转化率下降约 10%。12 个字段可能导致 60% 以上的潜在客户放弃填写。",
                    "action_zh": "保留 4-5 个核心字段（姓名、邮箱、电话、需求描述），将其余字段移至二次跟进环节。",
                    "needs_account": False,
                    "code_snippet": None,
                    "code_language": None,
                    "paste_location": None,
                },
            ],
        },
        {
            "icon": "🔍",
            "title_zh": "信任度内容梳理",
            "title_en": "Trust Content Audit",
            "score": 55,
            "summary_html": "<p>网站有产品详情页但缺少博客/资讯板块和客户案例。产品页面可信度元素不完整。</p>",
            "data_table": None,
            "findings": [
                {
                    "severity": "P1",
                    "rule_id": "TRUST-001",
                    "title_zh": "未检测到博客/资讯内容板块",
                    "evidence": "爬取路径 /blog, /news, /resources, /articles, /insights 均返回 404。站点地图中无内容页面。",
                    "confidence": 0.9,
                    "impact_zh": "博客内容是 Google SEO 的核心信号，也是建立行业权威的主要途径。无内容板块意味着放弃了自然搜索流量。",
                    "action_zh": "建议按三类内容矩阵规划: 行业趋势（吸引决策者）、产品实操（转化技术买家）、产品动态（维护现有客户）。",
                    "needs_account": False,
                    "code_snippet": None,
                    "code_language": None,
                    "paste_location": None,
                },
            ],
        },
        {
            "icon": "📊",
            "title_zh": "表单提交数据追踪",
            "title_en": "Conversion Tracking Audit",
            "score": 20,
            "summary_html": "<p>检测到 Google Ads 广告代码，但转化追踪链路完全缺失。广告预算处于'盲投'状态。</p>",
            "data_table": None,
            "findings": [
                {
                    "severity": "P0",
                    "rule_id": "TRACK-001",
                    "title_zh": "Thank You 页面无转化追踪代码",
                    "evidence": "Thank You 页面 (https://example-tech.com/thank-you) DOM 中未检测到 gtag('event', 'conversion', ...) 或 dataLayer.push 调用。已检测到 Google Ads tag (AW-123456789) 在首页。",
                    "confidence": 0.85,
                    "impact_zh": "Google Ads 无法将广告点击关联到表单提交。Smart Bidding 算法缺少转化信号，会持续投放低质量流量。这是广告预算浪费的最大单一原因。",
                    "action_zh": "在 Thank You 页面 <head> 中添加 Google Ads 转化追踪代码。",
                    "needs_account": True,
                    "code_snippet": "<!-- Google Ads 转化追踪 -->\n<!-- 粘贴到 Thank You 页面的 <head> 中 -->\n<script async src=\"https://www.googletagmanager.com/gtag/js?id=AW-123456789\"></script>\n<script>\n  window.dataLayer = window.dataLayer || [];\n  function gtag(){dataLayer.push(arguments);}\n  gtag('js', new Date());\n  gtag('config', 'AW-123456789');\n  // 转化事件\n  gtag('event', 'conversion', {\n    'send_to': 'AW-123456789/CONVERSION_LABEL',\n    'value': 1.0,\n    'currency': 'USD'\n  });\n</script>",
                    "code_language": "HTML",
                    "paste_location": "Thank You 页面 → <head> 标签内",
                },
                {
                    "severity": "P1",
                    "rule_id": "TRACK-002",
                    "title_zh": "未检测到 Consent Mode v2",
                    "evidence": "DOM 中未发现 gtag('consent', 'default', ...) 调用。Google 自 2024 年起要求欧盟地区必须实装 Consent Mode v2。",
                    "confidence": 0.8,
                    "impact_zh": "如果您投放欧盟市场的 Google Ads，缺少 Consent Mode v2 将导致 remarketing 和 conversion tracking 在欧盟用户中完全失效。",
                    "action_zh": "在所有页面 gtag 初始化之前添加 Consent Mode 默认设置。",
                    "needs_account": True,
                    "code_snippet": "<!-- Consent Mode v2 默认设置 -->\n<!-- 必须放在所有 gtag 代码之前 -->\n<script>\n  window.dataLayer = window.dataLayer || [];\n  function gtag(){dataLayer.push(arguments);}\n  gtag('consent', 'default', {\n    'ad_storage': 'denied',\n    'ad_user_data': 'denied',\n    'ad_personalization': 'denied',\n    'analytics_storage': 'granted'\n  });\n</script>",
                    "code_language": "HTML",
                    "paste_location": "所有页面 <head> 最顶部（在 gtag.js 之前）",
                },
            ],
        },
    ],
    "readiness_items": [
        {"name": "Google Analytics 4", "status": "partial", "description": "已安装但未配置转化事件"},
        {"name": "Google Tag Manager", "status": "not-ready", "description": "未安装"},
        {"name": "Consent Mode v2", "status": "not-ready", "description": "未检测到"},
        {"name": "Enhanced Conversions", "status": "not-ready", "description": "未配置用户数据匹配"},
        {"name": "reCAPTCHA", "status": "not-ready", "description": "未安装任何版本"},
        {"name": "Core Web Vitals", "status": "partial", "description": "中国地区合格，海外不达标"},
    ],
    "recommendations": {
        "blog_content_matrix": {
            "description": "内容矩阵分类指南 -- 按三个维度规划博客内容",
            "categories": [
                {
                    "name": "行业趋势",
                    "purpose": "吸引决策层关注，建立行业权威",
                    "topics": [
                        "2026年智能硬件行业出海趋势报告",
                        "欧美市场准入政策变化解读",
                        "跨境电商智能硬件品类竞争格局分析",
                        "AI 技术如何重塑智能硬件供应链",
                        "欧美消费者偏好变化与选品策略",
                    ],
                    "frequency": "每月 2 篇",
                    "seo_value": "长尾关键词覆盖，提升自然搜索排名",
                },
                {
                    "name": "产品实操",
                    "purpose": "转化技术型买家，展示专业能力",
                    "topics": [
                        "产品选型指南：如何选择适合欧美市场的智能传感器",
                        "智能传感器安装/使用教程（图文+视频）",
                        "常见问题解答 (FAQ) 与故障排除",
                        "智能传感器维护保养最佳实践",
                        "客户案例：Bosch 如何通过智能传感器提升效率",
                    ],
                    "frequency": "每月 3-4 篇",
                    "seo_value": "产品关键词密度提升，直接驱动询盘",
                },
                {
                    "name": "产品动态",
                    "purpose": "维护现有客户关系，传递品牌活力",
                    "topics": [
                        "新品发布：X200 系列智能传感器正式上线",
                        "参展回顾：某某科技亮相 CES 2026",
                        "认证更新：获得 UL 国际认证",
                        "产线升级：年产能提升至 500 万件",
                        "合作伙伴：与 Siemens 达成战略合作",
                    ],
                    "frequency": "每月 1-2 篇",
                    "seo_value": "品牌关键词强化，提升品牌搜索权重",
                },
            ],
        },
        "whitepaper_template": {
            "description": "白皮书内容结构标准规范",
            "structure": [
                {
                    "section": "封面",
                    "content": "标题 + 副标题 + 公司 logo + 日期",
                    "notes": "标题用数字和痛点吸引（如'2026年智能硬件出海成本降低30%的5个策略'）",
                },
                {
                    "section": "目录",
                    "content": "章节列表 + 页码",
                    "notes": "控制在 8-15 页",
                },
                {
                    "section": "摘要",
                    "content": "核心观点概述（300字以内）",
                    "notes": "让读者 30 秒内决定是否继续阅读",
                },
                {
                    "section": "行业背景",
                    "content": "市场规模 + 增长趋势 + 痛点分析",
                    "notes": "用第三方数据增强可信度（Statista/McKinsey/行业报告）",
                },
                {
                    "section": "解决方案",
                    "content": "分 3-5 个子章节展开",
                    "notes": "每个子章节：问题描述 -> 解决路径 -> 数据佐证 -> 案例",
                },
                {
                    "section": "案例研究",
                    "content": "1-2 个客户成功案例",
                    "notes": "格式：挑战 -> 方案 -> 结果（用具体数字）",
                },
                {
                    "section": "行动建议",
                    "content": "3-5 条具体可执行的建议",
                    "notes": "每条建议注明实施难度和预期效果",
                },
                {
                    "section": "留资转化",
                    "content": "CTA + 联系方式 + 二维码",
                    "notes": "白皮书的最终目的是获取联系方式",
                },
            ],
            "conversion_design": (
                "在白皮书下载页设置表单（姓名+邮箱+公司），"
                "下载完成后跳转 Thank You 页面并触发转化追踪代码"
            ),
        },
        "product_page_template": {
            "description": "高转化产品详情页模板与设计规范",
            "sections": [
                {
                    "name": "Hero 区域",
                    "elements": [
                        "产品主图（白底高清，至少 1200x1200px）",
                        "产品名称 + 一句话卖点",
                        "核心参数快速预览（3-5个）",
                        "CTA 按钮（询价/下载资料）",
                    ],
                    "priority": "必须",
                },
                {
                    "name": "可信度数据",
                    "elements": [
                        "年产量/出货量",
                        "服务客户数量",
                        "行业经验年数",
                        "质检通过率",
                    ],
                    "priority": "必须",
                },
                {
                    "name": "产品工作原理",
                    "elements": [
                        "技术原理图/流程图",
                        "核心技术优势说明",
                        "应用场景展示",
                    ],
                    "priority": "推荐",
                },
                {
                    "name": "产品参数",
                    "elements": [
                        "完整规格参数表（表格形式）",
                        "包装信息",
                        "物流/交期信息",
                    ],
                    "priority": "必须",
                },
                {
                    "name": "合规与安全认证",
                    "elements": [
                        "ISO/CE/FDA/SGS 认证 logo",
                        "检测报告编号（可查询）",
                        "合规声明",
                    ],
                    "priority": "必须",
                },
                {
                    "name": "客户背书",
                    "elements": [
                        "客户评价/推荐信",
                        "合作品牌 logo 墙",
                        "案例研究链接",
                    ],
                    "priority": "强烈推荐",
                },
                {
                    "name": "相似产品横向对比",
                    "elements": [
                        "对比表格（vs 竞品 A/B/C）",
                        "差异化优势高亮",
                        "价格区间参考",
                    ],
                    "priority": "推荐",
                },
            ],
        },
    },
    "form_best_practices": {
        "recommended_fields_by_funnel": [
            {
                "stage": "漏斗顶部（TOFU）",
                "purpose": "最大化线索量，降低获客成本",
                "fields": ["姓名", "邮箱"],
                "field_count": 2,
                "expected_conversion": "15-25%",
                "use_case": "白皮书下载、Newsletter 订阅、行业报告",
            },
            {
                "stage": "漏斗中部（MOFU）",
                "purpose": "筛选意向客户，获取业务背景",
                "fields": ["姓名", "邮箱", "公司", "职位"],
                "field_count": 4,
                "expected_conversion": "8-12%",
                "use_case": "产品演示申请、方案咨询、案例下载",
            },
            {
                "stage": "漏斗底部（BOFU）",
                "purpose": "获取高意向销售线索，支持销售跟进",
                "fields": ["姓名", "邮箱", "电话", "公司", "职位", "需求描述"],
                "field_count": 6,
                "expected_conversion": "3-5%",
                "use_case": "报价申请、定制方案、销售咨询",
            },
        ],
        "design_guidelines": [
            {
                "guideline": "单列垂直布局",
                "benchmark": "比水平布局转化率高 15.2%（CXL 2024）",
            },
            {
                "guideline": "价值导向的提交按钮文案",
                "benchmark": '"获取报价" vs "提交" 转化率高 28%（Unbounce 2024）',
            },
            {
                "guideline": "隐私声明/数据保护提示",
                "benchmark": "可提升转化率 19%（Baymard Institute 2025）",
            },
            {
                "guideline": "多步表单（分步骤填写）",
                "benchmark": "比同等字段的单页表单转化率高 37%（Formstack 2025）",
            },
            {
                "guideline": "进度指示器",
                "benchmark": "多步表单加进度条后完成率提升 12%",
            },
        ],
        "field_friction_benchmarks": {
            "source": "HubSpot 2024 + Formstack 2025",
            "per_field_conversion_drop": "4.1%",
            "abandonment_rate_above_7_fields": "67.8%",
            "optimal_field_count": "3-5",
        },
        "spam_benchmarks": {
            "source": "Formstack 2025",
            "unprotected_spam_rate": "99%",
            "recaptcha_v3_block_rate": "97%",
            "turnstile_block_rate": "95%",
        },
    },
    "next_steps_text": "本报告中标记为 P0 的 3 个问题建议在 7 天内优先处理。如需我们协助实施，请联系以下方式预约技术咨询。",
    "contact_email": "admin@canlah.ai",
    "contact_wechat": "CanlahAI",
    "contact_phone": "+86 138-xxxx-xxxx",
}


def render_html(data: dict) -> str:
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=False)
    tmpl = env.get_template("eac-report.html.j2")
    return tmpl.render(**data)


def main():
    html = render_html(DEMO_DATA)
    out = Path(__file__).parent / "output"
    out.mkdir(exist_ok=True)
    html_path = out / "eac-demo-report.html"
    html_path.write_text(html, encoding="utf-8")
    print(f"HTML report written to {html_path}")
    print(f"Open in browser: file://{html_path.resolve()}")


if __name__ == "__main__":
    main()
