import agent_gate as ag

def test_classify():
    assert ag.classify(0, True, True) == "checker"
    assert ag.classify(1, True, True) == "infra"
    assert ag.classify(0, True, True, stash_accepted_by_checker=True, ) == "checker"
    assert ag.classify(0, False, False, stash_accepted_by_checker=True) == "review_wrong"

def test_gate_learns():
    state = {"n": 0}
    def act(errors):
        state["n"] += 1
        return (False, ["erro"]) if state["n"] < 2 else (True, [])
    r = ag.run_gate(act, lambda: True, max_attempts=3, budget_seconds=60)
    assert r.ok and len(r.attempts) == 2
    assert "handoff" in ag.handoff(r)
