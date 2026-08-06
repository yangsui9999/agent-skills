---
name: ai-humanizer
description: Detects and removes AI writing traces from text, making it sound natural and human-written. Use when user mentions "去AI痕", "humanize", "去痕", "人性化", or "/ai-humanizer". Supports three intensity levels and five-dimension quality scoring.
---

# AI Humanizer - 去除 AI 写作痕迹

## Language

Match user's language. If user writes in Chinese, respond in Chinese.

## Usage

When invoked, follow this workflow:

1. **Determine input**: File path or inline text from user
2. **Read the content** if a file path is provided
3. **Ask intensity** (if not specified): gentle / medium / aggressive
4. **Process** the text following the detection rules below
5. **Output** the humanized text + change report + quality score
6. **Save** the result to a new file with `-humanized` suffix

## Input Detection

| Input | Action |
|-------|--------|
| File path (e.g., `drafts/article.md`) | Read the file, process content |
| Inline text | Process directly |
| No input specified | Ask user for file path or text |

## Intensity Levels

| Level | When to Use | Behavior |
|-------|-------------|----------|
| **gentle** (温和) | Text is already fairly natural | Only fix the most obvious AI patterns |
| **medium** (中等, default) | Most cases | Balanced: remove clear AI traces, preserve good expressions |
| **aggressive** (激进) | Text feels very AI-generated | Deep rewrite: restructure sentences, inject personality |

## Core Detection Rules

Scan for and fix these 22 patterns across 5 categories:

### Category 1: Content Patterns

1. **Overemphasis on significance** - Words like: 标志着、见证了、是…的体现、凸显了、象征着、为…奠定基础、关键转折点
2. **Overemphasis on prominence** - Repeatedly citing media reports or expert opinions without specific sources
3. **Shallow -ing analysis** - 突出/强调/确保…、反映/象征…、为…做出贡献
4. **Promotional language** - 拥有、充满活力的、丰富的、深刻的、令人叹为观止的
5. **Vague attribution** - 行业报告显示、观察者指出、专家认为 (without concrete sources)
6. **Formulaic "challenges and outlook"** - 尽管存在这些挑战、未来展望

### Category 2: Language & Grammar

7. **Overused "AI vocabulary"** - 此外、与…保持一致、至关重要、深入探讨、强调、持久的、增强、培养、获得、突出、复杂、关键、格局、展示、织锦
8. **Avoidance of "is/are"** - 作为/代表/标志着/充当、拥有/设有/提供
9. **Negative parallelism** - "不仅…而且…"、"这不仅仅是…而是…"
10. **Rule of three overuse** - Forcing ideas into groups of three
11. **Deliberate synonym cycling** - 主人公 → 主要角色 → 中心人物 → 英雄
12. **False scope** - "从 X 到 Y" where X and Y are not on the same scale

### Category 3: Style

13. **Dash overuse** - Using em dashes (—) more frequently than natural
14. **Bold overuse** - Mechanically bolding phrases
15. **Inline heading vertical lists** - Items starting with bold heading followed by colon
16. **Emoji decoration** - Emoji in headings or bullet points

### Category 4: Filler & Hedging

17. **Filler phrases** - 为了实现这一目标、由于下雨的事实、在这个时间点
18. **Over-qualification** - 可以潜在地可能被认为该政策可能会
19. **Generic positive conclusions** - 未来看起来光明、激动人心的时代即将到来

### Category 5: Collaboration Traces

20. **Collaborative communication traces** - 希望这对您有帮助、当然！、您想要…
21. **Knowledge cutoff disclaimers** - 截至 [日期]、根据我最后的训练更新
22. **Sycophantic tone** - Overly positive, people-pleasing language

## Processing Principles

1. **Delete filler phrases** - Remove openers and emphatic crutch words
2. **Break formulaic structures** - Avoid binary contrasts, dramatic segmentation, rhetorical setups
3. **Vary rhythm** - Mix sentence lengths. Two items beats three. Vary paragraph endings
4. **Trust the reader** - State facts directly, skip softening, justification, and hand-holding
5. **Remove quotable lines** - If it sounds like an inspirational quote, rewrite it

## Injecting Personality

Removing AI patterns is only half the job. Good writing needs a real person:

- **Have opinions** - React to facts, don't just neutrally report
- **Vary rhythm** - Short punchy sentences + longer ones that take time to unfold
- **Acknowledge complexity** - Real people have complex feelings
- **Use "I" appropriately** - First person is honest
- **Allow some messiness** - Perfect structure feels algorithmic
- **Be specific about feelings** - Not "concerning", but concrete scenarios

## Style Preservation

If the user specifies a writing style to preserve (e.g., "preserve my conversational tone"):
- Only remove unintentional AI traces
- Keep deliberate stylistic choices (e.g., using dashes for pauses)
- Maintain style consistency throughout

## Output Format

### When processing, output in this structure:

```
# Humanized Text

[The rewritten text with AI traces removed]

# Change Report

[Brief summary of major changes made]

## Key Changes
- [Change 1]: [reason]
- [Change 2]: [reason]
- ...

# Quality Score

| Dimension | Score | Notes |
|-----------|-------|-------|
| Directness | x/10 | [note] |
| Rhythm | x/10 | [note] |
| Trust | x/10 | [note] |
| Authenticity | x/10 | [note] |
| Conciseness | x/10 | [note] |
| **Total** | **x/50** | [rating] |
```

Rating scale:
- 45-50: Excellent - AI traces fully removed
- 35-44: Good - Minor improvements possible
- 25-34: Average - Needs further revision
- Below 25: Poor - Recommend reprocessing

## File Output

After processing, save the humanized text to:
- Same directory as input file
- Filename: `{original-name}-humanized.md`
- Only save the humanized text content (not the report/score)

Example: `drafts/article.md` → `drafts/article-humanized.md`

## Pipeline Integration

This skill is designed to work in a content pipeline:

```
Draft (markdown) → /ai-humanizer → /baoyu-post-to-wechat → WeChat drafts
```

After humanization is complete, suggest the next step:
"Humanization complete. Run `/baoyu-post-to-wechat` to format and publish to WeChat."
