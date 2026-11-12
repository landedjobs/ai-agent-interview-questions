# Planning and reasoning

<sub>[Question index](README.md) · [Repo home](../README.md) · Previous: [Tool use](02-tool-use.md) · Next: [Memory and context](04-memory-and-context.md)</sub>

10 questions, Q26 to Q35. Interviewers ask about planning to see if you know when explicit structure helps a model and when it just adds steps. Since reasoning models arrived, the honest answer to many of these is "less scaffolding than in 2023", and saying so with evidence scores well.

Difficulty is `Core`, `Senior` or `Staff`. `Representative` questions are written by us to match real loops; `Reported` questions link a public source.

---

<a id="q26"></a>
### Q26. What is plan-and-execute, and how does it differ from a ReAct loop?

`Core` · `Representative`

**Answer.** In plan-and-execute, one model call writes a plan up front, a list of steps, and an executor works through them, often with a cheaper model or plain code per step, then a replanner adjusts the remaining steps when results come in. A ReAct loop decides one step at a time with no explicit plan. Plan-and-execute helps when the task has a clear structure that is visible at the start, when you want a human to approve the plan before anything runs, and when you want to run independent steps in parallel. It costs you flexibility: a plan written before seeing any data is often wrong by step three, so without replanning it fails worse than ReAct. The Plan-and-Solve paper showed a related gain from simply asking the model to plan before solving. I treat the plan as a hypothesis the agent revises, never as a contract.

**Follow-ups**
- *When would you show the plan to the user?* Before any costly or irreversible work, like a data migration or a multi-hour research task.
- *Where do you store the plan?* In explicit state, a to-do list the agent updates, not only in the chat history where it gets compacted away.

**Read:** [Plan-and-Solve Prompting](https://arxiv.org/abs/2305.04091)

---

<a id="q27"></a>
### Q27. What is reflection, and does self-critique actually work?

`Senior` · `Representative`

**Answer.** Reflection is the agent reviewing its own output or trajectory and using the critique on the next attempt. Reflexion, from Shinn et al. in 2023, stored verbal reflections on failed attempts in memory and reported 91% pass@1 on HumanEval. The catch is the signal. Reflection works when the critique is grounded in something external: a failing test, a compiler error, a tool returning "not found", a checker that can say what is wrong. Pure self-critique with no new information is weaker, because the same model that made the mistake often cannot see it, and it can talk itself out of a correct answer. So in production I attach reflection to verifiers: run the tests, feed back the failures, try again, with a cap on attempts. For open-ended outputs I use a separate evaluator prompt with a rubric, and I check on my eval that the loop raises scores rather than just adding cost.

**Follow-ups**
- *How many reflection rounds?* Usually two or three. Gains flatten fast and cost grows linearly.
- *What is the evaluator-optimizer pattern?* The same idea as a workflow: a generator and an evaluator in a loop until the evaluator passes.

**Read:** [Reflexion](https://arxiv.org/abs/2303.11366)

---

<a id="q28"></a>
### Q28. How do reasoning models change agent design?

`Senior` · `Representative`

**Answer.** They move planning inside the model. A reasoning model spends tokens thinking before it answers, and models now do this between tool calls too, so a lot of the scaffolding we wrote in 2023, like explicit planner prompts and chain-of-thought instructions, adds little or gets in the way. What changes in my design: I write goals and constraints instead of step-by-step procedures. I budget for thinking tokens, which can dominate cost and latency, and I set the reasoning effort per task instead of maxing it everywhere. I keep the reasoning out of my parsing logic, since some providers hide or summarise it. And I route: a fast non-reasoning model for simple steps like classification or extraction, a reasoning model for the hard decisions. DeepSeek-R1 showed reasoning ability can come from reinforcement learning, which is why so many providers now ship it. Evals still decide: some tasks score the same with less thinking at a fraction of the cost.

**Follow-ups**
- *Do you still need chain-of-thought prompting?* Not with reasoning models. It can still help a small non-reasoning model.
- *How do you control cost?* Effort or budget settings per call, routing, and caching the stable prompt prefix.

**Read:** [DeepSeek-R1](https://arxiv.org/abs/2501.12948) · [Chain-of-thought prompting](https://arxiv.org/abs/2201.11903)

---

<a id="q29"></a>
### Q29. Tree of Thoughts, self-consistency, best-of-n: when do search methods pay off?

`Senior` · `Representative`

**Answer.** They trade compute for accuracy by exploring several candidate paths and picking the best. Self-consistency samples several answers and takes the majority. Best-of-n samples n candidates and picks one with a scorer. Tree of Thoughts, from Yao et al. in 2023, branches at intermediate steps and searches with a value estimate; it did well on puzzles like Game of 24. They pay off when two conditions hold: you have a reliable way to score candidates, like tests or a checker, and the cost of being wrong is much bigger than n times the cost of a call. Code generation with unit tests is the classic case. They pay off poorly when the scorer is another model with the same blind spots, or when actions have side effects, since you cannot explore three branches of "send the email". For agents, search usually belongs in pure reasoning or in a sandbox, not in the live environment.

**Follow-ups**
- *How do you pick n?* Plot accuracy against n on your eval and stop where the curve flattens. It often flattens early.
- *Relation to pass@k?* Best-of-n with a perfect verifier gets you pass@n.

**Read:** [Tree of Thoughts](https://arxiv.org/abs/2305.10601)

---

<a id="q30"></a>
### Q30. How do you stop an agent from looping forever?

`Core` · `Representative`

**Answer.** Hard limits first, because they cannot fail: max steps, max tokens or dollars per run, and a wall-clock timeout. Then detection. I fingerprint each tool call by name and arguments and stop or intervene when the same call repeats two or three times with the same result. I watch for no progress, like no new information or no state change in several steps. When a guard trips, I do something useful: inject a message telling the model it is repeating itself and must try another approach or stop, escalate to a human, or end with a partial result and an honest status. Then I fix the cause, which is usually a tool that returns an unhelpful error so the model keeps retrying, or an ambiguous goal so the model never knows it is done. A clear completion criterion in the prompt prevents more loops than any detector.

**Follow-ups**
- *What does the user see when you hit the limit?* What was done, what was not, and what the agent was stuck on. Never a silent failure.
- *How do you set the step limit?* From the distribution of successful runs on your eval: a bit above p99.

**Read:** [code/agent_loop.py](../code/agent_loop.py) in this repo

---

<a id="q31"></a>
### Q31. How should an agent decide it is done?

`Core` · `Representative`

**Answer.** Give it a checkable definition of done. "Fix the bug" is vague; "the failing test passes and no other test breaks" is checkable, and the agent can run the tests to confirm. In the prompt I state the completion criteria and the expected final output. Where possible I give the agent a verification tool and tell it to use it before finishing. For structured results I use a `submit` tool with a schema, so the run ends on an explicit signal with typed output, and my code checks the result before accepting it. The common failures are premature completion, where the agent claims success without checking, and never-ending polish. Anthropic's write-up on long-running agents found agents declaring a feature done without testing it end to end, and fixed it by having them test as a user would.

**Follow-ups**
- *What if the task has no objective check?* Use a rubric-based evaluator before returning, and ask the user to confirm on high-stakes outputs.
- *Should the agent ever stop without finishing?* Yes. Stopping with a clear question beats guessing on an ambiguous request.

**Read:** [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) (Anthropic)

---

<a id="q32"></a>
### Q32. When should an agent ask the user a clarifying question?

`Senior` · `Representative`

**Answer.** When the answer changes what it does and it cannot find the answer itself. I would not ask about something the agent can look up, like the user's timezone in their profile. I would ask before an irreversible or costly action based on an ambiguous request: "cancel my meeting" when there are two. The design question is the threshold, and it depends on the product. A chat assistant can ask freely. A background agent that runs for an hour should ask everything up front, then work, and batch any new questions instead of blocking on each one. I make asking a tool, like `ask_user`, so it shows up in traces and evals. Then I measure both failure types: guesses that were wrong, and questions that were unnecessary, which users find just as annoying.

**Follow-ups**
- *How does MCP handle this?* Elicitation lets a server request structured input from the user through the client.
- *How do you eval clarifying behaviour?* Include ambiguous tasks in the set and grade whether the agent asked, and whether it asked the right thing.

**Read:** [MCP elicitation (2026-07-28)](https://modelcontextprotocol.io/specification/2026-07-28/client/elicitation)

---

<a id="q33"></a>
### Q33. How do you handle long-horizon tasks that run for hours?

`Staff` · `Representative`

**Answer.** Assume the context will not hold the whole task and the process will die at least once. Anthropic's post on long-running harnesses describes a design I agree with. An initializer step sets up the environment and writes a feature list or plan as a file. Each later session reads a progress file and the git log, picks one item, does it, tests it, commits, and updates the progress notes. So state lives outside the model, in files and version control, and any session can resume from it. Around that I add durable execution for the orchestration so a crash resumes from the last completed step, checkpoints before risky actions, budgets per item rather than per run, and periodic human checkpoints on long jobs. The anti-pattern is one huge conversation that relies on compaction to remember everything; it drifts and forgets constraints.

**Follow-ups**
- *Why one item per session?* Smaller units fail cheaply, and each ends in a verified, committed state.
- *How do you detect drift from the original goal?* Re-read the goal and plan from files at each step; evaluate intermediate outputs against the original spec.

**Read:** [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)

---

<a id="q34"></a>
### Q34. Should the agent's plan be in the prompt, in state, or in code?

`Senior` · `Representative`

**Answer.** It depends on who should be able to change it. If the plan is fixed for every run, it belongs in code as a workflow, because then it is tested and cheap. If the model writes the plan, I keep it in explicit state, a structured to-do list or a file that the agent reads and updates through tools, not only in the message history. That gives three wins: it survives compaction and restarts, a human can inspect or edit it, and the UI can show progress. Coding agents now commonly have a to-do tool for exactly this. The prompt holds only the instruction to plan and to keep the list current. A plan that lives only in an early assistant message gets lost as the context grows or gets summarised.

**Follow-ups**
- *How much detail in the plan?* Enough to track progress and spot drift. Five to fifteen items, not fifty.
- *Who can edit it?* The agent and the user. Treat user edits as authoritative.

**Read:** [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)

---

<a id="q35"></a>
### Q35. How do you route between models in one agent?

`Senior` · `Representative`

**Answer.** By step type, decided on an eval, not on intuition. Simple steps, like classifying intent, extracting fields or summarising a tool result, go to a small fast model. Hard decisions, like planning, debugging or judging policy compliance, go to the strongest model with reasoning on. Multi-agent setups often do this structurally: Anthropic's research system used Claude Opus 4 as the lead and Claude Sonnet 4 as sub-agents. I build routing as a table I can change, measure the cost and quality of each step on its own, and keep a fallback: if the small model's output fails validation, escalate to the larger one. The risk is hidden quality loss on a minority of inputs, so I watch the per-route failure rate in production, not only the average.

**Follow-ups**
- *Learned router or rules?* Rules first. A learned router needs labelled data and its own evals.
- *What about provider fallback?* A different provider is a different model. It needs its own eval run before it serves traffic.

**Read:** [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)

---

<sub>[Question index](README.md) · Next: [Memory and context](04-memory-and-context.md)</sub>
