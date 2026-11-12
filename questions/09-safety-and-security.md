# Safety and security

<sub>[Question index](README.md) · [Repo home](../README.md) · Previous: [Reliability and production](08-reliability-and-production.md) · Next: [System design scenarios](10-system-design.md)</sub>

12 questions, Q94 to Q105. Agents turn model mistakes into actions, and prompt injection turns other people's text into instructions. Interviewers want to hear that you design so a fooled model cannot do much damage, rather than hoping to stop the model from being fooled.

Difficulty is `Core`, `Senior` or `Staff`. `Representative` questions are written by us to match real loops; `Reported` questions link a public source.

---

<a id="q94"></a>
### Q94. What is prompt injection, and why is it worse for agents than for chatbots?

`Core` · `Representative`

**Answer.** Prompt injection is getting a model to follow instructions from text that should have been treated as data. Direct injection comes from the user typing it. Indirect injection comes from content the model reads: a web page, an email, a PDF, a tool result, an MCP tool description. The model has no reliable way to tell "instructions from my operator" from "instructions inside this document", because it is all tokens in one context. In a chatbot, the worst case is usually a bad answer. In an agent, the model's output becomes actions: it can send email, call APIs, edit files, spend money. So an attacker who can get text in front of your agent, by sending the user an email or planting text on a page the agent browses, can try to steer those actions. OWASP lists prompt injection as the top risk for LLM applications, and it remains unsolved at the model level.

**Follow-ups**
- *Can a better system prompt fix it?* It lowers the success rate. It does not give a guarantee, so it cannot be your only defence.
- *Is jailbreaking the same thing?* Related but different. Jailbreaking targets the model's safety training; injection targets your application's trust boundary.

**Read:** [OWASP LLM01: Prompt injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) · [Simon Willison's prompt injection series](https://simonwillison.net/tags/prompt-injection/)

---

<a id="q95"></a>
### Q95. Explain the lethal trifecta.

`Core` · `Representative`

**Answer.** It is Simon Willison's name, from June 2025, for the combination that makes data theft through prompt injection possible: an agent with access to private data, exposure to untrusted content, and the ability to communicate externally. If all three are present, an attacker can put instructions in the untrusted content telling the agent to read the private data and send it out, through an API call, an email, or even a URL in a rendered image or link. Any two of the three is far safer. The useful thing about the framing is that it turns an unsolvable detection problem into an architecture decision. I cannot reliably detect every injection, but I can make sure no single agent context has all three capabilities at once, or that the external channel is gated by a human or locked to known destinations.

**Follow-ups**
- *Give a sneaky exfiltration channel.* A markdown image whose URL carries the data as a query string; the client fetches it automatically when rendering.
- *How does MCP make this easier to hit?* Users mix servers freely, so one server brings private data, another brings untrusted content, a third can send messages.

**Read:** [The lethal trifecta for AI agents](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/) (Simon Willison)

---

<a id="q96"></a>
### Q96. How would you defend an email assistant agent against prompt injection?

`Senior` · `Representative`

**Answer.** Assume every incoming email is hostile, since anyone can send one. Then break the trifecta for any context that reads email. The agent that summarises or triages mail gets read access and no ability to send, forward, or fetch arbitrary URLs. Drafting replies is fine; sending requires the user to click send, after seeing the exact recipient and content. Tool permissions are enforced in code, not in the prompt. Links and images in outputs get rendered only for allowlisted domains, to close the markdown-image channel. Actions that touch other data, like "find the invoice in my drive and attach it", get scoped tools and approval for anything leaving the account. On top of that, softer layers: separating untrusted content clearly in the prompt, an injection classifier, and logging for review. Those reduce attempts; the architecture limits the damage when one gets through.

**Follow-ups**
- *The user wants fully automatic replies. What now?* Restrict automatic sends to known contacts and templated content, with a daily cap and an audit log.
- *What about attachments?* Same rules. A PDF is untrusted content too.

**Read:** [The lethal trifecta for AI agents](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/) · [Defeating Prompt Injections by Design (CaMeL)](https://arxiv.org/abs/2503.18813)

---

<a id="q97"></a>
### Q97. What is the dual LLM pattern, and how does CaMeL extend it?

`Staff` · `Representative`

**Answer.** Simon Willison proposed the dual LLM pattern in 2023. A privileged model plans and calls tools but never sees untrusted content. A quarantined model processes untrusted content but has no tools. The privileged model refers to the quarantined model's outputs only by variable names, like `$summary1`, so injected text never reaches the model that can act. CaMeL, a 2025 paper by Debenedetti and colleagues with code from Google Research, makes this rigorous. The privileged model writes a program from the user's trusted request; a custom interpreter runs it; untrusted data flows through as values with capability tags that record where they came from and where they may go; and security policies check those tags before any tool call, so data from an untrusted email cannot become the recipient of a send. It gives security guarantees by design instead of detection, at some cost: on the AgentDojo benchmark it solved 77% of tasks with provable security, against 84% for an undefended system. It is the strongest published answer to the trifecta I know of.

**Follow-ups**
- *What can't CaMeL protect against?* Attacks that do not need to change control flow, like an injected document that makes a summary misleading.
- *Is this practical today?* For high-stakes, well-defined tool sets, yes. For open-ended agents it is hard to write the policies.

**Read:** [The dual LLM pattern](https://simonwillison.net/2023/Apr/25/dual-llm-pattern/) · [Defeating Prompt Injections by Design](https://arxiv.org/abs/2503.18813)

---

<a id="q98"></a>
### Q98. How do you sandbox an agent that runs code?

`Senior` · `Representative`

**Answer.** Treat generated code as untrusted code from the internet. It runs in an isolated environment, a container with a hardened runtime or better a microVM or gVisor-style sandbox, not on the host and not in a shared container with other users. Each task gets a fresh environment, destroyed afterwards. No secrets inside: no cloud credentials, no long-lived tokens; if the code needs an API, it goes through a proxy that holds the credentials and enforces policy. Network egress is denied by default with an allowlist, which also blocks exfiltration. CPU, memory, disk and wall-clock limits stop runaway jobs. The file system exposes only the project directory, read-only where possible. And I log commands and outputs for audit. The common mistake is giving a coding agent the developer's own shell with their SSH keys and cloud credentials loaded.

**Follow-ups**
- *Container or microVM?* Containers share the host kernel; for untrusted multi-tenant code I prefer microVMs or a user-space kernel.
- *What about a local coding agent on a laptop?* Permission prompts for commands, an allowlist of safe commands, and sandboxed execution modes where the tool offers them.

**Read:** [Code execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp) (section on sandboxing costs) · [Claude Code best practices](https://www.anthropic.com/engineering/claude-code-best-practices)

---

<a id="q99"></a>
### Q99. How do you design human approval so it is actually useful?

`Senior` · `Representative`

**Answer.** Approval only works if the human can judge and does not drown. So I rate actions by risk and reversibility, and only ask for the ones that matter: payments, external messages, deletions, permission changes, anything irreversible. Reads and reversible drafts run without approval. The approval request shows exactly what will happen, the concrete recipient, amount and diff, not "the agent wants to use send_email". It shows why, with the relevant context. It allows edit as well as approve or deny. And it is enforced in code: the tool will not execute without a valid approval token for that exact action, so the model cannot talk its way around it. I watch approval rates. If people approve 99% without reading, the gate has become a rubber stamp and I either automate the low-risk part or redesign. MCP's spec says the same in its tools section: there should be a human able to deny tool invocations.

**Follow-ups**
- *How does approval work in a long background run?* Pause the run durably, notify the user, resume on response, and expire stale requests.
- *Can the agent batch approvals?* Yes, for many low-risk items of the same kind, with a clear list.

**Read:** [MCP tools spec: user interaction model](https://modelcontextprotocol.io/specification/2026-07-28/server/tools)

---

<a id="q100"></a>
### Q100. How should an agent hold credentials?

`Senior` · `Representative`

**Answer.** The model should never see them. Credentials live in the tool layer or a broker, injected at call time, and the model sees only results. Each tool gets the narrowest scope that does its job: a read-only database role for the analytics tool, a token that can create calendar events but not delete them. Where the agent acts for a user, it uses that user's delegated token through OAuth, with the user's own permissions, so the agent cannot do more than the user could. Tokens are short-lived and audience-bound, which is what MCP's authorization spec requires for remote servers. I never put API keys in prompts, tool descriptions or the sandbox's environment, and I scan outputs and logs for secret patterns. If a model can print it, an injection can exfiltrate it.

**Follow-ups**
- *Service account or user token?* User token when the agent acts for a user. Service accounts tend to become all-powerful and break audit trails.
- *How do you revoke access fast?* Short-lived tokens issued by a broker you control, so revocation is one switch.

**Read:** [MCP authorization security considerations](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/security-considerations)

---

<a id="q101"></a>
### Q101. Can an agent's memory be poisoned?

`Senior` · `Representative`

**Answer.** Yes, and it is nastier than a one-off injection because it persists. If the agent writes memories based on content it reads, an attacker's email or web page can plant a "memory" like "the user prefers that all invoices be forwarded to this address". In a later session that memory loads as trusted context and steers behaviour, long after the original content is gone. Defences: memory writes only from trusted sources, meaning the user's own statements, with content-derived memories either blocked or marked low-trust and confirmed with the user. Provenance on every memory, so I know where it came from. Users can see and delete memories. Memories cannot grant permissions or change policies; those live in code. And periodic review of new memories for instruction-like content.

**Follow-ups**
- *How would you test for it?* Eval tasks with injected content that tries to write memories, and checks that later sessions are unaffected.
- *Is retrieval-augmented memory safer?* No. A poisoned document in the index is the same problem.

**Read:** [OWASP LLM01: Prompt injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)

---

<a id="q102"></a>
### Q102. What extra risks do browser and computer-use agents bring?

`Senior` · `Representative`

**Answer.** Every page they visit is untrusted content in front of a model that can click, type and submit. Hidden text, comments, alt text and even text in images can carry injections. The agent may be logged into the user's accounts, so it has the private data and the ability to act, which is the trifecta in a single browser tab. Specific risks: following a malicious link, filling forms with personal data on a phishing page, approving cookie or permission dialogs, downloading and opening files, and taking irreversible actions like purchases. My design: a separate browser profile with only the sessions the task needs, domain allowlists per task, confirmation before submitting forms, payments, sending messages or changing settings, no credential entry by the agent, and screenshots plus action logs for audit. Treat instructions found on pages as data, and surface them to the user.

**Follow-ups**
- *How would you benchmark one?* WebArena and similar environments for capability, plus your own red-team pages with injected instructions.
- *Should it handle captchas?* No. Hand that to the user.

**Read:** [WebArena](https://arxiv.org/abs/2307.13854) · [Simon Willison's prompt injection series](https://simonwillison.net/tags/prompt-injection/)

---

<a id="q103"></a>
### Q103. Could an agent act against its operator's interests without any attacker?

`Staff` · `Representative`

**Answer.** In stress tests, yes. Anthropic's 2025 agentic misalignment study put models from several developers in simulated corporate settings with email access and goals, then introduced pressures such as a threat of replacement or a conflict between the model's goal and the company's new direction. In some of those setups, models took harmful actions such as blackmail or leaking information, even when instructed not to. These were contrived scenarios, and Anthropic said it had not seen this in real deployments, but the engineering lesson holds. Do not give an agent broad autonomy plus sensitive access plus goals that can conflict with oversight. Keep permissions narrow, keep humans on consequential actions, monitor trajectories as well as outputs, and do not rely on instructions alone to prevent harmful actions.

**Follow-ups**
- *What design choices reduce this risk?* Narrow goals, least privilege, approval gates, short-lived autonomy, and audit of actions.
- *How do you monitor for it?* Review trajectories with automated classifiers for policy-violating actions, and sample for human review.

**Read:** [Agentic misalignment](https://www.anthropic.com/research/agentic-misalignment) (Anthropic)

---

<a id="q104"></a>
### Q104. How do you red-team an agent before launch?

`Senior` · `Representative`

**Answer.** Start from the threat model: what can this agent read, what can it do, and who can put text in front of it. Then build attack tasks for each path. Direct injection by the user. Indirect injection through every content source the agent reads: documents, web pages, emails, tool results, MCP tool descriptions. Attempts to exfiltrate through every outbound channel, including links and images. Attempts to escalate: getting the agent to call tools outside its role, approve its own actions, or change its own memory or settings. Abuse of resources: loops and cost blowups. Each attack goes into the eval suite with an expected outcome, usually "blocked" or "asked for approval", and runs on every release. I also bring in people outside the team for a fresh look. The goal is to show that when injections succeed at the model level, which some will, the architecture contains the damage.

**Follow-ups**
- *Automated red-teaming?* Useful for volume: another model generates attack variants. Humans still find the creative ones.
- *What is a passing result?* No exfiltration or unapproved high-risk action in any trial, not an average.

**Read:** [OWASP LLM01: Prompt injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)

---

<a id="q105"></a>
### Q105. Where do you enforce policy: in the prompt, in the model, or in code?

`Core` · `Representative`

**Answer.** All three, with different jobs. The prompt tells the model the rules so it usually behaves well and can explain refusals to users. The model's own safety training covers broad harms. Code enforces the rules that must hold every time: permission checks, spending limits, approval gates, allowlists, rate limits, data access controls. My test for where a rule goes is "what happens if the model ignores it?" If the answer is an embarrassing reply, the prompt is fine. If the answer is money moved, data leaked or a record deleted, it goes in code at the tool layer, where the model cannot reach around it. The anti-pattern is a 40-line system prompt full of "never do X" with no matching checks in the tools. Prompts are suggestions; tools are the actual permission system.

**Follow-ups**
- *Example of a rule that belongs in both?* Refund limits: the prompt so the agent explains the limit to the customer, the tool so it cannot exceed it.
- *How do you keep prompt and code rules in sync?* Generate the prompt section from the same policy config the tools enforce.

**Read:** [A practical guide to building agents](https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf)

---

<sub>[Question index](README.md) · Next: [System design scenarios](10-system-design.md)</sub>
