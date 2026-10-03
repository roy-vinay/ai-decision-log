"""Sample-size math behind D-002. Standard library only.

    python models/d002_eval_sample_size.py
"""
from math import sqrt
from statistics import NormalDist

Z = NormalDist().inv_cdf


def wilson(passes: int, n: int, conf: float = 0.95) -> tuple[float, float]:
    """Wilson score interval for a pass rate."""
    z = Z(1 - (1 - conf) / 2)
    p = passes / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return centre - half, centre + half


def cases_to_detect(p_before: float, p_after: float, alpha: float = 0.05, power: float = 0.8) -> int:
    """Cases per run needed to tell two pass rates apart (one-sided, two independent runs)."""
    za, zb = Z(1 - alpha), Z(power)
    pbar = (p_before + p_after) / 2
    num = za * sqrt(2 * pbar * (1 - pbar)) + zb * sqrt(p_before * (1 - p_before) + p_after * (1 - p_after))
    return int(-(-num ** 2 // (p_before - p_after) ** 2))


print("If a suite shows a 90% pass rate, the true rate is somewhere in:")
for n in (12, 50, 100, 200, 400, 1000):
    lo, hi = wilson(round(0.9 * n), n)
    print(f"  {n:>5} cases: {lo:.0%} to {hi:.0%}")

print("\nCases per run to reliably catch a quality drop (95% confidence, 80% power):")
for a, b in ((0.95, 0.80), (0.95, 0.90), (0.95, 0.93), (0.99, 0.97)):
    print(f"  {a:.0%} -> {b:.0%}: {cases_to_detect(a, b):,} cases")
