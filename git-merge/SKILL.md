---
name: git-merge
description: '将当前 feature 分支合并到目标分支（默认 main）。自动检查分支状态、运行测试、生成合并消息、执行合并、清理分支。Use when user asks to merge a branch, finish a story branch, or mentions "/merge".'
license: MIT
allowed-tools: Bash
---

# Git Merge Branch

## Overview

将 feature/story 分支安全合并到目标分支。自动化流程：状态检查 → 测试 → 合并 → 清理。

## Workflow

### 1. 检查当前状态

```bash
# 当前分支
git branch --show-current

# 工作区是否干净
git status --porcelain

# 查看分支提交历史（相对于目标分支）
git log --oneline main..HEAD
```

**阻塞条件（必须先解决）：**
- 工作区有未提交的改动 → 提示用户先提交或 stash
- 当前已在目标分支上 → 提示用户先切到 feature 分支

### 2. 确认合并信息

向用户展示：
- 当前分支名
- 目标分支（默认 main，可通过参数指定）
- 待合并的提交列表（`git log --oneline main..HEAD`）
- 合并策略：`--no-ff`（保留分支历史）

### 3. 运行测试（如果可用）

```bash
# 检测项目类型并运行测试
# Python: pytest / uv run pytest
# Node: npm test
# 如果测试失败，阻塞合并并报告
```

如果项目根目录或子目录有测试配置，运行测试。测试失败则阻塞合并。

### 4. 执行合并

```bash
# 切到目标分支
git checkout main

# 合并（保留分支历史）
git merge <branch-name> --no-ff -m "<merge-message>"
```

**合并消息格式：**
- 分析分支上的提交来生成摘要
- 格式：`<type>: <description>`
- 示例：`feat: Story 1.1 后端项目骨架搭建`
- 如果分支名包含 story/epic 编号，自动提取

### 5. 清理分支

```bash
# 删除已合并的本地分支
git branch -d <branch-name>
```

仅删除本地分支。如果有远程分支，提示用户是否也要删除（不主动执行）。

### 6. 报告结果

- 合并完成的提交 SHA
- 合并了多少个提交
- 当前分支状态
- 是否需要 `git push`

## 参数

用户可以通过参数指定目标分支：

```
/git-merge          → 合并到 main
/git-merge develop  → 合并到 develop
```

## 安全规则

- NEVER force merge（`--force`）
- NEVER delete unmerged branches（用 `-d` 不用 `-D`）
- 合并冲突时停下来让用户解决，不自动处理
- 工作区不干净时拒绝操作
- 合并前必须检查 `git status`（每次重新检查，不信任之前的状态）
