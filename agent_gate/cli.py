#!/usr/bin/env python3
"""agent-gate CLI + API local (stdlib)."""
from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import agent_gate as ag

DEMO_ROUNDS = {"n": 0}

def demo_act(errors):
    """Demonstração: aprendizagem com erro (2ª tentativa corrige)."""
    DEMO_ROUNDS["n"] += 1
    if DEMO_ROUNDS["n"] < 2:
        return False, ["syntax error: token inesperado ( simulated )"]
    return True, []

def demo_verify():
    return True

def main():
    p = argparse.ArgumentParser(prog="agent-gate", description=__doc__)
    p.add_argument("--version", action="version", version=ag.__version__)
    sub = p.add_subparsers(dest="cmd")
    q = sub.add_parser("classify", help="classifica motivo")
    q.add_argument("--rc", type=int, default=0)
    q.add_argument("--checker", action="store_true")
    q.add_argument("--infra", action="store_true")
    sub.add_parser("demo", help="roda gate de exemplo (aprende com erro)")
    q = sub.add_parser("api", help="API local")
    q.add_argument("--port", type=int, default=8791); q.add_argument("--bind", default="127.0.0.1")
    a = p.parse_args()
    if a.cmd == "classify":
        print(ag.classify(a.rc, a.checker, True, throttled=a.infra))
    elif a.cmd == "demo":
        r = ag.run_gate(demo_act, demo_verify, max_attempts=3, budget_seconds=60)
        print(json.dumps(r.to_dict(), ensure_ascii=False, indent=2))
        print(ag.handoff(r))
    elif a.cmd == "api":
        class H(BaseHTTPRequestHandler):
            def _s(self, c, o):
                b = json.dumps(o, ensure_ascii=False).encode()
                self.send_response(c); self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
            def do_GET(self):
                if self.path in ("/health", "/"):
                    return self._s(200, {"ok": True, "service": "agent-gate", "version": ag.__version__})
                if self.path == "/contract":
                    return self._s(200, {"rule": ["error_as_context","clean_retry",
                        "adaptive_budget","checker_is_judge","classify_motive","handoff"]})
                self._s(404, {"error": "not found"})
            def log_message(self, *x): pass
        print(f"agent-gate API em http://{a.bind}:{a.port}")
        ThreadingHTTPServer((a.bind, a.port), H).serve_forever()
    else:
        print("use: agent-gate classify|demo|api")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
