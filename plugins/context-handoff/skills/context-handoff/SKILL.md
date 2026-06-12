---
name: context-handoff
description: >
  Use when a long session's context is filling up, the conversation is being
  summarized/compacted, or work must continue in a new terminal or session — to
  decide whether to hand off and produce a resume document. Triggers: "context
  full", "running low on context", "new terminal", "start fresh", "handoff",
  "resume in another session", before clearing/compacting context (/clear,
  /compact). Chinese triggers: 看看context, 新开终端, 上下文满了, 交接文档.
---

# Context Handoff

## Overview

Long sessions degrade: context gets summarized/compacted, the prompt cache goes cold, and earlier detail is lost. A **handoff document** lets a fresh session (often in a new terminal) resume seamlessly. This skill does four things: (1) give a **direct yes/no** on whether to hand off now, (2) if yes, write the handoff file, (3) tell the user exactly how to resume, (4) keep the handoff safe and complete — **above all, no secrets**.

## Step 1 — Decide: hand off, or keep going? (answer YES or NO directly)

You usually can't read exact token counts, so judge from signals and **state a clear recommendation** — don't make the user guess.

**Lean YES (hand off now) when several hold:**
- The session is long, with many large tool results or full file reads.
- The agent/harness has shown context-low or "this conversation will be summarized" notices, or summarization already happened.
- You're between logical units of work (a task just finished) — a clean seam to cut.
- Replies feel like they're losing earlier detail.

**Lean NO (keep going) when:**
- Mid-task with momentum and the finish line is close.
- The session is still short / light.

**Output format (always):** one line — `Recommendation: hand off now ✅` or `Recommendation: keep going ▶️` — plus a one-sentence why. Then add: *"Your client's context-usage indicator is the authoritative source — confirm against it."* Proceed to Step 2 only if YES (or the user says go).

## Step 2 — Write the handoff file

Save it into the **project repo** so the next session can read it: `docs/handoff-YYYY-MM-DD.md` (date-stamped; follow any existing project convention). Fill every section — omit none:

```markdown
# Handoff — <project/task> (<date>)
Read this file, then continue. The next step is <one sentence>.

## 1. What this is / goal
## 2. Progress (done vs. next)      ← table, mark ✅ / 📝 in-progress / ⏳ todo
## 3. Repo state                    ← paths, current branch, uncommitted changes, remote?
## 4. Next step (most important)    ← concrete, copy-pasteable commands/steps — not "keep building"
## 5. How to run & dev environment  ← exact commands; tunnels/ports/services it depends on
## 6. Gotchas & lessons             ← traps hit this session the next one will re-hit
## 7. Docs & memory index           ← paths to specs/plans/notes
## 8. Open questions / risks
```

Principles: **point, don't paste** (link to files; never dump large content into the handoff). Make "next step" concrete enough to execute verbatim. Date-stamp it — a handoff is a snapshot of one moment.

## Step 3 — Tell the user how to resume

Give the exact thing to paste into the **new** session:

> Open a new session in your agent and send: "Read `docs/handoff-<date>.md`, then continue <next step>."

If the new session is a separate checkout/worktree, remind them to commit or share the file first.

## ⚠️ Handoff writing rules — SECRETS come first

The handoff is often **committed to git and may be pushed**. Anything written here can leak permanently (git history persists even after the file is deleted).

**NEVER put real secrets in the handoff:**
- Passwords, API keys/secrets (e.g. AWS `AKIA…`, Aliyun `LTAI…` + AccessKeySecret), tokens, JWT secrets.
- Connection strings with embedded passwords (`postgres://user:pass@host/db`).
- `.env` contents, private keys (`BEGIN … PRIVATE KEY`), sensitive internal hostnames/IPs (if the repo is public).

**Instead, point to where they live** — e.g. *"DB password & OSS keys are in `config.local.toml` (gitignored)."* Reference, never reproduce.

**Throwaway dev creds** (e.g. `admin/admin123` for a local-only DB) are a judgment call: prefer pointing to the seed script/config; include them only if needed for a resume smoke test, mark them **dev-only/throwaway**, and never if the repo has a public remote.

**MANDATORY before committing the handoff — scan it:**
```bash
grep -nEi 'AKIA|LTAI[0-9A-Za-z]|secret|password|passwd|api[_-]?key|token|BEGIN [A-Z ]*PRIVATE KEY|://[^/@: ]+:[^/@ ]+@' docs/handoff-*.md
```
A match on **pointer text** ("see `config.local.toml`") is fine; a match on an **actual value** is not — redact it (replace with a pointer) before `git add`. Tell the user you scanned and it's clean.

## Common Mistakes

| Mistake | Fix |
|--------|-----|
| Pasting a connection string / API key "for convenience" | Point to the gitignored config file; scan before commit |
| "Next: keep building the frontend" (vague) | Name the exact file/command the next session runs |
| Dumping large file contents into the handoff | Link to the path; keep the handoff scannable |
| Describing context but giving no verdict | Always give a direct hand-off / keep-going recommendation |
| Forgetting how the new session uses it | Always include the copy-paste resume instruction |
| Handoff silently goes stale | Date-stamp it; treat it as a snapshot |

## Red Flags — STOP

- About to write a value that looks like a key/password/token/connection string → **redact, point to its file**.
- Committing the handoff without running the secret grep → **run it first**.
- Saying "context is fine/full" without a clear **hand off / keep going** answer → **decide**.
