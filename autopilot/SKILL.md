---
name: autopilot
description: 无人值守地把一个 feature 的工单队列做空:逐单实现、决策写日志而不是问人、卡住的单标 needs-human。用户以 /autopilot 启动,或要求"不盯着跑完这批工单"时使用。
argument-hint: <feature-slug 或 父issue>
arguments: queue
disallowed-tools: AskUserQuestion
---

# Autopilot

无人值守地把 `$queue` 的工单队列做空。本次调用就是 CLAUDE.md「自治模式」的进入条件:清单内的 skill(implement-spec、implement、tdd、code-review、git-commit)直接 invoke;需要拍板的点自己定并写进 `tasks/decisions.md`;卡住的单标 `needs-human` 后继续。

## 队列在哪

`$queue` 是 feature slug(本地 tracker)或父 issue(GitHub)。读 `docs/agents/issue-tracker.md` 决定怎么列工单:本地是 `.scratch/$queue/issues/*.md`,看每个文件的 `Status` 字段;GitHub 是父 issue 下带 `ready-for-agent` 标签的子 issue。这份文档不存在就停下并报告:需要先跑 `/setup-matt-pocock-skills`。

## 步骤

1. 读 spec(含 Decision Boundary)、`tasks/lessons.md`、`tasks/decisions.md`(缺的建空文件)。没有 spec 就以工单为准,决策边界视为全部授权。
2. 回流:`tasks/decisions.md` 里行尾带「改:」的条目,每条转成一张新工单(标题取「改:」后的内容,Blocked by 为 None),并在该行末尾追加「→ 已转工单 NN」。
3. 集成分支 `feat/$queue`,已存在就续用。
4. invoke `implement-spec` 驱动前沿(frontier):每单一个 worktree 子代理,模型档位按 CLAUDE.md 分档表显式传入;子代理的"完成"只认 diff 和测试输出。
5. 碰到 Decision Boundary 的保留项、同一单失败两次、或下一步落在硬边界上:`Status` 改 `needs-human`,原因写进工单,回到前沿继续。
6. 前沿清空后 `code-review` 一次,修掉阻塞级问题;本次踩的坑追加到 `tasks/lessons.md`(症状 → 根因 → 规则)。
7. 打印收尾表。

完成标准:每张工单的 `Status` 都是 `done` 或 `needs-human`,集成分支全量测试通过,收尾表已打印。

## 决策日志格式

`tasks/decisions.md` 一条一行,追加在文件末尾:

```markdown
- [ ] 03 · 列表分页用游标还是页码 · 候选:游标 / 页码 · 选 游标 · 理由:ADR-004 已定实时流用游标
```

用户复核时:勾成 `[x]` 即认可;行尾写「改: <要怎么做>」即要改,下次运行在第 2 步转成工单;两者都没有的行保持原样。

## 收尾表

每轮回复的结尾都带这张表,`/goal` 的判定器只看对话内容,看不到文件:

| 工单 | Status | 本轮动作 |
|---|---|---|

表后三行:`decisions.md` 新增条数;`needs-human` 的单和原因;下一轮打算做的单,队列空了就写 `QUEUE_EMPTY`。

## 启动方式(给人看)

autopilot 只接管中间的执行段。前段仍是人在场:grill-with-docs → `/to-spec` → `/to-tickets`,产物是工单队列。后段也是人:读 `tasks/decisions.md`,不认可的决策改成新工单;处理 `needs-human`;`/retro`。


交互会话,两行:

```text
/autopilot <slug>
/goal <slug> 的工单全部 done 或 needs-human,集成分支全量测试通过,或运行超过 4 小时后停止
```

无人值守脚本(`ccpd` 是交互别名,脚本里用它展开后的形式):

```bash
until withproxy claude -p "/autopilot <slug>" --dangerously-skip-permissions --permission-prompts none \
      | grep -q QUEUE_EMPTY; do :; done
```
