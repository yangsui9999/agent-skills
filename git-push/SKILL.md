---
name: git-push
description: '安全推送本地提交到远程仓库。自动检查状态、拉取远程变更、处理冲突、推送。Use when user asks to push, sync with remote, or mentions "/push".'
license: MIT
allowed-tools: Bash
---

# Git Push

## Overview

安全推送本地提交到远程。自动化流程：状态检查 → fetch → 对比 → rebase → push。

## Workflow

### 1. 检查当前状态

```bash
git status --porcelain
git branch --show-current
git remote -v
```

**阻塞条件：**
- 工作区有未提交的改动 → 提示用户先运行 `/git-commit`（不自动提交，因为 commit 需要人工判断分组和消息）
- 没有配置远程仓库 → 提示用户添加 remote
- 当前分支没有 upstream → 自动使用 `-u origin <branch>`

**关联 skill：** 本 skill 不包含提交逻辑。如需提交，先用 `/git-commit`，再用 `/git-push`。

### 2. Fetch 远程最新状态

```bash
git fetch origin
```

### 3. 对比本地与远程

```bash
# 本地领先远程多少
git log --oneline origin/<branch>..<branch>

# 远程领先本地多少（需要合并的）
git log --oneline <branch>..origin/<branch>
```

**三种情况：**

| 情况 | 本地领先 | 远程领先 | 操作 |
|------|---------|---------|------|
| 仅本地有新提交 | ✅ | ❌ | 直接 push |
| 远程也有新提交 | ✅ | ✅ | 先 rebase 再 push |
| 本地无新提交 | ❌ | - | 提示"没有需要推送的提交" |

### 4. 处理远程有新提交的情况

```bash
# 用 rebase 而非 merge，保持线性历史
git pull --rebase origin <branch>
```

**如果 rebase 产生冲突：**
1. 立即停止，**不自动解决**
2. 告知用户冲突文件列表（`git diff --name-only --diff-filter=U`）
3. 给出解决步骤：
   - 手动编辑冲突文件
   - `git add <resolved-files>`
   - `git rebase --continue`
   - 再次运行 `/git-push`
4. 提供放弃选项：`git rebase --abort` 回到 rebase 前状态

### 5. 执行推送

```bash
# 首次推送（无 upstream）
git push -u origin <branch>

# 后续推送
git push
```

### 6. 报告结果

- 推送了多少个提交
- 远程分支 URL
- 当前状态（`git log --oneline -1`）

## 参数

```
/git-push              → 推送当前分支到 origin
/git-push <remote>     → 推送到指定 remote
```

## 安全规则

- NEVER force push（`--force` / `-f`），除非用户显式要求
- NEVER push 到 main/master 以外的保护分支时不警告
- 冲突时停下来让用户解决，不自动处理
- 每次执行前必须 `git status` 检查（不信任之前的状态）
- 推送前必须 fetch + 对比，不盲目 push
