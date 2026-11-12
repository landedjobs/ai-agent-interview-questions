# Question index

<sub>[Repo home](../README.md)</sub>

Every question in the repo, grouped by topic. Each links to its full answer, follow-ups and sources. Difficulty: `Core` (every candidate should nail it), `Senior`, `Staff`.

| Topic | Questions | Core | Senior | Staff |
|---|---|---|---|---|
| [Fundamentals: agents, workflows and the loop](01-fundamentals.md) | 12 | 7 | 5 | 0 |
| [Tool use and function calling](02-tool-use.md) | 13 | 6 | 7 | 0 |
| [Planning and reasoning](03-planning-and-reasoning.md) | 10 | 3 | 6 | 1 |
| [Memory and context engineering](04-memory-and-context.md) | 12 | 3 | 8 | 1 |
| [MCP (Model Context Protocol)](05-mcp.md) | 13 | 3 | 7 | 3 |
| [Multi-agent systems](06-multi-agent.md) | 9 | 2 | 6 | 1 |
| [Evals for agents](07-evals.md) | 12 | 5 | 7 | 0 |
| [Reliability and production](08-reliability-and-production.md) | 12 | 5 | 6 | 1 |
| [Safety and security](09-safety-and-security.md) | 12 | 3 | 7 | 2 |
| [System design scenarios](10-system-design.md) | 5 | 0 | 3 | 2 |
| [Coding exercises](11-coding.md) | 4 | 2 | 2 | 0 |
| **Total** | **114** | **39** | **64** | **11** |

## Fundamentals: agents, workflows and the loop

- [Q1. What is the difference between an agent and a workflow?](01-fundamentals.md#q1) `Core`
- [Q2. Walk me through the agent loop.](01-fundamentals.md#q2) `Core`
- [Q3. Explain ReAct. Is it still how agents work?](01-fundamentals.md#q3) `Core`
- [Q4. When should you not build an agent?](01-fundamentals.md#q4) `Core`
- [Q5. Name the common workflow patterns and when each fits.](01-fundamentals.md#q5) `Core`
- [Q6. Why do errors compound in long agent runs, and what do you do about it?](01-fundamentals.md#q6) `Senior`
- [Q7. What goes into an agent's system prompt?](01-fundamentals.md#q7) `Core`
- [Q8. What is the difference between a model and a harness, and which matters more?](01-fundamentals.md#q8) `Senior`
- [Q9. How does an agent decide to call a tool versus answer from its own knowledge?](01-fundamentals.md#q9) `Core`
- [Q10. Single agent with many tools, or several specialised agents?](01-fundamentals.md#q10) `Senior`
- [Q11. What do you look for when choosing an agent framework, or would you skip one?](01-fundamentals.md#q11) `Senior`
- [Q12. What are code agents, and when do they beat JSON tool calling?](01-fundamentals.md#q12) `Senior`

## Tool use and function calling

- [Q13. How does function calling actually work under the hood?](02-tool-use.md#q13) `Core`
- [Q14. How do you design a good tool schema?](02-tool-use.md#q14) `Core`
- [Q15. Should you expose every API endpoint as a tool?](02-tool-use.md#q15) `Core`
- [Q16. What should a tool return?](02-tool-use.md#q16) `Core`
- [Q17. A tool call fails. What should the agent see?](02-tool-use.md#q17) `Core`
- [Q18. The agent keeps hallucinating tool arguments. How do you debug it?](02-tool-use.md#q18) `Senior`
- [Q19. How do parallel tool calls work, and when are they safe?](02-tool-use.md#q19) `Senior`
- [Q20. You have 300 tools. What do you do?](02-tool-use.md#q20) `Senior`
- [Q21. What is the difference between function calling and structured outputs?](02-tool-use.md#q21) `Core`
- [Q22. How do you version tools without breaking running agents?](02-tool-use.md#q22) `Senior`
- [Q23. What is the "think" tool and is it still useful with reasoning models?](02-tool-use.md#q23) `Senior`
- [Q24. How do you make a tool safe to call more than once?](02-tool-use.md#q24) `Senior`
- [Q25. How would you evaluate a new tool before giving it to the agent?](02-tool-use.md#q25) `Senior`

## Planning and reasoning

- [Q26. What is plan-and-execute, and how does it differ from a ReAct loop?](03-planning-and-reasoning.md#q26) `Core`
- [Q27. What is reflection, and does self-critique actually work?](03-planning-and-reasoning.md#q27) `Senior`
- [Q28. How do reasoning models change agent design?](03-planning-and-reasoning.md#q28) `Senior`
- [Q29. Tree of Thoughts, self-consistency, best-of-n: when do search methods pay off?](03-planning-and-reasoning.md#q29) `Senior`
- [Q30. How do you stop an agent from looping forever?](03-planning-and-reasoning.md#q30) `Core`
- [Q31. How should an agent decide it is done?](03-planning-and-reasoning.md#q31) `Core`
- [Q32. When should an agent ask the user a clarifying question?](03-planning-and-reasoning.md#q32) `Senior`
- [Q33. How do you handle long-horizon tasks that run for hours?](03-planning-and-reasoning.md#q33) `Staff`
- [Q34. Should the agent's plan be in the prompt, in state, or in code?](03-planning-and-reasoning.md#q34) `Senior`
- [Q35. How do you route between models in one agent?](03-planning-and-reasoning.md#q35) `Senior`

## Memory and context engineering

- [Q36. What is context engineering, and how is it different from prompt engineering?](04-memory-and-context.md#q36) `Core`
- [Q37. Short-term versus long-term memory in agents: what are they, concretely?](04-memory-and-context.md#q37) `Core`
- [Q38. How do you decide what an agent should write to long-term memory?](04-memory-and-context.md#q38) `Senior`
- [Q39. What is compaction, and what goes wrong with it?](04-memory-and-context.md#q39) `Senior`
- [Q40. How do sub-agents help with context?](04-memory-and-context.md#q40) `Senior`
- [Q41. Just-in-time retrieval or preloading context: which do you choose?](04-memory-and-context.md#q41) `Senior`
- [Q42. How does prompt caching change agent architecture?](04-memory-and-context.md#q42) `Senior`
- [Q43. How do you give an agent memory of a codebase or large document set?](04-memory-and-context.md#q43) `Senior`
- [Q44. Your agent forgets an instruction given 40 turns ago. Why, and what do you do?](04-memory-and-context.md#q44) `Core`
- [Q45. How would you design memory for a personal assistant agent used daily?](04-memory-and-context.md#q45) `Staff`
- [Q46. What is "context rot" and how do you measure it in your own agent?](04-memory-and-context.md#q46) `Senior`
- [Q47. Where should agent state live: the conversation, a database, or files?](04-memory-and-context.md#q47) `Senior`

## MCP (Model Context Protocol)

- [Q48. What is MCP and what problem does it solve?](05-mcp.md#q48) `Core`
- [Q49. Explain MCP's architecture: host, client and server.](05-mcp.md#q49) `Core`
- [Q50. What transports does MCP support, and when do you use each?](05-mcp.md#q50) `Core`
- [Q51. What changed in the 2026-07-28 MCP revision, and why does it matter for scaling?](05-mcp.md#q51) `Staff`
- [Q52. How does authorization work for a remote MCP server?](05-mcp.md#q52) `Senior`
- [Q53. What is token passthrough and why is it forbidden?](05-mcp.md#q53) `Senior`
- [Q54. What is tool poisoning?](05-mcp.md#q54) `Senior`
- [Q55. Why would a company put an MCP gateway in front of its servers?](05-mcp.md#q55) `Staff`
- [Q56. How would you design a good MCP server for an internal API?](05-mcp.md#q56) `Senior`
- [Q57. Function calling, MCP and agent-to-agent protocols: how do they relate?](05-mcp.md#q57) `Senior`
- [Q58. A user connects 15 MCP servers and the agent gets worse. Why?](05-mcp.md#q58) `Senior`
- [Q59. How do long-running operations work in MCP?](05-mcp.md#q59) `Staff`
- [Q60. How does an MCP server get information from the user mid-call?](05-mcp.md#q60) `Senior`

## Multi-agent systems

- [Q61. When does a multi-agent system beat a single agent?](06-multi-agent.md#q61) `Senior`
- [Q62. What is the case against multi-agent systems?](06-multi-agent.md#q62) `Senior`
- [Q63. Describe the orchestrator-worker pattern.](06-multi-agent.md#q63) `Core`
- [Q64. What is a handoff, and how is it different from calling an agent as a tool?](06-multi-agent.md#q64) `Core`
- [Q65. How do you debug a failure in a multi-agent system?](06-multi-agent.md#q65) `Senior`
- [Q66. How do agents share state safely?](06-multi-agent.md#q66) `Staff`
- [Q67. Orchestration versus choreography for agents?](06-multi-agent.md#q67) `Senior`
- [Q68. How do you evaluate a multi-agent system?](06-multi-agent.md#q68) `Senior`
- [Q69. What does a multi-agent system cost, and how do you keep it in check?](06-multi-agent.md#q69) `Senior`

## Evals for agents

- [Q70. How do you evaluate an agent?](07-evals.md#q70) `Core`
- [Q71. Trajectory evaluation versus outcome evaluation: what is the difference and when do you use each?](07-evals.md#q71) `Senior`
- [Q72. Explain pass@k versus pass^k. Which one matters for a customer-facing agent?](07-evals.md#q72) `Core`
- [Q73. What is tau-bench and what does it teach about agent evaluation?](07-evals.md#q73) `Senior`
- [Q74. What is SWE-bench, and what are its limits?](07-evals.md#q74) `Core`
- [Q75. How do you use simulated users in agent evals?](07-evals.md#q75) `Senior`
- [Q76. How do you build an agent eval set when you have no data yet?](07-evals.md#q76) `Core`
- [Q77. How do you make LLM-as-judge reliable for agent outputs?](07-evals.md#q77) `Senior`
- [Q78. Your agent eval scores went up, but users are complaining more. What happened?](07-evals.md#q78) `Senior`
- [Q79. How do you evaluate tool selection specifically?](07-evals.md#q79) `Senior`
- [Q80. What is wrong with judging an agent on public benchmarks alone?](07-evals.md#q80) `Core`
- [Q81. How do evals fit into the release process for an agent?](07-evals.md#q81) `Senior`

## Reliability and production

- [Q82. How do you handle retries in an agent?](08-reliability-and-production.md#q82) `Core`
- [Q83. What is durable execution and why do agents need it?](08-reliability-and-production.md#q83) `Senior`
- [Q84. How do you control cost per agent task?](08-reliability-and-production.md#q84) `Core`
- [Q85. How do you reduce agent latency?](08-reliability-and-production.md#q85) `Senior`
- [Q86. What do you trace and log for an agent in production?](08-reliability-and-production.md#q86) `Core`
- [Q87. A tool times out after the agent sends a payment request. Did the payment go through?](08-reliability-and-production.md#q87) `Senior`
- [Q88. How do you handle model provider outages?](08-reliability-and-production.md#q88) `Senior`
- [Q89. How do you roll out a new model version to an agent in production?](08-reliability-and-production.md#q89) `Senior`
- [Q90. How do you scale an agent service to thousands of concurrent runs?](08-reliability-and-production.md#q90) `Staff`
- [Q91. What guardrails would you put around an agent in production?](08-reliability-and-production.md#q91) `Core`
- [Q92. How do you debug an agent failure a user reported?](08-reliability-and-production.md#q92) `Core`
- [Q93. What are the main ways agents fail in production?](08-reliability-and-production.md#q93) `Senior`

## Safety and security

- [Q94. What is prompt injection, and why is it worse for agents than for chatbots?](09-safety-and-security.md#q94) `Core`
- [Q95. Explain the lethal trifecta.](09-safety-and-security.md#q95) `Core`
- [Q96. How would you defend an email assistant agent against prompt injection?](09-safety-and-security.md#q96) `Senior`
- [Q97. What is the dual LLM pattern, and how does CaMeL extend it?](09-safety-and-security.md#q97) `Staff`
- [Q98. How do you sandbox an agent that runs code?](09-safety-and-security.md#q98) `Senior`
- [Q99. How do you design human approval so it is actually useful?](09-safety-and-security.md#q99) `Senior`
- [Q100. How should an agent hold credentials?](09-safety-and-security.md#q100) `Senior`
- [Q101. Can an agent's memory be poisoned?](09-safety-and-security.md#q101) `Senior`
- [Q102. What extra risks do browser and computer-use agents bring?](09-safety-and-security.md#q102) `Senior`
- [Q103. Could an agent act against its operator's interests without any attacker?](09-safety-and-security.md#q103) `Staff`
- [Q104. How do you red-team an agent before launch?](09-safety-and-security.md#q104) `Senior`
- [Q105. Where do you enforce policy: in the prompt, in the model, or in code?](09-safety-and-security.md#q105) `Core`

## System design scenarios

- [Q106. Design a customer support agent that can issue refunds.](10-system-design.md#q106) `Senior`
- [Q107. Design a coding agent that takes a GitHub issue and opens a pull request.](10-system-design.md#q107) `Staff`
- [Q108. Design a deep research agent that writes cited reports.](10-system-design.md#q108) `Senior`
- [Q109. Design an internal assistant that works across company tools through MCP.](10-system-design.md#q109) `Staff`
- [Q110. Design a data analysis agent that answers questions over a warehouse.](10-system-design.md#q110) `Senior`

## Coding exercises

- [Q111. Build a minimal agent loop in Python.](11-coding.md#q111) `Core`
- [Q112. Build a tool registry that generates schemas and validates calls.](11-coding.md#q112) `Core`
- [Q113. Write a retry wrapper for tool and model calls.](11-coding.md#q113) `Senior`
- [Q114. Test an agent loop without calling a model.](11-coding.md#q114) `Senior`

<sub>[Repo home](../README.md)</sub>
