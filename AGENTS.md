Always respond in Chinese-simplified.
回答简洁扼要, 所有符号全部使用半角.
若要执行终端命令, 请用 Macos-zsh(macos) bash(linux) powershell(Windows) 语境书写.

本仓库额外约束:

1. 若任务涉及代码修改, 先阅读:
   - `.codex/skills/knowledge-sanitization-vibe/SKILL.md`
   - `.codex/skills/server-first-workflow/SKILL.md`
   - `.codex/skills/repro-server-run/SKILL.md`
2. 默认工作模式是:
   - 在本地 MacOS 或 Windows 修改代码
   - 不假设本地具备 Linux 服务器运行环境
   - 不声称已经在本地完成服务器侧测试
   - 修改后推送到远程 fork
   - 明确提醒用户到 Linux 服务器 `git pull` 后再运行
3. 当前目标优先级:
   - 优先最小改动复现原论文
   - 不优先做多模型泛化改造
4. 涉及运行建议时:
   - 先给 1x4090D 这类单卡的保守 smoke test 配置
   - 再说明如何逐步放大
5. 进入服务器长任务前:
   - 优先提醒用户使用 `tmux`
   - 若用户不用 `tmux`, 再提示 `screen`
6. 若涉及结果查看, 调参, 运行手册, 优先参考:
   - `.codex/skills/knowledge-sanitization-vibe/references/server-runbook.md`
   - `.codex/skills/knowledge-sanitization-vibe/references/result-reading.md`
   - `.codex/skills/knowledge-sanitization-vibe/references/tuning.md`
   - `.codex/skills/knowledge-sanitization-vibe/references/cost-control.md`
   - `SERVER_NIGHT_RUN.md`
7. 进入任何需要联网的服务器步骤前:
   - 先提醒检查 `mihomo` / clash 是否已启动
8. 优先复用已有环境:
   - 不随意新建 conda 环境
   - 不随意重复安装大体积 torch/cuda 依赖
9. 大文件默认原则:
   - 模型, cache, 输出, checkpoint 全放数据盘
   - 系统盘只放必须放系统盘的内容
10. 长实验前:
   - 先确认用户当前显卡规格
   - 再按 24G / 40G-48G / 80G 档位建议参数
11. 跑完重要修改后:
   - 及时提交 git 并推送远程
