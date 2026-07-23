#!/usr/bin/env python3
"""
简历进化系统 · Headhunter Agent
===============================
职责：扫描四大求职方向的招聘市场数据（HC = Headcount）
方向：项目经理 / 产品经理 / 商业分析 / 战略规划
数据来源：LinkedIn / BOSS直聘 / 猎聘 / 拉勾
输出：data/market_hc.json（最新）+ data/market_hc.jsonl（追加历史）
"""

import json
import re
import time
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import quote

# ─────────────────────────────────────────────
# 配置
# ─────────────────────────────────────────────
WORKSPACE = Path(__file__).parent.parent
DATA_DIR   = WORKSPACE / "data"
CONFIG_FILE = DATA_DIR / "config.json"

# 四大求职方向
TRACKS = {
    "pm": {
        "label": "项目经理",
        "keywords": [
            "高级项目经理", "AI项目经理", "研发项目经理", "PMO",
            "项目集经理", "Scrum Master", "敏捷项目经理", "DevOps项目经理",
            "互联网项目经理", "软件项目经理"
        ],
        "exclude": ["销售", "实施", "客服", "市场推广"],
    },
    "product": {
        "label": "产品经理",
        "keywords": [
            "产品经理", "AI产品经理", "数字化产品经理",
            "C端产品经理", "B端产品经理", "数据产品经理",
            "高级产品经理", "出海产品经理", "社交产品经理"
        ],
        "exclude": ["运营", "推广", "商务"],
    },
    "ba": {
        "label": "商业分析",
        "keywords": [
            "商业分析", "研发效能", "数据分析", "BA",
            "商业数据分析师", "效能分析师", "HR分析师",
            "BI分析师", "数据运营", "指标分析师"
        ],
        "exclude": ["销售", "客服", "市场"],
    },
    "strategy": {
        "label": "战略规划",
        "keywords": [
            "战略规划", "OKR运营", "项目总监", "经营分析",
            "策略经理", "战略BP", "OKR教练", "COO",
            "运营总监", "经营企划"
        ],
        "exclude": ["销售", "市场"],
    },
}

CITIES = ["深圳", "广州", "上海", "北京"]

# ─────────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────────

def load_config():
    with open(CONFIG_FILE, encoding="utf-8") as f:
        return json.load(f)


def load_previous_hc():
    """加载已有HC数据（用于去重）"""
    hc_file = DATA_DIR / "market_hc.json"
    if hc_file.exists():
        with open(hc_file, encoding="utf-8") as f:
            data = json.load(f)
            return {item["url"]: item for item in data.get("listings", [])}
    return {}


def extract_salary(text: str) -> dict:
    """从文本中提取薪资范围"""
    patterns = [
        r"(\d+)K?-(\d+)K", r"(\d+)\s*~?\s*(\d+)\s*K",
        r"(\d+)\s*元/天", r"(\d+\.?\d*)\s*万\s*~\s*(\d+\.?\d*)\s*万",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            groups = m.groups()
            nums = [float(g) for g in groups if g]
            if len(nums) == 2:
                if nums[0] < 100:  # 假设单位K
                    low, high = nums[0], nums[1]
                else:  # 单位万
                    low, high = nums[0] * 10, nums[1] * 10
                return {"low": low, "high": high, "unit": "K", "raw": m.group()}
    return {"low": None, "high": None, "unit": None, "raw": None}


def detect_requirements(jd_text: str) -> list:
    """从JD描述中提取关键词（技能要求）"""
    # 优先关键词
    priority_keywords = [
        "PMP", "ACP", "NPDP", "Scrum", "SAFe", "DevOps",
        "AI", "LLM", "Agent", "大模型", "机器学习",
        "OKR", "KPI", "PEST", "SWOT", "五力模型",
        "SQL", "Python", "数据分析", "BI", "Tableau", "PowerBI",
        "Jira", "Confluence", "飞书", "MS Project",
        "GDPR", "LGPD", "合规", "出海", "跨境",
        "英语", "口语", "CET", "雅思",
        "数字化转型", "智能化", "SaaS", "B端", "C端",
        "ROI", "北极星指标", "A/B测试", "灰度发布",
        "敏捷", "持续交付", "CI/CD", "自动化测试",
        "跨部门", "多方协同", "治理", "PMO",
    ]
    found = []
    text_upper = jd_text.upper()
    for kw in priority_keywords:
        if kw.upper() in text_upper or kw in jd_text:
            found.append(kw)
    return found[:8]  # 最多取8个


def normalize_listing(raw: dict, track: str, source: str) -> dict:
    """标准化一条职位数据"""
    title = raw.get("title", "").strip()
    company = raw.get("company", "").strip()
    location_raw = raw.get("location", "")
    salary_raw = raw.get("salary", "")
    jd_text = raw.get("jd", "") or raw.get("description", "")

    # 城市提取
    city = None
    for c in CITIES:
        if c in location_raw:
            city = c
            break
    if not city:
        city = location_raw[:6] if location_raw else "深圳"

    # 薪资
    salary = extract_salary(salary_raw)

    # 技能要求
    skills = detect_requirements(jd_text)

    # 相关度（粗估：标题含关键词为高）
    score = 0.0
    if track in title: score += 0.3
    if any(kw in title for kw in TRACKS[track]["keywords"][:3]): score += 0.3
    if salary["low"]: score += 0.2
    if any(kw in jd_text for kw in ["PMP", "ACP", "Scrum", "OKR", "AI"]): score += 0.2

    return {
        "id": raw.get("id", hash(title + company + salary_raw) % 10**9),
        "title": title,
        "company": company,
        "location": city,
        "salary": salary,
        "source": source,
        "url": raw.get("url", ""),
        "track": track,
        "track_label": TRACKS[track]["label"],
        "requirements": skills,
        "jd_snippet": jd_text[:300] if jd_text else "",
        "relevance_score": min(score, 1.0),
        "collected_at": datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M"),
    }


def format_listing_for_display(item: dict) -> str:
    """格式化为可读行（用于日志）"""
    salary_str = ""
    if item["salary"]["raw"]:
        salary_str = f" [{item['salary']['raw']}]"
    reqs = " · ".join(item["requirements"][:4]) if item["requirements"] else ""
    return (
        f"  • {item['title']} @ {item['company']} "
        f"({item['location']}){salary_str}\n"
        f"    来源:{item['source']} | 相关度:{item['relevance_score']:.0%} | "
        f"技能:{reqs}"
    )


# ─────────────────────────────────────────────
# 模拟数据生成（实际运行时由 web_search / web_fetch 替换）
# ─────────────────────────────────────────────

def generate_realistic_listings(track: str, config: dict) -> list:
    """
    生成贴近真实市场的模拟职位数据。
    正式运行时替换为 web_search / web_fetch 抓取。
    """
    import random
    random.seed(datetime.now().strftime("%Y%m%d"))  # 每日固定，便于验证

    keywords = config["monitoring"]["keywords_by_track"].get(track, [])

    # 各方向典型雇主池
    employer_pools = {
        "pm": [
            ("腾讯", "深圳"), ("字节跳动", "深圳"), ("美团", "深圳"),
            ("阿里巴巴", "杭州"), ("华为", "深圳"), ("OPPO", "深圳"),
            ("平安科技", "深圳"), ("顺丰科技", "深圳"), ("Shopee", "深圳"),
            ("Lazada", "广州"), ("米哈游", "上海"), ("shein", "南京"),
        ],
        "product": [
            ("腾讯", "深圳"), ("字节跳动", "深圳"), ("阿里", "杭州"),
            ("美团", "深圳"), ("小红书", "上海"), ("快手", "北京"),
            ("B站", "上海"), ("得物", "上海"), ("Shopee", "深圳"),
            ("一加科技", "深圳"), ("大疆", "深圳"),
        ],
        "ba": [
            ("平安银行", "深圳"), ("招商银行", "深圳"), ("腾讯", "深圳"),
            ("字节跳动", "深圳"), ("美团", "深圳"), ("京东", "北京"),
            ("华为", "深圳"), ("阿里云", "杭州"),
        ],
        "strategy": [
            ("美团", "深圳"), ("字节跳动", "深圳"), ("腾讯", "深圳"),
            ("阿里巴巴", "杭州"), ("京东", "北京"), ("华为", "深圳"),
            ("平安集团", "深圳"), ("联想", "北京"),
        ],
    }

    # 各方向典型薪资（深圳，中位数范围）
    salary_ranges = {
        "pm":      (22, 45),
        "product": (20, 38),
        "ba":      (16, 28),
        "strategy":(22, 50),
    }

    companies = employer_pools.get(track, employer_pools["pm"])
    kw = keywords[0] if keywords else TRACKS[track]["keywords"][0]
    lo, hi = salary_ranges[track]

    listings = []
    for i, (company, city) in enumerate(random.sample(companies, min(8, len(companies)))):
        salary_low = random.randint(lo, hi - 5)
        salary_high = salary_low + random.randint(5, 15)
        salary_str = f"{salary_low}-{salary_high}K"

        # 生成带关键词的标题
        prefixes = ["", "高级", "资深", "AI"]
        prefix = random.choice(prefixes)
        title = f"{prefix}{kw}" if prefix else kw

        # 模拟JD
        jd_kws = random.sample([
            "PMP优先", "ACP认证优先", "Scrum经验", "AI项目经验",
            "跨境合规", "GDPR", "出海项目", "英语可工作",
            "OKR运营经验", "跨部门协调", "DevOps", "Jira",
            "数据驱动", "ROI评估", "指标体系", "SaaS",
            "C端产品", "B端产品", "0-1产品", "用户增长",
        ], k=random.randint(3, 6))
        jd_text = f"任职要求：{' / '.join(jd_kws)}"

        listings.append({
            "id": hash(f"{track}{company}{i}{datetime.now().date()}") % 10**9,
            "title": title,
            "company": company,
            "location": city,
            "salary": salary_str,
            "jd": jd_text,
            "url": f"https://example.com/job/{track}/{i}",
        })

    return listings


# ─────────────────────────────────────────────
# 主流程
# ─────────────────────────────────────────────

def run(limit_per_track: int = 15) -> dict:
    """
    执行猎取流程：
    1. 加载配置和已有数据
    2. 对每个Track搜索关键词
    3. 去重、标准化
    4. 保存 market_hc.json + market_hc.jsonl
    """
    print("=" * 60)
    print("🔍 简历进化系统 · Headhunter Agent")
    print(f"   执行时间：{datetime.now(timezone(timedelta(hours=8))):%Y-%m-%d %H:%M} (北京时间)")
    print("=" * 60)

    config = load_config()
    previous = load_previous_hc()
    all_new = []
    summary = {}

    for track, cfg in TRACKS.items():
        print(f"\n📡 扫描 Track [{track}]：{cfg['label']}")
        print("-" * 48)

        track_listings = []

        # 正式：web_search / web_fetch → 这里用模拟数据替代
        raw_listings = generate_realistic_listings(track, config)

        for raw in raw_listings:
            item = normalize_listing(raw, track, source="模拟")
            # 去重（同标题同公司跳过）
            key = f"{item['title']}@{item['company']}"
            if key in [f"{i['title']}@{i['company']}" for i in all_new]:
                continue
            if item["relevance_score"] < 0.3:
                continue
            all_new.append(item)
            track_listings.append(item)

        # 显示
        print(f"  找到 {len(track_listings)} 个有效岗位：")
        for item in track_listings[:5]:
            print(format_listing_for_display(item))
        if len(track_listings) > 5:
            print(f"  ... 还有 {len(track_listings)-5} 个")

        summary[track] = {
            "label": cfg["label"],
            "found": len(track_listings),
            "avg_salary": _avg_salary(track_listings),
            "top_skills": _top_skills(track_listings),
        }

    # ── 汇总统计 ──
    total = len(all_new)
    print(f"\n{'=' * 60}")
    print(f"✅ 本次扫描完成：共 {total} 个有效岗位")
    print(f"   项目经理 : {summary['pm']['found']} 个 | 平均 {summary['pm']['avg_salary']}")
    print(f"   产品经理 : {summary['product']['found']} 个 | 平均 {summary['product']['avg_salary']}")
    print(f"   商业分析 : {summary['ba']['found']} 个 | 平均 {summary['ba']['avg_salary']}")
    print(f"   战略规划 : {summary['strategy']['found']} 个 | 平均 {summary['strategy']['avg_salary']}")

    # ── 保存 JSON（最新）──
    DATA_DIR.mkdir(exist_ok=True)
    output = {
        "generated_at": datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M"),
        "total_listings": total,
        "by_track": {t: summary[t]["found"] for t in TRACKS},
        "salary_ranges": {t: summary[t]["avg_salary"] for t in TRACKS},
        "top_skills": {t: summary[t]["top_skills"] for t in TRACKS},
        "listings": all_new,
    }
    hc_path = DATA_DIR / "market_hc.json"
    with open(hc_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n📄 已保存：{hc_path}")

    # ── 追加到历史 ──
    jsonl_path = DATA_DIR / "market_hc.jsonl"
    with open(jsonl_path, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "ts": datetime.now(timezone(timedelta(hours=8))).isoformat(),
            "total": total,
            "by_track": {t: summary[t]["found"] for t in TRACKS},
        }, ensure_ascii=False) + "\n")
    print(f"📜 已追加历史：{jsonl_path}")

    return output


def _avg_salary(listings: list) -> str:
    salaries = [l["salary"] for l in listings if l["salary"]["low"]]
    if not salaries:
        return "面议"
    avg_low = sum(s["low"] for s in salaries) / len(salaries)
    avg_high = sum(s["high"] for s in salaries) / len(salaries)
    return f"{avg_low:.0f}-{avg_high:.0f}K"


def _top_skills(listings: list) -> list:
    from collections import Counter
    skills = []
    for l in listings:
        skills.extend(l.get("requirements", []))
    if not skills:
        return []
    top = Counter(skills).most_common(5)
    return [k for k, _ in top]


if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    result = run(limit)
    print(f"\n🎯 Headhunter 完成，返回 {result['total_listings']} 条数据")
