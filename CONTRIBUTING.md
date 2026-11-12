# Contributing

Thanks for helping improve this AI agent engineer interview guide. Contributions are welcome. They need to clear the quality bar below, and this file is that bar.

Maintained by [Landed](https://www.landed.jobs/?utm_source=github&utm_medium=referral&utm_campaign=github-ai-agent-interview-questions&utm_content=contributing). No affiliation with any company named in this repo.

---

## What we accept

- **Questions** on building AI agents: fundamentals, tool use, planning, memory and context, MCP, multi-agent, evals, reliability, safety. See [`questions/`](questions/).
- **Better answers.** Sharper wording, a missing tradeoff, a newer source.
- **Worked system designs** in the format of [System design scenarios](questions/10-system-design.md).
- **Code** for the coding round in [`code/`](code/): standard library only, with tests.
- **Fixes.** Broken links, wrong facts, stale spec details, mislabeled provenance.

## The rules

### 1. Honest provenance on every question

Every question carries one label:

- `Reported`: a public, checkable source shows the question was asked in a real interview. Link the source inline next to the label.
- `Representative`: written to match what agent loops ask, but not a quote from a specific interview.

No source means `Representative`. We never present a made-up question as reported.

### 2. Facts point to sources

Numbers, spec details and benchmark results link to a primary source: the paper, the spec page, the engineering post. Spec answers name the MCP revision they describe. Back-of-envelope numbers in system designs say they are estimates.

### 3. License discipline

This repo is **MIT** (see [`LICENSE`](LICENSE)).

| Source license | What you may do |
|---|---|
| MIT · Apache-2.0 · CC0 | Adapt text or code, with attribution. |
| CC-BY-4.0 | Link and comment. Do not copy verbatim. |
| CC-BY-SA | Link and comment only. Copying would relicense this repo. |
| Unknown or proprietary | Link only, and only if publicly readable. |

When in doubt, link instead of copying. Code in [`code/`](code/) must be original.

### 4. Style

- Answer first, then the mechanism, then the number.
- Write the answer the way a senior engineer says it in 60 to 90 seconds. Name the tradeoff and take a position.
- Plain words. No hype, no filler, no em dashes, sentence-case headings, straight quotes.
- Python uses 4-space indentation.

## Entry format

```markdown
<a id="q115"></a>
### Q115. The question, as an interviewer would ask it?

`Senior` · `Representative`

**Answer.** The 60 to 90 second senior answer.

**Follow-ups**
- *The next question the interviewer asks?* The short version of a good reply.

**Read:** [Primary source](https://example.com)
```

Difficulty is `Core` (every candidate should nail it), `Senior`, or `Staff`. Add new questions at the end of the topic file with the next free number, and add them to [`questions/README.md`](questions/README.md).

## How to contribute

1. Open an issue with a [template](.github/ISSUE_TEMPLATE/), or send a PR straight away for small fixes.
2. Fork, branch, edit.
3. Keep internal links relative and check they resolve. CI runs [lychee](.github/workflows/links.yml) on every PR. If you touch `code/`, run `python3 -m unittest test_code` in that folder.
4. Open the PR and fill in the [checklist](.github/PULL_REQUEST_TEMPLATE.md).

## Recognition

Contributors are credited in release notes.
