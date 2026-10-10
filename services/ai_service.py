"""AI service layer for CreatorsHub.

Uses an optional OpenAI-compatible API when OPENAI_API_KEY is set.
Otherwise returns reliable local mock generations so the demo never breaks.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request


def _api_key():
    return (os.getenv("OPENAI_API_KEY") or "").strip()


def ai_available() -> bool:
    return bool(_api_key())


def generate_brief_from_idea(idea: str) -> dict:
    idea = (idea or "").strip()
    if not idea:
        idea = "A premium product campaign using AI-native visual production."
    if ai_available():
        try:
            return _remote_brief(idea)
        except Exception:
            return _local_brief(idea)
    return _local_brief(idea)


def suggest_creator_matches(brief: dict, scored: list) -> str:
    if not scored:
        return "No strong matches yet. Broaden skills or tools to see more creators."
    top = scored[0]
    return (
        f"Recommended starting point: {top['name']} ({top['score']}% AI Match) — {top['why']}"
    )


def generate_creator_summary(creator) -> str:
    specs = ", ".join(s.name for s in creator.specializations[:2]) or "AI-native production"
    tools = ", ".join(t.name for t in creator.tools[:3]) or "leading generative tools"
    return (
        f"{creator.user.name} is a {specs.lower()} specialist with {creator.experience_years}+ years "
        f"shaping commercial work in {creator.tools[0].name if creator.tools else 'AI production'}. "
        f"Typical stack: {tools}. Availability: {creator.availability}."
    )


def _remote_brief(idea: str) -> dict:
    payload = {
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "temperature": 0.4,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Return JSON only for a creative brief with keys: title, campaign_objective, "
                    "content_type, style, visual_direction, suggested_skills (list), "
                    "suggested_tools (list), format, aspect_ratio, deliverables, "
                    "commercial_use, suggested_timeline, ai_requirements, creative_goal."
                ),
            },
            {"role": "user", "content": idea},
        ],
    }
    req = urllib.request.Request(
        os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {_api_key()}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=12) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    text = data["choices"][0]["message"]["content"]
    text = re.sub(r"^```json|```$", "", text.strip(), flags=re.I | re.M)
    parsed = json.loads(text)
    parsed["source"] = "live-api"
    return parsed


def _local_brief(idea: str) -> dict:
    text = idea.lower()
    content_type = "Video"
    tools = ["Runway", "Midjourney", "After Effects"]
    skills = ["Prompt Direction", "Cinematic Editing", "Color Grading"]
    style = "Cinematic, high-contrast, premium"
    aspect = "16:9"
    fmt = "MP4"
    title = "AI-Native Campaign Film"

    if any(w in text for w in ["fashion", "lookbook", "apparel", "luxury"]):
        content_type = "Fashion Film"
        tools = ["Kling", "Midjourney", "After Effects"]
        skills = ["Fashion Direction", "Motion Design", "Look Development"]
        style = "Editorial luxury, slow camera, tactile fabrics"
        title = "Luxury Fashion Drop Film"
    elif any(w in text for w in ["product", "launch", "startup", "saas", "tech"]):
        content_type = "Product Film"
        tools = ["Runway", "Sora", "ElevenLabs"]
        skills = ["Product Storytelling", "Sound Design", "3D Compositing"]
        style = "Futuristic, clean, luminous, restrained motion"
        title = "Futuristic Product Launch Film"
    elif any(w in text for w in ["3d", "product viz", "automotive", "industrial"]):
        content_type = "3D / CGI"
        tools = ["Blender", "Stable Diffusion", "ComfyUI"]
        skills = ["Lookdev", "Lighting", "Generative Texturing"]
        style = "Photoreal materials, studio lighting, hero product"
        title = "Photoreal Product Visualization"
        aspect = "1:1"
    elif any(w in text for w in ["social", "reel", "tiktok", "short"]):
        content_type = "Short-form Video"
        tools = ["Kling", "CapCut", "ElevenLabs"]
        skills = ["Vertical Storytelling", "Hook Design", "Sound Design"]
        style = "Bold type, kinetic cuts, high energy"
        aspect = "9:16"
        title = "Social Launch Series"
        fmt = "MP4 (9:16)"
    elif any(w in text for w in ["brand", "identity", "design", "still", "image"]):
        content_type = "Generative Design"
        tools = ["Midjourney", "Adobe Firefly", "Photoshop"]
        skills = ["Art Direction", "Generative Imaging", "Brand Systems"]
        style = "Refined, typographic, gallery-grade stills"
        aspect = "4:5"
        title = "Generative Brand World"
        fmt = "PNG / TIFF"
    elif any(w in text for w in ["anim", "motion", "explainer"]):
        content_type = "Motion Design"
        tools = ["Runway", "After Effects", "Adobe Firefly"]
        skills = ["Motion Systems", "Illustration", "Sound Design"]
        style = "Graphic, rhythmic, editorial motion"
        title = "Animated Brand Explainer"

    return {
        "title": title,
        "campaign_objective": idea if len(idea) > 24 else f"Produce a commercially ready {content_type.lower()} that positions the brand as contemporary and technically fluent.",
        "content_type": content_type,
        "creative_goal": "Create a distinctive, licensable asset that can live on site, social, and paid media without looking like generic AI output.",
        "style": style,
        "visual_direction": "Controlled palette, tactile lighting, restrained camera language, and a clear hero moment in the first three seconds. Avoid neon clichés and over-sharpened faces.",
        "suggested_skills": skills,
        "suggested_tools": tools,
        "format": fmt,
        "aspect_ratio": aspect,
        "deliverables": "Master file, social cutdowns, stills from key frames, and a short workflow note listing tools used.",
        "commercial_use": "Full commercial usage for paid, organic, and website placement. Creator must confirm model/training licenses for any third-party assets.",
        "suggested_timeline": "10–16 days including two revision rounds",
        "ai_requirements": "Disclose tools and models used. Prefer creators with verified workflows and commercial-use experience. No unlicensed likeness of real people.",
        "source": "local-intelligent-layer",
    }
