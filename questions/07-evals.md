# Evals for agents

<sub>[Question index](README.md) · [Repo home](../README.md) · Previous: [Multi-agent systems](06-multi-agent.md) · Next: [Reliability and production](08-reliability-and-production.md)</sub>

12 questions, Q70 to Q81. If you only prepare one section deeply, prepare this one. "How do you know it works?" comes up in almost every agent interview, and a concrete eval plan is the clearest signal that you have shipped one.

Difficulty is `Core`, `Senior` or `Staff`. `Representative` questions are written by us to match real loops; `Reported` questions link a public source.

---

<a id="q70"></a>
### Q70. How do you evaluate an agent?

`Core` · `Representative`

**Answer.** Like any eval, with tasks, graders and repeated trials, plus a few agent-specific parts. I build a task set from real usage and real failures, each task with clear inputs, an environment to run in, and success criteria. Anthropic's eval guide suggests 20 to 50 tasks drawn from real failures is a strong start, and I agree that waiting for hundreds is a mistake. For each task I run several trials in a clean, isolated environment, because agents are non-deterministic. I grade the outcome first: the final state of the environment, like whether the booking exists in the database, not whether the agent said it booked it. Then I add trajectory checks where they matter, like whether it asked for approval before refunding. I report success rate, pass^k for consistency, cost and latency per task, and I read transcripts every time, because the numbers say something broke and transcripts say what.

**Follow-ups**
- *Code graders or model graders?* Code where the outcome is checkable, model graders with a rubric for quality, humans to calibrate the model graders.
- *Offline or online?* Both. Offline gates releases; online catches what your task set missed.

**Read:** [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) (Anthropic)

---

<a id="q71"></a>
### Q71. Trajectory evaluation versus outcome evaluation: what is the difference and when do you use each?

`Senior` · `Representative`

**Answer.** Outcome evaluation checks the end state: tests pass, the record exists, the answer matches. Trajectory evaluation checks the path: which tools were called, in what order, with what arguments, and whether rules were followed along the way. I lead with outcomes, because agents often find valid paths I did not anticipate, and grading against one fixed sequence penalises them for it. Anthropic's guide says to grade outcomes rather than rigid step sequences, for that reason. Trajectory checks earn their place in three cases. Safety and policy, where the path itself matters: it must ask before refunding, must not read files outside the project. Efficiency, where I want to catch 40 tool calls for a 5-call task. And diagnosis, where finding the first wrong step tells me what to fix. A good suite has both, with the outcome as the gate and trajectory checks as constraints and diagnostics.

**Follow-ups**
- *How do you grade a trajectory without a fixed reference?* Assertions over the trace, like "no write tool called before approval", or a model grader with a rubric.
- *What is partial credit for?* Long tasks where all-or-nothing scoring hides progress.

**Read:** [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)

---

<a id="q72"></a>
### Q72. Explain pass@k versus pass^k. Which one matters for a customer-facing agent?

`Core` · `Representative`

**Answer.** pass@k is the probability that at least one of k attempts succeeds. It comes from code generation, where the Codex paper defined an unbiased estimator for it, and it fits cases where you can try several times and verify, like generating candidate patches and running tests. pass^k, introduced with tau-bench, is the probability that all k attempts succeed. It measures consistency. For a customer-facing agent pass^k is the one that matters, because every user gets one attempt, and the same request arriving a thousand times must succeed a thousand times. The two diverge fast. With 75% per-trial success, pass^3 is about 42%, the example in Anthropic's guide, while pass@3 is over 98%. tau-bench found GPT-4o under 50% pass^1 on its tasks and under 25% pass^8 in the retail domain. That gap between "can do it" and "does it every time" is the reliability problem in one number.

**Follow-ups**
- *How do you estimate pass^k from n trials with c successes?* C(c, k) divided by C(n, k), the analogue of the pass@k estimator.
- *How do you raise pass^k?* Reduce variance: better tools, clearer policies, verification steps, lower temperature where it helps.

**Read:** [tau-bench paper](https://arxiv.org/abs/2406.12045) · [Evaluating LLMs trained on code (pass@k)](https://arxiv.org/abs/2107.03374)

---

<a id="q73"></a>
### Q73. What is tau-bench and what does it teach about agent evaluation?

`Senior` · `Representative`

**Answer.** tau-bench, from Sierra in 2024, tests agents in customer-service domains, retail and airline, where the agent has domain API tools and a policy document, and talks to a simulated user played by a language model with a hidden goal. Success is judged by comparing the final database state to the annotated goal state, so the agent must both satisfy the user and follow policy. It teaches three things. Evaluate in conversation, because real tasks reveal information over several turns. Grade the outcome in the environment, not the transcript text. And measure consistency, which is why it introduced pass^k. Its follow-up, tau2-bench, added a telecom domain with dual control, where the user also has tools and must act in their own environment, which tests whether the agent can guide a user through troubleshooting.

**Follow-ups**
- *Weakness of an LLM-simulated user?* It can be unrealistic, inconsistent or too cooperative. Validate the simulator against real transcripts.
- *How would you build a tau-bench for your product?* Real policies, a sandbox copy of your APIs, user goals mined from real tickets, and database-state graders.

**Read:** [tau-bench paper](https://arxiv.org/abs/2406.12045) · [tau2-bench paper](https://arxiv.org/abs/2506.07982) · [Sierra: benchmarking AI agents](https://sierra.ai/blog/benchmarking-ai-agents)

---

<a id="q74"></a>
### Q74. What is SWE-bench, and what are its limits?

`Core` · `Representative`

**Answer.** SWE-bench, from Jimenez et al. in 2023, gives an agent a real GitHub issue and the repository at that commit, and asks for a patch. The patch is graded by running the tests that the real fix made pass, plus tests that must keep passing. The original set has 2,294 tasks from 12 popular Python repositories. SWE-bench Verified is a 500-task subset that human engineers screened for clear issue descriptions and fair tests, and it became the main reported number for coding agents. Its limits are worth knowing. It is Python-only and skewed to a few repos, Django above all. Tasks and fixes are public, so contamination is a real concern for models trained after the fact. Tests check the specific behaviour, not code quality. And scores depend heavily on the scaffold, so a leaderboard number measures a model plus harness, not a model.

**Follow-ups**
- *Why did SWE-bench Verified exist?* Many original tasks had underspecified issues or tests that rejected valid fixes.
- *What would you add for your own coding agent?* Tasks from your own repos and languages, held out from any training, with review of code quality.

**Read:** [SWE-bench paper](https://arxiv.org/abs/2310.06770) · [SWE-bench site](https://www.swebench.com/)

---

<a id="q75"></a>
### Q75. How do you use simulated users in agent evals?

`Senior` · `Representative`

**Answer.** For conversational agents, the input is not a single prompt, it is a person who reveals information over turns, changes their mind and makes mistakes. A simulated user is a model prompted with a persona, a goal and private facts, told to reveal them only when asked, and to stop when the goal is met or clearly failed. That makes multi-turn evals repeatable at scale. I write user goals from real conversations, include difficult personas (vague, impatient, wrong about their own order number), and make the simulator a different model or at least a different prompt from the agent so they do not share quirks. Then I validate the simulator. I read its transcripts, compare its behaviour with real users, and check that it does not leak its goal in the first message or accept wrong answers. A simulator that is too easy makes every agent look good.

**Follow-ups**
- *How do you stop the simulator from helping the agent?* Instruct it to answer only what is asked and grade it for leaks.
- *How many turns?* Cap at what real conversations need, plus margin, and treat hitting the cap as failure.

**Read:** [tau-bench paper](https://arxiv.org/abs/2406.12045)

---

<a id="q76"></a>
### Q76. How do you build an agent eval set when you have no data yet?

`Core` · `Representative`

**Answer.** Start by writing the tasks you would test by hand anyway. Before launch, I sit with the product owner and write 20 to 50 realistic tasks covering the main jobs, the edge cases we already worry about, and cases where the agent should refuse or ask. Each gets a reference outcome and a grader. I run them in a sandboxed environment with seeded data so the outcome is checkable. I add some tasks where a behaviour should not happen, so I do not optimise one-sidedly, which Anthropic's guide also recommends. After launch the set grows from production: every user-reported failure and every bad trace I find becomes a task. Within weeks the set is mostly real failures, which is the most valuable kind. I also keep a small capability set of hard tasks the agent cannot do yet, to see progress, separate from the regression set that must stay green.

**Follow-ups**
- *Can you generate tasks with an LLM?* Yes, for variety, but review them and anchor them in real usage. Synthetic-only sets miss real failure modes.
- *What does a 0% pass rate across trials tell you?* Usually that the task or grader is broken, not the agent.

**Read:** [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) · [Hamel Husain: Your AI product needs evals](https://hamel.dev/blog/posts/evals/)

---

<a id="q77"></a>
### Q77. How do you make LLM-as-judge reliable for agent outputs?

`Senior` · `Representative`

**Answer.** Treat the judge as a model that needs its own eval. I give it a specific rubric with concrete criteria and examples of each score, and ask for a short reason before the verdict. I prefer binary or few-level scores over 1 to 10 scales, which drift. Then I calibrate. I have humans label a sample, a hundred or so, measure agreement between the judge and the humans, and iterate on the rubric until agreement is acceptable. I know the known biases from the MT-Bench paper: position bias in pairwise comparisons, so I swap order and average; verbosity bias, so I penalise padding in the rubric; and self-preference, so I use a different model family from the agent where possible. I also give the judge the evidence it needs, like the tool results or the reference answer, so it is checking claims against something rather than judging fluency.

**Follow-ups**
- *When is a judge the wrong tool?* When the outcome is checkable by code. Use the code.
- *How often do you recalibrate?* When you change the judge model, the rubric or the product, and on a schedule with fresh human labels.

**Read:** [Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena](https://arxiv.org/abs/2306.05685)

---

<a id="q78"></a>
### Q78. Your agent eval scores went up, but users are complaining more. What happened?

`Senior` · `Representative`

**Answer.** The eval set no longer matches what users do. Common causes. The task set is stale: users moved on to tasks the set does not cover. The graders are gameable: the agent learned to produce outputs that pass the rubric, like longer answers for a verbosity-biased judge, or code that passes tests without solving the problem. Someone tuned prompts against the eval set until it overfit. The eval measures capability, but users care about something else, like latency, tone or asking too many questions. Or the eval environment differs from production: mocked tools that never time out, clean data. I would pull a sample of complaint transcripts, label the failure types, check whether the eval contains similar tasks, and add them. Then audit the graders against human judgment on recent outputs. And keep a held-out set that nobody tunes against.

**Follow-ups**
- *What online signals do you watch?* Task completion, escalation to humans, user corrections, retries, thumbs down, and abandonment.
- *How do you stop overfitting to the eval?* Held-out tasks, rotation of tasks, and regular refresh from production.

**Read:** [Hamel Husain: Your AI product needs evals](https://hamel.dev/blog/posts/evals/)

---

<a id="q79"></a>
### Q79. How do you evaluate tool selection specifically?

`Senior` · `Representative`

**Answer.** With a focused set of single-decision cases: a context and a request, and the tool or tools a correct agent should call, with key arguments. I run each through the agent's first turn only, which is cheap and fast, and measure precision and recall on tool choice plus argument accuracy. I include cases where no tool should be called and cases with near-duplicate tools, since that is where selection breaks. The Berkeley Function Calling Leaderboard does this at benchmark scale, including irrelevance detection, where the right answer is to call nothing. Then I tie it back to full-task evals, because a correct first call can still lead to a failed task. This set is my regression test for any change to tool descriptions, tool count or the model.

**Follow-ups**
- *Why include "no tool" cases?* Over-calling costs latency and can trigger side effects. You need to catch it.
- *How do you score argument correctness?* Exact match for ids and enums; normalised or judge-based comparison for free text like search queries.

**Read:** [Berkeley Function Calling Leaderboard](https://gorilla.cs.berkeley.edu/leaderboard.html)

---

<a id="q80"></a>
### Q80. What is wrong with judging an agent on public benchmarks alone?

`Core` · `Representative`

**Answer.** Public benchmarks tell you about general capability under someone else's tools, prompts and task distribution. My product has different tools, users and policies, and the gap is large. Benchmarks also leak: tasks and solutions are public, and models may have trained on them, so scores overstate ability on fresh tasks. Many measure models plus a specific scaffold, so they do not tell you how a model will do in your harness. And they optimise for what is easy to grade. I use them to shortlist models and to sanity-check claims, and then I decide with my own eval on my own tasks. GAIA, WebArena, SWE-bench and tau-bench are all useful references, and none of them is my product.

**Follow-ups**
- *Which benchmark would you cite for a support agent?* tau-bench or tau2-bench, because of the policy, multi-turn and consistency focus.
- *For a browser agent?* WebArena, which uses realistic self-hosted websites.

**Read:** [GAIA](https://arxiv.org/abs/2311.12983) · [WebArena](https://arxiv.org/abs/2307.13854)

---

<a id="q81"></a>
### Q81. How do evals fit into the release process for an agent?

`Senior` · `Representative`

**Answer.** As a gate, like tests. Any change to the model, prompt, tools, tool descriptions or harness triggers the eval suite in CI. The regression set must stay above its threshold on success rate and pass^k, and cost and latency must stay within budget; a drop blocks the release unless someone signs off with a reason. The capability set is reported but does not block. Because runs are expensive and noisy, I run several trials per task and compare with confidence intervals rather than reacting to a one-point swing. After the offline gate comes a staged rollout: shadow traffic or a small percentage, with online metrics and trace sampling, then wider. Every incident in production adds a task. The eval suite is the place where the team's knowledge of how the agent fails accumulates, so it gets the same care as the code.

**Follow-ups**
- *How do you deal with eval cost?* Smaller fast subset on every commit, full suite before release, cache model responses where inputs are unchanged.
- *Who owns the eval set?* The team that owns the agent, with product people contributing tasks.

**Read:** [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)

---

<sub>[Question index](README.md) · Next: [Reliability and production](08-reliability-and-production.md)</sub>
