# Multi-agent systems

<sub>[Question index](README.md) · [Repo home](../README.md) · Previous: [MCP](05-mcp.md) · Next: [Evals for agents](07-evals.md)</sub>

9 questions, Q61 to Q69. Multi-agent designs are popular in demos and costly in production. The strongest candidates can name the cases where several agents win, and argue against them everywhere else.

Difficulty is `Core`, `Senior` or `Staff`. `Representative` questions are written by us to match real loops; `Reported` questions link a public source.

---

<a id="q61"></a>
### Q61. When does a multi-agent system beat a single agent?

`Senior` · `Representative`

**Answer.** When the work splits into parallel, mostly independent pieces that each need a lot of reading, and the value of the result pays for the extra tokens. Broad research is the standard example. Anthropic's research system, with a Claude Opus 4 lead and Claude Sonnet 4 sub-agents, beat single-agent Opus 4 by 90.2% on their internal research eval. The same post says why: token usage alone explained 80% of the performance variance on BrowseComp, and multi-agent setups let you spend more tokens in parallel, each in a clean context. It also lists where multi-agent is a poor fit: tasks where agents must share context or have many dependencies, and most coding, which has few parallel subtasks. So my rule is parallel reads, single writer. Several agents gather, one agent decides and acts.

**Follow-ups**
- *What did it cost?* About 15 times the tokens of a chat, per the same post, versus about 4 times for a single agent.
- *How would you decide for your product?* Run both on the same eval, compare quality, tokens and latency, and see if the gain is worth the bill.

**Read:** [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) (Anthropic)

---

<a id="q62"></a>
### Q62. What is the case against multi-agent systems?

`Senior` · `Representative`

**Answer.** Cognition's "Don't build multi-agents" post makes it well. Their two principles are to share context, meaning full agent traces and not only individual messages, and that actions carry implicit decisions, and conflicting decisions produce bad results. Their example: split "build a Flappy Bird clone" into a background sub-agent and a bird sub-agent, and you may get a Super Mario style background and a bird that does not match, because each made reasonable but different assumptions. Every handoff loses context, and parallel agents writing to shared state make conflicting choices no one reconciles. Debugging is harder because a failure spans several traces. My take is that this is right for tightly coupled work like coding, and the Anthropic research post agrees by naming coding as a poor fit. For loosely coupled reads, multi-agent still wins. The skill is telling the two apart.

**Follow-ups**
- *What do you do instead for long coding tasks?* One agent with a linear history, plus compaction or a summarising model for older context.
- *Is a sub-agent that only answers a question okay?* Yes. That is a read, and it returns a result, not a decision about shared state.

**Read:** [Don't build multi-agents](https://cognition.ai/blog/dont-build-multi-agents) (Cognition)

---

<a id="q63"></a>
### Q63. Describe the orchestrator-worker pattern.

`Core` · `Representative`

**Answer.** A lead agent, the orchestrator, takes the task, decides how to split it, and spawns workers with specific sub-tasks. Workers run in their own contexts with their own tools and return results. The orchestrator merges them, decides if more work is needed, and produces the answer. It differs from a fixed parallel workflow because the orchestrator decides the sub-tasks at run time. What makes it work in practice: detailed task descriptions for each worker with an objective, output format, tool guidance and boundaries, which Anthropic found prevented duplicated effort; scaling effort to the query, so a simple question gets one worker and not ten; and workers returning condensed findings with sources, not raw dumps. What breaks it: workers with overlapping scope, an orchestrator that cannot judge when to stop, and results too long for the orchestrator's window.

**Follow-ups**
- *Should workers talk to each other?* Rarely. Hub and spoke through the orchestrator is easier to trace and bound.
- *Synchronous or asynchronous workers?* Synchronous is simpler; the Anthropic post notes the lead waiting on each batch is a bottleneck, and async adds coordination problems.

**Read:** [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) · [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)

---

<a id="q64"></a>
### Q64. What is a handoff, and how is it different from calling an agent as a tool?

`Core` · `Representative`

**Answer.** In a handoff, one agent transfers control of the conversation to another. The second agent takes over, usually with the conversation history, and talks to the user from then on. In the OpenAI Agents SDK, a handoff is presented to the model as a tool named like `transfer_to_refund_agent`, and calling it switches the active agent. A triage agent handing off to a billing specialist is the textbook case. In agent-as-tool, the manager calls a specialist, gets a result back, and stays in charge of the conversation. OpenAI's practical guide calls these the decentralised and manager patterns. Handoffs suit cases where the specialist needs to own a multi-turn exchange. Agent-as-tool keeps one consistent voice and one owner, and is easier to reason about. The traps with handoffs: what history to pass, whether the new agent sees tool results from the old one, and handing back.

**Follow-ups**
- *What do you filter on handoff?* Old tool calls and internal reasoning the next agent does not need, while keeping the user's messages and key facts.
- *How do you stop ping-pong handoffs?* Limit the number of handoffs per conversation and log each with a reason.

**Read:** [OpenAI Agents SDK: handoffs](https://openai.github.io/openai-agents-python/handoffs/) · [A practical guide to building agents](https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf)

---

<a id="q65"></a>
### Q65. How do you debug a failure in a multi-agent system?

`Senior` · `Representative`

**Answer.** It starts with tracing built in from day one. Every agent run, model call, tool call and handoff is a span with a parent, so one trace shows the whole tree: what the orchestrator asked, what each worker did, what came back. Without that, you are reading interleaved logs. With it, I walk the tree looking for the first wrong output. It is usually one of four things. A vague task description from the orchestrator. A worker that went out of scope or returned too much. Information lost at a handoff or in a summary. Or the orchestrator ignoring or misreading a correct worker result. I reproduce by replaying the run with the recorded inputs to the failing agent, which is easier if each agent's input is fully captured. Then the fix goes with a new eval case, scored on the final outcome and on the intermediate step that broke.

**Follow-ups**
- *What standard would you use for spans?* OpenTelemetry's GenAI semantic conventions, which define agent and tool operation spans.
- *Non-determinism makes replay flaky. What then?* Replay with temperature 0 or with cached model responses up to the failing step.

**Read:** [OpenTelemetry GenAI semantic conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/)

---

<a id="q66"></a>
### Q66. How do agents share state safely?

`Staff` · `Representative`

**Answer.** As little as possible, and through explicit, owned stores rather than shared conversation. My default is that each piece of state has exactly one writer. Workers return results to the orchestrator, and the orchestrator writes. If several agents must write, they go through a store with real concurrency control: versioned records with compare-and-set, locks with timeouts, or an append-only event log that one process folds into state. Large artifacts go to files or object storage, and agents pass references. I avoid a shared scratchpad that every agent reads and edits freely, because agents overwrite each other's work and nobody notices. This is ordinary distributed systems practice; agents just make it easier to forget because the "writes" look like natural language.

**Follow-ups**
- *Two agents edit the same file. What happens?* Last writer wins unless you prevent it. Give each agent its own branch or worktree and merge deliberately.
- *How do you show shared state to an agent?* Render a read-only snapshot into its context, with a tool to request changes.

**Read:** [Don't build multi-agents](https://cognition.ai/blog/dont-build-multi-agents)

---

<a id="q67"></a>
### Q67. Orchestration versus choreography for agents?

`Senior` · `Representative`

**Answer.** Orchestration has a central coordinator that tells each agent what to do and collects results. Choreography has agents reacting to each other's messages or events with no central controller. In microservices both are common. For LLM agents I default to orchestration. The coordinator gives one place to enforce budgets, stop conditions and policies, one trace root, and one owner of the final answer. Choreographed agents can fall into chatter loops, where two agents keep politely handing work back and forth, and no single component knows if the overall task is done. Choreography makes sense for loosely coupled, event-driven systems with clear contracts, such as an agent that reacts to new support tickets and posts results to a queue another system consumes. Even then, each agent is a bounded unit with its own limits.

**Follow-ups**
- *How do you bound a choreographed system?* Budgets per agent, a time-to-live on each message, and a global circuit breaker.
- *Where does a human approval step go?* At the orchestrator, before any action with side effects.

**Read:** [A practical guide to building agents](https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf)

---

<a id="q68"></a>
### Q68. How do you evaluate a multi-agent system?

`Senior` · `Representative`

**Answer.** On the end result first, with the same task set and graders I would use for a single agent, so I can compare designs directly. Then I add component checks: does the orchestrator split tasks sensibly, do workers stay in scope, how often does information get lost at handoffs, how many tokens and how much wall time per task. Anthropic's research post reports using an LLM judge with a rubric covering factual accuracy, citation accuracy, completeness, source quality and tool efficiency, and also says they started evaluating with about 20 queries because early changes had large effects. I also run the single-agent baseline in every eval cycle. If multi-agent stops beating it by enough to pay for the extra tokens, I simplify. Human review of a sample stays in the loop, since judges miss things like a sub-agent preferring SEO content farms over authoritative sources, which Anthropic found by hand.

**Follow-ups**
- *Outcome or trajectory scoring?* Outcome as the main metric; trajectory checks for diagnosis.
- *How many runs per task?* Several, because variance is higher with more agents.

**Read:** [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)

---

<a id="q69"></a>
### Q69. What does a multi-agent system cost, and how do you keep it in check?

`Senior` · `Representative`

**Answer.** More than people expect. Each agent re-sends its own growing context every turn, and the orchestrator re-reads all worker results. Anthropic's figure is about 15 times the tokens of a chat interaction. Controls I use: scale the number of workers to the query, with explicit guidance like one worker for a fact lookup and more only for broad comparisons. Use smaller models for workers where the eval allows. Cap tokens and tool calls per worker and per run, and return condensed results. Cache stable prefixes like system prompts and tool definitions. And watch cost per successful task, not per run, because a cheaper design that fails more often costs more per useful answer. When the numbers do not work, collapse back to one agent with sub-calls for the parallel parts.

**Follow-ups**
- *What metric would you put on a dashboard?* Cost per successful task, p50 and p95, broken down by agent role.
- *How do you stop a runaway orchestrator from spawning 50 workers?* A hard cap in code on concurrent and total workers per run.

**Read:** [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)

---

<sub>[Question index](README.md) · Next: [Evals for agents](07-evals.md)</sub>
