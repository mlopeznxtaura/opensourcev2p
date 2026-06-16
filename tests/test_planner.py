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


def test_project_management_mode():
    out = planner.build_plan(
        "We are behind schedule on the Q2 milestone. A vendor delay is blocking "
        "integration and the client wants a stakeholder update.",
        mode="project_management",
    )
    assert "project" in out["problem_statement"].lower()
    assert out["risk_level"] in {"low", "moderate", "high"}
    assert any("blocker" in x.lower() or "milestone" in x.lower() for x in out["plan"]["immediate"])
    assert not any("confession" in x.lower() for x in out["plan"]["immediate"])


def test_manufacturing_safety_mode():
    out = planner.build_plan(
        "Near miss on line 3: forklift almost hit a pedestrian. No injury but "
        "PPE was missing and machine guarding looked unsafe.",
        mode="manufacturing_safety",
    )
    assert "safety" in out["problem_statement"].lower()
    assert out["risk_level"] in {"moderate", "high"}
    assert any("supervisor" in x.lower() or "area" in x.lower() for x in out["plan"]["immediate"])
    assert not any("prayer" in x.lower() for x in out["plan"]["immediate"])


def test_mode_title():
    assert planner.mode_title("project_management") == "Project Execution Plan"
    assert planner.mode_title("manufacturing_safety") == "Manufacturing Safety Corrective Plan"
