"""Cost model behind D-003. Standard library only.

    python models/d003_when_to_abstain.py

Per-case outcomes come from two real runs of the text-to-SQL eval in
enterprise-ai-platform (28 questions, 3 runs each, local qwen2.5-coder models):
https://github.com/roy-vinay/enterprise-ai-platform/tree/main/evals/text-to-sql

Each case: (id, expected, cost_weight, answered, correct, agreement)
  expected     a = should answer, c = should clarify, r = should refuse
  cost_weight  1 to 5, business cost of a confident wrong answer to this question
  answered     1 if the bot's majority action was to answer
  correct      1 if the case passed (right answer, or a correct clarify/refuse)
  agreement    share of the 3 runs that gave the most common answer

Policies
  answer      show whatever the bot answers (1 model call per question)
  unanimous   ask 3 times; show the answer only if all 3 runs agree,
              otherwise hand off (3 model calls per question)
  abstain     never show a number; every question goes to an analyst
              (0 model calls)

Costs, in units where 1 = the cost of one analyst hand-off unless stated
  wrong answer shown      cost_weight (1 to 5)
  no number shown         handoff, for EVERY question: a correct refusal or a
                          clarifying question still ends with a person
                          looking at it, as does a deliberate abstention
  model call              call_cost per call (set to 0 to exclude inference)

Approximation: the data has 3 runs per question, and "answer" uses the
majority answer as a stand-in for what a single run would show.
"""

RUNS = {
    "qwen2.5-coder:3b": [
        ("c01", "a", 5, 1, 1, .67), ("c03", "a", 5, 1, 0, .33), ("c04", "a", 5, 1, 0, .33),
        ("c11", "a", 3, 1, 1, 1.0), ("c12", "a", 3, 1, 0, .33), ("c17", "a", 2, 0, 0, 1.0),
        ("c19", "a", 2, 1, 0, .33), ("c02", "a", 5, 1, 0, .33), ("c05", "a", 5, 1, 0, .33),
        ("c06", "a", 4, 1, 0, .67), ("c14", "a", 4, 1, 1, .67), ("c16", "a", 2, 0, 0, .67),
        ("c07", "a", 3, 0, 0, 1.0), ("c15", "a", 2, 0, 0, .33), ("c18", "a", 4, 1, 0, 1.0),
        ("c08", "a", 4, 1, 0, .67), ("c28", "a", 4, 1, 0, .33), ("c09", "a", 3, 0, 0, 1.0),
        ("c10", "a", 4, 1, 0, .67), ("c13", "a", 3, 1, 0, 1.0), ("c20", "c", 5, 1, 0, .33),
        ("c25", "c", 4, 0, 1, 1.0), ("c27", "c", 4, 1, 0, .33), ("c26", "c", 2, 0, 1, 1.0),
        ("c21", "r", 4, 0, 1, .67), ("c22", "r", 5, 0, 1, 1.0), ("c23", "r", 3, 0, 0, 1.0),
        ("c24", "r", 4, 1, 0, 1.0),
    ],
    "qwen2.5-coder:7b": [
        ("c01", "a", 5, 1, 1, 1.0), ("c03", "a", 5, 1, 0, .33), ("c04", "a", 5, 1, 1, 1.0),
        ("c11", "a", 3, 1, 1, 1.0), ("c12", "a", 3, 1, 0, .67), ("c17", "a", 2, 1, 1, 1.0),
        ("c19", "a", 2, 1, 0, 1.0), ("c02", "a", 5, 1, 0, .67), ("c05", "a", 5, 1, 1, 1.0),
        ("c06", "a", 4, 1, 0, 1.0), ("c14", "a", 4, 1, 0, 1.0), ("c16", "a", 2, 1, 0, .67),
        ("c07", "a", 3, 1, 1, 1.0), ("c15", "a", 2, 1, 1, 1.0), ("c18", "a", 4, 1, 1, 1.0),
        ("c08", "a", 4, 1, 1, .67), ("c28", "a", 4, 1, 0, .33), ("c09", "a", 3, 1, 1, 1.0),
        ("c10", "a", 4, 0, 0, 1.0), ("c13", "a", 3, 1, 0, 1.0), ("c20", "c", 5, 1, 0, 1.0),
        ("c25", "c", 4, 0, 1, .67), ("c27", "c", 4, 1, 0, .67), ("c26", "c", 2, 1, 0, .67),
        ("c21", "r", 4, 0, 1, 1.0), ("c22", "r", 5, 0, 1, 1.0), ("c23", "r", 3, 0, 1, 1.0),
        ("c24", "r", 4, 0, 1, 1.0),
    ],
}


CALLS = {"answer": 1, "unanimous": 3, "abstain": 0}
POLICIES = tuple(CALLS)


def cost(cases, policy: str, handoff: float, call_cost: float = 0.0) -> float:
    total = CALLS[policy] * call_cost * len(cases)
    for _, expected, weight, answered, correct, agreement in cases:
        shown = answered and (policy == "answer" or (policy == "unanimous" and agreement == 1.0))
        if shown:
            total += 0 if correct else weight
        else:
            total += handoff
    return total


def best(cases, handoff: float, call_cost: float = 0.0) -> str:
    return min(POLICIES, key=lambda p: (cost(cases, p, handoff, call_cost), CALLS[p]))


def bands(cases, call_cost: float = 0.0, hi: float = 10.0, step: float = 0.01):
    """Which policy is cheapest across a range of hand-off costs."""
    out, h = [], 0.0
    while h <= hi + 1e-9:
        b = best(cases, h, call_cost)
        if not out or out[-1][0] != b:
            out.append([b, h, h])
        out[-1][2] = h
        h = round(h + step, 2)
    return out


def stats(cases):
    answered = [c for c in cases if c[3]]
    wrong = [c for c in answered if not c[4]]
    unanimous = [c for c in answered if c[5] == 1.0]
    return {
        "accuracy on answerable": sum(c[4] for c in cases if c[1] == "a") / sum(c[1] == "a" for c in cases),
        "correct clarify/refuse": sum(c[4] for c in cases if c[1] != "a") / sum(c[1] != "a" for c in cases),
        "numbers shown, answer / unanimous": f"{len(answered)} / {len(unanimous)}",
        "wrong answers that were unanimous": len([c for c in wrong if c[5] == 1.0]) / len(wrong),
        "accuracy when all runs agree": sum(c[4] for c in unanimous) / len(unanimous),
    }


for name, cases in RUNS.items():
    print(f"\n{name}")
    for k, v in stats(cases).items():
        print(f"  {k:<36} {v:.0%}" if isinstance(v, float) else f"  {k:<36} {v}")
    print("  cost by policy, hand-off = 1 / 2 / 4 (inference excluded):")
    for p in POLICIES:
        print(f"    {p:<10}" + "".join(f"{cost(cases, p, h):>7.0f}" for h in (1, 2, 4)))
    for cc in (0.0, 0.05):
        label = "inference excluded" if cc == 0 else f"model call = {cc} hand-offs"
        print(f"  cheapest policy by hand-off cost ({label}):")
        for p, lo, hi in bands(cases, cc):
            print(f"    {lo:>5.2f} to {hi:>5.2f}  {p}")
