"""Review-round model behind D-004. Standard library only.

    python models/d004_review_rounds.py

Question: in regulated marketing, does an AI content agent cut time to approval
more by generating better drafts, by checking written brand rules, or by also
learning each reviewer's unwritten rules from their past corrections?

Every number below is an assumption, chosen to be plausible and stated so you
can change it. The point is the shape of the result and the break-even, not the
exact values.

How a campaign moves through review
  - It carries some objections a reviewer would raise (Poisson, mean OBJECTIONS).
  - Each objection is one of three kinds:
      written   breaks a documented brand or legal rule (missing disclaimer, contrast)
      repeat    an unwritten rule this reviewer has applied before ("no 'guaranteed'")
      novel     a genuine judgment call nobody could have predicted
  - Before review, the agent may remove some objections:
      written   caught by deterministic checks with probability RULE_RECALL
      repeat    caught by a reviewer-taught lesson with probability LESSON_RECALL
      novel     never caught before review
  - Each round, the reviewer spots each remaining objection with probability
    SPOT_RATE (reviewers skim; a miss surfaces next round). Every spotted
    objection is fixed, correctly with probability FIX_OK.
  - Review ends on the first round where the reviewer finds nothing. If an
    objection is still in it at that point, it shipped past review: an escape.
  - Each round costs WAIT_DAYS of queue time plus FIX_DAYS if anything was found.
"""

import math
import random

SEED = 7
CAMPAIGNS = 20_000

OBJECTIONS = 2.2            # mean objections per campaign before any pre-review
MIX = {"written": 0.30, "repeat": 0.45, "novel": 0.25}
SPOT_RATE = 0.75           # reviewer opens the whole file and skims
FOCUSED_SPOT_RATE = 0.92   # reviewer gets one highlighted decision with context
FIX_OK = 0.9
FIX_DAYS = 0.3

RULE_RECALL = 0.95          # deterministic checks are reliable on written rules
LESSON_RECALL = 0.70        # retrieval of the right lesson for the right reviewer

OPTIONS = {
    #  name                                   rules  lessons  wait  spot rate
    "A  Better generation only":             (False, False, 1.5, SPOT_RATE),
    "B  + Written-rule checks":              (True,  False, 1.5, SPOT_RATE),
    "C  + Reviewer-taught lessons, nudges":  (True,  True,  1.0, SPOT_RATE),
    "D  + Focused one-decision review":      (True,  True,  1.0, FOCUSED_SPOT_RATE),
}


def poisson(rng, lam):
    limit, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= limit:
            return k
        k += 1


def one_campaign(rng, rules, lessons, wait, spot, lesson_recall):
    remaining = 0
    for _ in range(poisson(rng, OBJECTIONS)):
        kind = rng.choices(list(MIX), weights=list(MIX.values()))[0]
        if kind == "written" and rules and rng.random() < RULE_RECALL:
            continue
        if kind == "repeat" and lessons and rng.random() < lesson_recall:
            continue
        remaining += 1
    rounds, days = 0, 0.0
    while True:
        rounds += 1
        days += wait
        found = sum(rng.random() < spot for _ in range(remaining))
        if found == 0:
            # Approved. If anything is left, the reviewer missed it: an escape.
            return rounds, days, remaining > 0
        days += FIX_DAYS
        remaining -= found
        remaining += sum(rng.random() > FIX_OK for _ in range(found))


def run(rules, lessons, wait, spot=SPOT_RATE, lesson_recall=LESSON_RECALL):
    rng = random.Random(SEED)
    rs, ds, escapes = [], [], 0
    for _ in range(CAMPAIGNS):
        r, d, escaped = one_campaign(rng, rules, lessons, wait, spot, lesson_recall)
        escapes += escaped
        rs.append(r)
        ds.append(d)
    ds.sort()
    n = len(rs)
    return {
        "mean_rounds": sum(rs) / n,
        "first_pass": sum(r == 1 for r in rs) / n,
        "three_plus": sum(r >= 3 for r in rs) / n,
        "p90_days": ds[int(0.9 * n)],
        "escapes": escapes / n,
    }


def row(name, m, base):
    cut = 1 - m["mean_rounds"] / base["mean_rounds"]
    print(f"{name:40} {m['mean_rounds']:7.2f} {cut:6.0%} {m['first_pass']:9.0%} {m['three_plus']:8.0%}"
          f" {m['p90_days']:9.1f} {m['escapes']:8.1%}")


def main():
    print(f"{CAMPAIGNS:,} simulated campaigns per option, seed {SEED}\n")
    print(f"{'Option':40} {'Rounds':>7} {'Cut':>6} {'1st pass':>9} {'3+ rnds':>8} {'p90 days':>9} {'Escapes':>8}")
    base = run(*OPTIONS["A  Better generation only"])
    for name, args in OPTIONS.items():
        row(name, run(*args), base)
    print("\nFloor: every campaign needs at least one round, so the most any option can cut is "
          f"{1 - 1 / base['mean_rounds']:.0%}.")

    print("\nWhat it takes to halve rounds (option D, varying lesson recall)")
    for rec in (0.0, 0.5, 0.7, 0.9):
        m = run(True, True, 1.0, FOCUSED_SPOT_RATE, rec)
        print(f"  recall {rec:.0%}: {1 - m['mean_rounds'] / base['mean_rounds']:.0%} fewer rounds, "
              f"first pass {m['first_pass']:.0%}")

    print("\nIf most objections are novel judgment calls (written/repeat/novel = 20/20/60)")
    saved = dict(MIX)
    MIX.update({"written": 0.2, "repeat": 0.2, "novel": 0.6})
    a2 = run(False, False, 1.5)
    d2 = run(True, True, 1.0, FOCUSED_SPOT_RATE)
    print(f"  A {a2['mean_rounds']:.2f} rounds, D {d2['mean_rounds']:.2f} rounds, "
          f"{1 - d2['mean_rounds'] / a2['mean_rounds']:.0%} fewer")
    MIX.update(saved)

    print("\nBest case tried: few novel calls and strong recall (written/repeat/novel = 35/55/10, recall 90%)")
    MIX.update({"written": 0.35, "repeat": 0.55, "novel": 0.10})
    a3 = run(False, False, 1.5)
    d3 = run(True, True, 1.0, FOCUSED_SPOT_RATE, 0.9)
    print(f"  A {a3['mean_rounds']:.2f} rounds, D {d3['mean_rounds']:.2f} rounds, "
          f"{1 - d3['mean_rounds'] / a3['mean_rounds']:.0%} fewer")
    MIX.update(saved)


if __name__ == "__main__":
    main()
