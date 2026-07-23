# HEARTBEAT.md

## 系统运行状态

✅ 所有脚本已升级为 PM/AI 方向定制版

## 定期检查清单

- [ ] 市场HC数据是否超过7天未更新？→ 运行 `python3 scripts/monitor_jobs.py`
- [ ] Gap分析是否超过48小时未生成？→ 运行 `python3 scripts/analyze_resume.py`
- [ ] 有没有需要用户批准的Major变更？
- [ ] GitHub Pages 网站是否可访问？
- [ ] 四大简历文件是否完整存在？

## 已知问题

- 市场HC数据为模拟数据（正式运行需接入真实API）
- GitHub Push 需要 GITHUB_TOKEN 环境变量
- 当前匹配度偏低（44%）是因为简历没有充分强调某些技能

## 快速命令

```bash
# 完整流程
python3 scripts/run_full_pipeline.py --dry-run   # 预览
python3 scripts/run_full_pipeline.py --approve  # 执行

# 单独运行
python3 scripts/monitor_jobs.py
python3 scripts/analyze_resume.py
python3 scripts/evolve_resume.py --dry-run
python3 scripts/evolve_resume.py --approve
python3 scripts/render_website.py --push
```
