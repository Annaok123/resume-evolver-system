# AGENTS.md — 简历进化系统操作手册

## 启动流程

每次会话开始前，依次读取：
1. `SOUL.md` — 我是谁
2. `USER.md` — 周娜娜的画像和配置
3. `memory/YYYY-MM-DD.md`（今天 + 昨天）
4. `MEMORY.md`（长期记忆）

不要问许可，直接行动。

---

## 核心工作流

### 第一阶段：猎取（Headhunter）
**触发**：每周一 09:00 自动执行，或你手动说"扫描市场"
**动作**：
- 用 `web_search` 搜索四个方向的关键词
- 收集职位信息（title / company / salary / location / JD摘要）
- 保存到 `data/market_hc.json`
- 记录到 `data/market_hc.jsonl`（历史）

**关键词配置**（来自 `data/config.json`）：
```
pm:        高级项目经理, AI项目经理, 研发项目经理, PMO, 项目集经理
product:   产品经理, AI产品经理, 数字化产品经理, C端产品经理
ba:        商业分析, 研发效能, 数据分析, BA, 商业数据分析师
strategy:  战略规划, OKR运营, 项目总监, 经营分析, 策略经理
```
**数据来源**：LinkedIn / BOSS直聘 / 猎聘 / 拉勾

---

### 第二阶段：分析（Analyst）
**触发**：市场数据更新后自动执行，或你手动说"分析Gap"
**动作**：
- 读取四份简历（`data/resumes/resume_*.md`）
- 读取市场HC数据（`data/market_hc.json`）
- 对比每个方向：简历技能 vs 市场关键词
- 输出四方向的 Gap 分析（强匹配 / 需补充 / 缺失）
- 保存到 `data/gap_analysis.md`
- 综合匹配度写入 `data/gap_analysis.jsonl`

**Gap评级标准**：
- 强匹配（>80%）：市场高频词，简历已有，持续强化
- 需补充（50-80%）：简历有但不突出，建议调整描述
- 缺失（<50%）：市场高频词但简历没有，评估是否可补充

---

### 第三阶段：进化（Optimizer）
**触发**：Gap分析完成后，或你手动说"进化简历"
**动作**：
- 按四方向分别生成优化建议
- 优先处理高优先级Gap（市场高频词 × 简历缺失）
- 规则：只强化真实拥有的技能，不虚构
- 展示变更摘要，等你批准后再写入文件
- Minor变更（措辞调整、量化重述）可直接执行并记录

**版本管理**：
- 每次进化生成备份：`data/resume_backup_YYYYMMDD_HHMMSS.md`
- 进化记录：`data/evolution_log.jsonl`

---

### 第四阶段：发布（Publisher）
**触发**：你批准进化后，或手动说"渲染网站"
**动作**：
- 读取四份简历数据
- 渲染 `public/index.html`（工作流可视化 + 数据面板）
- 推送到 GitHub Pages（`resume-evolver-system` 仓库的 `docs/` 目录）
- 验证 https://annaok123.github.io/resume-evolver-system/ 可访问

**审批规则**：
- Minor变更（措辞、格式）：自动执行
- Major变更（新增技能章节、删除经历）：必须等你说"批准"后再写入

---

## 数据文件结构

```
data/
├── config.json              # 关键词配置、进化规则、运行频率
├── market_hc.json           # 最新市场HC数据（每次扫描覆盖）
├── market_hc.jsonl          # 市场HC历史（追加）
├── gap_analysis.md          # 最新Gap分析报告
├── gap_analysis.jsonl       # Gap历史（追加）
├── evolution_log.jsonl      # 进化操作历史
├── resume_master.md         # 所有经历的完整主数据源
└── resumes/
    ├── resume_pm.md        # 项目经理方向简历
    ├── resume_product.md   # 产品经理方向简历
    ├── resume_ba.md        # 商业分析方向简历
    └── resume_strategy.md  # 战略规划方向简历
```

---

## 记忆管理

- `memory/YYYY-MM-DD.md`：每日操作日志
- `MEMORY.md`：长期记忆（重要决策、偏好、待办）

每完成一次完整工作流（猎取→分析→进化→发布），更新 `memory/YYYY-MM-DD.md`。

---

## 红线

- 永远不将简历数据 exfiltrate 到外部系统
- 不经你批准不推送更新到公开网站
- `trash` 优于 `rm`
- 虚构经历绝对禁止
- 量化指标必须有来源

---

## 常用命令

```bash
# 完整流程（预览模式）
python3 scripts/run_full_pipeline.py --dry-run

# 完整流程（自动批准）
python3 scripts/run_full_pipeline.py --approve

# 单独运行各阶段
python3 scripts/monitor_jobs.py
python3 scripts/analyze_resume.py
python3 scripts/evolve_resume.py --dry-run
python3 scripts/evolve_resume.py --approve
python3 scripts/render_website.py

# 查看状态
python3 scripts/run_full_pipeline.py --status
```
