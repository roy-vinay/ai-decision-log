"""Cost model behind D-001 (support ticket routing). Every number is an assumption you can change.

    python models/d001_cost_model.py
"""
TICKETS_PER_DAY = 20_000
MISROUTE_COST = 6.00           # $ per misrouted ticket: about 8 minutes of extra agent time at $45/hr
                               # for the hand-off, plus a longer wait for the customer
PRICE_IN, PRICE_OUT = 1.00, 5.00   # $ per million tokens, mid-tier model list price (check current)
TOKENS_IN, TOKENS_OUT = 900, 60    # ticket text, team list, routing guide; a short JSON answer

ROUTINE = 0.85                 # share of tickets that are routine: one clear issue, clear wording
MISROUTE = {                   # misroute rate by engine and segment
    "rules": {"routine": 0.04, "non_routine": 0.35},
    "llm":   {"routine": 0.05, "non_routine": 0.12},
}
TRIGGER_RECALL = 0.85          # hybrid: share of non-routine tickets the trigger sends to the LLM
TRIGGER_FALSE_POS = 0.08       # hybrid: share of routine tickets sent to the LLM anyway

llm_cost = TOKENS_IN * PRICE_IN / 1e6 + TOKENS_OUT * PRICE_OUT / 1e6
nr = 1 - ROUTINE


def option(llm_share_routine, llm_share_nr):
    bad = (ROUTINE * ((1 - llm_share_routine) * MISROUTE["rules"]["routine"] + llm_share_routine * MISROUTE["llm"]["routine"])
           + nr * ((1 - llm_share_nr) * MISROUTE["rules"]["non_routine"] + llm_share_nr * MISROUTE["llm"]["non_routine"]))
    llm_share = ROUTINE * llm_share_routine + nr * llm_share_nr
    inference = TICKETS_PER_DAY * llm_share * llm_cost * 30
    misroutes = TICKETS_PER_DAY * bad * MISROUTE_COST * 30
    return llm_share, bad, inference, misroutes


rows = {
    "A. Rules only": option(0, 0),
    "B. LLM on every ticket": option(1, 1),
    "C. Hybrid (rules + LLM on flagged tickets)": option(TRIGGER_FALSE_POS, TRIGGER_RECALL),
}
print(f"LLM cost per ticket: ${llm_cost:.5f}\n")
print(f"{'Option':44}{'LLM share':>10}{'Misroutes':>11}{'Inference/mo':>14}{'Misroutes/mo':>14}{'Total/mo':>12}")
for name, (share, bad, inf, fail) in rows.items():
    print(f"{name:44}{share:>10.1%}{bad:>11.2%}{inf:>14,.0f}{fail:>14,.0f}{inf + fail:>12,.0f}")
rules_bad_nr = nr * MISROUTE["rules"]["non_routine"]
print(f"\nNon-routine tickets are {nr:.0%} of volume but {rules_bad_nr / option(0, 0)[1]:.0%} of rules-only misroutes.")
