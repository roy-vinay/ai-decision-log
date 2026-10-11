# D-003: When should a BI bot answer, and when should it stay quiet?

**Status:** Decided · **Area:** Evaluation, trust, cost · **Model:** [`models/d003_when_to_abstain.py`](../models/d003_when_to_abstain.py)

## Context

A BI chat bot turns business questions into SQL and replies with a number. People act on that number, and
nothing about a wrong answer looks wrong: it is formatted the same, arrives just as fast, and usually comes
from SQL that runs. The usual scorecard asks "how accurate is it?" The decision a product owner actually
faces is different: for each answer, show it, or hand the question to an analyst?

## Options

| | Option | How it works |
| --- | --- | --- |
| A | Answer | Show whatever the bot answers. One model call per question. |
| B | Gate on agreement | Ask 3 times. Show the answer only if all 3 runs agree; otherwise hand off. Three calls. |
| C | Abstain | Never show a number; every question goes to an analyst. No calls. |

## Evidence

Two local models (qwen2.5-coder 3B and 7B) on a 28-question trap set over a synthetic B2B SaaS warehouse,
3 runs each, graded by the [text-to-SQL eval](https://github.com/roy-vinay/enterprise-ai-platform/tree/main/evals/text-to-sql).
A wrong number shown costs 1 to 5 by business impact. Every question that ends without a number costs one
hand-off, including correct refusals, because a person still picks it up. Inference is excluded unless stated.

| | 3B | 7B |
| --- | ---: | ---: |
| Accuracy on answerable questions | 15% | 50% |
| Correct clarify or refuse | 50% | 62% |
| Wrong answers that were unanimous across runs | 20% | 42% |
| Accuracy when all 3 runs agree | 25% | 64% |
| Cost at hand-off = 1: A / B / C | 71 / 35 / **28** | 49 / 32 / **28** |
| Cheapest policy, hand-off below | C to 2.8 | C to 1.3 |
| Cheapest policy, hand-off between | B, 2.8 to 3.6 | B, 1.3 to 3.1 |
| Cheapest policy, hand-off above | A, 3.6 | A, 3.1 |

Pricing a model call at 0.05 hand-offs removes B entirely for 3B and narrows it to 1.6 to 2.8 for 7B.

Three wrong answers the 7B model gave the same way on every run:

- **"What was total MRR in 2025?"** It summed twelve monthly snapshots into one number, roughly 10x real MRR.
- **"How many active accounts do we have?"** It returned 581, every account that ever paid, not the 405 paying today.
- **"MRR by plan in September 2026"** It dropped the internal test-account filter and overstated MRR by about 3%: small enough to look right, wrong enough to matter in a board deck.

## Decision

**Choose by the price of a hand-off relative to a wrong number, not by accuracy.** For the 7B model: abstain
below about 1.3, gate on agreement between 1.3 and 3.1, and answer directly only above 3.1. Ship the 3B model
to no one.

## Why

1. **The ratio decides, not the model.** With hand-offs and wrong answers priced on the same scale, every
   policy wins somewhere. A team needs that ratio before it needs a leaderboard.
2. **Answering everything only wins when a hand-off costs more than a mid-severity wrong answer.** That can
   be true (no analysts, a decision that can't wait), but it is a statement about the organization, not the bot.
3. **Agreement gating is useful and has limits.** It cut the cost of answering by a third to a half here. In
   these two runs the better model's errors were more often unanimous (42% vs 20%), so the gate caught less
   of what was left. Two runs can't show that this holds generally.

## Trade-offs accepted

- Three runs per question triples model cost and latency, which shrinks the range where B wins.
- With the 7B model, 7 of 20 answerable questions still go to an analyst, and 5 of the 14 answers it does
  show are wrong.
- Unanimous wrong answers get through. Only the trap set and SQL rule checks catch those, so the gate does
  not replace the eval.
- The "answer" policy is approximated from the majority of 3 runs, not a true single run.
- 28 cases is small; treat the crossover points as directional, not precise.

## Revisit if

- Accuracy when all runs agree falls below today's 64%. The gate then leaks too much.
- The share of unanimous wrong answers keeps rising in newer models. Add a second, independent signal, such
  as an interpretation check by a different model, rather than more runs.
- The cost of a hand-off changes: a self-serve dashboard makes it cheaper (abstain wins wider), losing the
  analyst makes it dearer (answering wins wider).

## What I'd tell a team starting this

Before arguing about accuracy, price two things: a wrong number shown to a decision maker, and a question
handed to an analyst. The ratio between them decides whether the bot should be answering at all.
