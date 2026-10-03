# D-002: How many evals are enough?

**Status:** Decided · **Area:** Evaluation · **Model:** [`models/d002_eval_sample_size.py`](../models/d002_eval_sample_size.py)

## Context

Every team shipping an LLM feature asks this, usually after a prompt change "felt better" and then
broke something nobody tested. The honest answer depends on which question the evals are meant to answer:

1. **Did we break a rule?** A refund over the limit, a leaked prompt, a made-up policy. One failure is news.
2. **Did quality move?** Answers got slightly worse or better on average. That's a rate, and rates need sample size.

Most teams run one suite and expect it to answer both. It can't.

## Options

| | Option | How it works |
| --- | --- | --- |
| A | Small golden set only | 10 to 30 hand-written cases, run on every change |
| B | Large sampled set only | Hundreds of real conversations, scored by an LLM judge |
| C | Two suites | A small must-pass gate for rules, plus a large sampled set for quality rates |

## Evidence

From the model in this repo. Suppose a suite shows a **90% pass rate**. The true rate could be:

| Cases | Plausible true pass rate (95% confidence) |
| ---: | --- |
| 12 | 65% to 99% |
| 50 | 79% to 96% |
| 100 | 83% to 94% |
| 400 | 87% to 93% |
| 1,000 | 88% to 92% |

And to reliably catch a drop between two runs (95% confidence, 80% power):

| Drop to detect | Cases per run |
| --- | ---: |
| 95% to 80% | 60 |
| 95% to 90% | 343 |
| 95% to 93% | 1,743 |
| 99% to 97% | 605 |

A 12-case suite can't tell 70% from 99%. But a 12-case suite of **properties** ("never refund over
$50 without approval") doesn't need statistics: any failure is a real bug.

## Decision

**C, two suites.**

- **Gate:** 10 to 30 must-pass cases, each a property that can never fail, run on every commit in CI.
  One failure blocks the change. Example: the [12 trajectory evals](https://github.com/roy-vinay/applied-ai-agents/tree/main/production-patterns/guarded-support-agent)
  and fault-injection benchmark in applied-ai-agents.
- **Quality:** about 350 cases sampled from real traffic, scored by a calibrated LLM judge, run on every
  model or prompt change. That's enough to catch a 5-point drop.

## Why

1. **The two questions need different math.** Rules are pass/fail per case; quality is a rate with an error bar.
2. **Small gates are cheap and fast.** They run in seconds, so they run on every commit.
3. **350 is where rate checks become useful.** Below about 100 cases, normal run-to-run noise hides real regressions.

## Trade-offs accepted

- The quality suite costs LLM-judge calls on every run, and the judge itself needs monthly calibration
  against human grades.
- Drops smaller than about 5 points will slip through. Catching a 2-point drop takes 1,700+ cases per
  run; at that point a production A/B test is cheaper.
- Sampled cases go stale as traffic changes, so the set needs refreshing every quarter.

## Revisit if

- Failures cluster in one category. Stratify the sample so that category gets its own 350.
- The quality bar tightens to 2-point changes. Move rate measurement to production experiments.
- The judge disagrees with human graders on more than 10% of cases. Fix the judge before trusting any rate.

## What I'd tell a team starting this

Write the gate first: list the five things your feature must never do and turn each into a case. Then
count how many cases you'd need to notice the quality change you actually care about, before deciding
whether to build the big suite at all.
