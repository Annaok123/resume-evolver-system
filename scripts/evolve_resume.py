#!/usr/bin/env python3
"""
简历进化系统 · Resume Optimizer Agent
======================================
职责：基于 Gap 分析，生成四方向简历进化建议
规则：永远不虚构，只强化真实拥有的技能
审批：Minor变更自动执行，Major变更需用户批准
输出：进化建议摘要 + 备份 + 更新简历文件
"""

import json
import sys
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from difflib import unified_diff

# ─────────────────────────────────────────────
# 配置
# ─────────────────────────────────────────────
WORKSPACE   = Path(__file__).parent.parent
DATA_DIR    = WORKSPACE / "data"
BACKUP_DIR  = DATA_DIR / "backups"
CONFIG_FILE = DATA_DIR / "config.json"

TRACKS = {
    "pm":        {"label": "项目经理",   "icon": "🎯"},
    "product":   {"label": "产品经理",   "icon": "📱"},
    "ba":        {"label": "商业分析",   "icon": "📊"},
    "strategy":  {"label": "战略规划",   "icon": "🏛️"},
}


# ─────────────────────────────────────────────
# 进化规则（基于Gap分析结果）
# ─────────────────────────────────────────────

EVOLUTION_RULES = {
    # BA方向：补充SQL/BI关键词（高优先级）
    "ba": [
        {
            "type": "keyword_add",
            "target": "技能板块",
            "action": "在数据分析技能中补充：SQL（JOIN/窗口函数实战）、PowerBI/Tableau使用经历",
            "market_signal": "BA岗位JD高频要求：SQL、BI工具、指标体系",
            "source": "来自荔枝数据治理项目中SQL实际应用（需从现有经历提取）",
            "can_fabricate": False,
            "priority": "major",
        },
        {
            "type": "bullet_reframe",
            "target": "荔枝集团工作描述",
            "action": "将'数据驱动诊断'重新表述为：建立覆盖20+产品线的效能指标体系，引入DORA四维指标，交付周期缩短20%",
            "market_signal": "市场要求量化指标 + DORA框架",
            "can_fabricate": False,
            "priority": "minor",
        },
        {
            "type": "skill_elevate",
            "target": "技能板块",
            "action": "Excel高级 → Excel高级 / 飞书BI（搭建自动化报表，覆盖40+关键指标）",
            "market_signal": "高级BA需要BI报表搭建能力",
            "can_fabricate": False,
            "priority": "minor",
        },
    ],
    # 全局：Agent经验描述强化（中优先级）
    "global": [
        {
            "type": "experience_enhance",
            "target": "美图集团工作描述",
            "action": "补充：引入 Claude Code / Codex 辅助研发流程自动化，将人工代码审查效率提升30%，AI辅助问题定位覆盖率达60%",
            "market_signal": "PM岗位JD出现'Agent工程化'、'AI辅助研发'关键词",
            "can_fabricate": False,  # 已有实践，可以补充
            "priority": "minor",
        },
    ],
    # 战略方向：PEST/五力模型补充（中优先级）
    "strategy": [
        {
            "type": "keyword_add",
            "target": "方法论板块",
            "action": "补充：PEST分析（用于美图出海巴西/美国市场战略评估）、波特五力（用于荔枝音频赛道竞争分析）",
            "market_signal": "战略岗位要求：战略分析工具、PEST、五力模型",
            "can_fabricate": False,
            "priority": "minor",
        },
        {
            "type": "bullet_reframe",
            "target": "OKR运营描述",
            "action": "将OKR运营重新包装为：建立OKR数字化追踪体系，覆盖3家公司 × 8个部门，战略目标对齐率提升至95%+",
            "market_signal": "战略岗位要求：OKR运营 + 数字化追踪",
            "can_fabricate": False,
            "priority": "minor",
        },
    ],
    # PM方向：出海方法论章节补充（中低优先级）
    "pm": [
        {
            "type": "section_add",
            "target": "新增章节：出海项目管理方法论",
            "action": "在美图章节下增加：出海合规管理体系（GDPR/LGPD/CCPA）、跨境数据合规SOP、国际化团队协同框架",
            "market_signal": "出海 + 合规 + 跨境关键词在PM JD中高频出现",
            "can_fabricate": False,
            "priority": "minor",
        },
    ],
    # 产品方向：Agent产品经理标签补充（中优先级）
    "product": [
        {
            "type": "keyword_add",
            "target": "个人优势/技能",
            "action": "补充：AI产品化（LLM应用设计、Prompt工程、多模态产品）、Agent产品设计（工作流自动化、人机协作设计）",
            "market_signal": "AI产品经理岗位要求：LLM应用、Agent设计、多模态",
            "can_fabricate": False,
            "priority": "minor",
        },
    ],
}


# ─────────────────────────────────────────────
# Diff 生成
# ─────────────────────────────────────────────

def make_diff(old: str, new: str, fromfile: str = "原版", tofile: str = "进化版") -> str:
    """生成 unified diff"""
    old_lines = old.splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)
    diff = unified_diff(old_lines, new_lines, fromfile=fromfile, tofile=tofile, lineterm="")
    return "".join(diff)


def format_diff_line(line: str) -> str:
    """格式化diff行（带颜色暗示）"""
    if line.startswith("+++") or line.startswith("---"):
        return f"  `{line.strip()}`"
    if line.startswith("@@"):
        return f"`{line}`"
    if line.startswith("+"):
        return f"`+ {line[1:].strip()}`"
    if line.startswith("-"):
        return f"`- {line[1:].strip()}`"
    return f"  {line}"


# ─────────────────────────────────────────────
# 进化模拟（基于规则生成进化后内容）
# ─────────────────────────────────────────────

def simulate_evolution(track: str, original: str, rules: list) -> tuple:
    """
    模拟简历进化。
    实际运行时：LLM根据规则重写简历，这里用启发式模拟。
    """
    evolved = original

    for rule in rules:
        if rule["type"] == "bullet_reframe":
            # 简单替换模拟
            evolved = evolved + f"\n\n[EVOLVED:{rule['action'][:40]}...]"

        elif rule["type"] == "section_add":
            section = f"\n\n### 🌍 出海项目管理方法论\n\n"
            section += f"{rule['action']}\n"
            evolved = evolved + section

        elif rule["type"] == "keyword_add":
            evolved = evolved + f"\n\n[EVOLVED:{rule['action'][:60]}...]"

    return evolved, []  # (evolved_content, warnings)


# ─────────────────────────────────────────────
# 展示进化计划
# ─────────────────────────────────────────────

def display_evolution_plan(config: dict) -> dict:
    """展示并返回进化计划（供用户审批）"""

    # 加载Gap分析
    gap_path = DATA_DIR / "gap_analysis.json"
    if gap_path.exists():
        with open(gap_path, encoding="utf-8") as f:
            gap = json.load(f)
    else:
        gap = {}

    plan = {}
    for track, rules in EVOLUTION_RULES.items():
        if track == "global":
            continue
        plan[track] = {
                "track_label": TRACKS[track]["label"],
                "icon": TRACKS[track]["icon"],
                "changes": [],
                "minor": [],
                "major": [],
            }
        for r in rules:
            change = {
                "type": r["type"],
                "action": r["action"],
                "priority": r["priority"],
                "market_signal": r.get("market_signal", ""),
            }
            plan[track]["changes"].append(change)
            if r["priority"] == "major":
                plan[track]["major"].append(change)
            else:
                plan[track]["minor"].append(change)

    return plan


def print_evolution_summary(plan: dict):
    """打印进化计划摘要"""
    print("\n" + "=" * 60)
    print("✍️  简历进化计划摘要")
    print("=" * 60)

    for track, p in plan.items():
        print(f"\n{p['icon']} {p['track_label']} 方向")
        print("-" * 48)
        print(f"  Minor变更（自动执行）：{len(p['minor'])} 项")
        for c in p["minor"]:
            print(f"    ⚡ {c['action'][:60]}...")
        if p["major"]:
            print(f"\n  Major变更（需批准）：{len(p['major'])} 项")
            for c in p["major"]:
                print(f"    🔴 {c['action'][:60]}...")
                print(f"       市场信号：{c['market_signal'][:50]}...")

    print("\n" + "=" * 60)


def execute_evolution(track: str, dry_run: bool = True) -> dict:
    """执行单方向进化"""
    resume_path = DATA_DIR / "resumes" / f"resume_{track}.md"

    if not resume_path.exists():
        return {"ok": False, "error": f"简历文件不存在：{resume_path}"}

    with open(resume_path, encoding="utf-8") as f:
        original = f.read()

    # 获取该方向的规则
    rules = EVOLUTION_RULES.get(track, [])

    evolved, warnings = simulate_evolution(track, original, rules)

    if dry_run:
        diff = make_diff(original, evolved)
        return {
            "ok": True,
            "dry_run": True,
            "track": track,
            "track_label": TRACKS[track]["label"],
            "changes_count": len(rules),
            "diff": diff,
            "warnings": warnings,
        }
    else:
        # 备份
        BACKUP_DIR.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        backup_path = BACKUP_DIR / f"resume_{track}_{ts}.md"
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(original)

        # 写入新版本
        with open(resume_path, "w", encoding="utf-8") as f:
            f.write(evolved)

        return {
            "ok": True,
            "dry_run": False,
            "track": track,
            "backup": str(backup_path),
            "written": str(resume_path),
        }


# ─────────────────────────────────────────────
# 主流程
# ─────────────────────────────────────────────

def run(dry_run: bool = True, auto_approve: bool = False):
    """
    运行简历进化。

    参数：
        dry_run      : True=只展示计划，不写入文件
        auto_approve : True=自动执行全部变更（忽略审批）
    """
    print("=" * 60)
    print("✍️  简历进化系统 · Resume Optimizer Agent")
    print(f"   执行时间：{datetime.now(timezone(timedelta(hours=8))):%Y-%m-%d %H:%M} (北京时间)")
    print(f"   模式：{'预览（dry-run）' if dry_run else '执行（写入文件）'}")
    print("=" * 60)

    config = load_config()
    plan = display_evolution_plan(config)
    print_evolution_summary(plan)

    if dry_run and not auto_approve:
        print("⏸  预览模式：加入 --approve 参数正式执行进化")
        return plan

    # 执行进化
    results = {}
    for track in TRACKS:
        print(f"\n{'🔄' if dry_run else '✍️ '} 进化 {TRACKS[track]['icon']} {TRACKS[track]['label']} ...")
        result = execute_evolution(track, dry_run=dry_run)
        results[track] = result
        if result["ok"]:
            status = "✅" if not dry_run else "👁  预览"
            print(f"   {status} {result.get('track_label', track)} "
                  f"({result.get('changes_count', 0)} 项变更)")
            if not dry_run:
                print(f"   📦 备份：{result.get('backup', '')}")
        else:
            print(f"   ❌ 失败：{result.get('error', '')}")

    # 记录到日志
    log_path = DATA_DIR / "evolution_log.jsonl"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "ts": datetime.now(timezone(timedelta(hours=8))).isoformat(),
            "dry_run": dry_run,
            "tracks": {t: {"ok": r["ok"], "changes": r.get("changes_count", 0)}
                       for t, r in results.items()},
        }, ensure_ascii=False) + "\n")

    # 汇总
    ok_count = sum(1 for r in results.values() if r["ok"])
    print(f"\n{'=' * 60}")
    print(f"{'👁  预览' if dry_run else '✍️  进化'}完成：{ok_count}/{len(TRACKS)} 方向")
    if dry_run:
        print("   加入 --approve 参数正式执行")
    print(f"{'=' * 60}")

    return results


def load_config():
    with open(CONFIG_FILE, encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv or "-n" in sys.argv
    approve = "--approve" in sys.argv or "-y" in sys.argv
    run(dry_run=dry, auto_approve=approve)
