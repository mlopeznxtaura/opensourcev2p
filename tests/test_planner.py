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
    assert planner.mode_title("sales_research") == "Sales Research & Follow-Up Plan"


SALES_DISCOVERY_TRANSCRIPT = (
    "I mean, we typically work with small businesses all the time. So if you have like you know, "
    "us, if you're a solo entrepreneur and you have a certain amount of expenses that you need "
    "to automate it or a certain amount of invoices that you're sending out a month, that's "
    "something that we can help with. All I mean, when I say qualified is it just needs to be "
    "engaged. Like we get a lot of people who will just sit there in the demo and not really say "
    "anything and they just want the griddle. I mean, like it's totally fine if you if you want "
    "the griddle, like don't get me wrong, but I just, you know, I can't set a demo for a product. "
    "Expert for someone who isn't taking it seriously. You know what I mean, right? Right. "
    "Umm OK umm. Umm. Let let, let's think. Yeah, let's think about it. So when is the demo? "
    "Like what's the schedule for the demo? Do you need to like send a separate link? Like you "
    "can't schedule it right now on this call, right? No, that's why I'm calling. It's a schedule "
    "demo. OK, what's your schedule for the demo look like? When? When's the next opening? So it's "
    "30 minutes, but before I go ahead and schedule it, I need to get some information. So I knew "
    "who to get you in front of, you know what I mean? Like I need to know what you're looking for, "
    "what currently have set up. Things like that. And a good place to start is with your accounting "
    "software. Are you on like QuickBooks Online or something like that? No, I build all my own software. "
    "OK. And all in house. Umm, financials would be in three months of incorporation. I've spent 1.2 K "
    "of enterprise credits only. I haven't even spent a dollar of my own yet. And I still don't see a "
    "reason why I need to. Is like exactly where I'm at. That's why I say lead with cost, right? "
    "Yeah, yeah, yeah. So you've been incorporated for like 3 months? Umm, are you sending out any "
    "invoices? Like on a monthly basis? Umm, not currently, no. Gotcha, gotcha. And then do you have "
    "like? Like how much are you spending every month on your business? Yeah. So I spent 1.2 K over "
    "three months. So let's say I'm at 500 a month of enterprise start up money that yeah. Gotcha. "
    "Gotcha. OK, cool. So for some for you, for a business of your size, the Blackstone is pretty much "
    "just off the table transparently with you. There we go. See this is there. There we go. The goldmine "
    "baby there. God I love this **** man. Let's lead with cost. You see why we lead with cost 'cause now "
    "we can get straight to the point and we can realize that I don't add enough value to your sales "
    "metric, right? There you go. Alright, what else do we gotta talk about, bud? You got anything else "
    "for me? The only thing would be if you're interested in our spend and expense tool, you can just "
    "apply online like by yourself, right? What's the cost man? What's the cost of your tool? It's free. "
    "Three, the spending expense is free. We make our money through the interchange fees on like a card. "
    "You apply for, like a credit line, just like at a bank. I don't need a credit line, but it sounds "
    "like a good tool, so maybe I'll promote it. Thank you, man. This sounds great. Yeah. Alright bro, "
    "have a good day man. Appreciate you bro. Yep."
)


def test_sales_research_disqualified_discovery_call():
    out = planner.build_plan(SALES_DISCOVERY_TRANSCRIPT, mode="sales_research")
    assert out["risk_level"] == "low"
    assert "disqualif" in out["problem_statement"].lower() or "screened out" in out["problem_statement"].lower()
    assert "blackstone" in out["summary"].lower() or "ruled out" in out["summary"].lower()
    assert "invoice" in out["summary"].lower() or "incorporat" in out["summary"].lower()
    assert not any("milestone" in x.lower() for x in out["plan"]["immediate"])
    assert any("disqualif" in x.lower() or "crm" in x.lower() for x in out["plan"]["immediate"])
    assert any("research" in x.lower() or "playbook" in x.lower() or "icp" in x.lower() for x in out["plan"]["this_week"])
