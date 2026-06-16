from server import planner


def test_build_plan_basic():
    out = planner.build_plan("I feel overwhelmed and distant from my family.")
    assert out["risk_level"] in {"low", "moderate", "high"}
    assert isinstance(out["plan"]["immediate"], list)
    assert out["summary"]
    assert out["problem_statement"]
    assert out["tally"]["total_actions"] >= 1


def test_build_plan_high_risk():
    out = planner.build_plan("I want to kill myself and I feel unsafe.")
    assert out["risk_level"] == "high"
    assert any("safety" in x.lower() for x in out["risk_flags"])
    assert out["tally"]["immediate"] >= 2


def test_build_plan_chronic_habit_support_case():
    out = planner.build_plan(
        "I've been smoking for 24 years and need support to quit. "
        "I may regress and need community resources."
    )
    assert out["risk_level"] == "moderate"
    assert any("24 years" in x.lower() for x in out["risk_flags"])
    assert any("resource request" in x.lower() for x in out["risk_flags"])
    assert out["tally"]["total_actions"] >= 7
