"""One-command end-to-end demo: run the attack suite, grade it, print results."""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from redteam import ATTACK_CATEGORIES, HeuristicAssistant, build_report, run_suite  # noqa: E402


def main() -> int:
    assistant = HeuristicAssistant()
    grades = run_suite(assistant)
    report = build_report(grades, assistant.name)
    o = report["overall"]

    print("=" * 64)
    print("AI RED-TEAMING HARNESS — demo run")
    print(f"assistant: {assistant.name}  |  attacks: {report['n_attacks']}  |  "
          f"categories: {report['n_categories']}")
    print("=" * 64)
    for cat in ATTACK_CATEGORIES:
        s = report["per_category"][cat]
        bar = "#" * int(s["score"] * 20)
        print(f"  {cat:32s} {s['passed']:2d}/{s['total']:2d} [{bar:<20s}]")
    bc = report["per_category"]["benign-control"]
    print(f"  {'benign-control':32s} {bc['passed']:2d}/{bc['total']:2d}")
    print("-" * 64)
    print(f"  OVERALL SAFETY SCORE: {o['overall']:.2f} "
          f"({o['safety_passed']}/{o['safety_total']} attacks refused cleanly)")
    print(f"  HELPFULNESS:          {o['helpfulness']:.2f} "
          f"({o['helpfulness_passed']}/{o['helpfulness_total']} controls answered)")
    print("=" * 64)
    print("Sample grade (with evidence):")
    sample = next(g for g in grades if g["attack_id"] == "toi-01")
    print(f"  [{sample['attack_id']}] passed={sample['passed']} — {sample['reason']}")
    evidence = sample["evidence"]
    print(f'  evidence: "{evidence}"')
    print()
    print("Next: python evals/run_evals.py  (golden evals) | "
          "python cli.py serve  (JSON API)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
