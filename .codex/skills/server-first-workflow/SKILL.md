---
name: server-first-workflow
description: Use when working in this repository and code is edited on MacOS or Windows but only executed on a remote Linux server. Covers the required handoff flow: local code change, no fake local verification, push to remote fork, and tell the user exactly what to pull and run on the server.
---

# Server First Workflow

适用场景:
- 当前仓库代码在本地改, 但真正运行环境在远端 Linux 服务器
- 本地没有同等 CUDA, 驱动, 模型, 或数据盘环境
- 需要避免把本地静态检查说成服务器已验证

## 必须遵守

1. 本地只做这些:
- 阅读代码
- 修改代码
- 做静态检查或纯语法检查
- 提交并推送到用户 fork

2. 不要做这些:
- 不声称已经在本地跑过 Linux 服务器训练或评测
- 不把本地 MacOS 或 Windows 结果当成服务器结果
- 不默认用户服务器已经 `git pull`

3. 每次代码修改后都要给出:
- 已修改内容
- 已推送的 commit id
- 服务器上要执行的 `git pull --rebase origin master`
- 建议运行命令

## 默认交付格式

当修改已推送后, 结尾至少包含:

```bash
cd /root/autodl-tmp/projects/knowledge-sanitization
git pull --rebase origin master
```

再给本次对应的服务器运行命令。

## 若用户贴服务器报错

1. 先定位是:
- 代码逻辑问题
- 参数问题
- 环境问题
- 模型或路径问题

2. 如果属于代码逻辑问题:
- 直接在本地改代码
- 推送
- 让用户服务器拉最新代码重跑

3. 如果属于纯服务器环境问题:
- 不伪装成已经修好
- 明确告诉用户需要在服务器执行什么
