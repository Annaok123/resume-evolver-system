# 🎯 简历进化者 — 个人简历自动化网站

> 基于市场招聘需求（HC）自动进化的个人简历 + 个人网站系统
> 以上使用QClaw工具生成

---
## 外网预览地址：
https://annaok123.github.io/resume-evolver-system/

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│              Resume Evolver Agent Team                  │
│                                                         │
│  👁️ Headhunter ──抓取招聘数据──▶ data/market_hc.json   │
│       │                                                   │
│       ▼                                                   │
│  🔍 Analyst ──差距分析──▶ data/gap_analysis.md           │
│       │                                                   │
│       ▼                                                   │
│  ✍️ Optimizer ──进化简历──▶ data/resume.md              │
│       │                                                   │
│       ▼                                                   │
│  🌐 Publisher ──渲染网站──▶ public/index.html          │
└─────────────────────────────────────────────────────────┘
```

---

## 快速开始

### 1. 安装依赖

```bash
# 无需安装！纯 Python 标准库，直接运行
python3 --version  # 推荐 3.10+
```

### 2. 配置个人信息

编辑 `data/config.json`：
```json
{
  "owner": {
    "name": "你的名字",
    "target_role": "Senior Backend Engineer",
    "target_city": "Shanghai",
    "email": "you@example.com"
  },
  "monitoring": {
    "keywords": ["Senior Backend Engineer", "Python Engineer"],
    "sources": ["linkedin", "indeed", "zhipin"]
  }
}
```

### 3. 填写简历

编辑 `data/resume.md`，填入你的真实信息。

### 4. 运行完整流程

```bash
cd ~/.qclaw/workspace-resume-evolver

# 预览模式（不修改任何文件）
python3 scripts/run_full_pipeline.py

# 完整运行（自动更新简历 + 网站）
python3 scripts/run_full_pipeline.py --approve

# 查看状态
python3 scripts/run_full_pipeline.py --status
```

### 5. 预览网站

```bash
# macOS
open public/index.html

# 或启动本地服务器
cd public && python3 -m http.server 8080
# 访问 http://localhost:8080
```

---

## 单独运行各 Agent

```bash
# 岗位猎手：抓取最新招聘数据
python3 scripts/monitor_jobs.py
python3 scripts/monitor_jobs.py --source linkedin  # 仅 LinkedIn

# 简历分析师：生成差距报告
python3 scripts/analyze_resume.py        # 完整报告
python3 scripts/analyze_resume.py --quick # 快速摘要

# 简历优化器：预览并确认变更
python3 scripts/evolve_resume.py --dry-run    # 预览 diff
python3 scripts/evolve_resume.py --approve    # 批准写入

# 网站发布器：渲染静态网站
python3 scripts/render_website.py
python3 scripts/render_website.py --preview    # 渲染并打开浏览器
```

---

## 数据文件说明

| 文件 | 说明 |
|------|------|
| `data/resume.md` | **主简历文件** — 所有优化的核心数据源 |
| `data/config.json` | 监控配置（关键词、来源、频率等） |
| `data/market_hc.json` | 最近一次抓取的招聘数据 |
| `data/market_hc.jsonl` | 历史招聘数据（追加写入） |
| `data/gap_analysis.md` | 简历与市场的差距分析报告 |
| `data/gap_analysis.jsonl` | 历史分析记录 |
| `data/evolution_log.jsonl` | 简历进化历史 |
| `public/index.html` | 渲染后的个人网站 |

---

## 定时任务（自动运行）

### 每 6 小时自动抓取招聘数据

```bash
# 终端中设置 cron（macOS/Linux）
crontab -e

# 添加以下行（每天 8:00, 14:00, 20:02 运行）
0 8,14,20 * * * cd ~/.qclaw/workspace-resume-evolver && /usr/bin/python3 scripts/run_full_pipeline.py >> logs/cron.log 2>&1
```

---

## 连接真实数据源（高级）

当前 `scripts/monitor_jobs.py` 中的 `fetch_*` 函数为模拟数据。要接入真实数据：

### LinkedIn（需要 LinkedIn API Access）
```python
def fetch_linkedin(keywords, max_results):
    # 使用 LinkedIn API 或第三方服务
    # 推荐：Glider.ai, Apollo.io, Hiration
    response = linkedin_api.search_jobs(keywords=keywords, ...)
    return [parse_job(j) for j in response['jobs']]
```

### Boss直聘（非官方，需遵守 ToS）
```python
def fetch_zhipin(keywords, max_results):
    # 使用 Playwright 登录抓取，或第三方 API
    # 注意：Boss直聘有反爬机制，建议使用付费 API
    pass
```

---

## 进化原则

✅ **允许**：重新措辞已有技能、强化真实经验、量化成就  
❌ **禁止**：虚构不存在的技能、夸大经验、造假  
⚠️ **需用户批准**：任何写入操作都需要 `--approve` 确认

---

## 自定义网站主题

编辑 `data/config.json`：
```json
"website": {
  "theme": "dark"   // "dark" 或 "light"
}
```
