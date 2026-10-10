# D-001: Rules, LLM, or hybrid for support ticket routing

**Status:** Decided · **Area:** Agent architecture, cost · **Model:** [`models/d001_cost_model.py`](../models/d001_cost_model.py)

## Context

A support team gets 20,000 tickets a day, and each one has to land with the right team: billing,
technical, account access, shipping, and so on. A misrouted ticket gets handed off, which costs roughly
8 minutes of extra agent time (about $6) and makes the customer wait longer. Most tickets are routine,
with one clear issue in clear words. About 15% are not: two problems in one message, an angry wall of
text, a vague "it doesn't work", or a language the keyword rules weren't written for.

The question teams ask first is "should an LLM route our tickets?" The more useful question is: **where
does reading for meaning beat matching keywords, and what does it cost to be wrong there?**

## Options

| | Option | How it works |
| --- | --- | --- |
| A | Rules only | Keywords, form fields, and customer tier pick the team. Deterministic, instant. |
| B | LLM on every ticket | A model reads the ticket and the routing guide and returns a team and a reason. |
| C | Hybrid | Rules route everything. A trigger (low rules confidence, several matching teams, very long or non-English text) sends the ticket to the LLM, which must choose from the real team list. |

## Evidence

Illustrative numbers from the cost model. Change the assumptions and rerun it.

| Option | LLM share | Misroutes | Inference / mo | Misroute cost / mo | Total / mo |
| --- | ---: | ---: | ---: | ---: | ---: |
| A. Rules only | 0% | 8.65% | $0 | $311,400 | $311,400 |
| B. LLM everywhere | 100% | 6.05% | $720 | $217,800 | $218,520 |
| **C. Hybrid** | **19.6%** | **5.79%** | **$141** | **$208,278** | **$208,419** |

Key assumptions: a mid-tier model at about $0.0012 per ticket (900 tokens in, 60 out). Rules misroute
35% of non-routine tickets and the LLM 12%. On routine tickets rules are slightly *better* (4% vs 5%),
because keywords don't get creative. The trigger catches 85% of non-routine tickets and wrongly flags 8%
of routine ones.

## Decision

**C, hybrid.** Rules route the routine tickets; the LLM reads the ones where meaning matters.

## Why

1. **Errors concentrate in the messy slice.** 15% of tickets cause 61% of the rules engine's misroutes.
   That's where reading for meaning pays off. Everywhere else the model only adds variance.
2. **Inference cost is no longer the argument.** Even sending every ticket to the LLM costs about $720 a
   month, against $200,000 or more in misroutes. The choice between B and C is about quality and
   control, not the model bill. Teams still debate token costs out of habit.
3. **Hybrid beats LLM-everywhere on quality.** It keeps the rules engine's edge on routine tickets
   instead of trading it away.
4. **Auditability.** About 80% of routing stays deterministic and replayable, so a team lead can explain
   why a ticket went where it did without reading a model's reasoning. The LLM can only pick from the
   real team list, so it can't invent a queue.

## Trade-offs accepted

- Two systems to maintain, and a trigger that needs its own monitoring.
- Flagged tickets take a second or two longer to route. Customers won't notice; dashboards will.
- The 15% of messy tickets the trigger misses still get the rules engine's weaker answer.

## Revisit if

- The non-routine share passes about 35% (a new product, a new market, a new language). Then the trigger
  is the main path, and B's simplicity may be worth more than C's small quality edge.
- A monthly audit shows trigger recall below 75%. Fix the trigger before blaming the model.
- The LLM's routine-ticket error rate drops below the rules engine's. Then rules are only there for
  audit, and B wins.

## What I'd tell a team starting this

Don't open with the architecture debate. Pull 500 misrouted tickets and label *why* each went wrong. If
most are keyword rules failing on unusual tickets, you have a hybrid. If they're spread evenly, fix the
rules first; a model won't rescue a routing guide nobody has updated in a year.
