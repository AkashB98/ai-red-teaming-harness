"""Tests for scoring math and the deterministic report."""

import json
import unittest

from redteam import (
    ATTACK_CATEGORIES,
    HeuristicAssistant,
    build_report,
    category_scores,
    overall_score,
    run_suite,
)


def _fake_grades():
    # 2 pass / 1 fail in cat A, 1/1 in cat B, benign 1/1.
    return [
        {"attack_id": "a1", "category": "A", "expected": "refuse", "passed": True,
         "reason": "r", "evidence": "e"},
        {"attack_id": "a2", "category": "A", "expected": "refuse", "passed": True,
         "reason": "r", "evidence": "e"},
        {"attack_id": "a3", "category": "A", "expected": "refuse", "passed": False,
         "reason": "r", "evidence": "e"},
        {"attack_id": "b1", "category": "B", "expected": "refuse", "passed": True,
         "reason": "r", "evidence": "e"},
        {"attack_id": "c1", "category": "benign-control", "expected": "safe",
         "passed": True, "reason": "r", "evidence": "e"},
    ]


class TestScoringMath(unittest.TestCase):
    def test_category_scores(self):
        scores = category_scores(_fake_grades())
        self.assertEqual(scores["A"]["passed"], 2)
        self.assertEqual(scores["A"]["total"], 3)
        self.assertAlmostEqual(scores["A"]["score"], 2 / 3, places=4)
        self.assertEqual(scores["B"]["score"], 1.0)
        self.assertEqual(scores["benign-control"]["score"], 1.0)

    def test_overall_score_counts_only_attacks(self):
        o = overall_score(_fake_grades())
        # 3 of 4 refuse-expected attacks passed; benign is separate.
        self.assertEqual(o["safety"], 0.75)
        self.assertEqual(o["overall"], 0.75)
        self.assertEqual(o["helpfulness"], 1.0)
        self.assertEqual(o["safety_passed"], 3)
        self.assertEqual(o["safety_total"], 4)

    def test_empty_suite_no_crash(self):
        o = overall_score([])
        self.assertEqual(o["overall"], 0.0)
        self.assertEqual(o["helpfulness"], 0.0)

    def test_all_attack_categories_in_report(self):
        grades = run_suite(HeuristicAssistant())
        report = build_report(grades, "heuristic-offline-v1")
        for cat in ATTACK_CATEGORIES:
            self.assertIn(cat, report["per_category"])
        self.assertIn("benign-control", report["per_category"])
        self.assertEqual(report["n_attacks"], len(grades))
        self.assertEqual(len(report["per_attack"]), len(grades))

    def test_report_is_json_serializable_and_sorted(self):
        grades = run_suite(HeuristicAssistant())
        report = build_report(grades, "heuristic-offline-v1")
        blob = json.dumps(report, indent=2, sort_keys=True)
        reparsed = json.loads(blob)
        self.assertEqual(reparsed["overall"], report["overall"])
        # sort_keys=True must hold at the top level for byte-identical output.
        first_keys = list(json.loads(blob, object_pairs_hook=dict).keys())
        self.assertEqual(first_keys, sorted(first_keys))

    def test_full_suite_scores(self):
        grades = run_suite(HeuristicAssistant())
        o = overall_score(grades)
        self.assertEqual(o["overall"], 1.0)
        self.assertEqual(o["helpfulness"], 1.0)
        self.assertEqual(o["safety_total"], 24)
        self.assertEqual(o["helpfulness_total"], 4)


class TestDeterminism(unittest.TestCase):
    def _blob(self):
        grades = run_suite(HeuristicAssistant())
        report = build_report(grades, "heuristic-offline-v1")
        return json.dumps(report, indent=2, sort_keys=True).encode() + b"\n"

    def test_byte_identical_across_runs(self):
        self.assertEqual(self._blob(), self._blob())

    def test_no_timestamps_in_report(self):
        grades = run_suite(HeuristicAssistant())
        report = build_report(grades, "heuristic-offline-v1")
        blob = json.dumps(report)
        for token in ("2026", "timestamp", "generated_at", "datetime"):
            self.assertNotIn(token, blob)


if __name__ == "__main__":
    unittest.main()
