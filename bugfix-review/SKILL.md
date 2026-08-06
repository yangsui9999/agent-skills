---
name: bugfix-review
description: Use when a bug has been fixed and the user wants a structured postmortem or retrospective document. Triggers on "/bugfix-review", "写个复盘", "事故回顾", "bug总结", postmortem, retrospective, incident review, root cause analysis, lessons learned.
---

# Bugfix Review

## Overview

Generate structured postmortem documents for resolved bugs/incidents. Focus on **causal chains** and **cognitive blind spots**, not generic methodology advice.

**Core principle:** Only write what you actually know. Never fabricate timelines, responsible persons, or details not provided.

## When to Use

- Bug is already fixed, user wants a retrospective document
- User says: "写个复盘", "总结一下这个 bug", "postmortem", "事故回顾"
- NOT for active debugging (use superpowers:systematic-debugging instead)

## Document Structure (Fixed 4 Sections)

Always use this exact structure. Do not add, merge, or rename sections.

### Section 1: Error Root Cause (错误详细原因)

Three required layers + one conditional layer:

```
现象 → 直接原因 → 根本原因 → 技术细节
                              ↓
                    为什么之前没问题（如适用）
```

- **现象**: What the user/system actually saw (error message, behavior)
- **直接原因**: The immediate technical cause
- **根本原因**: The underlying systemic/process cause
- **技术细节**: Deep explanation of the mechanism (e.g., how pip resolves deps, how shared libs load)
- **为什么之前没问题**: If the bug surfaced suddenly in a previously-working system, explain what changed. This is often the most insightful part.

### Section 2: Failed Attempts (修复过程中的错误)

For EACH failed attempt, use this exact sub-structure:

```
**策略**: What was tried and why it seemed reasonable
**代码/操作**: The actual commands or code changes
**失败原因**: Technical reason it didn't work
**教训**: The specific cognitive blind spot or knowledge gap exposed
```

**Critical rule for 教训:**
- Point to the specific technical knowledge gap, NOT generic methodology
- BAD: "应该先看数据再动手" (vague methodology)
- GOOD: "没有理解 pip 的依赖解析机制——opencv-python-headless 和 opencv-python 在 pip 元数据层面是完全不同的包，互不满足依赖" (specific blind spot)

### Section 3: Final Fix (最终修复方案)

- Show the actual code/commands
- **For each key decision, explain WHY it is necessary** — not just what was done
- Example: don't just write `--force-reinstall`, explain "确保 pip 不会跳过任何文件的写入"

### Section 4: Prevention (预防措施)

- Each measure must be **specific and actionable** with code examples
- BAD: "加强监控" (too vague)
- GOOD: Show the exact monitoring command, CI check script, or config change

## Anti-Patterns

| Don't | Do Instead |
|-------|-----------|
| Fabricate timestamps you don't know | Omit timeline or use relative order only |
| Add 负责人/完成时间 not provided | Only include information actually given |
| Use 5-Why as a rigid framework | Use the 4-layer causal chain above |
| Write methodology slogans as lessons | Identify specific technical knowledge gaps |
| Describe final fix without explaining decisions | Explain WHY each flag/step/parameter matters |
| Add sections beyond the 4 defined | Stick to the fixed structure |

## Quick Checklist

Before finalizing, verify:

- [ ] 根因分析有 3-4 层递进，不是只说表面原因
- [ ] 每次失败尝试的教训指向具体认知盲区
- [ ] "为什么之前没问题" 已回答（如适用）
- [ ] 最终方案的每个关键决策都有解释
- [ ] 没有编造任何未提供的信息
- [ ] 预防措施有代码示例，可直接执行
