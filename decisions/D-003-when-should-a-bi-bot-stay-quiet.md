# D-003: When should a BI bot answer, and when should it stay quiet?

**Status:** Decided (no launch yet) · **Area:** Evaluation, trust, cost · **Model:** [`models/d003_when_to_abstain.py`](../models/d003_when_to_abstain.py)

## Context

A BI chat bot turns business questions into SQL and replies with a number. People act on that number, and
nothing about a wrong answer looks wrong: it is formatted the same, arrives just as fast, and usually comes
from SQL that runs. The usual scorecard asks "how accurate is it?" The decision a product owner faces is
different: for each answer, show it, or hand the question to an analyst? And what evidence is enough to
start showing answers at all?

## Options

| | Gate | Shows the bot's answer when | Model calls |
| --- | --- | --- | --- |
| A | None | it answered and the SQL ran | 1 |
| B | Agreement | all 3 runs give the same action and the same result values | 3 |
| C | Abstain | never | 0 |
| D | Deterministic checks | one run's SQL passes rule checks for known failure modes | 1 |
| E | Agreement + checks | both B and D pass | 3 |

"Agreement" here means the same numbers, not the same SQL or the same business interpretation. Two runs can
agree on a number while both apply the wrong definition, which is exactly how unanimous errors happen.
The checks cover snapshot metrics summed over time, missing test-account and soft-delete filters, filter
values the question never mentioned, and missing date filters.

## Evidence

Two local models (qwen2.5-coder 3B and 7B) on a 28-question trap set over a synthetic B2B SaaS warehouse,
3 runs each, graded by the [text-to-SQL eval](https://github.com/roy-vinay/enterprise-ai-platform/tree/main/evals/text-to-sql).
A wrong number costs 1 to 5 by business impact (5 = critical). Every question that ends without a number
costs one hand-off, including correct refusals, because a person still picks it up. A query that fails to
run counts as a hand-off, not a wrong answer.

7B, at a hand-off cost of 1, inference excluded:

| Gate | Answers shown | Wrong (95% CI) | Severity | Critical | Hand-offs | Calls | Cost |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| A None | 19 | 7, 37% (19 to 59%) | 25 | 2 | 9 | 28 | 34 |
| B Agreement | 13 | 4, 31% (13 to 58%) | 14 | 1 | 15 | 84 | 29 |
| C Abstain | 0 | n/a | 0 | 0 | 28 | 0 | 28 |
| D Checks | 12 | 1, 8% (1 to 35%) | 3 | 0 | 16 | 28 | **19** |
| E Agreement + checks | 8 | 1, 12% (2 to 47%) | 3 | 0 | 20 | 84 | 23 |

- **Agreement is never the cheapest gate**, at any hand-off cost, for either model. With checks in place it
  only removes correct answers (12 shown to 8, same single error).
- **Checks catch known SQL mistakes, not definitions.** Three errors the 7B model made the same way on every
  run: it summed twelve monthly MRR snapshots into "2025 MRR" (about 10x), dropped the test-account filter
  (MRR about 3% high), and counted 581 "active" accounts instead of the 405 paying today. The checks catch the
  first two. The third is the one error that survives every gate.
- **The 3B model fails every gate:** even with checks, 5 of its 12 shown answers are wrong.
- **These checks are in-sample.** They were written against this same trap set, so D and E are a hypothesis
  to validate, not a measured result. 12 shown answers can't establish a launch threshold either: the 95%
  interval on D's error rate runs from 1% to 35%.
- Not measured: latency, and whether a clarifying question actually resolved the ambiguity (a clarification
  counts as correct when the case allows one).

## Decision

**Do not enable automated answers yet. Take deterministic checks (D) forward as the candidate gate, and drop
three-run agreement.** At a hand-off cost of 1, D is the cheapest observed policy for the 7B model, but the
evidence is in-sample. The 3B model should not answer anyone.

Before enabling answers:

- Freeze the gate, then evaluate it on held-out questions split by question family, so paraphrases of a
  training question can't leak into the test set.
- Add a sample of real workload questions, weighted by how often they are asked; a trap set over-represents
  hard cases and can't estimate production economics on its own.
- Require, for the intended use: no critical errors in the release suite, a shown-answer error rate whose upper
  confidence bound is under an agreed limit, enough coverage to be worth it, and an analyst queue the team
  can absorb.
- Report coverage, wrong answers with intervals, severity, hand-offs, inference cost and latency together.

## Why

1. **An interesting result is not evidence to ship.** The experiment shows which gate looks best on 28
   questions the checks were designed around. It does not show the remaining error rate is acceptable.
2. **Cheap, specific checks beat repeated sampling.** Three runs cost three times as much and catch fewer
   errors, because a model that misreads a definition tends to misread it the same way every time.
3. **What is left after the checks is definitional.** "Active accounts" is ambiguous; the right move is a
   metric definition or a clarifying question, not another gate.

## Trade-offs accepted

- More than half of questions still go to an analyst under D (16 of 28 for 7B).
- The checks need maintaining: every new metric or filter convention needs a rule, or it becomes a blind spot.
- Severity weights and the hand-off price are assumptions; the crossover points move with them (D stays
  cheapest for 7B between hand-off costs of about 0.3 and 3.1, inference excluded).
- 28 questions, two small local models, one synthetic warehouse. Directional only.

## Revisit if

- The held-out evaluation puts D's upper error bound above the agreed limit, or shows any critical error.
- Definitional errors dominate what gets through. Invest in metric definitions and clarification, not gates.
- A new failure mode appears that rules can't express. Then a second, independent signal (such as an
  interpretation check by a different model) may earn its cost, where repeated sampling did not.

## What I'd tell a team starting this

Price two things before arguing about accuracy: a wrong number shown to a decision maker, and a question
handed to an analyst. Then write checks for the mistakes you already know about, and test the gate on
questions it was not built from. Agreement between runs feels like confidence; on this evidence it mostly
isn't.
