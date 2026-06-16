"""Voice confession to pastoral action plan."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class PlanConfig:
    urgent_keywords: tuple[str, ...] = (
        "suicide",
        "kill myself",
        "self harm",
        "self-harm",
        "abuse",
        "overdose",
        "violent",
        "unsafe",
    )
    stress_keywords: tuple[str, ...] = (
        "anxious",
        "anxiety",
        "depressed",
        "burned out",
        "panic",
        "overwhelmed",
        "afraid",
        "fear",
    )
    relationship_keywords: tuple[str, ...] = (
        "wife",
        "husband",
        "marriage",
        "family",
        "parent",
        "child",
        "relationship",
    )
    habit_keywords: tuple[str, ...] = (
        "smoking",
        "nicotine",
        "tobacco",
        "vape",
        "vaping",
        "gambling",
        "porn",
        "alcohol",
        "drugs",
        "addiction",
        "anger",
        "lying",
        "lust",
    )
    relapse_keywords: tuple[str, ...] = (
        "relapse",
        "regress",
        "backslide",
        "slip",
        "craving",
        "withdrawal",
    )
    resource_keywords: tuple[str, ...] = (
        "community resource",
        "community resources",
        "support group",
        "program",
        "counselor",
        "coach",
        "help me quit",
        "quit",
    )


CFG = PlanConfig()


def _contains_any(text: str, words: tuple[str, ...]) -> bool:
    lower = text.lower()
    return any(w in lower for w in words)


def _extract_sentences(text: str) -> list[str]:
    pieces = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    return [p.strip() for p in pieces if p.strip()]


def _extract_max_years(text: str) -> int:
    years = [int(y) for y in re.findall(r"\b(\d{1,2})\s*(?:year|years|yr|yrs)\b", text.lower())]
    return max(years) if years else 0


def build_plan(transcript: str) -> dict:
    text = transcript.strip()
    if not text:
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "problem_statement": "No confession transcript was provided.",
            "summary": "No transcript content supplied.",
            "risk_level": "unknown",
            "risk_flags": [],
            "plan": {
                "immediate": ["Capture a short confession summary first."],
                "this_week": [],
                "follow_up": [],
            },
            "tally": {"immediate": 1, "this_week": 0, "follow_up": 0, "total_actions": 1},
            "notes": [],
        }

    sentences = _extract_sentences(text)
    summary = " ".join(sentences[:2])[:320]

    risk_flags: list[str] = []
    if _contains_any(text, CFG.urgent_keywords):
        risk_flags.append("Potential immediate safety concern detected.")
    if _contains_any(text, CFG.stress_keywords):
        risk_flags.append("Emotional distress indicators present.")
    if _contains_any(text, CFG.habit_keywords):
        risk_flags.append("Recurring habit/behavior struggle detected.")
    if _contains_any(text, CFG.relationship_keywords):
        risk_flags.append("Relationship or family strain mentioned.")

    years = _extract_max_years(text)
    chronic_habit = _contains_any(text, CFG.habit_keywords)
    relapse_risk = _contains_any(text, CFG.relapse_keywords)
    resource_request = _contains_any(text, CFG.resource_keywords)
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

    notes = [
        "This plan is decision-support and not medical/legal advice.",
        "Use pastoral judgment and local safeguarding policy before sharing any data.",
    ]

    problem_statement = (
        f"Confession indicates a {risk_level} pastoral care situation requiring structured support, "
        "clear accountability, and scheduled follow-up."
    )
    tally = {
        "immediate": len(immediate),
        "this_week": len(this_week),
        "follow_up": len(follow_up),
        "total_actions": len(immediate) + len(this_week) + len(follow_up),
    }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "problem_statement": problem_statement,
        "summary": summary,
        "risk_level": risk_level,
        "risk_flags": risk_flags,
        "plan": {
            "immediate": immediate,
            "this_week": this_week,
            "follow_up": follow_up,
        },
        "tally": tally,
        "notes": notes,
    }
