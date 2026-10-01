"""ai-red-teaming-harness — adversarial prompt suite with graded safety evals.

Public API:
    from redteam import ATTACKS, SampleAssistant, run_suite, grade, is_refusal

The suite is fully offline: the bundled SampleAssistant is a heuristic,
deterministic responder. An optional OpenAI-compatible LLM backend can be
plugged in behind the REDTEAM_LLM_* env vars for red-teaming a real model,
but tests and evals never touch the network.
"""

from .attacks import ATTACKS, ATTACK_CATEGORIES
from .assistant import HeuristicAssistant, SampleAssistant, get_assistant
from .grader import grade, is_refusal, has_leakage
from .scoring import run_suite, category_scores, overall_score, build_report

__all__ = [
    "ATTACKS",
    "ATTACK_CATEGORIES",
    "HeuristicAssistant",
    "SampleAssistant",
    "get_assistant",
    "grade",
    "is_refusal",
    "has_leakage",
    "run_suite",
    "category_scores",
    "overall_score",
    "build_report",
]
