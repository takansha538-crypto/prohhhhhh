# CreatorsHub

**Discover. Verify. Hire. Create.**

CreatorsHub is a professional marketplace where brands discover, verify, connect with, and hire AI-native creators — filmmakers, animators, generative designers, and creative directors.

This repository is a complete, runnable National Hackathon prototype. It is a real Flask application with SQLite, seeded demo data, and working journeys (search, briefs, matching, hire, messages). It does not depend on an AI API key.

## Problem

Generative production created a new class of commercial creatives. Existing freelance sites do not show tools, workflows, licensing, or verification in a way legal and brand teams can trust.

## Features

- Creator profiles and AI portfolios (tools, workflow, commercial-use, verification)
- Multi-step brief builder plus AI-assisted structuring (local layer or optional API)
- Creator discovery with filters that query the database
- Rule-based AI Match scores with written reasons (not a trained ML model)
- Connect, message, save, follow, apply, hire, project stages
- Creator and brand dashboards, notifications, demo logins
- Landing, presentation, and a non-intrusive Demo Guide

## Tech stack

- HTML, CSS, vanilla JavaScript
- Python, Flask
- SQLite via Flask-SQLAlchemy
- Optional OpenAI-compatible API for brief generation

## Folder structure

```
app.py
requirements.txt
README.md
DATA_MODEL.md
.env.example
database/schema.py
database/seed.py
services/ai_service.py
services/matching.py
templates/
static/css/style.css
static/js/
static/images/
instance/creatorshub.db   (created on first run)
```

## Installation and how to run

Requires Python 3.10+.

```bash
cd path/to/this/folder
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

macOS / Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

The first start creates `instance/creatorshub.db` and seeds demo data automatically.

## Demo accounts

Password for both: `demo123`

| Role | Email | Name |
| --- | --- | --- |
| Brand | novaframe@creatorshub.test | NovaFrame Studios (Maya Ellison) |
| Creator | aria@creatorshub.test | Aria Chen |

Or use **Explore Demo** on the login page:

- Demo as Brand
- Demo as Creator

Judges should not need to register.

## AI functionality

`services/ai_service.py` exposes:

- `generate_brief_from_idea()`
- `suggest_creator_matches()`
- `generate_creator_summary()`

If `OPENAI_API_KEY` is set in `.env`, brief generation can call an OpenAI-compatible endpoint. If it is missing or the call fails, a local intelligent layer still returns a structured brief. Search, profiles, hire, and messaging never require a key.

Copy `.env.example` to `.env` only if you want a live provider.

## Matching

Matching is transparent and rule-based (skills, tools, specialization, availability, budget, verification). The UI states this clearly. It is not a trained model.

## Verification

Levels 1–5 (Profile, Tools, Workflow, Portfolio, Trusted) are product review signals. Tool names on profiles are creator-declared unless the corresponding badge is present.

## Future improvements

- Production auth and payments
- Versioned generation logs / model cards
- Agency seats and SSO
- Live video transcoding for portfolio files

See `DATA_MODEL.md` for entities and fields. See `/demo-guide` and `/presentation` in the running app for the judging path.
