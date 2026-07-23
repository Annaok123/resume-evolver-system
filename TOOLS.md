# TOOLS.md — 本地工具配置

Skills 定义了工具的使用方式。此文件记录你本地特有的配置。

## 工作区结构

- `data/resume.md` — 核心简历数据（主数据源）
- `data/config.json` — 监控配置（关键词、来源、频率）
- `data/market_hc.json` — 最新市场招聘数据
- `data/gap_analysis.md` — 简历差距分析报告
- `public/index.html` — 渲染后的个人网站
- `scripts/` — Agent 执行脚本

## 主要执行命令

```bash
# 完整流程（预览模式）
python3 scripts/run_full_pipeline.py

# 完整流程（自动批准进化）
python3 scripts/run_full_pipeline.py --approve

# 单独执行各 Agent
python3 scripts/monitor_jobs.py         # 岗位猎手
python3 scripts/analyze_resume.py       # 简历分析师
python3 scripts/evolve_resume.py        # 简历优化器
python3 scripts/render_website.py        # 网站发布器

# 状态查看
python3 scripts/run_full_pipeline.py --status
```

## Python 环境

- Python 3.10+ required
- 无额外第三方依赖（使用标准库）
- 运行路径：工作区根目录

## 浏览器预览

发布后可用以下命令预览网站：

```bash
# macOS
open public/index.html

# Linux
xdg-open public/index.html

# 或使用 python3 -m http.server
cd public && python3 -m http.server 8080
```
