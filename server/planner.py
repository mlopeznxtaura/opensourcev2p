"""Voice/text intake to structured action plans — pastoral, project, or safety."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone

MODES = frozenset({"pastoral_confession", "project_management", "manufacturing_safety"})


@dataclass(frozen=True)
class PastoralConfig:
    urgent_keywords: tuple[str, ...] = (
        "suicide", "kill myself", "self harm", "self-harm", "abuse",
        "overdose", "violent", "unsafe",
    )
    stress_keywords: tuple[str, ...] = (
        "anxious", "anxiety", "depressed", "burned out", "panic",
        "overwhelmed", "afraid", "fear",
    )
    relationship_keywords: tuple[str, ...] = (
        "wife", "husband", "marriage", "family", "parent", "child", "relationship",
    )
    habit_keywords: tuple[str, ...] = (
        "smoking", "nicotine", "tobacco", "vape", "vaping", "gambling", "porn",
        "alcohol", "drugs", "addiction", "anger", "lying", "lust",
    )
    relapse_keywords: tuple[str, ...] = (
        "relapse", "regress", "backslide", "slip", "craving", "withdrawal",
    )
    resource_keywords: tuple[str, ...] = (
        "community resource", "community resources", "support group", "program",
        "counselor", "coach", "help me quit", "quit",
    )


PASTORAL = PastoralConfig()


def _contains_any(text: str, words: tuple[str, ...]) -> bool:
    lower = text.lower()
    return any(w in lower for w in words)


def _extract_sentences(text: str) -> list[str]:
    pieces = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    return [p.strip() for p in pieces if p.strip()]


def _extract_max_years(text: str) -> int:
    years = [int(y) for y in re.findall(r"\b(\d{1,2})\s*(?:year|years|yr|yrs)\b", text.lower())]
    return max(years) if years else 0


def _empty_plan(message: str, immediate: list[str]) -> dict:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "problem_statement": message,
        "summary": message,
        "risk_level": "unknown",
        "risk_flags": [],
        "plan": {"immediate": immediate, "this_week": [], "follow_up": []},
        "tally": {"immediate": len(immediate), "this_week": 0, "follow_up": 0, "total_actions": len(immediate)},
        "notes": [],
    }


def _finalize(plan: dict) -> dict:
    p = plan["plan"]
    plan["tally"] = {
        "immediate": len(p["immediate"]),
        "this_week": len(p["this_week"]),
        "follow_up": len(p["follow_up"]),
        "total_actions": len(p["immediate"]) + len(p["this_week"]) + len(p["follow_up"]),
    }
    return plan


def build_pastoral_plan(transcript: str) -> dict:
    text = transcript.strip()
    if not text:
        return _empty_plan(
            "No confession transcript was provided.",
            ["Capture a short confession summary first."],
        )

    sentences = _extract_sentences(text)
    summary = " ".join(sentences[:2])[:320]

    risk_flags: list[str] = []
    if _contains_any(text, PASTORAL.urgent_keywords):
        risk_flags.append("Potential immediate safety concern detected.")
    if _contains_any(text, PASTORAL.stress_keywords):
        risk_flags.append("Emotional distress indicators present.")
    if _contains_any(text, PASTORAL.habit_keywords):
        risk_flags.append("Recurring habit/behavior struggle detected.")
    if _contains_any(text, PASTORAL.relationship_keywords):
        risk_flags.append("Relationship or family strain mentioned.")

    years = _extract_max_years(text)
    chronic_habit = _contains_any(text, PASTORAL.habit_keywords)
    relapse_risk = _contains_any(text, PASTORAL.relapse_keywords)
    resource_request = _contains_any(text, PASTORAL.resource_keywords)
    long_horizon = years >= 5

    if long_horizon:
        risk_flags.append(f"Long-horizon behavior pattern noted ({years} years).")
    if relapse_risk:
        risk_flags.append("Relapse risk language detected.")
    if chronic_habit and resource_request:
        risk_flags.append("Support/community resource request detected.")

    if any("immediate safety" in f.lower() for f in risk_flags):
        risk_level = "high"
    elif chronic_habit and (long_horizon or relapse_risk or resource_request):
        risk_level = "moderate"
    else:
        risk_level = "moderate" if risk_flags else "low"

    immediate = [
        "Begin with prayer and reaffirm confidentiality boundaries.",
        "Reflect back the confession in one sentence for confirmation.",
    ]
    this_week = [
        "Define one concrete repentance step and one accountability step.",
        "Create a 7-day plan with one daily spiritual practice (scripture/prayer/journal).",
    ]
    follow_up = [
        "Schedule a pastoral check-in within 72 hours.",
        "Schedule a second follow-up in 7 days to measure progress.",
    ]

    if risk_level == "high":
        immediate.insert(0, "Pause planning and complete immediate safety assessment.")
        immediate.append("Escalate to emergency or safeguarding protocol if imminent risk is confirmed.")
    elif chronic_habit:
        immediate.append("Identify top triggers and set a clear first 24-hour commitment window.")
        this_week.append("Connect to one concrete support resource (support group, counselor, or cessation service).")
        if relapse_risk:
            this_week.append("Write a relapse response plan with named accountability contacts.")
        follow_up.append("Track progress weekly (streaks/lapses) and adjust support intensity as needed.")

    problem_statement = (
        f"Confession indicates a {risk_level} pastoral care situation requiring structured support, "
        "clear accountability, and scheduled follow-up."
    )

    return _finalize({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "problem_statement": problem_statement,
        "summary": summary,
        "risk_level": risk_level,
        "risk_flags": risk_flags,
        "plan": {"immediate": immediate, "this_week": this_week, "follow_up": follow_up},
        "notes": [
            "This plan is decision-support and not medical/legal advice.",
            "Use pastoral judgment and local safeguarding policy before sharing any data.",
        ],
    })


def build_project_plan(transcript: str) -> dict:
    text = transcript.strip()
    if not text:
        return _empty_plan(
            "No project input was provided.",
            ["Capture project status, blockers, and deadlines first."],
        )

    sentences = _extract_sentences(text)
    summary = " ".join(sentences[:2])[:320]

    critical_keywords = (
        "missed deadline", "blocked", "blocker", "critical", "production down",
        "customer escalation", "budget overrun", "over budget", "failed launch",
    )
    schedule_keywords = (
        "delay", "delayed", "behind schedule", "slipping", "at risk", "late",
        "deadline", "milestone", "sprint", "timeline",
    )
    scope_keywords = ("scope creep", "scope change", "requirements changed", "out of scope", "rework")
    resource_keywords = (
        "understaffed", "short staffed", "need headcount", "capacity", "bandwidth",
        "dependency", "waiting on", "vendor delay",
    )
    stakeholder_keywords = ("stakeholder", "executive", "sponsor", "client", "customer", "leadership")

    risk_flags: list[str] = []
    if _contains_any(text, critical_keywords):
        risk_flags.append("Critical delivery or budget risk detected.")
    if _contains_any(text, schedule_keywords):
        risk_flags.append("Schedule or milestone pressure indicated.")
    if _contains_any(text, scope_keywords):
        risk_flags.append("Scope instability or change risk detected.")
    if _contains_any(text, resource_keywords):
        risk_flags.append("Resource or dependency constraint mentioned.")
    if _contains_any(text, stakeholder_keywords):
        risk_flags.append("Stakeholder visibility or escalation may be required.")

    if _contains_any(text, critical_keywords):
        risk_level = "high"
    elif len(risk_flags) >= 2:
        risk_level = "moderate"
    elif risk_flags:
        risk_level = "moderate"
    else:
        risk_level = "low"

    immediate = [
        "Confirm current objective, owner, and target date in one sentence.",
        "List top three blockers and assign an owner to each.",
    ]
    this_week = [
        "Rebuild the execution plan with dated milestones for the next 7 days.",
        "Identify dependencies and send status updates to stakeholders.",
        "Define success metrics for this sprint or delivery window.",
    ]
    follow_up = [
        "Hold a mid-week checkpoint to re-baseline schedule and scope.",
        "Review burndown/milestone progress in the next planning session.",
    ]

    if risk_level == "high":
        immediate.insert(0, "Escalate critical blockers to project sponsor within 24 hours.")
        immediate.append("Freeze non-essential scope until delivery path is stable.")
        this_week.append("Run a risk review: budget, timeline, quality, and staffing.")
    elif _contains_any(text, scope_keywords):
        this_week.append("Document scope changes and get written approval before new work starts.")
    if _contains_any(text, resource_keywords):
        immediate.append("Quantify capacity gap (hours/FTE) and propose reallocation or hire plan.")

    problem_statement = (
        f"Project intake indicates a {risk_level} execution situation requiring "
        "clear ownership, milestone control, and stakeholder alignment."
    )

    return _finalize({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "problem_statement": problem_statement,
        "summary": summary,
        "risk_level": risk_level,
        "risk_flags": risk_flags,
        "plan": {"immediate": immediate, "this_week": this_week, "follow_up": follow_up},
        "notes": [
            "This plan is operational guidance, not legal or contractual advice.",
            "Validate dates, owners, and approvals with your project governance process.",
        ],
    })


def build_safety_plan(transcript: str) -> dict:
    text = transcript.strip()
    if not text:
        return _empty_plan(
            "No safety report was provided.",
            ["Capture what happened, where, and who was involved first."],
        )

    sentences = _extract_sentences(text)
    summary = " ".join(sentences[:2])[:320]

    injury_keywords = (
        "injury", "injured", "hurt", "hospital", "ambulance", "laceration",
        "fracture", "burn", "amputation", "fatality", "death",
    )
    imminent_keywords = (
        "chemical spill", "fire", "explosion", "toxic", "gas leak", "entrapment",
        "machine guarding", "lockout", "tagout", "loto",
    )
    hazard_keywords = (
        "hazard", "unsafe", "near miss", "near-miss", "incident", "osha",
        "ppe", "guard", "slip", "trip", "fall", "forklift", "conveyor",
    )
    process_keywords = (
        "root cause", "corrective action", "preventive action", "capa",
        "investigation", "8d", "five why", "5 why",
    )

    risk_flags: list[str] = []
    if _contains_any(text, injury_keywords):
        risk_flags.append("Actual or potential injury language detected.")
    if _contains_any(text, imminent_keywords):
        risk_flags.append("Active or high-consequence hazard indicated.")
    if _contains_any(text, hazard_keywords):
        risk_flags.append("Operational safety hazard or near-miss reported.")
    if _contains_any(text, process_keywords):
        risk_flags.append("Formal corrective/preventive process may be required.")

    if _contains_any(text, injury_keywords) or _contains_any(text, imminent_keywords):
        risk_level = "high"
    elif _contains_any(text, hazard_keywords):
        risk_level = "moderate"
    elif risk_flags:
        risk_level = "moderate"
    else:
        risk_level = "low"

    immediate = [
        "Secure the area and confirm no ongoing exposure to personnel.",
        "Preserve the scene and identify involved equipment/materials.",
        "Notify the on-duty supervisor and safety representative.",
    ]
    this_week = [
        "Complete initial incident documentation with time, location, and witnesses.",
        "Start root-cause analysis (5-Why or fishbone) with cross-functional team.",
        "Define interim controls until permanent corrective actions are verified.",
    ]
    follow_up = [
        "Verify corrective actions in the field within 7 days.",
        "Close the loop with operations and EHS on preventive controls.",
    ]

    if risk_level == "high":
        immediate.insert(0, "Stop work if imminent danger remains; follow emergency response protocol.")
        immediate.append("Engage medical response and regulatory notification requirements if applicable.")
        this_week.append("Conduct formal incident review and assign CAPA owners with due dates.")
    elif _contains_any(text, process_keywords):
        this_week.append("Map findings to existing CAPA tracker and set verification checkpoints.")
    else:
        this_week.append("Assess if similar hazards exist on parallel lines or shifts.")

    problem_statement = (
        f"Safety report indicates a {risk_level} manufacturing risk requiring containment, "
        "documented investigation, and verified corrective action."
    )

    return _finalize({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "problem_statement": problem_statement,
        "summary": summary,
        "risk_level": risk_level,
        "risk_flags": risk_flags,
        "plan": {"immediate": immediate, "this_week": this_week, "follow_up": follow_up},
        "notes": [
            "This plan supports safety workflow and is not a substitute for regulatory reporting.",
            "Follow your site EHS policy, OSHA requirements, and internal incident standards.",
        ],
    })


def build_plan(transcript: str, mode: str = "pastoral_confession") -> dict:
    if mode not in MODES:
        mode = "pastoral_confession"
    if mode == "project_management":
        return build_project_plan(transcript)
    if mode == "manufacturing_safety":
        return build_safety_plan(transcript)
    return build_pastoral_plan(transcript)


def mode_title(mode: str) -> str:
    return {
        "pastoral_confession": "Pastoral Action Plan",
        "project_management": "Project Execution Plan",
        "manufacturing_safety": "Manufacturing Safety Corrective Plan",
    }.get(mode, "Action Plan")
