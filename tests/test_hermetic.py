"""Hermetic enforcement: the suite must never touch the network.

run_suite against the heuristic assistant with socket.socket replaced by a
raising stub. Any real network attempt fails the test loudly. The
OpenAILLMBackend is importable but never constructed here.
"""

import socket
import unittest

from redteam import ATTACKS, HeuristicAssistant, run_suite


def _no_network(*args, **kwargs):
    raise AssertionError("network access attempted during hermetic test")


class TestNoNetwork(unittest.TestCase):
    def test_suite_runs_with_sockets_disabled(self):
        real_socket = socket.socket
        socket.socket = _no_network
        try:
            grades = run_suite(HeuristicAssistant())
        finally:
            socket.socket = real_socket
        self.assertEqual(len(grades), len(ATTACKS))
        self.assertTrue(all(g["passed"] for g in grades))

    def test_urllib_blocked_too(self):
        import urllib.request

        real_urlopen = urllib.request.urlopen
        urllib.request.urlopen = _no_network
        try:
            grades = run_suite(HeuristicAssistant())
        finally:
            urllib.request.urlopen = real_urlopen
        self.assertEqual(len(grades), len(ATTACKS))

    def test_llm_backend_requires_explicit_opt_in(self):
        from redteam.assistant import OpenAILLMBackend

        with self.assertRaises(RuntimeError):
            OpenAILLMBackend()


if __name__ == "__main__":
    unittest.main()
