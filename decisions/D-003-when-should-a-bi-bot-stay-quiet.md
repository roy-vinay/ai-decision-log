# D-003: When should a BI bot answer, and when should it stay quiet?

**Status:** Decided · **Area:** Evaluation, trust · **Model:** [`models/d003_when_to_abstain.py`](../models/d003_when_to_abstain.py)

## Context

A BI chat bot turns business questions into SQL and replies with a number. People act on that number, and
nothing about a wrong answer looks wrong: it is formatted the same, arrives just as fast, and usually comes
from SQL that runs. The usual scorecard asks "how accurate is it?" The decision a product owner actually
faces is different: for each answer, show it, or hand the question to an analyst?

## Options

| | Option | How it works |
| --- | --- | --- |
| A | Answer | Show whatever the bot answers. Measure accuracy. |
| B | Gate on agreement | Ask 3 times. Show the answer only if all 3 runs agree; otherwise hand off. |
| C | Abstain | Never show a number; route every question to an analyst. |

## Evidence

Two local models (qwen2.5-coder 3B and 7B) on a 28-question trap set over a synthetic B2B SaaS warehouse,
3 runs each, graded by the [text-to-SQL eval](https://github.com/roy-vinay/enterprise-ai-platform/tree/main/evals/text-to-sql).
Each wrong answer costs 1 to 5 by business impact; each hand-off costs 1.

| | 3B | 7B |
| --- | ---: | ---: |
| Accuracy on answerable questions | 15% | 50% |
| Correct clarify or refuse | 50% | 62% |
| Wrong answers that were unanimous across runs | 20% | 42% |
| Cost: A (answer) | 66 | 44 |
| Cost: B (gate on agreement) | 28 | 25 |
| Cost: C (abstain) | **20** | **20** |
| B beats C once a hand-off costs more than | 3.7 | 1.4 |

Three wrong answers the 7B model gave the same way on every run:

- **"What was total MRR in 2025?"** It summed twelve monthly snapshots into one number, roughly 10x real MRR.
- **"How many active accounts do we have?"** It returned 581, every account that ever paid, not the 405 paying today.
- **"MRR by plan in September 2026"** It dropped the internal test-account filter and overstated MRR by about 3%: small enough to look right, wrong enough to matter in a board deck.

## Decision

**B, gate on agreement, but only for a model good enough that gated answers clear the hand-off cost.**
Below that bar, C. Never A.

## Why

1. **Answering everything is the most expensive option for both models.** A confident wrong number costs
   more than a slow right one.
2. **Agreement is a useful gate, and a weakening one.** Requiring unanimity cuts the cost of answering by 43 to 58%,
   but the better model's errors are more often unanimous (42% vs 20%). Stronger models fail consistently,
   so the gate catches less of what is left.
3. **Whether to ship depends on the hand-off cost, not on accuracy.** The 7B model is worth showing once an
   analyst follow-up costs more than about 1.4 units. The 3B model needs 3.7, close to the price of
   the worst wrong answer, so it should not be answering anyone.

## Trade-offs accepted

- Three runs per question triples model cost and latency.
- With the 7B model, about a third of answerable questions still go to an analyst, and 5 of the 14 answers
  it does show are wrong.
- Unanimous wrong answers get through. Only the trap set and SQL rule checks catch those, so the gate does
  not replace the eval.
- 28 cases is small. On held-out halves, abstaining won both folds for both models at a hand-off cost of 1,
  so treat the crossover points as directional, not precise.

## Revisit if

- Unanimous answers fall below today's 64% accuracy on the trap set, or the hand-off cost drops below 1.4.
  The gate then costs more than it saves.
- A model's share of unanimous wrong answers keeps rising. Add a second, independent signal, such as an
  interpretation check by a different model, rather than more runs.
- Hand-off is cheap (a self-serve dashboard exists for the question). Abstaining wins outright.

## What I'd tell a team starting this

Before arguing about accuracy, price two things: a wrong number shown to a decision maker, and a question
handed to an analyst. The ratio between them decides whether the bot should be answering at all.
