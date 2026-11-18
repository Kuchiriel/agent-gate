# agent-gate

Gate que faz **modelo pequeno render como especialista**: o erro vira contexto,
a tentativa recomeça limpa, o orçamento é adaptativo e o veredito é do checker.

Extraído do harness `nightwatch` (3065 linhas) e provado no laboratório A/B
onde modelos de 4B/8B passaram L1 100% e o gate separou falha de modelo de
falha de infra.

## Regra

```
act(errors) -> verify() -> classify() -> retry com erro | handoff
```

- `checker` — veredito do checker travado
- `review` — revisor abortou
- `review_wrong` — revisor rejeitou o que o checker aceita
- `infra` — erro de máquina/roteamento/429 (não é culpa do modelo)

## Uso

```bash
pip install agent-gate
agent-gate demo       # aprende com erro: tentativa 2 corrige
agent-gate classify --checker
agent-gate api        # GET /health, /contract
```

API: `GET /health` → `{"ok":true,...}`; `GET /contract` → as 6 regras.

MIT. Sem segredo, sem path absoluto, agnóstico de modelo e de runtime.
