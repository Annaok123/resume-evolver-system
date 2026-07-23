#!/usr/bin/env python3
"""
Resume Evolver — 主工作流脚本
将 Headhunter → Analyst → Optimizer → Publisher 四个 Agent 串联执行。

Usage:
    python3 scripts/run_full_pipeline.py              # 完整流程
    python3 scripts/run_full_pipeline.py --skip-publish  # 跳过发布
    python3 scripts/run_full_pipeline.py --approve   # 自动批准进化
"""

import json
import re
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

WORKSPACE = Path(__file__).parent.parent
DATA_DIR = WORKSPACE / "data"

SCRIPTS = {
    "headhunter": WORKSPACE / "scripts" / "monitor_jobs.py",
    "analyst": WORKSPACE / "scripts" / "analyze_resume.py",
    "optimizer": WORKSPACE / "scripts" / "evolve_resume.py",
    "publisher": WORKSPACE / "scripts" / "render_website.py",
}


def run_script(name: str, script: Path, extra_args: list[str] = None) -> bool:
    """运行单个 Agent 脚本。"""
    args = ["python3", str(script)]
    if extra_args:
        args.extend(extra_args)
    print(f"\n{'='*60}")
    print(f"🤖 [{name.upper()}] Agent 启动")
    print(f"{'='*60}")
    result = subprocess.run(args, capture_output=False)
    success = result.returncode == 0
    status = "✅" if success else "❌"
    print(f"{status} [{name.upper()}] 完成 (exit={result.returncode})")
    return success


def run_pipeline(approve: bool = False, skip_publish: bool = False):
    """执行完整的多 Agent 流水线。"""
    print("🎯 Resume Evolver — 多 Agent 团队工作流")
    print(f"📁 工作区: {WORKSPACE}")
    print(f"⏰ 开始时间: {datetime.now(timezone.utc).isoformat()}")

    steps = [
        ("Headhunter", SCRIPTS["headhunter"], []),
        ("Analyst", SCRIPTS["analyst"], []),
        ("Optimizer", SCRIPTS["optimizer"], ["--dry-run"]),
    ]

    for name, script, extra in steps:
        ok = run_script(name, script, extra)
        if not ok:
            print(f"\n⚠️  [{name}] 执行失败，后续步骤可能受影响")

    # 检查是否有进化建议
    if approve:
        run_script("Optimizer", SCRIPTS["optimizer"], ["--approve"])

    if not skip_publish:
        run_script("Publisher", SCRIPTS["publisher"], [])

    # 生成报告
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "workspace": str(WORKSPACE),
        "steps_completed": ["headhunter", "analyst", "optimizer"] + ([] if skip_publish else ["publisher"]),
    }
    report_file = DATA_DIR / "pipeline_report.json"
    report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\n📊 流水线报告 → {report_file}")
    print("✅ 全部完成！请检查 public/index.html 查看更新后的个人网站。")


def show_status():
    """显示当前状态概览。"""
    print("📊 Resume Evolver 状态概览\n")

    config_path = DATA_DIR / "config.json"
    if config_path.exists():
        config = json.loads(config_path.read_text())
        print(f"监控关键词: {config.get('monitoring', {}).get('keywords', [])}")
        print(f"数据来源: {config.get('monitoring', {}).get('sources', [])}")

    market_path = DATA_DIR / "market_hc.json"
    if market_path.exists():
        data = json.loads(market_path.read_text())
        print(f"\n📈 最新市场数据: {data.get('fetched_at', '未知')} — {data.get('count', 0)} 条HC")

    gap_path = DATA_DIR / "gap_analysis.md"
    if gap_path.exists():
        text = gap_path.read_text()
        mr = re.search(r"匹配率[:：]\s*\*\*(\d+(?:\.\d+)?)\%\*\*", text)
        if mr:
            print(f"🔍 最新匹配率: {mr.group(1)}%")

    resume_path = DATA_DIR / "resume.md"
    if resume_path.exists():
        text = resume_path.read_text()
        vm = re.search(r"\*\*版本号:\*\* (v\d+\.\d+)", text)
        dm = re.search(r"\*\*最后更新:\*\* (.+)", text)
        print(f"\n📄 简历版本: {vm.group(1) if vm else '未知'}")
        print(f"📅 最后更新: {dm.group(1) if dm else '未知'}")


if __name__ == "__main__":
    if "--status" in sys.argv:
        show_status()
    else:
        approve = "--approve" in sys.argv
        skip_publish = "--skip-publish" in sys.argv
        run_pipeline(approve=approve, skip_publish=skip_publish)
