# Reliability and production

<sub>[Question index](README.md) · [Repo home](../README.md) · Previous: [Evals for agents](07-evals.md) · Next: [Safety and security](09-safety-and-security.md)</sub>

12 questions, Q82 to Q93. This section is mostly distributed systems with a model inside. Candidates who have run services in production do well here, and that experience is worth drawing on out loud.

Difficulty is `Core`, `Senior` or `Staff`. `Representative` questions are written by us to match real loops; `Reported` questions link a public source.

---

<a id="q82"></a>
### Q82. How do you handle retries in an agent?

`Core` · `Representative`

**Answer.** At two levels, with different rules. Infrastructure retries live in code. Model API calls and tool calls that fail with timeouts, 429s or 5xx get retried with exponential backoff and jitter, honouring any `Retry-After` header, with a cap on attempts and a total deadline. AWS's Builders' Library article on timeouts, retries and backoff with jitter is the reference I would cite. Retries on writes only happen if the operation is idempotent, which means an idempotency key per logical operation reused across attempts. Then there are agent-level retries, where the model sees a failure and decides to try differently. Those are for semantic errors like a bad argument or an empty search, and they cost a turn each, so I keep them bounded too. What I avoid is retries at every layer stacking up: if the SDK retries 3 times, my wrapper 3 times and the agent 3 times, one outage becomes 27 calls.

**Follow-ups**
- *Why jitter?* So many clients retrying after an outage do not hit the service in synchronised waves.
- *Which errors never get retried?* Validation errors, auth failures, policy refusals. Retrying will not change the answer.

**Read:** [Timeouts, retries and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) (AWS) · [code/retry.py](../code/retry.py)

---

<a id="q83"></a>
### Q83. What is durable execution and why do agents need it?

`Senior` · `Representative`

**Answer.** Durable execution means a workflow's progress is persisted as it runs, so if the process crashes, it resumes from the last completed step instead of starting over. Temporal is the best-known engine: it records an event history of each workflow and replays it to rebuild state, while activities, the steps with side effects, get automatic retries. Agents need this because they are long-running, multi-step, and expensive. A 40-minute run that dies at minute 35 and restarts from zero wastes money, and worse, it may repeat side effects like sending an email twice. With durable execution, each model call and tool call is a recorded step, completed steps are not re-run, human approvals can pause a workflow for days, and deploys do not kill in-flight runs. The design constraint is determinism: orchestration code must replay the same way, so model calls and tool calls go in activities, never inline.

**Follow-ups**
- *Do you need Temporal for this?* No. A database row per step with status and outputs, plus a resumable worker, gets you most of it.
- *What about the model's non-determinism?* Recorded outputs are replayed, not regenerated. That is the point.

**Read:** [Temporal: workflows](https://docs.temporal.io/workflows)

---

<a id="q84"></a>
### Q84. How do you control cost per agent task?

`Core` · `Representative`

**Answer.** First, measure it per task, not per call, broken down by model calls, tool calls and steps. Then the levers, roughly by impact. Better tools so tasks take fewer steps. Smaller tool results and compaction so each turn re-sends less. Prompt caching with a stable prefix, so the repeated history is cheap. Routing simple steps to smaller models. Setting reasoning effort per step instead of maximum everywhere. And hard budgets enforced in code: tokens or dollars per run, per user per day, with a graceful stop when hit. Last, I check value. A run that costs $2 and saves a support agent 15 minutes is cheap. A run that costs $0.10 and fails half the time is expensive. So the number I report is cost per successful task.

**Follow-ups**
- *Where does most cost hide?* Long contexts re-sent every turn, verbose tool outputs, and reasoning tokens.
- *How do you set a per-run budget?* From the distribution of successful runs on the eval, with headroom, then tighten using production data.

**Read:** [Anthropic prompt caching](https://docs.claude.com/en/docs/build-with-claude/prompt-caching)

---

<a id="q85"></a>
### Q85. How do you reduce agent latency?

`Senior` · `Representative`

**Answer.** Count the turns, because each model call is a round trip and each tool call adds its own time. The biggest win is fewer turns: task-shaped tools, parallel tool calls for independent reads, and a workflow for steps that never need a decision. Then make each turn faster. Shorter contexts and prompt caching cut time to first token. Smaller models for simple steps. Lower reasoning effort where the eval allows. Faster tools, with caches for repeated lookups. Then improve perceived latency. Stream the model's output, show progress like "searching your orders", and return a partial answer while background work continues. For long tasks, make them asynchronous: accept the request, run it in a worker, notify on completion. Users accept a 3-minute research task if they know it is running, and abandon a 20-second spinner that shows nothing.

**Follow-ups**
- *What is the latency budget of a voice agent?* Very tight, often well under a second per turn, which rules out multi-step loops on the hot path.
- *Speculative execution?* Prefetch likely-needed data in parallel with the model call. Only for reads.

**Read:** [An LLM Compiler for Parallel Function Calling](https://arxiv.org/abs/2312.04511)

---

<a id="q86"></a>
### Q86. What do you trace and log for an agent in production?

`Core` · `Representative`

**Answer.** Every run is a trace, and every model call, tool call, retry, handoff and approval is a span inside it, with parent-child links. For model calls I record the model and version, token counts in and out, cached tokens, latency, finish reason, and the messages, redacted where needed. For tool calls: name, arguments, result size, latency, status and error kind. At the run level: user or tenant, agent version, prompt and tool-set versions, total cost, steps, outcome and the stop reason. I follow the OpenTelemetry GenAI semantic conventions so traces work with standard backends, and they now define agent spans for creating and invoking agents and executing tools. The point of all this is answering, within a minute, "what exactly did the model see at step 7, and why did it call that tool?" If I cannot, the logging is not good enough.

**Follow-ups**
- *Full prompts in logs: privacy problem?* Yes. Redact PII, restrict access, set retention, and sample full content rather than storing all of it.
- *What alerts do you set?* Error rate, stop-reason mix (budget and max-steps spikes), cost per task, latency, and tool error rates.

**Read:** [OpenTelemetry GenAI semantic conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/)

---

<a id="q87"></a>
### Q87. A tool times out after the agent sends a payment request. Did the payment go through?

`Senior` · `Representative`

**Answer.** You do not know, and the design must make that safe. A timeout means the request may have been processed, so blindly retrying could pay twice, and telling the user it failed could be wrong. The fix starts before the call. I send an idempotency key derived from the run and step, so a retry with the same key returns the original result instead of creating a second payment. After a timeout I retry with the same key, or query the status by key or by a client reference I attached. If the status stays unknown, the agent tells the user honestly that the payment is being confirmed, and a background job reconciles it. The agent should never improvise here. The tool encapsulates the protocol, and the model just sees "pending, will confirm". I would also log the case for reconciliation reports.

**Follow-ups**
- *What if the payment API has no idempotency support?* Attach your own reference, check for it before retrying, and accept a reconciliation process.
- *Where does this logic live?* In the tool, not the prompt. Models should not handle exactly-once semantics.

**Read:** [Stripe idempotent requests](https://docs.stripe.com/api/idempotent_requests)

---

<a id="q88"></a>
### Q88. How do you handle model provider outages?

`Senior` · `Representative`

**Answer.** Plan for them, because they happen. Short blips get handled by retries with backoff. Longer outages need a fallback: a second provider or a second model, behind a common interface, with a circuit breaker that switches after a threshold of errors and switches back after a health check. The catch is that a fallback model is a different agent. Prompts, tool calling behaviour and quality differ, so the fallback needs its own eval run and possibly its own prompt variant, and I would rather degrade gracefully than silently serve a worse agent. Degraded modes can be useful: turn off non-essential agentic features, queue background tasks to run later, or answer with a plain workflow. Long-running runs on durable execution just pause and resume when the provider returns. And I tell users when quality or features are reduced.

**Follow-ups**
- *How do you test failover?* Chaos testing in staging: inject errors from the primary provider and check the switch and the quality.
- *Cross-provider prompt caching?* It does not carry over. Expect higher cost and latency during failover.

**Read:** [Timeouts, retries and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)

---

<a id="q89"></a>
### Q89. How do you roll out a new model version to an agent in production?

`Senior` · `Representative`

**Answer.** Like any risky dependency upgrade. Pin model versions explicitly, never a floating alias, so nothing changes under me. Run the full eval suite on the new model, comparing success, pass^k, cost, latency and the failure types in transcripts, since a new model can fix some cases and break others. Adjust prompts if needed; a prompt tuned for one model is rarely optimal for the next. Then roll out gradually: shadow traffic where both run and I compare outputs, then a small percentage with online metrics and trace review, then wider, with a quick rollback. I watch for subtle changes like more tool calls per task, different refusal behaviour or a shift in output length, which may not show up as errors but change cost and user experience.

**Follow-ups**
- *The new model is better on average but worse on one segment. Ship?* Depends on the segment's value. Route that segment to the old model or fix it before shipping.
- *How long do you keep the old version available?* Until the provider retires it, and plan the migration early.

**Read:** [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)

---

<a id="q90"></a>
### Q90. How do you scale an agent service to thousands of concurrent runs?

`Staff` · `Representative`

**Answer.** Separate the request path from the work. An API accepts tasks and writes them to a queue; a pool of stateless workers runs agent steps; run state lives in a durable store, so any worker can pick up any run after a step. The bottlenecks are usually not CPU. They are model provider rate limits, measured in requests and tokens per minute, and the rate limits of downstream tools. So I add a token-aware rate limiter shared across workers, per-tenant quotas so one customer cannot starve the rest, priority lanes for interactive versus batch work, and backpressure that returns "queued" instead of failing. Sandboxes for code execution are the other heavy resource; pool and reuse them per run, with fresh ones per task. I size it from back-of-envelope numbers: runs per minute, steps per run, tokens per step, and compare with provider limits before anything else.

**Follow-ups**
- *Rough numbers?* 1,000 runs a minute at 10 steps and 20,000 input tokens per step is 200 million input tokens a minute. That is an estimate to show the scale, and why caching and shorter contexts matter.
- *Batch APIs?* Use them for non-interactive work. Cheaper, with slower completion.

**Read:** [Temporal: workflows](https://docs.temporal.io/workflows)

---

<a id="q91"></a>
### Q91. What guardrails would you put around an agent in production?

`Core` · `Representative`

**Answer.** Layers, because no single check is enough. OpenAI's practical guide makes the same point. On input: relevance and abuse classifiers, PII detection, and checks for obvious injection attempts. On tools: least-privilege credentials, allowlists of what each tool may touch, argument validation, rate limits, and risk ratings that put high-impact actions behind human approval. On output: schema validation, policy and safety checks, and checks that claims are grounded in tool results where that matters. Around the run: budgets, step limits, timeouts, and a kill switch. I put the strongest guardrails in deterministic code at the tool layer, because a prompt-level rule is a request and a code-level rule is a guarantee. Classifier-style guardrails can run in parallel with the main model call so they add little latency, with the action blocked if they trip.

**Follow-ups**
- *Guardrails add latency. How do you manage it?* Run them in parallel, use small fast models or rules, and gate only the risky actions.
- *How do you test guardrails?* Red-team task sets in the eval suite, with expected blocks and expected passes.

**Read:** [A practical guide to building agents](https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf) (OpenAI)

---

<a id="q92"></a>
### Q92. How do you debug an agent failure a user reported?

`Core` · `Representative`

**Answer.** Get the trace by run id; this is why you log them. Read it from the start and find the first step where things went wrong, because everything after that is consequence. Then classify the root cause. Bad input understanding. Wrong tool or wrong arguments. Tool returned an error or misleading data. Correct tool result the model misread. Context lost through compaction or truncation. A policy the model did not follow. Or an infrastructure fault. Then reproduce: replay the run with recorded tool results to see if the model makes the same choice, and vary one thing at a time. Fix at the right layer, which is usually the tool or the context, not a new line in the prompt. Then add the case to the eval set and check that the fix does not break other cases.

**Follow-ups**
- *You cannot reproduce it. Now what?* Run the same input many times to measure the failure rate. A 5% failure is still a bug.
- *Prompt patch or tool fix?* Prefer the tool fix. Prompt patches pile up and conflict.

**Read:** [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) (the section on reading transcripts)

---

<a id="q93"></a>
### Q93. What are the main ways agents fail in production?

`Senior` · `Representative`

**Answer.** They cluster into a handful of kinds. Premature success: the agent says it is done without verifying. Loops: repeating the same failing call. Tool misuse: wrong tool, made-up arguments, ignoring errors. Context failures: forgetting a constraint, losing track after compaction, getting distracted by irrelevant tool output. Policy violations: doing something allowed by the tools but forbidden by rules, like refunding over the limit. Over-asking or under-asking the user. Cost blowups from long contexts or runaway sub-agents. And security failures, mainly prompt injection through content the agent reads. Each has a matching control: verification steps, loop detection, better tool design and validation, state outside the context, code-enforced policy, eval-tuned clarification behaviour, budgets, and isolating untrusted content from powerful tools. Interviewers like this question because a list of failures shows real experience faster than a list of features.

**Follow-ups**
- *Which is hardest to catch?* Silent wrong answers that look plausible. You need outcome checks and sampling with human review.
- *Which do you prevent in code versus prompts?* Policy, budgets, loops and permissions in code; judgment calls in prompts.

**Read:** [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)

---

<sub>[Question index](README.md) · Next: [Safety and security](09-safety-and-security.md)</sub>
