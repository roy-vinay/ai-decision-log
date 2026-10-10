# AI Decision Log

One-page memos on real product decisions in applied AI: what the options were, the numbers, what was
picked, and what would change the answer.

Most writing about AI products covers what to build. These memos cover **how to choose**, with the
trade-offs and the "revisit if" conditions left in. Where a memo has numbers, the model that produced
them is in [`models/`](models/) so you can change the assumptions and rerun it.

Numbers are illustrative and company-agnostic. The reasoning is the point.

## Decisions

| ID | Decision | Area |
| --- | --- | --- |
| [D-001](decisions/D-001-ticket-routing-rules-llm-hybrid.md) | Rules, LLM, or hybrid for support ticket routing | Agent architecture, cost |
| [D-002](decisions/D-002-how-many-evals-are-enough.md) | How many evals are enough? | Evaluation |

### Coming next

| ID | Decision |
| --- | --- |
| D-003 | Rules or an LLM classifier for prompt-injection screening? |
| D-004 | RAG or long context for a policy knowledge base? |
| D-005 | One model, or route between a small and a large one? |
| D-006 | Structured output or free text for customer-facing answers? |
| D-007 | When is fine-tuning worth it? |
| D-008 | Should an agent explain its decision to the user? |

## Format

Every memo follows [`TEMPLATE.md`](TEMPLATE.md): Context, Options, Evidence, Decision, Why,
Trade-offs accepted, Revisit if. One page, no more.

## Author

[Vinay Roy](https://github.com/roy-vinay). VP of Product at Burq, Head Instructor for the AI/ML executive
program at UC Berkeley Executive Education. Writing on [Medium](https://vinaysays.medium.com) and
[Substack](https://vinayroy.substack.com).

Related: [production-agent-patterns](https://github.com/roy-vinay/production-agent-patterns), runnable
code for the patterns these decisions lean on.

## License

Memos: CC BY 4.0. Code: MIT.
