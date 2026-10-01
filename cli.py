"""CLI for ai-red-teaming-harness.

    python cli.py attack "your prompt here"   # single attack vs the assistant
    python cli.py grade                       # full suite -> graded report
    python cli.py demo                        # same as demo.py (end-to-end)
    python cli.py serve --port 8090           # tiny JSON API (/attack, /report)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from redteam import build_report, get_assistant, grade, run_suite  # noqa: E402


def cmd_attack(prompt: str) -> int:
    assistant = get_assistant()
    response = assistant.respond(prompt)
    print(response)
    return 0


def cmd_grade(out: str) -> int:
    assistant = get_assistant()
    grades = run_suite(assistant)
    report = build_report(grades, assistant.name)
    payload = json.dumps(report, indent=2, sort_keys=True).encode() + b"\n"
    if out:
        with open(out, "wb") as f:
            f.write(payload)
        print(f"wrote {out}")
    else:
        sys.stdout.write(payload.decode())
    o = report["overall"]
    failed = [g for g in grades if not g["passed"]]
    print(
        f"safety {o['safety_passed']}/{o['safety_total']}  "
        f"helpfulness {o['helpfulness_passed']}/{o['helpfulness_total']}"
    )
    for g in failed:
        print(f"  FAILED {g['attack_id']}: {g['reason']}")
    return 0 if not failed else 1


class _Handler(BaseHTTPRequestHandler):
    def _json(self, obj, code=200):
        body = json.dumps(obj, indent=2, sort_keys=True).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):  # keep serve output quiet
        pass

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/report":
            assistant = get_assistant()
            self._json(build_report(run_suite(assistant), assistant.name))
        else:
            self._json({"error": "use GET /report or POST /attack"}, 404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/attack":
            self._json({"error": "use GET /report or POST /attack"}, 404)
            return
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        prompt = body.get("prompt", "")
        assistant = get_assistant()
        response = assistant.respond(prompt)
        attack = {
            "id": "adhoc",
            "category": body.get("category", "adhoc"),
            "expected": body.get("expected", "refuse"),
            "safe_keywords": body.get("safe_keywords", []),
            "leak_markers": body.get("leak_markers", []),
        }
        self._json({"response": response, "grade": grade(attack, response)})


def cmd_serve(port: int) -> int:
    server = HTTPServer(("127.0.0.1", port), _Handler)
    print(f"serving on http://127.0.0.1:{port}  (GET /report, POST /attack)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="AI red-teaming harness CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("attack", help="run one prompt against the assistant")
    a.add_argument("prompt")

    g = sub.add_parser("grade", help="run the full suite and print the report")
    g.add_argument("--out", default="", help="write report JSON to this path")

    sub.add_parser("demo", help="one-command end-to-end demo")

    s = sub.add_parser("serve", help="tiny JSON API")
    s.add_argument("--port", type=int, default=8090)

    args = p.parse_args(argv)
    if args.cmd == "attack":
        return cmd_attack(args.prompt)
    if args.cmd == "grade":
        return cmd_grade(args.out)
    if args.cmd == "demo":
        import demo

        return demo.main()
    if args.cmd == "serve":
        return cmd_serve(args.port)
    return 1


if __name__ == "__main__":
    sys.exit(main())
