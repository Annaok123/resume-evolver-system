#!/usr/bin/env python3
"""
简历进化系统 · Publisher Agent
==============================
职责：将简历数据渲染为可视化工作台网站
输入：四份简历 + 市场HC数据 + Gap分析
输出：public/index.html
"""

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

WORKSPACE  = Path(__file__).parent.parent
DATA_DIR   = WORKSPACE / "data"
PUBLIC_DIR = WORKSPACE / "public"
TEMPLATE   = PUBLIC_DIR / "index.html"


def load_data() -> dict:
    """加载所有数据源"""
    data = {
        "config": {},
        "market": {"listings": [], "summary": {}},
        "gap": {},
        "resumes": {},
    }

    # 配置文件
    cfg_path = DATA_DIR / "config.json"
    if cfg_path.exists():
        with open(cfg_path, encoding="utf-8") as f:
            data["config"] = json.load(f)

    # 市场HC
    hc_path = DATA_DIR / "market_hc.json"
    if hc_path.exists():
        with open(hc_path, encoding="utf-8") as f:
            raw = json.load(f)
            data["market"]["listings"] = raw.get("listings", [])
            data["market"]["summary"] = {
                "total": raw.get("total_listings", 0),
                "by_track": raw.get("by_track", {}),
                "collected_at": raw.get("generated_at", ""),
            }

    # Gap分析
    gap_path = DATA_DIR / "gap_analysis.json"
    if gap_path.exists():
        with open(gap_path, encoding="utf-8") as f:
            data["gap"] = json.load(f)

    # 简历内容（摘要）
    for track in ["pm", "product", "ba", "strategy"]:
        path = DATA_DIR / "resumes" / f"resume_{track}.md"
        if path.exists():
            with open(path, encoding="utf-8") as f:
                text = f.read()
                # 提取关键信息
                data["resumes"][track] = {
                    "word_count": len(text),
                    "has_experience": "工作经历" in text or "##" in text,
                    "updated": datetime.fromtimestamp(
                        path.stat().st_mtime, tz=timezone(timedelta(hours=8))
                    ).strftime("%Y-%m-%d"),
                }

    return data


def build_status_summary(data: dict) -> dict:
    """构建前端状态对象"""
    config = data["config"]
    owner  = config.get("owner", {})
    tracks = config.get("resume_tracks", {}).get("tracks", ["pm", "product", "ba", "strategy"])

    # Gap评分
    gap_scores = {}
    if "gap" in data and "tracks" in data["gap"]:
        for t in tracks:
            tdata = data["gap"]["tracks"].get(t, {})
            gap_scores[t] = tdata.get("score", 80.0)

    # 市场数据
    market_summary = data["market"].get("summary", {})
    total_hc = market_summary.get("total", 0)

    return {
        "owner": owner,
        "tracks": tracks,
        "track_labels": config.get("resume_tracks", {}).get("track_labels", {}),
        "track_colors": config.get("resume_tracks", {}).get("track_colors", {}),
        "market": {
            "total": total_hc,
            "by_track": market_summary.get("by_track", {}),
            "collected_at": market_summary.get("collected_at", "未知"),
        },
        "gap": {
            "scores": gap_scores,
            "overall": data["gap"].get("summary", {}).get("overall_score", 80.0),
            "recommend_first": data["gap"].get("summary", {}).get("recommend_evolve_first", "pm"),
            "action_items": data["gap"].get("summary", {}).get("total_high_priority", 0),
        },
        "resumes": data["resumes"],
        "website": config.get("website", {}),
    }


def render_html(data: dict) -> str:
    """
    渲染完整HTML。
    完整版渲染（使用已优化的 public/index.html 模板，
    并注入实时状态数据）。
    """
    status = build_status_summary(data)

    # 读取当前模板
    if TEMPLATE.exists():
        with open(TEMPLATE, encoding="utf-8") as f:
            html = f.read()
    else:
        html = _minimal_html()

    # 注入状态数据
    status_json = json.dumps(status, ensure_ascii=False)
    html = html.replace(
        "/* INJECT_STATUS_JSON */",
        f"const SYSTEM_STATUS = {status_json};"
    )

    return html


def _minimal_html() -> str:
    """兜底：生成最小化页面（当模板不存在时）"""
    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>简历进化系统</title></head>
<body><h1>简历进化系统 · {datetime.now():%Y-%m-%d}</h1>
<p>数据加载中...</p></body></html>"""


def push_to_github(github_repo: str, file_path: str, content: str, branch: str = "main") -> dict:
    """
    推送到 GitHub Pages。
    使用 GitHub API 将 public/index.html 推送到 repo 的 docs/ 目录。

    注意：需要 GITHUB_TOKEN 环境变量。
    """
    import os, base64, urllib.request, urllib.error

    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        return {"ok": False, "error": "缺少 GITHUB_TOKEN 环境变量"}

    # 构建 GitHub API URL
    # 文件路径：docs/index.html
    path_in_repo = "docs/index.html"
    api_url = f"https://api.github.com/repos/{github_repo}/contents/{path_in_repo}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
    }

    # 检查当前SHA
    req = urllib.request.Request(api_url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            current = json.loads(resp.read())
            sha = current["sha"]
    except urllib.error.HTTPError as e:
        if e.code == 404:
            sha = None
        else:
            return {"ok": False, "error": f"检查文件失败: {e.code}"}

    # 上传文件
    payload = {
        "message": f"chore: 更新简历进化系统 {datetime.now():%Y-%m-%d %H:%M}",
        "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
        "branch": branch,
    }
    if sha:
        payload["sha"] = sha

    req = urllib.request.Request(
        api_url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="PUT",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            return {
                "ok": True,
                "commit": result["commit"]["sha"],
                "url": f"https://github.com/{github_repo}/commit/{result['commit']['sha']}",
            }
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        return {"ok": False, "error": f"上传失败 {e.code}: {body[:200]}"}


# ─────────────────────────────────────────────
# 主流程
# ─────────────────────────────────────────────

def run(auto_push: bool = False):
    print("=" * 60)
    print("🌐 简历进化系统 · Publisher Agent")
    print(f"   执行时间：{datetime.now(timezone(timedelta(hours=8))):%Y-%m-%d %H:%M} (北京时间)")
    print("=" * 60)

    # 加载数据
    data = load_data()
    print(f"\n📊 数据加载完成：")
    print(f"   市场HC：{data['market']['summary'].get('total', 0)} 个岗位")
    print(f"   Gap分析：{'已加载' if data['gap'] else '暂无'}")
    print(f"   简历数量：{len(data['resumes'])} 份")

    # 渲染
    html = render_html(data)

    # 保存
    PUBLIC_DIR.mkdir(exist_ok=True)
    output_path = PUBLIC_DIR / "index.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    size_kb = len(html) // 1024
    print(f"\n✅ 网站已渲染：{output_path} ({size_kb} KB)")

    # GitHub Push
    config = data["config"]
    website_cfg = config.get("website", {})
    repo = website_cfg.get("github_repo", "Annaok123/resume-evolver-system")

    if auto_push:
        print(f"\n🚀 正在推送到 GitHub：{repo}/docs/index.html ...")
        result = push_to_github(repo, "docs/index.html", html)
        if result["ok"]:
            print(f"   ✅ 已推送！Commit: {result['commit']}")
            print(f"   🔗 {result['url']}")
            print(f"   🌐 https://annaok123.github.io/resume-evolver-system/")
        else:
            print(f"   ❌ 推送失败：{result['error']}")
            print(f"   💡 可手动执行：cd public && git push")
    else:
        print(f"\n⏸  未触发推送（使用 --push 参数自动推送）")
        print(f"   GitHub Repo：{repo}")
        print(f"   手动推送：cd public && git push")

    return {"ok": True, "size_kb": size_kb}


if __name__ == "__main__":
    push = "--push" in sys.argv or "-p" in sys.argv
    run(auto_push=push)
