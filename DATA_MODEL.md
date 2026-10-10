# CreatorsHub data model

Beginner-oriented map of the SQLite schema. All tables live in `instance/creatorshub.db`.

## User

Shared login record.

- email, password hash, name, role (`creator` | `brand`), avatar, location, demo flag

A user has **either** a CreatorProfile **or** a BrandProfile.

## Creator profile fields

- slug, headline, bio, workflow, years of experience
- availability (`Available` | `Limited` | `Booked`)
- languages
- hourly rate, project rate min/max
- commercial-use policy (text)
- content types (comma-separated)
- statistics: profile views, rating, review count, earnings YTD, completed projects
- verification_level (1–5) plus flags: profile, tools, workflow, portfolio, trusted

### Linked collections

- **Skills** — practice labels (Prompt Direction, Color Grading, …)
- **AI tools** — Midjourney, Runway, Sora, Firefly, ComfyUI, … (creator-declared)
- **Specializations** — AI Filmmaker, AI Animator, Generative Designer, …

## Portfolio project fields

- title, description, content type
- tools/models used, skills involved, workflow
- commercial-use status, license information
- aspect ratio, outcome
- cover image, verified flag, featured flag
- belongs to one creator

## Formats

Stored as strings on briefs and projects, not a separate table:

- format (MP4, TIFF, EXR, …)
- aspect ratio (16:9, 9:16, 4:5, 1:1, 21:9)
- resolution (4K, 6K, 300dpi, …)

## Commercial-use fields

- Creator: `commercial_use` policy text
- Portfolio: `commercial_use` + `license_info`
- Brief: `commercial_use` + `licensing` + revision count

## Verification

Product review tiers, not vendor certifications:

1. Profile Verified  
2. AI Tools Verified  
3. Workflow Verified  
4. Portfolio Verified  
5. Creator Trusted  

Individual project rows may also be `verified`.

## Brand profile

- company, industry, about, website, size
- owns many **Briefs** and **Projects**

## Brief fields

- campaign title, description, content type, creative goal
- style, visual direction, AI requirements
- required skills, preferred tools (M2M)
- format, aspect ratio, resolution, quantity
- deadline, budget min/max
- commercial-use, licensing, revisions
- deliverables, reference links, notes
- status, optional `ai_generated` flag

## Application fields

- creator, brief, cover message
- relevant portfolio items (M2M)
- proposed budget, estimated delivery
- status: Applied, Shortlisted, Interview, Accepted, Rejected, Completed

Accepting an application opens a **Project** at stage Hire.

## Relationships (summary)

```
User 1—1 CreatorProfile
User 1—1 BrandProfile
CreatorProfile *—* Skill, AITool, Specialization
CreatorProfile 1—* PortfolioProject
BrandProfile 1—* Brief
Brief *—* Skill, AITool
Brief 1—* Application *—* PortfolioProject
User *—* User via Connection, Follow, Message
Brand User 1—* SavedCreator → CreatorProfile
BrandProfile 1—* Project → CreatorProfile (optional Brief)
```

## Other entities

- **Connection** — requester, addressee, pending/accepted/rejected
- **Follow** — follower, followed
- **Message** — sender, recipient, body, optional portfolio/brief attachment
- **SavedCreator** — brand user + creator + saved date
- **Project** — stage in Discovery → Completed pipeline
- **Notification** — in-app events
- **Review** — brand → creator rating and text

Matching is computed at read time in `services/matching.py`; it is not stored as a model.
