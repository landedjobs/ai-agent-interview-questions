# Tool use and function calling

<sub>[Question index](README.md) · [Repo home](../README.md) · Previous: [Fundamentals](01-fundamentals.md) · Next: [Planning and reasoning](03-planning-and-reasoning.md)</sub>

13 questions, Q13 to Q25. The tool layer is the model's real interface to the world, and it is where most agent bugs live. Interviewers use these questions to separate people who have shipped tools from people who have wrapped an API and hoped.

Difficulty is `Core`, `Senior` or `Staff`. `Representative` questions are written by us to match real loops; `Reported` questions link a public source.

---

<a id="q13"></a>
### Q13. How does function calling actually work under the hood?

`Core` · `Representative`

**Answer.** I send the model a list of tools, each with a name, a description and a JSON Schema for its parameters. The provider renders those into the prompt in a format the model was trained on. When the model decides to use a tool, it emits a structured block with the tool name, a call id and arguments as JSON. Many providers can constrain decoding so the arguments match the schema. The model does not run anything. My code receives the call, validates it, executes the function, and sends the result back as a tool-result message linked to the call id. Then the model continues. Two things follow from this. Tool definitions cost input tokens on every turn, so 80 verbose tools are a real bill and a real distraction. And the tool result is untrusted text that lands in the context, which is the root of indirect prompt injection.

**Follow-ups**
- *What is strict mode or structured outputs for tools?* Constrained decoding so arguments always parse and match the schema. It removes format errors, not wrong values.
- *Who executes the tool in a hosted tool like web search?* The provider. You get the result without running it, and you give up control over what it fetched.

**Read:** [OpenAI function calling guide](https://platform.openai.com/docs/guides/function-calling) · [Anthropic tool use docs](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/implement-tool-use)

---

<a id="q14"></a>
### Q14. How do you design a good tool schema?

`Core` · `Representative`

**Answer.** I write it for a smart new hire who has never seen our system. The name says the action and the resource, namespaced if there are several services, like `crm_search_contacts`. The description says what it does, when to use it, when not to, and what it returns. Parameter names are unambiguous, so `user_id` instead of `user`. I use enums wherever the value set is closed, required fields only where truly required, and formats with examples, such as "ISO 8601 date, e.g. 2026-11-12". I make it hard to call wrongly: absolute paths instead of relative ones, ids the model got from a previous tool instead of free text. Anthropic calls this poka-yoke design. Then I test it. I run the agent on real tasks, read the transcripts for wrong calls, and change the description or schema. Tools get the same eval-driven iteration as prompts.

**Follow-ups**
- *Free text or enum for a "priority" field?* Enum. Free text invites "urgent-ish".
- *How long should a description be?* As long as it needs to remove ambiguity. Three or four sentences is normal for a tool with judgment involved.

**Read:** [Writing effective tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents) (Anthropic)

---

<a id="q15"></a>
### Q15. Should you expose every API endpoint as a tool?

`Core` · `Representative`

**Answer.** No. An API built for programs is the wrong shape for a model. Endpoints are fine-grained and assume the caller can hold state cheaply, while every agent call costs a model turn and context. I design tools around tasks. Anthropic's tool-writing post gives good examples: one `schedule_event` tool instead of `list_users`, `list_events` and `create_event`; a `search_logs` tool that returns relevant lines with context instead of `read_logs`; one `get_customer_context` instead of three lookups. Fewer, task-shaped tools mean shorter trajectories, fewer chances to compound errors, and less schema in the context. The exception is when the agent genuinely needs the flexibility, like a coding agent that should have a shell. Then I give it one general tool and good guidance instead of 40 narrow ones.

**Follow-ups**
- *Doesn't consolidation hide useful control?* Sometimes. Keep a lower-level escape hatch for rare cases and watch whether the agent needs it.
- *What does an auto-generated OpenAPI-to-tools wrapper get wrong?* Too many tools, machine-oriented descriptions, and huge raw responses.

**Read:** [Writing effective tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents)

---

<a id="q16"></a>
### Q16. What should a tool return?

`Core` · `Representative`

**Answer.** The smallest thing that lets the model take its next step, in a form it can read. That means human-meaningful fields over internal ones: names and titles rather than bare UUIDs, which Anthropic found reduced hallucinated ids. It means pagination, filtering and truncation with sensible defaults, and a note when results are truncated telling the model how to narrow the query. Claude Code caps tool responses at 25,000 tokens by default, which is a useful reference point. A `response_format` parameter that offers concise or detailed output lets the agent choose; in Anthropic's Slack example the concise version used about a third of the tokens. I also return the ids the model will need for follow-up calls, so it never has to guess them. And I keep raw blobs out of the context: if a tool produces a 5 MB CSV, it writes the file and returns the path plus a summary.

**Follow-ups**
- *JSON or plain text?* Whichever the model handles better on your eval. Structured content is easier for code to check; short text is often easier for the model to read.
- *Why does output size matter beyond cost?* Long contexts degrade attention. Every irrelevant token makes the next decision worse.

**Read:** [Writing effective tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents)

---

<a id="q17"></a>
### Q17. A tool call fails. What should the agent see?

`Core` · `Representative`

**Answer.** A structured, actionable error as the tool result, not a crash and not a stack trace. It should say what kind of failure it was, whether retrying makes sense, and how to fix the call. "Invalid date '12/11/26'. Use ISO 8601, for example 2026-11-12" lets the model self-correct on the next turn. "Error 400" does not. I split errors into three groups. Validation errors go back to the model so it can fix the arguments; the MCP spec changed in 2025 to say input validation errors should be tool execution errors for exactly this reason. Transient errors like timeouts and 503s get retried by my code with backoff before the model ever sees them, and only surface if retries run out. Permanent errors like permission denied go back to the model with a clear message so it can try another route or tell the user. Infrastructure failures in my own harness crash the run and alert.

**Follow-ups**
- *Should the model retry transient errors itself?* Usually no. Code retries are cheaper and deterministic. The model should hear about it only when it needs to change plan.
- *What if the error message contains attacker text?* It is still untrusted input. Treat tool errors like any other tool output.

**Read:** [MCP 2025-11-25 changelog](https://modelcontextprotocol.io/specification/2025-11-25/changelog) · [Writing effective tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents)

---

<a id="q18"></a>
### Q18. The agent keeps hallucinating tool arguments. How do you debug it?

`Senior` · `Representative`

**Answer.** First I find out which arguments and when, by reading failed transcripts. The causes fall into a few buckets. The model never got the value: it is asked for an `account_id` but no earlier tool returned one, so it invents a plausible one. Fix by adding a lookup tool or returning the id from an earlier call. The schema is ambiguous: a parameter called `id` that could mean three things. Fix the name and description. The format is underspecified: dates, currencies, units. Add formats, enums and examples, and turn on strict schema decoding. Or the context is too long and the value sits 80,000 tokens back. Fix with summaries or by passing state explicitly. Then I make the server reject bad values with a clear error so the model can recover. I add the failing cases to the eval so the fix stays fixed.

**Follow-ups**
- *Would fine-tuning help?* Rarely the first move. Schema and tool fixes are cheaper and transfer across models.
- *How do you validate that an id exists?* Server-side lookup that returns "not found, here are close matches" instead of acting on a guess.

**Read:** [Berkeley Function Calling Leaderboard](https://gorilla.cs.berkeley.edu/leaderboard.html)

---

<a id="q19"></a>
### Q19. How do parallel tool calls work, and when are they safe?

`Senior` · `Representative`

**Answer.** Modern models can return several tool calls in one turn. My harness runs them concurrently and returns all the results, each tied to its call id, before the next model call. That cuts latency for independent reads, such as fetching weather for three cities or searching three sources. It is safe when the calls are independent and side-effect free. It gets dangerous with writes, because two calls may race on the same resource, and with calls where one's output should shape the other's input. My rules: run read-only tools in parallel, serialise writes or anything marked destructive, and keep ordering in the results deterministic so traces are readable. Some providers let you turn parallel calls off per request, which I do for workflows that must be strictly sequential. LLMCompiler pushed the idea further by planning a dependency graph of calls and running independent ones in parallel.

**Follow-ups**
- *One of three parallel calls fails. What happens?* Return two results and one error. Do not fail the whole turn.
- *How do you mark tools as safe to parallelise?* Metadata on the tool, like MCP's read-only hint, enforced in your own code, not trusted from a third-party server.

**Read:** [An LLM Compiler for Parallel Function Calling](https://arxiv.org/abs/2312.04511)

---

<a id="q20"></a>
### Q20. You have 300 tools. What do you do?

`Senior` · `Representative`

**Answer.** I do not put 300 schemas in the context. It costs tokens on every turn and tool selection degrades as similar tools pile up. The options, roughly in order. Consolidate: many of the 300 are probably endpoint wrappers that collapse into task-level tools. Scope by stage or role: a workflow step or a sub-agent only sees the tools it needs. Add tool search: index the tool descriptions, give the agent a search tool that returns the top matches, and load only those schemas. Or move to code execution, where tools are files or modules in a sandbox and the agent reads only what it needs, which Anthropic describes in its code execution with MCP post. Whichever I pick, I measure tool-selection accuracy on an eval set, because the failure is silent: the agent just picks the second-best tool.

**Follow-ups**
- *Downside of tool search?* An extra step per task and a new failure mode when retrieval misses the right tool. Keep the top few tools always loaded.
- *Does tool order in the list matter?* It can, and a stable order also keeps the prompt cache warm. The 2026-07-28 MCP spec asks servers to list tools in a deterministic order for this reason.

**Read:** [Code execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp) · [MCP 2026-07-28 changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog)

---

<a id="q21"></a>
### Q21. What is the difference between function calling and structured outputs?

`Core` · `Representative`

**Answer.** Both use JSON Schema, but they answer different questions. Function calling lets the model choose whether to act and which action to take; the schema describes a tool's inputs, and my code runs something with them. Structured outputs constrain the model's final answer to a schema, with no action implied, which is what I want for extraction or for an agent's final report. In practice they blur: some teams model the final answer as a `submit_result` tool so the agent ends with a typed object, and that is a fine pattern because it makes "done" explicit and checkable. The interview trap is thinking that schema-valid means correct. Constrained decoding guarantees the shape. It says nothing about whether the values are true, so I still validate semantics in code.

**Follow-ups**
- *When would you use a `finish` tool?* When you need a structured final result and want the loop to end only on an explicit signal.
- *Can constrained decoding hurt quality?* Very tight schemas can. Keep schemas simple and let the model write free-text reasoning fields if it needs them.

**Read:** [OpenAI function calling guide](https://platform.openai.com/docs/guides/function-calling)

---

<a id="q22"></a>
### Q22. How do you version tools without breaking running agents?

`Senior` · `Representative`

**Answer.** Treat tool schemas like a public API, because the model's learned behaviour and your prompts depend on them. Additive changes are safe: a new optional parameter with a default, a new field in the response. Renames, removed parameters and changed meanings are breaking, and I ship those as a new tool name, such as `search_v2`, and keep the old one until traffic stops. Long-running agents are the hard case: a run that started yesterday may resume today against a new tool set, and its history contains calls to the old schema. So I pin the tool set version in the run's state and resume with the same version, or migrate the history explicitly. Every schema change runs through the eval suite first. A description edit can shift tool selection as much as a code change.

**Follow-ups**
- *Why is a description change risky?* It changes model behaviour without a code diff anyone reviews. Version and eval it like code.
- *How does MCP signal tool changes?* A `listChanged` capability with notifications, and in the 2026-07-28 spec, cache hints on list results.

**Read:** [MCP tools spec (2026-07-28)](https://modelcontextprotocol.io/specification/2026-07-28/server/tools)

---

<a id="q23"></a>
### Q23. What is the "think" tool and is it still useful with reasoning models?

`Senior` · `Representative`

**Answer.** Anthropic's think tool, from March 2025, is a tool with one string parameter that does nothing except give the model a place to reason between tool calls. On tau-bench airline, the think tool with an optimised prompt raised pass^1 from 0.370 to 0.570, a 54% relative gain; on retail it helped a little even without prompting. It helped most on policy-heavy, sequential tasks where the model had to check tool results against rules before acting. With reasoning models that think between tool calls natively, the case is weaker, and Anthropic's own note on the post now recommends extended thinking over a dedicated think tool in most cases. The lesson I would draw in an interview is the general one: giving the model space to check tool output against policy before an irreversible step measurably helps.

**Follow-ups**
- *When does it not help?* Single calls, parallel independent calls, and simple instruction following.
- *How would you check if it helps your agent?* Run the eval with and without it, look at pass^k on policy-heavy tasks.

**Read:** [The "think" tool](https://www.anthropic.com/engineering/claude-think-tool) (Anthropic)

---

<a id="q24"></a>
### Q24. How do you make a tool safe to call more than once?

`Senior` · `Representative`

**Answer.** Make the write idempotent. The agent loop retries, the model sometimes repeats a call, and network timeouts leave you not knowing whether the first call landed. For a read this is harmless. For "charge the card" or "send the email" it is a real incident. The fix is an idempotency key per logical operation. My harness generates it, not the model, from the run id and step id, and passes it with every attempt. The server stores the key with the first result and returns that result on repeats. Stripe's API works this way. Where I cannot change the server, I add a check-then-act guard in the tool: look up whether the refund for this order already exists before issuing one. I also design tool semantics to be naturally idempotent where possible, like "set status to shipped" instead of "advance status".

**Follow-ups**
- *Why not let the model pass the key?* It will reuse or invent keys inconsistently. Keys are infrastructure.
- *How long do you keep keys?* Long enough to cover your retry window and any resumes. Stripe says it may prune keys once they are at least 24 hours old.

**Read:** [Stripe idempotent requests](https://docs.stripe.com/api/idempotent_requests) · [Idempotent receiver pattern](https://martinfowler.com/articles/patterns-of-distributed-systems/idempotent-receiver.html)

---

<a id="q25"></a>
### Q25. How would you evaluate a new tool before giving it to the agent?

`Senior` · `Representative`

**Answer.** I build a small task set where the tool should be used, plus some where it should not, and run the agent many times on each. I measure whether it calls the tool when it should, whether the arguments are valid and correct, how many calls it takes to finish, total tokens, and task success. Then I read transcripts, because the numbers tell me something is off and the transcripts tell me why: the model misread the description, the output was too long, the error message was useless. Anthropic's tool-writing post goes further and has the model itself review transcripts and suggest description changes, which works well as a first pass. I compare against the baseline without the tool to make sure it helps on net, since a new tool can confuse selection for the existing ones.

**Follow-ups**
- *What metric tells you a tool is badly designed?* High call counts per task, many validation errors, or the agent calling it and then ignoring the result.
- *How many tasks do you need?* Start with 20 to 50 drawn from real usage; that is the range Anthropic suggests for a first agent eval.

**Read:** [Writing effective tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents) · [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)

---

<sub>[Question index](README.md) · Next: [Planning and reasoning](03-planning-and-reasoning.md)</sub>
