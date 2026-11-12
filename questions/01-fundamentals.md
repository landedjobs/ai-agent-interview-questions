# Fundamentals: agents, workflows and the loop

<sub>[Question index](README.md) · [Repo home](../README.md) · Next: [Tool use and function calling](02-tool-use.md)</sub>

12 questions, Q1 to Q12. Every agent loop starts here, and a weak answer to Q1 colours the rest of the interview. The interviewer wants to hear that you know what the model controls, what your code controls, and why you would pick one over the other.

How to read each entry. The **answer** is what a senior candidate says in 60 to 90 seconds. The **follow-ups** are where the interviewer goes next, with the short version of a good reply. Difficulty is `Core` (every candidate), `Senior` or `Staff`. `Representative` means we wrote the question to match what agent loops ask; `Reported` means a public source shows it was asked, and the source is linked.

---

<a id="q1"></a>
### Q1. What is the difference between an agent and a workflow?

`Core` · `Representative`

**Answer.** The question is who owns the control flow. In a workflow, my code decides the sequence. I call the model at fixed points, maybe route on its output, but the path is a graph I wrote. In an agent, the model decides the next step at run time. It picks a tool, reads the result, and decides whether to call another tool or stop. Anthropic's "Building effective agents" draws the line the same way: workflows run LLMs and tools through predefined code paths, agents direct their own process and tool use. The practical consequence is predictability. A workflow is cheaper, faster and easier to test because I can enumerate its paths. An agent handles open-ended tasks where I cannot write the paths ahead of time, such as fixing an arbitrary bug in an unknown repo, and I pay for that in tokens, latency and variance. My default is the simplest thing that meets the bar. Most production "agents" I have seen are workflows with one or two agentic steps inside.

**Follow-ups**
- *Give me an example where you would switch a workflow to an agent.* When the number of branches explodes or depends on what the tools return, for example a support case that may need zero or six lookups.
- *Is a router an agent?* No. The model picks one branch once; your code still owns the loop.
- *What is the "augmented LLM"?* A single model call with retrieval, tools and memory attached. It is the building block for both workflows and agents.

**Read:** [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) (Anthropic)

---

<a id="q2"></a>
### Q2. Walk me through the agent loop.

`Core` · `Representative`

**Answer.** The loop is small. I send the model a system prompt, the conversation so far, and the tool schemas. The model returns either a final answer or one or more tool calls with arguments. If it returned tool calls, my code validates the arguments, runs the tools, and appends each result to the message history tied to its call id. Then I call the model again with the longer history. That repeats until the model answers without a tool call or a guard trips. The model is stateless, so the message list is the agent's working memory, and every turn re-sends it. That is why long runs get slow and expensive, and why prompt caching matters. The parts that make it production-grade are outside the model: a step limit, a token or dollar budget, a timeout, detection of repeated identical calls, approval gates for destructive tools, truncation of huge tool results, and a trace of every step. I can write this loop in about 60 lines; [code/agent_loop.py](../code/agent_loop.py) in this repo is one version.

**Follow-ups**
- *What ends the loop?* A turn with no tool calls, a max-steps or budget limit, a stuck detector, a human denial, or an explicit `finish` tool if you want the model to declare completion with a structured result.
- *Why re-send the whole history?* The model keeps no state between calls. Caching makes the repeated prefix cheap, not free.
- *Where do errors go?* Back into the history as tool results, so the model can correct itself. Only crash the loop on infrastructure failure.

**Read:** [ReAct paper](https://arxiv.org/abs/2210.03629) · [OpenAI function calling guide](https://platform.openai.com/docs/guides/function-calling)

---

<a id="q3"></a>
### Q3. Explain ReAct. Is it still how agents work?

`Core` · `Representative`

**Answer.** ReAct, from Yao et al. in 2022, interleaves reasoning traces and actions. The model writes a thought, picks an action, gets an observation, and repeats. The paper showed that mixing the two beat reasoning-only chain of thought on fact-checking and question answering, because the model could look things up instead of hallucinating, and beat acting-only baselines on ALFWorld and WebShop, because the thoughts helped it plan and recover. The original version parsed "Thought / Action / Observation" out of plain text. Today the same loop runs on native tool calling. The model emits structured tool calls, and reasoning models do their thinking in a separate reasoning channel rather than in the visible text. So the idea survived and the text format did not. When someone says "a ReAct agent" in 2026 they usually mean a single tool-calling loop without an explicit planner, which is still the right default for most tasks.

**Follow-ups**
- *What did ReAct get wrong or leave out?* No budget, no memory beyond the prompt, and no recovery from a bad early step. Those became separate techniques like reflection and planning.
- *Why did native tool calling replace text parsing?* Fewer format errors, typed arguments, parallel calls, and providers trained the models on that format.

**Read:** [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629)

---

<a id="q4"></a>
### Q4. When should you not build an agent?

`Core` · `Representative`

**Answer.** When the task has a small, known set of paths. If I can draw the flowchart, I should code the flowchart and call the model at the nodes that need language. I also avoid agents when latency must be low and predictable, like an autocomplete; when a wrong action is expensive and I have no verifier; and when the volume is high and the margin thin, because agents use several times more tokens than a single call. Anthropic's multi-agent research post puts agents at about 4 times the tokens of a chat and multi-agent systems at about 15 times. The honest test is an eval. I build the single-call or workflow version first, measure it on real tasks, and only add autonomy where the failures are of the "it needed one more lookup" kind. Autonomy is a cost I take on to fix a measured gap, not a starting point.

**Follow-ups**
- *Your PM wants "an agent" for invoice extraction. What do you say?* Extraction with a schema and a validator is a single call plus retries. I would ship that and add an agentic fallback only for the documents it fails on.
- *How do you show the cost difference?* Tokens per task and p95 latency on the same eval set for both designs.

**Read:** [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) (Anthropic)

---

<a id="q5"></a>
### Q5. Name the common workflow patterns and when each fits.

`Core` · `Representative`

**Answer.** Anthropic lists five, and they cover most of what I build. Prompt chaining splits a task into fixed steps, each call working on the previous output, with code checks between steps. I use it for outline-then-draft or extract-then-validate. Routing classifies the input and sends it to a specialised prompt or a cheaper model, which suits support triage. Parallelization comes in two forms: sectioning runs independent subtasks at once, and voting runs the same task several times and aggregates, which helps for things like flagging risky code. Orchestrator-workers has a model break the task into subtasks it decides at run time and hand them to workers, then merge; that is the bridge to agents. Evaluator-optimizer pairs a generator with a critic in a loop until the critic passes it, which works when you have clear criteria, like a translation style guide. The skill being tested is matching the pattern to the shape of the task instead of reaching for a framework.

**Follow-ups**
- *Which of these is closest to an agent?* Orchestrator-workers, because the model chooses the subtasks.
- *What is the risk with evaluator-optimizer?* The critic and generator share blind spots, and the loop can run long. Cap iterations and ground the critic in checks code can run.

**Read:** [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)

---

<a id="q6"></a>
### Q6. Why do errors compound in long agent runs, and what do you do about it?

`Senior` · `Representative`

**Answer.** If each step succeeds independently with probability p, a run of n steps succeeds with roughly p to the n. At 95% per step, 20 steps give you about 36%. Real steps are not independent, which can help or hurt, but the shape is right: long trajectories fail more, and an early mistake poisons everything after it because later steps build on it. I attack this four ways. Shorten the run by giving the agent better tools, so one call does what used to take five. Verify at checkpoints with something code can check, like tests passing or a record existing. Let the agent see errors as data so it can recover rather than plough on. And design for restart: save state at milestones so a failure costs one segment, not the whole run. In evals I look at where in the trajectory the first wrong step happens, because that tells me which tool or prompt to fix.

**Follow-ups**
- *Does a stronger model fix it?* It raises p, which helps a lot because of the exponent, but it does not remove the need for checkpoints on long tasks.
- *How do you find the first bad step?* Trajectory review on failed runs, ideally with a grader that labels each step.

**Read:** [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) (Anthropic)

---

<a id="q7"></a>
### Q7. What goes into an agent's system prompt?

`Core` · `Representative`

**Answer.** The role and the goal in plain terms. The tools and when to use each, though the tool descriptions do most of that work. Hard rules the agent must follow, like "never issue a refund over $500 without approval", stated once and specifically. How to handle uncertainty: when to ask the user, when to stop. The output contract for the final answer. And a few examples of good behaviour if the task is subtle, kept diverse so the model does not copy one. What I leave out matters as much. I do not stuff the prompt with every edge case; Anthropic's context engineering post calls this finding the right altitude, specific enough to guide behaviour but not a brittle list of if-then rules. I keep it stable across turns so the provider can cache it, and I put anything that changes per request, like the user's account data, after the stable part.

**Follow-ups**
- *Where do policies go, prompt or code?* Both. The prompt tells the model the rule; code enforces it at the tool layer, because prompts are suggestions.
- *How do you test a prompt change?* Run the eval set before and after, and read a sample of transcripts. Never ship a prompt change on vibes.

**Read:** [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) (Anthropic)

---

<a id="q8"></a>
### Q8. What is the difference between a model and a harness, and which matters more?

`Senior` · `Representative`

**Answer.** The model is the weights behind an API. The harness is everything around it: the loop, the tools, the system prompt, context management, the sandbox, permissions and retries. For a coding agent the harness decides what files the model can see, how it edits them, how test output comes back, and when old turns get compacted. Both matter, and the honest answer is that the harness is where the engineer can move the numbers. The same model can score very differently on SWE-bench depending on the scaffold. In "Building effective agents", Anthropic says that while building their SWE-bench agent they spent more time on tools than on the overall prompt. If I am interviewing for an agent role, the harness is my job: I cannot change the weights, but I can change what the model sees and what it can do.

**Follow-ups**
- *Give an example of a harness change that moved a metric.* A typical one is switching file edits from line-number patches to exact string replacement, because models count lines badly. Anthropic's SWE-bench write-up describes an edit tool built on string replacement.
- *When does the model dominate?* On tasks needing deep reasoning the harness cannot supply, like a hard algorithm. A better scaffold will not make a weak model plan well.

**Read:** [Raising the bar on SWE-bench Verified](https://www.anthropic.com/research/swe-bench-sonnet) (Anthropic) · [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) · [SWE-agent paper](https://arxiv.org/abs/2405.15793)

---

<a id="q9"></a>
### Q9. How does an agent decide to call a tool versus answer from its own knowledge?

`Core` · `Representative`

**Answer.** The model decides, based on its training and what the prompt and tool descriptions tell it. My job is to make the right choice obvious. I describe each tool with when to use it, not only what it does: "use this for any question about the user's orders; never guess order status." For facts that change or are private, I instruct the model that its memory is not a source. If a task must always hit a tool, I do not leave it to judgment: I force it with tool choice settings on the first turn, or I make it a workflow step. The failure in both directions is common. Under-calling gives confident stale answers; over-calling wastes latency on things the model knows. I measure both in evals by checking whether the expected tool was called, and by checking answers against ground truth.

**Follow-ups**
- *What does `tool_choice` do?* Lets you force a specific tool, require any tool, or forbid tools for a turn. It is the deterministic override.
- *How do you catch hallucinated facts that should have come from a tool?* Grade answers against the tool's ground truth, and flag answers with no supporting tool call.

**Read:** [Implement tool use](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/implement-tool-use) (Anthropic docs)

---

<a id="q10"></a>
### Q10. Single agent with many tools, or several specialised agents?

`Senior` · `Representative`

**Answer.** Start with one agent and push it as far as it will go. OpenAI's practical guide to building agents says the same: maximise a single agent first, then split when it fails. One agent is easier to trace, has one context, and avoids the coordination failures that multi-agent systems introduce. I split when one of two things is true. The tool set has grown so large or overlapping that the model picks wrong tools, even after I improve descriptions and add tool search. Or the prompt has grown so many conditional instructions that following one breaks another. Even then, I first try giving a single agent different prompts or tool subsets per stage, which is a workflow, before I add agents talking to agents. True multi-agent pays off mostly for parallel, read-heavy work like research.

**Follow-ups**
- *What number of tools is "too many"?* There is no fixed number. I watch tool-selection accuracy on the eval as I add tools. Overlap between tools hurts more than count.
- *What is the first multi-agent shape you would try?* A manager that calls specialists as tools and keeps the conversation, so there is still one owner.

**Read:** [A practical guide to building agents](https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf) (OpenAI, PDF)

---

<a id="q11"></a>
### Q11. What do you look for when choosing an agent framework, or would you skip one?

`Senior` · `Representative`

**Answer.** I am happy to skip one for a first version. The core loop is small, and writing it myself means I know exactly what goes into the context, which is the thing I most need to control. Anthropic's guidance is the same: start with the API directly, and if you use a framework, understand the code underneath. I adopt a framework when it gives me something expensive to build: durable state and resumption, human-in-the-loop interrupts, tracing that plugs into my observability stack, or a graph model for complex workflows. LangGraph, the OpenAI Agents SDK, the Claude Agent SDK and smolagents all cover different subsets. The red flags are frameworks that hide the prompt, make it hard to see the exact messages sent, or force their own retry and memory logic that I cannot override. Whatever I pick, I keep my tools and evals framework-independent so I can switch.

**Follow-ups**
- *What would make you rip a framework out?* Debugging time. If I cannot answer "what exactly did the model see on step 7" in a minute, the abstraction costs more than it saves.
- *What do SDKs give you that matters?* Tracing, handoffs, guardrails and session state, mostly.

**Read:** [OpenAI Agents SDK docs](https://openai.github.io/openai-agents-python/) · [smolagents](https://huggingface.co/blog/smolagents) (Hugging Face)

---

<a id="q12"></a>
### Q12. What are code agents, and when do they beat JSON tool calling?

`Senior` · `Representative`

**Answer.** A code agent writes and runs code as its action, instead of emitting one JSON tool call per step. The CodeAct paper showed that code actions beat JSON or text actions on several benchmarks, with up to about 20% higher success, because code can loop, branch, store intermediate values in variables and compose several tools in one action. You see the same idea in Anthropic's "code execution with MCP" post, where presenting tools as a code API cut one example from 150,000 tokens to 2,000, because intermediate data stayed in the sandbox instead of passing through the context. Code agents win on data-heavy, multi-step tasks: filter 10,000 rows, join two sources, then summarise. They cost you a sandbox, a bigger attack surface and harder-to-read traces. For a few simple calls, JSON tool calling is easier to validate and to approve step by step.

**Follow-ups**
- *What do you need before letting a model run code?* An isolated sandbox with no secrets, network allowlists, CPU and time limits, and a fresh environment per task.
- *How do you approve actions if the model writes code?* Approve at the tool-API boundary the code calls, not at the code level, because reading generated code is not a reliable review.

**Read:** [Executable Code Actions Elicit Better LLM Agents](https://arxiv.org/abs/2402.01030) · [Code execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp) (Anthropic)

---

<sub>[Question index](README.md) · Next: [Tool use and function calling](02-tool-use.md)</sub>
