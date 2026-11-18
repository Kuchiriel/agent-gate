#!/usr/bin/env python3
"""agent-gate — gate que faz modelo pequeno render como especialista.

Padrão extraído do harness nightwatch (3065 linhas) e provado no laboratório
A/B da casa:

  - erro vira CONTEXTO para a próxima tentativa (não repeat cego)
  - cada tentativa recomeça de branch LIMPO (estado não contamina)
  - orçamento adaptativo: retry serve para convergir, não para monopolizar
  - veredito é do CHECKER travado, não do revisor LLM
  - motivo é classificado: checker | review | review_wrong | infra
  - handoff deixa o próximo agente continuar sem perder o que já foi feito

Agnóstico: não sabe de git, de OpenCode nem de modelo. Recebe funções.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from typing import Callable

__version__ = "0.1.0"


@dataclass
class Attempt:
    n: int
    ok: bool
    motive: str
    errors: list[str] = field(default_factory=list)
    seconds: float = 0.0


@dataclass
class GateResult:
    ok: bool
    attempts: list[Attempt]
    motive: str
    handoff: str
    elapsed: float

    def to_dict(self):
        d = asdict(self)
        d["ok"] = self.ok
        return d


def classify(rc: int, checker_ok: bool, review_ok: bool,
             stash_accepted_by_checker: bool = False, throttled: bool = False) -> str:
    """Veredito honesto (não confunde máquina com modelo)."""
    if rc != 0 or throttled:
        return "infra"
    if not review_ok:
        return "review_wrong" if stash_accepted_by_checker else "review"
    return "checker" if checker_ok else "checker"


def run_gate(
    act: Callable[[list[str]], tuple[bool, list[str]]],
    verify: Callable[[], bool],
    *,
    max_attempts: int = 3,
    budget_seconds: float = 600,
    on_event: Callable[[str, dict], None] | None = None,
) -> GateResult:
    """Executa act -> verify; em falha, realimenta erros e tenta de novo."""
    started = time.time()
    errors: list[str] = []
    attempts: list[Attempt] = []
    n = max(1, max_attempts)
    for i in range(n):
        # orçamento adaptativo (o padrão medido no harness)
        frac = (time.time() - started) / budget_seconds if budget_seconds else 0
        if frac > 0.75 and n > 1:
            n = i + 1
        t0 = time.time()
        ok, errs = act(list(errors))
        checker_ok = verify() if ok else False
        motive = classify(0, checker_ok, True) if ok else "infra"
        attempts.append(Attempt(i+1, ok and checker_ok, motive,
                                list(errs), round(time.time()-t0, 3)))
        if on_event: on_event("attempt", attempts[-1].to_dict())
        if ok and checker_ok:
            return GateResult(True, attempts, "checker",
                              "concluido; proximo agente pode retomar",
                              round(time.time()-started, 3))
        errors.extend(errs or [f"tentativa {i+1} falhou"])
    last = attempts[-1] if attempts else Attempt(0, False, "infra")
    return GateResult(False, attempts, last.motive,
                      f"retomar com {len(errors)} erro(s) como contexto",
                      round(time.time()-started, 3))


def handoff(result: GateResult) -> str:
    """Texto curto que um agente deixa para o próximo (visível, não bloqueante)."""
    return (f"[handoff] ok={result.ok} motivo={result.motive} "
            f"tentativas={len(result.attempts)} {result.handoff}")
