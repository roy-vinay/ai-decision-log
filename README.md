<picture>
  <source media="(prefers-color-scheme: dark)" srcset=".github/assets/masthead-dark.svg">
  <img src=".github/assets/masthead-light.svg" width="100%" alt="AI Decision Log: one-page memos on applied AI product choices. By Vinay Roy.">
</picture>

One-page memos on real product decisions in applied AI: what the options were, the numbers, what was
picked, and what would change the answer.

Most writing about AI products covers what to build. These memos cover **how to choose**, with the
trade-offs and the "revisit if" conditions left in. Where a memo has numbers, the model that produced
them is in [`models/`](models/) so you can change the assumptions and rerun it.

Numbers are illustrative and company-agnostic. The reasoning is the point.

## Decisions

<p>
<a href="decisions/D-001-ticket-routing-rules-llm-hybrid.md"><picture><source media="(prefers-color-scheme: dark)" srcset=".github/assets/tile-d-001-dark.svg"><img src=".github/assets/tile-d-001-light.svg" width="32%" alt="D-001: rules, LLM, or hybrid for support ticket routing?"></picture></a>
<a href="decisions/D-002-how-many-evals-are-enough.md"><picture><source media="(prefers-color-scheme: dark)" srcset=".github/assets/tile-d-002-dark.svg"><img src=".github/assets/tile-d-002-light.svg" width="32%" alt="D-002: how many evals are enough?"></picture></a>
<a href="decisions/D-003-when-should-a-bi-bot-stay-quiet.md"><picture><source media="(prefers-color-scheme: dark)" srcset=".github/assets/tile-d-003-dark.svg"><img src=".github/assets/tile-d-003-light.svg" width="32%" alt="D-003: when should a BI bot answer, and when should it stay quiet?"></picture></a>
</p>

### Coming next

| ID | Decision |
| --- | --- |
| D-004 | Rules or an LLM classifier for prompt-injection screening? |
| D-005 | RAG or long context for a policy knowledge base? |
| D-006 | One model, or route between a small and a large one? |
| D-007 | Structured output or free text for customer-facing answers? |
| D-008 | When is fine-tuning worth it? |
| D-009 | Should an agent explain its decision to the user? |

## Format

Every memo follows [`TEMPLATE.md`](TEMPLATE.md): Context, Options, Evidence, Decision, Why,
Trade-offs accepted, Revisit if. One page, no more.

## About

<a href="https://www.linkedin.com/in/royvinay"><picture><source media="(prefers-color-scheme: dark)" srcset=".github/assets/about-dark.svg"><img src=".github/assets/about-light.svg" width="100%" alt="About Vinay Roy: VP of Product at Burq.ai, leading Product and AI. Career from NVIDIA (2008), Qualcomm, Apple (Sidecar), Zeus Living, Vista, and a founding product role at an AI SaaS startup, to Burq.ai. Seven years as Head Instructor for the AI/ML executive program at UC Berkeley Executive Education. 3 US patents, MBA from Berkeley Haas, MS from IIT Roorkee."></picture></a>

Writing on [Substack](https://vinayroy.substack.com) and [Medium](https://vinaysays.medium.com). More projects at [github.com/roy-vinay](https://github.com/roy-vinay).

Related: [production-agent-patterns](https://github.com/roy-vinay/production-agent-patterns), runnable
code for the patterns these decisions lean on, and [enterprise-ai-platform](https://github.com/roy-vinay/enterprise-ai-platform),
the eval harness behind D-003.

## License

Memos: CC BY 4.0. Code: MIT.
