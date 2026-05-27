# agent-skills

A collection of reusable, **cross-agent** coding skills by [@yangsui9999](https://github.com/yangsui9999), packaged as a Claude Code plugin marketplace.

A *skill* is a small Markdown reference (`SKILL.md`) that a coding agent reads to apply a proven technique. The skills here are written to be agent-agnostic — they work in Claude Code, and the raw `SKILL.md` files can be dropped into other agents (Codex, etc.).

## Skills

| Skill | What it's for |
|-------|---------------|
| **context-handoff** | When a long session's context fills up, decide whether to hand off, then write a safe, complete resume document so a fresh terminal/session can continue. Includes a mandatory secret-scan before committing the handoff. |

## Install — Claude Code

```shell
# 1) add this marketplace (owner/repo)
/plugin marketplace add yangsui9999/agent-skills

# 2) install a plugin (plugin-name@marketplace-name)
/plugin install context-handoff@yangsui-skills
```

Then invoke it as `/context-handoff:context-handoff`, or just let it trigger on phrases like "context full", "new terminal", "handoff".

## Use with other agents (Codex, etc.)

The skill content is portable Markdown. Copy the `SKILL.md` into your agent's skills directory:

```shell
# Codex (example)
mkdir -p ~/.agents/skills/context-handoff
cp plugins/context-handoff/skills/context-handoff/SKILL.md ~/.agents/skills/context-handoff/

# Generic: place SKILL.md wherever your agent discovers skills
```

The skill body avoids tool-specific syntax; commands like `/clear` and `/compact` appear only as trigger examples — substitute your agent's equivalents.

## Managing skills (desktop)

Prefer a GUI over editing files by hand? **[SkillDeck](https://github.com/crossoverJie/SkillDeck)** is a macOS desktop app for browsing, organizing, and managing agent skills — a handy companion for installing and toggling skills like these.

## Repository layout

```
agent-skills/
├── .claude-plugin/
│   └── marketplace.json                 # marketplace catalog
└── plugins/
    └── context-handoff/
        ├── .claude-plugin/plugin.json   # plugin manifest
        └── skills/context-handoff/SKILL.md
```

## Versioning

Each plugin sets an explicit `version` in its `plugin.json`. Bump it when you change a skill so installs are recognized as updates (without a version, the commit SHA is used as the version).

## License

[MIT](./LICENSE) © yangsui

---

## 中文说明

[@yangsui9999](https://github.com/yangsui9999) 的可复用 **跨 agent** 编码 skill 集合，打包成 Claude Code 插件市场。

skill 就是一份 agent 会读的 Markdown 参考文档（`SKILL.md`），告诉它怎么用某个经验技巧。这里的 skill 都写成与具体 agent 无关，Claude Code 可一键安装，原始 `SKILL.md` 也能直接拷给 Codex 等其它 agent 用。

**Claude Code 安装：**
```shell
/plugin marketplace add yangsui9999/agent-skills
/plugin install context-handoff@yangsui-skills
```
之后用 `/context-handoff:context-handoff` 调用，或说"上下文满了 / 新开终端 / 写个交接"等自动触发。

**其它 agent（如 Codex）：** 把 `plugins/context-handoff/skills/context-handoff/SKILL.md` 拷到该 agent 的 skills 目录（Codex 约为 `~/.agents/skills/context-handoff/`）即可。

**桌面管理（推荐）：** 喜欢图形界面、不想手动改文件的话，[SkillDeck](https://github.com/crossoverJie/SkillDeck) 是一款 macOS 桌面应用，可浏览、整理、管理 agent skill，配合这类 skill 使用很方便。

**已有 skill：**
- **context-handoff** — 长会话 context 快满时，判断要不要新开终端，并写一份安全完整的交接文档让新会话无缝接上；提交交接文档前会强制扫一遍有没有泄漏密钥。
