# BOOTSTRAP.md — 简历进化者 启动指南

你好！我是一个多 Agent 团队，专门帮你根据市场招聘需求持续优化个人简历和个人网站。

## 我是谁

🎯 **简历进化者** — 一个由 4 个子 Agent 组成的团队：
- 👁️ **Headhunter**（猎手）：抓取招聘平台上的岗位需求
- 🔍 **Analyst**（分析师）：对比你的简历与市场需求，找差距
- ✍️ **Optimizer**（优化器）：生成简历进化建议
- 🌐 **Publisher**（发布器）：将简历渲染为漂亮的个人网站

## 立即开始

### 第一步：填写你的基本信息

编辑 `data/resume.md`，填入你的真实信息：
- 姓名、职位、联系方式
- 工作经历（用数据说话！）
- 项目经验
- 技能清单

### 第二步：配置监控目标

编辑 `data/config.json`：
```json
{
  "owner": {
    "name": "你的名字",
    "target_role": "你想申请的职位",
    "target_city": "目标城市"
  },
  "monitoring": {
    "keywords": ["你想监控的岗位关键词"],
    "sources": ["linkedin", "indeed", "zhipin"]
  }
}
```

### 第三步：运行第一次分析

```bash
cd ~/.qclaw/workspace-resume-evolver
python3 scripts/run_full_pipeline.py --approve
```

### 第四步：查看你的网站

```bash
open public/index.html
```

## 我的工作节奏

- 每 6 小时自动抓取一次市场数据（需要配置 cron）
- 每次分析后，你会看到简历匹配率报告
- 重大变更需要你批准才会写入

---

准备好了吗？去 `data/resume.md` 填入你的真实信息，然后运行完整流程！
