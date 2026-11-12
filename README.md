<a name="top"></a>

<div align="center">

<a href="https://www.landed.jobs/?utm_source=github&utm_medium=referral&utm_campaign=github-ai-agent-interview-questions&utm_content=repo-home"><picture><source media="(prefers-color-scheme: dark)" srcset="https://static.b100x.ai/github-repos/images/brand/landed-wordmark-dark.png"><img src="https://static.b100x.ai/email/landed-wordmark.png" alt="Landed" width="200"></picture></a>

<img src="assets/banner.svg" alt="AI Agent Interview Questions" width="100%">

[![Stars](https://img.shields.io/github/stars/landedjobs/ai-agent-interview-questions?style=social)](https://github.com/landedjobs/ai-agent-interview-questions)
[![License: MIT](https://img.shields.io/badge/License-MIT-6C2BD9.svg)](LICENSE)
[![Updated](https://img.shields.io/badge/updated-2026--11-00A86B)](#faq)
[![Questions](https://img.shields.io/badge/questions-114-6C2BD9)](questions/)
[![System designs](https://img.shields.io/badge/system%20designs-5-6C2BD9)](questions/10-system-design.md)
[![Visit Landed](https://img.shields.io/badge/Visit-Landed-6C2BD9?logo=rocket&logoColor=white)](https://www.landed.jobs/?utm_source=github&utm_medium=referral&utm_campaign=github-ai-agent-interview-questions&utm_content=repo-home)

**AI agent engineer interview prep for 2026**: 114 questions with senior answers and follow-ups, 5 worked system designs and runnable Python for the coding round.

*Maintained by [Landed](https://www.landed.jobs/?utm_source=github&utm_medium=referral&utm_campaign=github-ai-agent-interview-questions&utm_content=repo-home): daily AI-native job matches, agent help with every application, and mock-interview prep.*

</div>

<!-- landed-apply-cta -->
<table><tr><td>
<b>⚡ <a href="https://app.landed.jobs/signup?from=github&amp;cta=github-guide-apply&amp;item=ai-agent-interview-questions&amp;utm_source=github&amp;utm_medium=referral&amp;utm_campaign=github-ai-agent-interview-questions&amp;utm_content=guide-apply">Auto-apply to AI agent engineer jobs that match you →</a></b><br>
Upload your resume once. <a href="https://www.landed.jobs">landed</a> finds the roles that fit you and applies within hours of them going live, so you actually hear back.
</td></tr></table>


---

Agent engineering interviews ask what happens when a model is allowed to act. Can you design tools a model uses correctly? Can you keep a 50-step run on budget? Can you prove it works with an eval, and stop a poisoned web page from emailing your customer list to a stranger? This repo covers that loop: each question has the answer a senior engineer gives in about 90 seconds, the follow-ups interviewers ask next, and links to the primary sources (the MCP spec, Anthropic and OpenAI engineering guides, the tau-bench and SWE-bench papers, Simon Willison on prompt injection).

All answers are dated November 2026. MCP answers follow the current spec revision, 2026-07-28, which removed sessions and the initialize handshake. If you learned MCP in 2025, read [Q51](questions/05-mcp.md#q51) first.

## Contents

- [What agent interviews test](#what-agent-interviews-test)
- [Question index](#question-index)
- [The 20 questions to know cold](#the-20-questions-to-know-cold)
- [1-week study plan](#1-week-study-plan)
- [Code for the coding round](#code-for-the-coding-round)
- [Primary sources](#primary-sources)
- [FAQ](#faq)
- [Contributing](#contributing)

## What agent interviews test

Titles vary (AI agent engineer, applied AI engineer, LLM engineer, forward deployed engineer), but agent loops test the same six things. Companies merge or skip rounds, so treat this as a map of topics rather than a fixed schedule. Classic algorithm puzzles are rare.

| Round | What they are checking | Where to prep |
|---|---|---|
| Concepts screen | You know what the model controls and what your code controls; agent vs workflow; when not to build an agent | [Fundamentals](questions/01-fundamentals.md) |
| Tools and MCP deep dive | Tool schema design, error handling, tool count, MCP architecture, auth and its security problems | [Tool use](questions/02-tool-use.md) · [MCP](questions/05-mcp.md) |
| Agent coding | Build the loop, a tool layer or a retry wrapper in 30 to 45 minutes, then extend it | [Coding exercises](questions/11-coding.md) · [`code/`](code/) |
| Agent system design | Design a support, coding, research or internal agent with numbers, evals and failure modes | [System design scenarios](questions/10-system-design.md) |
| Evals and reliability | Outcome vs trajectory grading, pass^k, simulated users, retries, idempotency, tracing | [Evals](questions/07-evals.md) · [Reliability](questions/08-reliability-and-production.md) |
| Safety | Prompt injection, the lethal trifecta, sandboxing, approval design | [Safety and security](questions/09-safety-and-security.md) |

> [!TIP]
> The thread through every round: say where the model's judgment ends and your code's guarantees begin. Policies, budgets, permissions and idempotency belong in code. Interviewers listen for that line.

## Question index

| # | Topic | Questions | Covers |
|---|---|---|---|
| 1 | [Fundamentals](questions/01-fundamentals.md) | 12 | Agent vs workflow, the loop, ReAct, workflow patterns, error compounding, harness vs model, code agents |
| 2 | [Tool use and function calling](questions/02-tool-use.md) | 13 | Schema design, tool results, errors, parallel calls, 300 tools, versioning, idempotent tools |
| 3 | [Planning and reasoning](questions/03-planning-and-reasoning.md) | 10 | Plan-and-execute, reflection, reasoning models, search, loops, stop conditions, long-horizon runs |
| 4 | [Memory and context](questions/04-memory-and-context.md) | 12 | Context engineering, short and long-term memory, compaction, sub-agents, caching, context rot |
| 5 | [MCP](questions/05-mcp.md) | 13 | Architecture, transports, the 2026-07-28 stateless revision, OAuth, token passthrough, tool poisoning, gateways |
| 6 | [Multi-agent systems](questions/06-multi-agent.md) | 9 | When it wins, the case against, orchestrator-worker, handoffs, shared state, cost |
| 7 | [Evals for agents](questions/07-evals.md) | 12 | Outcome vs trajectory, pass@k vs pass^k, tau-bench, SWE-bench, simulated users, judges |
| 8 | [Reliability and production](questions/08-reliability-and-production.md) | 12 | Retries, durable execution, cost, latency, tracing, outages, rollouts, guardrails |
| 9 | [Safety and security](questions/09-safety-and-security.md) | 12 | Prompt injection, lethal trifecta, dual LLM and CaMeL, sandboxing, approvals, credentials |
| 10 | [System design scenarios](questions/10-system-design.md) | 5 | Support agent with refunds, coding agent, research agent, MCP internal assistant, data agent |
| 11 | [Coding exercises](questions/11-coding.md) | 4 | Agent loop, tool registry, retry wrapper, testing with a fake model |
| | **Total** | **114** | 39 Core, 64 Senior, 11 Staff. [Full list](questions/README.md) |

Every entry follows the same format: the question, a difficulty tag (`Core`, `Senior`, `Staff`), a provenance label, the 60 to 90 second answer, follow-ups with short replies, and sources. Provenance is either `Representative` (we wrote the question to match what agent loops ask) or `Reported` (a public source shows it was asked, linked inline). Every question in this first edition is `Representative`. We would rather mark them honestly than borrow credibility; if you were asked one of these and can point to a public write-up, open a PR to relabel it.

## The 20 questions to know cold

If you have one evening, read these. They come up in some form in nearly every agent loop.

1. [Q1. What is the difference between an agent and a workflow?](questions/01-fundamentals.md#q1)
2. [Q2. Walk me through the agent loop.](questions/01-fundamentals.md#q2)
3. [Q4. When should you not build an agent?](questions/01-fundamentals.md#q4)
4. [Q6. Why do errors compound in long agent runs?](questions/01-fundamentals.md#q6)
5. [Q14. How do you design a good tool schema?](questions/02-tool-use.md#q14)
6. [Q17. A tool call fails. What should the agent see?](questions/02-tool-use.md#q17)
7. [Q20. You have 300 tools. What do you do?](questions/02-tool-use.md#q20)
8. [Q24. How do you make a tool safe to call more than once?](questions/02-tool-use.md#q24)
9. [Q30. How do you stop an agent from looping forever?](questions/03-planning-and-reasoning.md#q30)
10. [Q36. What is context engineering?](questions/04-memory-and-context.md#q36)
11. [Q39. What is compaction, and what goes wrong with it?](questions/04-memory-and-context.md#q39)
12. [Q49. Explain MCP's architecture: host, client and server.](questions/05-mcp.md#q49)
13. [Q54. What is tool poisoning?](questions/05-mcp.md#q54)
14. [Q61. When does a multi-agent system beat a single agent?](questions/06-multi-agent.md#q61)
15. [Q70. How do you evaluate an agent?](questions/07-evals.md#q70)
16. [Q72. Explain pass@k versus pass^k.](questions/07-evals.md#q72)
17. [Q83. What is durable execution and why do agents need it?](questions/08-reliability-and-production.md#q83)
18. [Q86. What do you trace and log for an agent in production?](questions/08-reliability-and-production.md#q86)
19. [Q95. Explain the lethal trifecta.](questions/09-safety-and-security.md#q95)
20. [Q105. Where do you enforce policy: in the prompt, in the model, or in code?](questions/09-safety-and-security.md#q105)

## 1-week study plan

About two hours a day. Say each answer out loud with a timer; if it runs past 90 seconds, cut it.

| Day | Read | Do |
|---|---|---|
| 1 | [Fundamentals](questions/01-fundamentals.md), [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) | Write the agent loop from memory without looking at [`code/agent_loop.py`](code/agent_loop.py). Then compare. |
| 2 | [Tool use](questions/02-tool-use.md), [Writing effective tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents) | Rewrite one real API you know as three task-shaped tools with schemas. |
| 3 | [Memory and context](questions/04-memory-and-context.md), [Planning](questions/03-planning-and-reasoning.md) | Add compaction and a step budget to your loop. Explain what you keep and why. |
| 4 | [MCP](questions/05-mcp.md), the [MCP changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog) | Draw host, client, server and the OAuth flow on paper. Explain token passthrough in two sentences. |
| 5 | [Evals](questions/07-evals.md), [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) | Write 20 eval tasks for your loop with outcome graders. Compute pass^3 by hand from 5 trials. |
| 6 | [Reliability](questions/08-reliability-and-production.md), [Safety](questions/09-safety-and-security.md), [The lethal trifecta](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/) | Add retries with idempotency keys and an approval gate. Threat-model an email agent. |
| 7 | [System design](questions/10-system-design.md), [Multi-agent](questions/06-multi-agent.md) | Do two designs cold in 45 minutes each, out loud. Then the 20 must-know questions as a final pass. |

For structured practice, landed has free courses that match the later days: [Reliable tool contracts for agents](https://www.landed.jobs/resources/courses/agent-tool-contracts?utm_source=github&utm_medium=referral&utm_campaign=github-ai-agent-interview-questions&utm_content=study-plan), [Stateful agent workflows](https://www.landed.jobs/resources/courses/agent-stateful-workflows?utm_source=github&utm_medium=referral&utm_campaign=github-ai-agent-interview-questions&utm_content=study-plan), [Agent failure investigation lab](https://www.landed.jobs/resources/courses/agent-failure-lab?utm_source=github&utm_medium=referral&utm_campaign=github-ai-agent-interview-questions&utm_content=study-plan) and [Agents, evals and LLMOps](https://www.landed.jobs/resources/courses/agents-evals-llmops?utm_source=github&utm_medium=referral&utm_campaign=github-ai-agent-interview-questions&utm_content=study-plan).

## Code for the coding round

[`code/`](code/) has a small, original, standard-library-only implementation of what agent coding rounds ask for. It runs without an API key, because the loop takes any model callable and the tests use a scripted fake.

| File | What it shows |
|---|---|
| [`agent_loop.py`](code/agent_loop.py) | The loop with max steps, token budget, repeated-call detection, approval for destructive tools, parallel tool execution and result truncation |
| [`tool_registry.py`](code/tool_registry.py) | Decorator that builds JSON Schemas from type hints, validates arguments and returns errors the model can act on |
| [`retry.py`](code/retry.py) | Exponential backoff with full jitter, deadline, `retry_after`, and one idempotency key across attempts |
| [`test_code.py`](code/test_code.py) | Deterministic tests of the harness with a scripted model |

```bash
cd code
python3 -m unittest test_code -v
```

The walkthroughs, with talk tracks and follow-ups, are in [Coding exercises](questions/11-coding.md).

## Primary sources

The answers cite these. If you read nothing else, read the first four.

- [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) (Anthropic). Workflows vs agents and the five workflow patterns.
- [Writing effective tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents) (Anthropic). Tool design with concrete examples.
- [MCP specification, 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28) and its [changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog).
- [The lethal trifecta for AI agents](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/) (Simon Willison).
- [A practical guide to building agents](https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf) (OpenAI, PDF). Single vs multi-agent, guardrails.
- [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) (Anthropic).
- [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) (Anthropic) and [Don't build multi-agents](https://cognition.ai/blog/dont-build-multi-agents) (Cognition). Read them together.
- [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) (Anthropic).
- [tau-bench](https://arxiv.org/abs/2406.12045), [tau2-bench](https://arxiv.org/abs/2506.07982) and [SWE-bench](https://arxiv.org/abs/2310.06770) papers.
- [ReAct](https://arxiv.org/abs/2210.03629), [Reflexion](https://arxiv.org/abs/2303.11366) and [CodeAct](https://arxiv.org/abs/2402.01030) papers.
- [Defeating Prompt Injections by Design (CaMeL)](https://arxiv.org/abs/2503.18813).

## FAQ

**What is an AI agent engineer, and how is the interview different from an AI engineer interview?**
An AI agent engineer builds systems where a model calls tools and takes actions over many steps: support agents, coding agents, research agents, internal assistants. The general AI engineer loop spends more time on RAG, fine-tuning and model basics. The agent loop goes deeper on tool design, MCP, multi-step evals, reliability and prompt injection. For the broader loop, see [awesome-ai-engineer-interview](https://github.com/landedjobs/awesome-ai-engineer-interview).

**Do I need to know a framework like LangGraph or the OpenAI Agents SDK?**
Know one well enough to discuss its tradeoffs, but expect to write the loop without it. Interviewers care more that you can explain what goes into the context on each step than which library you used. See [Q11](questions/01-fundamentals.md#q11).

**How current is the MCP section?**
It follows the 2026-07-28 revision, which made the protocol stateless, replaced server-initiated requests with multi round-trip requests, moved tasks into an extension and deprecated roots, sampling and logging. Older material that walks through `initialize` and session ids describes 2025 revisions.

**Why are all questions labeled Representative?**
Because we could not find public, checkable sources for specific agent questions asked at specific companies, and we will not invent them. The questions reflect what agent loops cover. If you can link a public write-up of a question you were asked, a PR to relabel it as `Reported` is welcome.

**How long does it take to prepare?**
With some experience building LLM apps, one focused week using the [study plan](#1-week-study-plan). Starting from zero on agents, build a small agent end to end first; the answers make more sense after you have watched a loop fail.

**Where can I find agent engineering jobs?**
[llm-engineer-jobs](https://github.com/landedjobs/llm-engineer-jobs) lists LLM and AI agent engineer roles, refreshed every two days.

---

## Contributing

PRs and issues welcome: add a question, sharpen an answer, fix a stale fact or a broken link, or add a worked design. This is a sourced repo, so every factual claim should point to something checkable, and questions are labeled honestly as `Representative` or `Reported`. See **[CONTRIBUTING.md](CONTRIBUTING.md)** for the format and quality bar.

---

### Part of the Landed AI-native jobs family

The umbrella maps every AI-native role; the siblings go deep per role.

- 🧭 [awesome-ai-native-jobs](https://github.com/landedjobs/awesome-ai-native-jobs): the umbrella that maps the whole AI-native job landscape
- 🤖 [llm-engineer-jobs](https://github.com/landedjobs/llm-engineer-jobs): LLM and AI agent engineer jobs, refreshed every 2 days
- 🚀 [ai-engineer-jobs](https://github.com/landedjobs/ai-engineer-jobs): 300 live AI engineer roles, auto-updated
- 🎯 [awesome-ai-engineer-interview](https://github.com/landedjobs/awesome-ai-engineer-interview): the full AI engineer interview loop, with company breakdowns
- 🔎 [rag-engineer-interview-questions](https://github.com/landedjobs/rag-engineer-interview-questions): RAG interview questions and worked designs
- 🤝 [forward-deployed-engineer-jobs](https://github.com/landedjobs/forward-deployed-engineer-jobs): FDE & customer-facing engineering
- 📘 [ai-interview-guides](https://github.com/landedjobs/ai-interview-guides): interview guides for 200 companies
- ❓ [ai-interview-questions](https://github.com/landedjobs/ai-interview-questions): 759 AI interview questions with answers
- 📦 [ai-engineer-portfolio-projects](https://github.com/landedjobs/ai-engineer-portfolio-projects): 80+ buildable portfolio projects

---

<div align="center">

### Stop spraying. Get **matched**, get **prepped**, get **Landed**.

[![Get Started](https://img.shields.io/badge/Get%20Started%20Free-→-6C2BD9?style=for-the-badge)](https://www.landed.jobs/?utm_source=github&utm_medium=referral&utm_campaign=github-ai-agent-interview-questions&utm_content=repo-home)

<sub>Maintained by [Landed](https://www.landed.jobs/?utm_source=github&utm_medium=referral&utm_campaign=github-ai-agent-interview-questions&utm_content=repo-home) · No affiliation with the companies named. Content MIT-licensed; linked resources retain their own licenses. Questions are provenance-labeled, reported questions cite public sources.</sub>

<br/>

[![Star History Chart](https://api.star-history.com/svg?repos=landedjobs/ai-agent-interview-questions&type=Date)](https://star-history.com/#landedjobs/ai-agent-interview-questions&Date)

</div>
