---
name: git-status
description: '友好展示仓库状态：分支、未提交改动、本地/远程对比、最近提交。Use when user asks about repo status, or mentions "/status".'
license: MIT
allowed-tools: Bash
---

# Git Status

## Overview

一站式展示仓库当前状态，用中文友好输出。帮助用户在 commit/push/merge 前了解全局。

## Workflow

并行执行以下命令收集信息，然后组织为友好的报告：

```bash
# 并行收集
git branch --show-current
git status --porcelain
git stash list
git log --oneline -5
git remote -v
```

如果有远程仓库，还需要：
```bash
git fetch origin --quiet
git rev-list --count origin/<branch>..<branch>    # 本地领先
git rev-list --count <branch>..origin/<branch>    # 远程领先
```

## 输出格式

按以下结构组织输出（省略无内容的区块）：

```
📍 分支: main

📝 工作区变更:
  修改: backend/app/main.py
  新增: web-teacher/src/routes/login.tsx
  删除: old-file.txt

📦 暂存区（待提交）:
  backend/app/schemas/auth.py

🔄 远程同步:
  本地领先 origin/main 3 个提交
  远程领先本地 0 个提交
  → 可以直接 /git-push

📜 最近提交:
  48ed683 fix: config.dev.toml 移除真实密钥
  00c7043 refactor: 简化配置文件策略
  263e9e1 fix(web): 显式指定 OAuth scopes

💡 建议:
  有未提交的改动 → 运行 /git-commit
  本地领先远程 → 运行 /git-push
```

## 建议逻辑

根据状态自动给出下一步建议：

| 状态 | 建议 |
|------|------|
| 有未追踪/已修改文件 | `有未提交的改动 → /git-commit` |
| 暂存区有内容 | `有已暂存的改动 → /git-commit` |
| 本地领先远程 | `本地领先远程 N 个提交 → /git-push` |
| 远程领先本地 | `远程有新提交 → git pull --rebase` |
| 工作区干净 + 已同步 | `一切就绪，没有待处理的操作` |
| 有 stash | `有 N 个 stash 暂存 → git stash list 查看` |

## 注意事项

- `git fetch` 可能因网络问题失败 → 跳过远程对比，提示"无法连接远程"
- 分支没有 upstream → 跳过远程对比，提示"当前分支未关联远程"
- 输出保持简洁，不超过 30 行
