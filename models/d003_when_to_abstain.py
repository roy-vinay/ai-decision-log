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
  answer      ship whatever the bot answers
  unanimous   only show an answer when all 3 runs agree; otherwise hand off
  abstain     never show a number; every question goes to an analyst

Costs
  wrong answer shown       cost_weight
  answerable question      handoff_cost (an analyst picks it up)
    not shown
  correct clarify/refuse   0
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


def cost(cases, policy: str, handoff: float) -> float:
    total = 0.0
    for _, expected, weight, answered, correct, agreement in cases:
        shown = answered and (policy == "answer" or (policy == "unanimous" and agreement == 1.0))
        if shown and not correct:
            total += weight
        elif not shown and expected == "a":
            total += handoff
    return total


def stats(cases):
    answered = [c for c in cases if c[3]]
    wrong = [c for c in answered if not c[4]]
    confident_wrong = [c for c in wrong if c[5] == 1.0]
    unanimous = [c for c in answered if c[5] == 1.0]
    right_when_unanimous = sum(c[4] for c in unanimous)
    return {
        "accuracy on answerable": sum(c[4] for c in cases if c[1] == "a") / sum(c[1] == "a" for c in cases),
        "correct clarify/refuse": sum(c[4] for c in cases if c[1] != "a") / sum(c[1] != "a" for c in cases),
        "wrong answers shown (answer)": len(wrong),
        "wrong even though all runs agreed": len(confident_wrong),
        "share of wrong answers that were unanimous": len(confident_wrong) / len(wrong),
        "accuracy when all runs agree": right_when_unanimous / len(unanimous),
    }


def crossover(cases, policy: str) -> float | None:
    """Smallest handoff cost at which `policy` beats abstaining on everything."""
    h = 0.0
    while h <= 10:
        if cost(cases, policy, h) < cost(cases, "abstain", h):
            return h
        h = round(h + 0.05, 2)
    return None


for name, cases in RUNS.items():
    print(f"\n{name}")
    for k, v in stats(cases).items():
        print(f"  {k:<44} {v:.0%}" if isinstance(v, float) else f"  {k:<44} {v}")
    print("  cost by policy (handoff cost = 1, 2, 3):")
    for policy in ("answer", "unanimous", "abstain"):
        print(f"    {policy:<10}" + "".join(f"{cost(cases, policy, h):>7.0f}" for h in (1, 2, 3)))
    for policy in ("answer", "unanimous"):
        x = crossover(cases, policy)
        print(f"  '{policy}' beats abstaining once a handoff costs more than "
              f"{x:.2f}" if x is not None else f"  '{policy}' never beats abstaining (handoff up to 10)")
