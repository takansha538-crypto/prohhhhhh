"""Transparent rule-based creator matching. Not a trained ML model."""


def score_creator_against_brief(creator, brief) -> dict:
    reasons = []
    score = 18

    brief_skills = {s.name.lower() for s in brief.skills}
    creator_skills = {s.name.lower() for s in creator.skills}
    skill_overlap = brief_skills & creator_skills
    if brief_skills:
        ratio = len(skill_overlap) / max(len(brief_skills), 1)
        pts = int(28 * ratio)
        score += pts
        if skill_overlap:
            reasons.append("overlapping skills: " + ", ".join(sorted(skill_overlap)[:4]))

    brief_tools = {t.name.lower() for t in brief.tools}
    creator_tools = {t.name.lower() for t in creator.tools}
    tool_overlap = brief_tools & creator_tools
    if brief_tools:
        ratio = len(tool_overlap) / max(len(brief_tools), 1)
        score += int(24 * ratio)
        if tool_overlap:
            reasons.append("shared AI tools: " + ", ".join(sorted(x.title() if x.islower() else x for x in tool_overlap)[:4]))

    specs = {s.name.lower() for s in creator.specializations}
    ct = (brief.content_type or "").lower()
    if ct and any(ct in s or s in ct for s in specs):
        score += 16
        reasons.append(f"specializes in {brief.content_type}")
    elif ct and ct in (creator.content_types or "").lower():
        score += 12
        reasons.append(f"regularly delivers {brief.content_type}")

    if creator.availability == "Available":
        score += 8
        reasons.append("currently available")
    elif creator.availability == "Limited":
        score += 4
        reasons.append("limited availability")

    mid = ((brief.budget_min or 0) + (brief.budget_max or 0)) / 2 or creator.project_rate_min
    if creator.project_rate_min <= mid <= creator.project_rate_max * 1.2:
        score += 8
        reasons.append("rate range fits the brief budget")

    if creator.verification_level >= 4:
        score += 6
        reasons.append("portfolio-verified creator")
    elif creator.verification_level >= 3:
        score += 3

    score = max(12, min(99, score))
    why = (
        "Strong match because this creator " + "; ".join(reasons) + "."
        if reasons
        else "Partial match based on general AI production experience."
    )
    return {"score": score, "why": why}


def rank_creators(creators, brief, limit=6):
    ranked = []
    for c in creators:
        result = score_creator_against_brief(c, brief)
        ranked.append(
            {
                "creator": c,
                "name": c.user.name,
                "score": result["score"],
                "why": result["why"],
            }
        )
    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked[:limit]
