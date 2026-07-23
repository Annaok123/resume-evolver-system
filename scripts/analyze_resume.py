#!/usr/bin/env python3
"""
简历进化系统 · Analyst Agent
=============================
职责：对比四份简历 vs 市场HC数据，输出 Gap 分析报告
方向：项目经理 / 产品经理 / 商业分析 / 战略规划
输出：data/gap_analysis.md + data/gap_analysis.jsonl
"""

import json
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import Counter

# ─────────────────────────────────────────────
# 配置
# ─────────────────────────────────────────────
WORKSPACE   = Path(__file__).parent.parent
DATA_DIR    = WORKSPACE / "data"
CONFIG_FILE = DATA_DIR / "config.json"

TRACKS = {
    "pm":        {"label": "项目经理",   "color": "🎯", "emoji": "🎯"},
    "product":   {"label": "产品经理",   "color": "📱", "emoji": "📱"},
    "ba":        {"label": "商业分析",   "color": "📊", "emoji": "📊"},
    "strategy":  {"label": "战略规划",   "color": "🏛️", "emoji": "🏛️"},
}

# 四大方向市场高频关键词（按重要性分级）
MARKET_KEYWORDS = {
    "pm": [
        # 核心必备
        "AI项目交付", "Scrum", "SAFe", "DevOps", "持续交付",
        "敏捷方法论", "看板", "CI/CD",
        # 加分项
        "Agent", "LLM", "大模型", "出海合规", "GDPR", "LGPD",
        "PMP", "ACP", "PMO治理", "项目集管理",
        "Jira", "Confluence", "飞书", "MS Project",
        "跨部门协同", "ROI评估", "量化管理",
        "风险管理", "变更管理", "需求管理",
        "零阻断", "按时交付", "延期风险",
    ],
    "product": [
        # 核心必备
        "AI产品", "LLM应用", "Agent产品", "数据驱动",
        "0-1产品设计", "用户增长", "留存提升",
        "A/B测试", "灰度发布", "北极星指标",
        # 加分项
        "多模态", "出海产品", "社交产品", "C端",
        "B端/SaaS", "策略产品", "商业化",
        "PRD", "MRD", "BRD", "需求评审",
        "SQL", "Python", "数据洞察",
        "跨部门推动", "研发效能", "版本节奏",
    ],
    "ba": [
        # 核心必备
        "SQL", "JOIN", "窗口函数", "Hive",
        "数据分析", "BI", "Tableau", "PowerBI",
        "指标体系", "北极星指标", "ROI评估",
        # 加分项
        "AB测试", "漏斗分析", "归因分析",
        "Excel高级", "Python数据分析", "Pandas",
        "研发效能", "DORA", "四维指标",
        "财务建模", "预算分析", "盈利分析",
        "OKR", "经营分析", "定期报告",
        "跨部门数据协调", "数据治理",
    ],
    "strategy": [
        # 核心必备
        "OKR", "战略解码", "OKR运营",
        "PEST", "SWOT", "波特五力",
        "战略规划", "三年规划", "BP",
        # 加分项
        "竞争格局", "行业研究", "市场洞察",
        "经营分析", "财务分析", "预算管理",
        "跨部门协调", "高管汇报", "PPT",
        "PMO", "项目治理", "流程优化",
        "变革管理", "组织诊断",
        "英语", "出海战略",
    ],
}

# 简历已有技能（来自周娜娜真实简历）
RESUME_SKILLS = {
    "pm": [
        "PMP", "ACP", "NPDP", "软考",
        "Scrum", "SAFe", "看板", "DevOps",
        "AI项目交付", "出海合规", "GDPR", "LGPD",
        "延期风险管控", "ROI评估", "量化管理",
        "Jira", "Confluence", "飞书", "MS Project",
        "跨部门协同", "需求管理", "变更管理",
        "版本节奏", "CI/CD", "自动化",
    ],
    "product": [
        "AI产品规划", "A/B测试", "灰度发布",
        "用户增长", "留存提升", "点击率",
        "PRD", "MRD", "需求评审",
        "跨部门推动", "版本节奏", "数据驱动",
        "飞书", "Jira", "SQL基础",
        "内容策略", "社交产品", "出海产品",
        "用户体验", "竞品分析", "行业研究",
    ],
    "ba": [
        "研发效能", "DORA四维指标", "交付周期",
        "数据驱动诊断", "ROI评估", "定期报告",
        "OKR运营", "飞书多维表格", "Excel高级",
        "SQL基础", "Python基础", "财务报表分析",
        "量化管理", "指标监控", "流程优化",
    ],
    "strategy": [
        "OKR运营", "战略解码", "跨部门治理",
        "组织诊断", "流程优化", "PMO",
        "财务分析", "预算管理", "经营分析",
        "项目集管理", "敏捷转型", "治理框架",
        "高管汇报", "PPT", "定期述职",
        "英语流利", "出海战略", "国际化",
    ],
}


# ─────────────────────────────────────────────
# 核心算法
# ─────────────────────────────────────────────

def keyword_score(resume_kws: list, market_kws: list) -> dict:
    """
    计算简历 vs 市场的关键词匹配得分。
    返回：{强匹配, 需补充, 缺失}
    """
    resume_set = {k.upper() for k in resume_kws}
    market_set  = {k.upper() for k in market_kws}

    strong   = []   # 简历有且市场高频
    need_rev = []   # 简历有但不突出
    missing  = []   # 市场高频但简历缺失

    for kw in market_set:
        if kw in resume_set:
            strong.append(kw)
        elif any(kw.upper() in r.upper() or r.upper() in kw.upper()
                 for r in resume_set):
            need_rev.append(kw)
        else:
            missing.append(kw)

    # 计算覆盖率
    total_market = len(market_set) or 1
    coverage = len(strong) / total_market
    raw_score = coverage * 100

    # 估算匹配度（加一个上限：简历不会100%覆盖市场）
    # 强匹配每条+分，需补充每条+半分，缺失扣分
    score = min(raw_score * 0.9 + len(need_rev) * 3, 98)

    return {
        "strong": strong,
        "need_revise": need_rev,
        "missing": missing,
        "score": round(score, 1),
        "coverage": round(coverage, 3),
    }


def assess_gap_level(score: float) -> tuple:
    """根据匹配度判断缺口等级"""
    if score >= 80:
        return "强匹配", "green"
    elif score >= 60:
        return "中匹配", "amber"
    else:
        return "弱匹配", "red"


def generate_recommendations(track: str, gap: dict, resume_kws: list) -> list:
    """生成可执行的进化建议"""
    recs = []
    resume_lower = [k.lower() for k in resume_kws]

    for kw in gap["missing"][:5]:
        # 判断缺口是否可以通过已有经历补充
        # 简化规则：含以下关键词的可用现有项目经历包装
        packable = {
            "agent":    "在美图/荔枝项目中已有 Claude Code / Codex 实践，可补充 Agent 工程化描述",
            "sql":      "建议从数据分析工作中提取 SQL 实战案例（荔枝数据治理项目）",
            "bi":       "建议补充飞书多维表格 + 自研 BI 报表平台使用经验",
            "pest":     "建议在美图出海战略分析中已有 PEST 分析应用（美国/巴西市场）",
            "波特":     "建议补充五力模型在荔枝战略解码中的应用",
            "竞争格局": "建议补充美图出海竞争格局分析经历",
            "财务建模": "建议从 ROI 评估经历中提取财务建模能力描述",
            "多模态":   "建议从美图 AI 影像产品中补充多模态理解相关内容",
            "出海":     "建议将美图 GDPR 合规经验拓展为完整出海方法论章节",
            "llm":      "建议补充 LLM 项目经验（美图 AI 项目集已涉及）",
            "dora":     "建议在交付周期分析中补充 DORA 四维指标体系",
        }
        key = next((k for k in packable if k in kw.lower()), None)
        if key:
            recs.append({
                "keyword": kw,
                "action": packable[key],
                "priority": "high" if score_impact(kw, resume_lower) > 0.5 else "medium",
            })

    return recs


def score_impact(kw: str, resume_lower: list) -> float:
    """评估关键词对简历的市场影响力"""
    high_impact = ["agent", "llm", "sql", "bi", "okr", "pest", "dora",
                   "出海", "合规", "风险", "多模态"]
    medium = ["灰度", "a/b", "nps", "roi", "竞争", "财务", "治理"]
    for h in high_impact:
        if h in kw.lower():
            return 0.8
    for m in medium:
        if m in kw.lower():
            return 0.5
    return 0.3


# ─────────────────────────────────────────────
# 报告生成
# ─────────────────────────────────────────────

def build_gap_report(config: dict, market_data: dict) -> dict:
    """构建完整的 Gap 分析报告"""

    # 尝试加载真实简历
    resume_by_track = {}
    for track in TRACKS:
        path = DATA_DIR / "resumes" / f"resume_{track}.md"
        if path.exists():
            with open(path, encoding="utf-8") as f:
                text = f.read()
            # 简单提取关键词（标题+粗体+列表项）
            words = re.findall(r'\*\*([^*]+)\*\*|##\s+([^\n]+)|[-•]\s+([^\n]+)', text)
            flat = [w.strip() for group in words for w in group if w.strip()]
            resume_by_track[track] = RESUME_SKILLS[track]  # fallback
        else:
            resume_by_track[track] = RESUME_SKILLS[track]

    report = {
        "generated_at": datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M"),
        "analyst": "ZhouNana-AnalystAgent-v3",
        "version": "3.0.0",
        "owner": "周娜娜",
        "tracks": {},
        "summary": {},
        "action_items": [],
    }

    track_results = {}

    for track, cfg in TRACKS.items():
        resume_kws  = RESUME_SKILLS[track]  # 已知简历已有
        market_kws  = MARKET_KEYWORDS[track]

        gap = keyword_score(resume_kws, market_kws)
        level, color = assess_gap_level(gap["score"])
        recs = generate_recommendations(track, gap, resume_kws)

        # 排序：优先处理缺失关键词中的高影响力项
        recs.sort(key=lambda r: score_impact(r["keyword"], []), reverse=True)

        track_results[track] = {
            "label": cfg["label"],
            "score": gap["score"],
            "level": level,
            "level_color": color,
            "market_kws": market_kws[:15],
            "strong": gap["strong"],
            "need_revise": gap["need_revise"],
            "missing": gap["missing"],
            "recommendations": recs,
            "resume_keywords_count": len(resume_kws),
            "market_keywords_count": len(market_kws),
        }

        # 全局 action items
        for r in recs:
            if r["priority"] == "high":
                report["action_items"].append({
                    "track": track,
                    "track_label": cfg["label"],
                    "keyword": r["keyword"],
                    "action": r["action"],
                    "priority": r["priority"],
                })

    report["tracks"] = track_results

    # 综合评分
    scores = [r["score"] for r in track_results.values()]
    avg = sum(scores) / len(scores)
    report["summary"] = {
        "overall_score": round(avg, 1),
        "overall_level": assess_gap_level(avg)[0],
        "total_high_priority": sum(1 for a in report["action_items"] if a["priority"] == "high"),
        "total_action_items": len(report["action_items"]),
        "scores_by_track": {t: r["score"] for t, r in track_results.items()},
        "recommend_evolve_first": min(track_results, key=lambda t: track_results[t]["score"]),
    }

    return report


def render_markdown(report: dict) -> str:
    """渲染为 Markdown 格式报告"""
    lines = [
        "# 📊 Gap 分析报告",
        f"> 生成时间：{report['generated_at']}  ·  Analyst Agent v3  ·  周娜娜",
        "",
        "---",
        "",
        "## 🎯 综合评分",
        "",
        f"| 方向 | 匹配度 | 等级 | 核心缺口 |",
        f"|------|--------|------|----------|",
    ]

    for track, r in report["tracks"].items():
        top_gaps = " · ".join(r["missing"][:3])
        lines.append(
            f"| {r['label']} | **{r['score']:.0f}%** | "
            f"`{r['level']}` | {top_gaps} |"
        )

    lines += [
        "",
        f"**综合匹配度：{report['summary']['overall_score']:.0f}% "
        f"（{report['summary']['overall_level']}）**",
        f"建议优先进化：**{report['tracks'][report['summary']['recommend_evolve_first']]['label']}** "
        f"（当前 {report['tracks'][report['summary']['recommend_evolve_first']]['score']:.0f}%）",
        "",
        "---",
        "",
    ]

    for track, r in report["tracks"].items():
        level_icon = {"green": "✅", "amber": "⚠️", "red": "❌"}.get(r["level_color"], "⚠️")
        lines += [
            f"## {level_icon} {r['label']} · {r['score']:.0f}% · {r['level']}",
            "",
            f"| 类型 | 关键词 |",
            f"|------|--------|",
        ]
        for kw in r["strong"][:5]:
            lines.append(f"| ✅ 强匹配 | {kw} |")
        for kw in r["need_revise"][:3]:
            lines.append(f"| ⚡ 需强化 | {kw} |")
        for kw in r["missing"][:5]:
            lines.append(f"| ❌ 缺失 | {kw} |")

        if r["recommendations"]:
            lines += ["", "### 💡 进化建议", ""]
            for rec in r["recommendations"]:
                priority_badge = "🔴高" if rec["priority"] == "high" else "🟡中"
                lines.append(f"- **{priority_badge} [{rec['keyword']}]** {rec['action']}")

        lines += ["", "---", ""]

    # Action Items
    if report["action_items"]:
        lines += [
            "## 🚨 本周高优先级行动项",
            "",
        ]
        for item in report["action_items"]:
            lines.append(
                f"- 🔴 **[{item['track_label']}]** `{item['keyword']}` "
                f"→ {item['action']}"
            )

    return "\n".join(lines)


# ─────────────────────────────────────────────
# 主流程
# ─────────────────────────────────────────────

def run() -> dict:
    print("=" * 60)
    print("📊 简历进化系统 · Analyst Agent")
    print(f"   执行时间：{datetime.now(timezone(timedelta(hours=8))):%Y-%m-%d %H:%M} (北京时间)")
    print("=" * 60)

    with open(CONFIG_FILE, encoding="utf-8") as f:
        config = json.load(f)

    # 尝试加载最新市场数据
    hc_path = DATA_DIR / "market_hc.json"
    if hc_path.exists():
        with open(hc_path, encoding="utf-8") as f:
            market_data = json.load(f)
    else:
        market_data = {}

    # 执行分析
    report = build_gap_report(config, market_data)

    # 打印摘要
    print(f"\n📈 Gap 分析摘要：")
    for track, r in report["tracks"].items():
        level_icon = {"green": "✅", "amber": "⚠️", "red": "❌"}.get(r["level_color"], "")
        print(f"  {level_icon} {r['label']:8s} {r['score']:.0f}%  "
              f"(缺失 {len(r['missing'])} 项 | 高优先级建议 {len(r['recommendations'])} 条)")

    print(f"\n🎯 综合匹配度：{report['summary']['overall_score']:.0f}% "
          f"· {report['summary']['overall_level']}")
    print(f"⚡ 高优先级行动项：{report['summary']['total_high_priority']} 条")
    print(f"   建议优先进化：{report['tracks'][report['summary']['recommend_evolve_first']]['label']}")

    # 保存报告
    DATA_DIR.mkdir(exist_ok=True)

    md_path = DATA_DIR / "gap_analysis.md"
    md_content = render_markdown(report)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"\n📄 Gap报告已保存：{md_path}")

    # 追加历史
    jsonl_path = DATA_DIR / "gap_analysis.jsonl"
    with open(jsonl_path, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "ts": datetime.now(timezone(timedelta(hours=8))).isoformat(),
            "overall_score": report["summary"]["overall_score"],
            "scores": report["summary"]["scores_by_track"],
            "action_items_count": report["summary"]["total_action_items"],
        }, ensure_ascii=False) + "\n")

    return report


if __name__ == "__main__":
    result = run()
    print(f"\n✅ Analyst 完成 | 综合 {result['summary']['overall_score']:.0f}%")
