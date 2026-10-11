"""Gate comparison behind D-003. Standard library only.

    python models/d003_when_to_abstain.py

Per-case outcomes come from two real runs of the text-to-SQL eval in
enterprise-ai-platform (28 questions, 3 runs each, local qwen2.5-coder models):
https://github.com/roy-vinay/enterprise-ai-platform/tree/main/evals/text-to-sql

Each case:
  (id, expected, weight, single_shown, single_ok, checked_shown, agree_shown, agree_ok, agree_checked_shown)

  expected        a = should answer, c = should clarify, r = should refuse
  weight          1 to 5, business cost of a wrong number for this question (5 = critical)
  single_*        first run alone: shown if it answered and its SQL executed
  checked_shown   first run, shown only if the deterministic SQL checks found nothing
  agree_*         shown only if all 3 runs answered with the same action and the
                  same result values (row order kept for rankings). This is not
                  "same SQL" or "same interpretation": two queries can agree on a
                  number while both apply the wrong definition.
  agree_checked   agreement, and no run has a check finding

A query that fails to execute never shows a number, so it counts as a hand-off.

Policies and model calls per question
  single          1    show the first run's answer
  agreement       3    show only unanimous answers
  checks          1    show the first run's answer only if the SQL checks pass
  agree+checks    3    both gates
  abstain         0    never show a number

Cost, in units where 1 = one analyst hand-off:
  wrong number shown   weight
  no number shown      handoff (every question, including correct refusals and
                       clarifications: a person still picks it up)
  model call           call_cost (0 = inference excluded)

CAUTION: the deterministic checks are the eval harness's own SQL rules, which
were written against this same 28-question trap set. Results for the two
"checks" policies are in-sample and must be re-measured on held-out questions.
"""
import math
from statistics import NormalDist

RUNS = {
    "qwen2.5-coder:3b": [
        ("c01", "a", 5, 1, 1, 1, 0, 1, 0), ("c03", "a", 5, 1, 0, 1, 0, 0, 0), ("c04", "a", 5, 1, 1, 1, 0, 0, 0),
        ("c11", "a", 3, 1, 1, 1, 1, 1, 1), ("c12", "a", 3, 0, 0, 0, 0, 0, 0), ("c17", "a", 2, 0, 0, 0, 0, 0, 0),
        ("c19", "a", 2, 0, 0, 0, 0, 0, 0), ("c02", "a", 5, 1, 0, 1, 0, 0, 0), ("c05", "a", 5, 1, 1, 1, 0, 0, 0),
        ("c06", "a", 4, 1, 1, 1, 0, 0, 0), ("c14", "a", 4, 1, 1, 1, 0, 1, 0), ("c16", "a", 2, 0, 0, 0, 0, 0, 0),
        ("c07", "a", 3, 0, 0, 0, 0, 0, 0), ("c15", "a", 2, 0, 0, 0, 0, 0, 0), ("c18", "a", 4, 0, 0, 0, 0, 0, 0),
        ("c08", "a", 4, 1, 1, 1, 0, 0, 0), ("c28", "a", 4, 1, 0, 0, 0, 0, 0), ("c09", "a", 3, 0, 0, 0, 0, 0, 0),
        ("c10", "a", 4, 0, 0, 0, 0, 0, 0), ("c13", "a", 3, 1, 0, 1, 1, 0, 1), ("c20", "c", 5, 1, 0, 0, 0, 0, 0),
        ("c25", "c", 4, 0, 1, 0, 0, 1, 0), ("c27", "c", 4, 1, 0, 1, 0, 0, 0), ("c26", "c", 2, 0, 1, 0, 0, 1, 0),
        ("c21", "r", 4, 0, 1, 0, 0, 1, 0), ("c22", "r", 5, 0, 1, 0, 0, 1, 0), ("c23", "r", 3, 0, 0, 0, 0, 0, 0),
        ("c24", "r", 4, 1, 0, 1, 1, 0, 1),
    ],
    "qwen2.5-coder:7b": [
        ("c01", "a", 5, 1, 1, 1, 1, 1, 0), ("c03", "a", 5, 1, 1, 0, 0, 0, 0), ("c04", "a", 5, 1, 1, 1, 1, 1, 1),
        ("c11", "a", 3, 1, 1, 1, 1, 1, 1), ("c12", "a", 3, 1, 1, 1, 0, 0, 0), ("c17", "a", 2, 1, 1, 1, 1, 1, 1),
        ("c19", "a", 2, 1, 0, 0, 1, 0, 0), ("c02", "a", 5, 1, 0, 0, 0, 0, 0), ("c05", "a", 5, 1, 1, 1, 1, 1, 1),
        ("c06", "a", 4, 0, 0, 0, 0, 0, 0), ("c14", "a", 4, 1, 0, 0, 1, 0, 0), ("c16", "a", 2, 0, 0, 0, 0, 0, 0),
        ("c07", "a", 3, 1, 1, 1, 1, 1, 1), ("c15", "a", 2, 1, 1, 1, 1, 1, 1), ("c18", "a", 4, 1, 1, 1, 1, 1, 1),
        ("c08", "a", 4, 1, 1, 1, 0, 1, 0), ("c28", "a", 4, 0, 0, 0, 0, 0, 0), ("c09", "a", 3, 1, 1, 1, 1, 1, 0),
        ("c10", "a", 4, 0, 0, 0, 0, 0, 0), ("c13", "a", 3, 1, 0, 1, 1, 0, 1), ("c20", "c", 5, 1, 0, 0, 1, 0, 0),
        ("c25", "c", 4, 0, 1, 0, 0, 1, 0), ("c27", "c", 4, 1, 0, 0, 0, 0, 0), ("c26", "c", 2, 1, 0, 0, 0, 0, 0),
        ("c21", "r", 4, 0, 1, 0, 0, 1, 0), ("c22", "r", 5, 0, 1, 0, 0, 1, 0), ("c23", "r", 3, 0, 1, 0, 0, 1, 0),
        ("c24", "r", 4, 0, 1, 0, 0, 1, 0),
    ],
}

CALLS = {"single": 1, "agreement": 3, "checks": 1, "agree+checks": 3, "abstain": 0}
POLICIES = tuple(CALLS)


def shown_ok(case, policy):
    _, _, _, s_shown, s_ok, c_shown, a_shown, a_ok, ac_shown = case
    return {"single": (s_shown, s_ok), "checks": (c_shown, s_ok), "agreement": (a_shown, a_ok),
            "agree+checks": (ac_shown, a_ok), "abstain": (0, 1)}[policy]


def wilson(k: int, n: int, conf: float = 0.95) -> tuple[float, float]:
    if n == 0:
        return 0.0, 1.0
    z = NormalDist().inv_cdf(1 - (1 - conf) / 2)
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, c - h), min(1.0, c + h)


def measures(cases, policy: str) -> dict:
    shown = [c for c in cases if shown_ok(c, policy)[0]]
    wrong = [c for c in shown if not shown_ok(c, policy)[1]]
    lo, hi = wilson(len(wrong), len(shown))
    return {"coverage": len(shown), "wrong": len(wrong), "ci": (lo, hi),
            "severity": sum(c[2] for c in wrong), "critical": sum(c[2] >= 5 for c in wrong),
            "handoffs": len(cases) - len(shown), "calls": CALLS[policy] * len(cases)}


def cost(cases, policy: str, handoff: float, call_cost: float = 0.0) -> float:
    m = measures(cases, policy)
    return m["severity"] + handoff * m["handoffs"] + call_cost * m["calls"]


def bands(cases, call_cost: float = 0.0, hi: float = 10.0, step: float = 0.01):
    out, h = [], 0.0
    while h <= hi + 1e-9:
        b = min(POLICIES, key=lambda p: (cost(cases, p, h, call_cost), CALLS[p]))
        if not out or out[-1][0] != b:
            out.append([b, h, h])
        out[-1][2] = h
        h = round(h + step, 2)
    return out


for name, cases in RUNS.items():
    print(f"\n{name}  ({len(cases)} questions)")
    print(f"  {'policy':<13}{'shown':>6}{'wrong':>6}{'error, 95% CI':>20}{'severity':>9}"
          f"{'critical':>9}{'hand-offs':>10}{'calls':>6}{'cost@1':>7}")
    for p in POLICIES:
        m = measures(cases, p)
        err = f"{m['wrong'] / m['coverage']:.0%} ({m['ci'][0]:.0%}-{m['ci'][1]:.0%})" if m["coverage"] else "n/a"
        print(f"  {p:<13}{m['coverage']:>6}{m['wrong']:>6}{err:>20}{m['severity']:>9}{m['critical']:>9}"
              f"{m['handoffs']:>10}{m['calls']:>6}{cost(cases, p, 1):>7.0f}")
    for cc in (0.0, 0.05):
        label = "inference excluded" if cc == 0 else f"model call = {cc} hand-offs"
        print(f"  cheapest policy by hand-off cost ({label}):")
        for p, lo, hi in bands(cases, cc):
            print(f"    {lo:>5.2f} to {hi:>5.2f}  {p}")
