# MCP (Model Context Protocol)

<sub>[Question index](README.md) · [Repo home](../README.md) · Previous: [Memory and context](04-memory-and-context.md) · Next: [Multi-agent systems](06-multi-agent.md)</sub>

13 questions, Q48 to Q60. MCP went from a launch post in November 2024 to the default way agents connect to tools, and the spec has changed a lot since. Interviewers check two things: that you know the moving parts, and that you treat every MCP server as untrusted code with a text channel into your model.

Spec references below point at the current revision, **2026-07-28**, unless they say otherwise. If your interviewer learned MCP in 2025, expect questions about the initialize handshake and sessions; know that the 2026-07-28 revision removed both, and say so.

Difficulty is `Core`, `Senior` or `Staff`. `Representative` questions are written by us to match real loops; `Reported` questions link a public source.

---

<a id="q48"></a>
### Q48. What is MCP and what problem does it solve?

`Core` · `Representative`

**Answer.** MCP is an open protocol, announced by Anthropic in November 2024, that standardises how AI applications connect to tools and data. Before it, every app wrote its own integration for every service: M apps times N services. With MCP, a service writes one server and any MCP-capable client can use it, so the work becomes M plus N. The spec compares it to the Language Server Protocol, which did the same for editors and programming languages. It uses JSON-RPC 2.0 messages. A server exposes tools the model can call, resources the app can read as context, and prompts the user can pick as templates. What MCP does not do is make tools good or safe. A badly designed API wrapped in MCP is still badly designed, and a third-party server is code and text you did not write running next to your model.

**Follow-ups**
- *When would you skip MCP and use plain function calling?* One app, a few internal tools, tight latency. In-process functions are simpler and faster.
- *When is MCP clearly worth it?* When the same tools must work across several clients, like an IDE, a chat app and your own agent, or when you consume third-party integrations.

**Read:** [Introducing the Model Context Protocol](https://www.anthropic.com/news/model-context-protocol) · [MCP specification](https://modelcontextprotocol.io/specification/2026-07-28)

---

<a id="q49"></a>
### Q49. Explain MCP's architecture: host, client and server.

`Core` · `Representative`

**Answer.** The host is the AI application the user runs, like an IDE or a chat app. It manages the model, the user interface and the security decisions. Inside the host, each client keeps a connection to one server. A server is a program that exposes capabilities: tools (functions the model can invoke), resources (data identified by URIs that the application can read and put in context) and prompts (templates the user can choose). The host aggregates tools from all its connected servers and shows them to the model. When the model calls one, the host routes the call through the right client to that server, gets the result, and passes it back to the model. The important point is that the host is the trust boundary. It decides which servers are connected, which tools the model sees, and which calls need user approval. Servers should not see each other's data or the full conversation.

**Follow-ups**
- *Tools versus resources?* Tools are model-controlled actions. Resources are application-controlled context the app decides to load.
- *Who controls prompts?* The user. They are meant to be picked explicitly, like slash commands.

**Read:** [MCP architecture](https://modelcontextprotocol.io/specification/2026-07-28/architecture) · [Learn: architecture overview](https://modelcontextprotocol.io/docs/learn/architecture)

---

<a id="q50"></a>
### Q50. What transports does MCP support, and when do you use each?

`Core` · `Representative`

**Answer.** Two standard ones. stdio: the host launches the server as a local subprocess and they exchange JSON-RPC over standard input and output. It suits local tools like file system or git access, has no network exposure, and takes credentials from the environment rather than OAuth. Streamable HTTP: the server is a remote HTTP service, the client POSTs JSON-RPC requests, and the server can reply with plain JSON or stream messages back. That is what you use for hosted, multi-user servers. The older HTTP plus SSE transport has been deprecated since the 2025-03-26 revision and the 2026-07-28 revision marks it for removal. The 2026-07-28 revision also simplified Streamable HTTP: no protocol-level sessions, no separate GET stream, and opt-in change notifications through a single `subscriptions/listen` stream.

**Follow-ups**
- *What security check does the spec require for local HTTP servers?* Validate the `Origin` header to block DNS rebinding, and bind to localhost.
- *Can I run MCP over WebSockets?* Custom transports are allowed, but you lose interop with standard clients.

**Read:** [MCP transports](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/index)

---

<a id="q51"></a>
### Q51. What changed in the 2026-07-28 MCP revision, and why does it matter for scaling?

`Staff` · `Representative`

**Answer.** It made the protocol stateless. The initialize handshake is gone; every request now carries its protocol version and client capabilities in `_meta`, and servers implement a `server/discover` call for clients that want to negotiate up front. The `Mcp-Session-Id` header and protocol-level sessions were removed, so tool lists no longer vary per connection, and servers that need cross-call state hand out explicit handles as ordinary tool arguments. Server-initiated requests like sampling and elicitation were replaced by a multi round-trip pattern: the server returns an `input_required` result and the client retries the original request with the answers. Tasks moved into an official extension. For scaling this is a big deal. A stateless server can sit behind an ordinary load balancer with no sticky sessions, any replica can serve any request, and list results now carry cache hints, so gateways and clients can cache them.

**Follow-ups**
- *How do you keep state across calls now?* The server mints a handle, returns it from one tool call, and the model passes it to the next. State is explicit.
- *What did they deprecate?* Roots, sampling and logging, plus dynamic client registration in favour of client ID metadata documents.

**Read:** [MCP 2026-07-28 changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog) · [Multi round-trip requests](https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/mrtr)

---

<a id="q52"></a>
### Q52. How does authorization work for a remote MCP server?

`Senior` · `Representative`

**Answer.** It is OAuth 2.1, with the MCP server acting as a resource server and the client as an OAuth client. When the client calls the server without a token, the server returns 401 and points to its Protected Resource Metadata (RFC 9728), which names the authorization server. The client discovers the authorization server's metadata, registers or identifies itself, and runs the authorization code flow with PKCE so the user can consent. The current spec recommends Client ID Metadata Documents for client identity and deprecates dynamic client registration. The client must send the `resource` parameter (RFC 8707) so the token is bound to that specific MCP server, and the server must check that a token was issued for it. Scopes can be stepped up later through a `WWW-Authenticate` challenge. For stdio servers the spec says not to use this flow; credentials come from the environment.

**Follow-ups**
- *Why does audience binding matter?* Without it, a token issued for server A could be replayed against server B. That is the confused deputy problem.
- *Who runs the authorization server?* Often your existing identity provider. The spec leaves that implementation open.

**Read:** [MCP authorization](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/index) · [Authorization security considerations](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/security-considerations)

---

<a id="q53"></a>
### Q53. What is token passthrough and why is it forbidden?

`Senior` · `Representative`

**Answer.** Token passthrough is when an MCP server accepts a token from the client and forwards it unchanged to a downstream API, or accepts tokens that were not issued for itself. The MCP security guidance forbids it. The problems are concrete. The server cannot tell who is calling or enforce its own rate limits and policies. Audit trails at the downstream API show the client, not the server, so you lose accountability. A stolen token works across services. And it breaks the trust boundary, because the downstream API trusts a token that the MCP server never validated. The right design: the MCP server validates tokens issued for itself, then uses its own credentials to call downstream services. Where it acts on behalf of the user, it gets a separate downstream token, for example through a token exchange or a separate consent flow.

**Follow-ups**
- *What is the confused deputy problem in MCP?* A proxy server with static credentials to a third-party API gets tricked into using its privileges for a client the user never approved. The spec requires per-client consent to prevent it.
- *Where do you store the downstream tokens?* Server-side, encrypted, scoped per user, never in the model's context.

**Read:** [MCP security best practices (2025-11-25)](https://modelcontextprotocol.io/specification/2025-11-25/basic/security_best_practices)

---

<a id="q54"></a>
### Q54. What is tool poisoning?

`Senior` · `Representative`

**Answer.** Tool poisoning is hiding malicious instructions in a tool's metadata, usually the description, which the model reads but the user rarely sees. Invariant Labs showed it in April 2025: a harmless-looking "add" tool whose description told the model to read the user's SSH keys and config files and pass them as a hidden argument. Two variants make it worse. A rug pull, where a server changes its tool descriptions after the user approved it. And shadowing, where one malicious server's descriptions change how the model uses another, trusted server's tools, for example rewriting the recipient of every email. The defences: only connect servers you trust and pin their versions. Show users full tool descriptions and diff them when they change, requiring re-approval. Scan descriptions for instruction-like text. Isolate servers from each other's data. And enforce sensitive rules in code at the host, because the model will follow text it reads.

**Follow-ups**
- *Are tool annotations like "read-only" trustworthy?* The spec says clients must treat annotations as untrusted unless they come from trusted servers.
- *Can tool results poison too?* Yes. Any text from a server is a prompt injection channel, not only descriptions.

**Read:** [Invariant Labs: tool poisoning attacks](https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks) · [Simon Willison: MCP has prompt injection security problems](https://simonwillison.net/2025/Apr/9/mcp-prompt-injection/)

---

<a id="q55"></a>
### Q55. Why would a company put an MCP gateway in front of its servers?

`Staff` · `Representative`

**Answer.** Once dozens of teams ship MCP servers and hundreds of employees connect clients to them, you need one place to apply policy. A gateway sits between clients and servers and handles authentication against the company identity provider, authorisation per user and per tool, an allowlist of approved servers and pinned tool descriptions, audit logging of every call with arguments and results, rate limits and quotas, secrets so that clients never hold downstream credentials, and scanning of descriptions and results for injection or sensitive data. It can also aggregate several servers behind one endpoint and filter which tools each user's agent sees, which helps the tool-count problem. The tradeoffs are an extra hop, a single point of failure, and a team that has to own it. With the stateless 2026-07-28 revision, gateways get simpler because they can cache list results and route any request to any replica.

**Follow-ups**
- *What would you log per call?* User, agent, server, tool, arguments hash or redacted arguments, result size, latency, decision (allowed, denied, approved by human).
- *Can a gateway stop prompt injection?* It can reduce it, by scanning and by limiting what tools combine. It cannot guarantee it.

**Read:** [MCP security best practices (2025-11-25)](https://modelcontextprotocol.io/specification/2025-11-25/basic/security_best_practices) · [MCP caching utilities](https://modelcontextprotocol.io/specification/2026-07-28/server/utilities/caching)

---

<a id="q56"></a>
### Q56. How would you design a good MCP server for an internal API?

`Senior` · `Representative`

**Answer.** The same way I design any agent tool, plus protocol hygiene. I start from the tasks agents will do, not from the endpoint list, and expose a handful of task-shaped tools with clear names, namespacing, tight schemas and concise outputs with pagination. I return validation errors as tool execution errors with a message the model can act on, which the spec has recommended since 2025-11-25. I give an output schema and structured content where results are data. I mark read-only and destructive tools honestly, knowing clients may not trust the marks. For a remote server I implement OAuth with audience checks and least-privilege scopes, and I never pass the user's token through. I keep it stateless, listing tools in a deterministic order so clients can cache. And I ship it with an eval: a set of tasks run through a real client and model, because a server that passes unit tests can still be unusable by an agent.

**Follow-ups**
- *Local stdio or remote HTTP for an internal API?* Remote, so auth, logging and updates are central. stdio fits tools that need the user's local machine.
- *How do you test it?* The MCP Inspector for protocol checks, then agent-level evals.

**Read:** [MCP tools spec](https://modelcontextprotocol.io/specification/2026-07-28/server/tools) · [Writing effective tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents)

---

<a id="q57"></a>
### Q57. Function calling, MCP and agent-to-agent protocols: how do they relate?

`Senior` · `Representative`

**Answer.** They sit at different layers. Function calling is the model API feature: the model emits a structured call, your code runs it. MCP is how your application discovers and talks to tool providers over a standard protocol; the host still uses function calling to show those tools to the model. So MCP is plumbing between the app and tools, and function calling is plumbing between the app and the model. Agent-to-agent protocols, such as Google's A2A, address a different problem: one agent delegating a task to another agent, often from a different vendor, with task lifecycle and capability discovery. You can wrap an agent as an MCP tool too, and many teams do, but then it looks like a function to the caller. My view: use function calling always, MCP when tools are shared or third-party, and an agent protocol only when you truly need independent agents across organisational boundaries.

**Follow-ups**
- *Does MCP replace REST APIs?* No. MCP servers usually wrap REST APIs. It is an adapter for model clients.
- *What does MCP's sampling feature do?* It let a server ask the client's model for a completion. The 2026-07-28 revision deprecates it in favour of calling a provider API directly.

**Read:** [MCP 2026-07-28 changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog) · [OpenAI function calling guide](https://platform.openai.com/docs/guides/function-calling)

---

<a id="q58"></a>
### Q58. A user connects 15 MCP servers and the agent gets worse. Why?

`Senior` · `Representative`

**Answer.** Every connected server adds its tool definitions to the context on every turn. Fifteen servers can easily mean 100 or more tools and tens of thousands of tokens before the user says anything. That costs money and latency and crowds the window. Worse, tools from different servers overlap: three "search" tools, two ways to create a ticket. Selection accuracy drops and the agent picks the wrong one or hesitates between them. And each server is another injection surface. The fixes: let users or admins enable servers per workspace or task, not globally. Filter tools by relevance with tool search, loading only the matches. Namespace names so the model can tell `github_search` from `jira_search`. Or present tools as code modules the agent loads on demand, the approach in Anthropic's code execution with MCP post, which reported cutting one workflow from 150,000 tokens to 2,000.

**Follow-ups**
- *How would you measure the harm?* Tool-selection accuracy and task success on an eval, with 1, 5 and 15 servers connected.
- *Does prompt caching solve the cost?* It helps cost if the tool list is stable. It does not help selection quality.

**Read:** [Code execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp) · [Cloudflare: Code Mode](https://blog.cloudflare.com/code-mode/)

---

<a id="q59"></a>
### Q59. How do long-running operations work in MCP?

`Staff` · `Representative`

**Answer.** A normal tool call is request and response, which breaks down for jobs that take minutes or hours, like a large export or a build. The 2025-11-25 revision added experimental tasks: a call can return a task handle, and the client polls for status and fetches the result later. The 2026-07-28 revision moved tasks into an official extension, replaced the blocking result call with polling through `tasks/get`, added `tasks/update` for sending input mid-task, and lets servers return task handles without per-request opt-in. Progress notifications still flow on the response stream of the request they relate to. Because the 2026-07-28 revision also removed stream resumability, a dropped HTTP stream loses the in-flight request, so anything long should be a task, not a long-held response. Design-wise I make long operations idempotent and resumable on the server, and give the agent a way to check status cheaply rather than re-running the job.

**Follow-ups**
- *What does the agent do while waiting?* Other work, or it yields back to the user and resumes when the task finishes. Do not burn turns polling in a tight loop.
- *How do you cancel?* The spec defines cancellation; the server must handle it and leave state consistent.

**Read:** [MCP 2026-07-28 changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog) · [MCP tasks (2025-11-25)](https://modelcontextprotocol.io/specification/2025-11-25/basic/utilities/tasks)

---

<a id="q60"></a>
### Q60. How does an MCP server get information from the user mid-call?

`Senior` · `Representative`

**Answer.** Through elicitation. A server can ask the client to collect structured input from the user, like a confirmation, a choice from an enum, or a few form fields, described with a restricted JSON Schema. The client shows a form, and the user can accept, decline or cancel. There is also a URL mode for flows that must happen outside the client, such as an OAuth consent or a payment page, so sensitive data never passes through the client or the model. In the 2026-07-28 revision this works through the multi round-trip pattern: the tool call returns an `input_required` result listing what it needs, and the client retries the call with the user's answers. The security rule from the spec is that servers must not use form elicitation to ask for passwords, API keys or other secrets. Those go through URL mode or proper auth.

**Follow-ups**
- *Why not just let the model ask in chat?* Elicitation gives a typed, validated answer, and the client can show the user which server is asking.
- *Can a malicious server abuse elicitation?* It can phish. Clients must show which server is asking and let users decline.

**Read:** [MCP elicitation](https://modelcontextprotocol.io/specification/2026-07-28/client/elicitation)

---

<sub>[Question index](README.md) · Next: [Multi-agent systems](06-multi-agent.md)</sub>
